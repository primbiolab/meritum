"""
Componentes compartidos de la interfaz.

* :class:`Binder` registra textos traducibles de widgets y los reaplica al
  cambiar de idioma (retraducción en vivo, sin reiniciar la aplicación).
* :func:`param_row` crea la fila de un parámetro científico: nombre descriptivo
  con símbolo, ayuda contextual (tooltip) y botón «?» con la ayuda completa.
* :class:`FigurePanel` incrusta una figura de matplotlib con su barra de
  navegación y exportación.
* Utilidades de mensajes y diálogos de archivo traducidos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget, QHeaderView, QSizePolicy,
)

from meritum_cat.i18n import get_translator
from meritum_cat.plotting import new_figure
from meritum_cat.utils.logging_setup import get_logger

log = get_logger("gui")


def tr(key: str, **kwargs: Any) -> str:
    return get_translator().t(key, **kwargs)


class Binder:
    """Registro de actualizaciones de texto a reaplicar al cambiar el idioma."""

    def __init__(self) -> None:
        self._updaters: list[Callable[[], None]] = []

    def call(self, fn: Callable[[], None]) -> None:
        self._updaters.append(fn)
        fn()

    def text(self, widget, key: str, **kwargs: Any) -> None:
        self.call(lambda: widget.setText(tr(key, **kwargs)))

    def title(self, widget, key: str) -> None:
        self.call(lambda: widget.setTitle(tr(key)))

    def tooltip(self, widget, key: str) -> None:
        self.call(lambda: widget.setToolTip(tr(key)))

    def tab(self, tabs, page: QWidget, key: str) -> None:
        self.call(lambda: tabs.setTabText(tabs.indexOf(page), tr(key)))

    def combo(self, combo: QComboBox, items: list[tuple[Any, str]]) -> None:
        """Rellena un combo con (dato, clave) conservando la selección al retraducir."""
        combo.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        combo.setMinimumContentsLength(12)

        def update() -> None:
            current = combo.currentData()
            combo.blockSignals(True)
            combo.clear()
            for data, key in items:
                combo.addItem(tr(key), data)
            idx = combo.findData(current) if current is not None else 0
            combo.setCurrentIndex(max(idx, 0))
            combo.blockSignals(False)
        self.call(update)

    def headers(self, table: QTableWidget, keys: list[str]) -> None:
        self.call(lambda: table.setHorizontalHeaderLabels([tr(k) for k in keys]))

    def retranslate(self) -> None:
        for fn in self._updaters:
            fn()


def show_param_help(parent: QWidget, key: str) -> None:
    t = get_translator()
    p = t.param(key)
    body = f"<b>{p['name']}</b>"
    if p["symbol"]:
        body += f" &nbsp;({tr('help.symbol')}: <b>{p['symbol']}</b>)"
    body += f"<p>{p['help']}</p>"
    if p["range"]:
        body += f"<p><b>{tr('help.valid_range')}:</b> {p['range']}</p>"
    box = QMessageBox(parent)
    box.setWindowTitle(tr("help.title", name=p["name"]))
    box.setTextFormat(Qt.RichText)
    box.setText(body)
    box.setIcon(QMessageBox.Information)
    box.setStandardButtons(QMessageBox.Ok)
    box.button(QMessageBox.Ok).setText(tr("btn.close"))
    box.exec()
    box.deleteLater()  # libera el diálogo (evita acumular ventanas ocultas)


class ParamLabel(QWidget):
    """Etiqueta de parámetro: «Nombre descriptivo (símbolo)» + botón de ayuda «?»."""

    def __init__(self, key: str, binder: Binder, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.key = key
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.label = QLabel()
        self.label.setWordWrap(True)
        self.label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.help_button = QToolButton()
        self.help_button.setText("?")
        self.help_button.setProperty("kind", "help")
        self.help_button.setCursor(Qt.PointingHandCursor)
        self.help_button.clicked.connect(lambda: show_param_help(self, key))
        lay.addWidget(self.label, 1)
        lay.addWidget(self.help_button, 0, Qt.AlignTop)
        t = get_translator()
        binder.call(lambda: (self.label.setText(t.param_label(key)),
                             self.label.setToolTip(t.param_tooltip(key)),
                             self.help_button.setToolTip(tr("help.button_tooltip"))))


def param_row(form: QFormLayout, binder: Binder, key: str, widget: QWidget) -> ParamLabel:
    """Añade a un QFormLayout la fila de un parámetro científico con ayuda contextual."""
    label = ParamLabel(key, binder)
    t = get_translator()
    binder.call(lambda: widget.setToolTip(t.param_tooltip(key)))
    if form.rowWrapPolicy() == QFormLayout.WrapAllRows:
        # Etiqueta y campo en filas de ancho completo: el nombre nunca se recorta.
        label.setContentsMargins(0, 4, 0, 0)
        form.addRow(label)
        form.addRow(widget)
    else:
        form.addRow(label, widget)
    return label


def make_form(stacked: bool = True) -> QFormLayout:
    """
    Formulario de parámetros. Con ``stacked`` la etiqueta descriptiva va encima
    del campo, de modo que los nombres largos nunca se recortan.
    """
    form = QFormLayout()
    form.setLabelAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
    if stacked:
        form.setRowWrapPolicy(QFormLayout.WrapAllRows)
    form.setHorizontalSpacing(10)
    form.setVerticalSpacing(4)
    return form


def side_panel(content: QWidget, min_width: int = 360, max_width: int = 440):
    """Panel lateral desplazable verticalmente (sin desplazamiento horizontal)."""
    from PySide6.QtWidgets import QScrollArea
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setWidget(content)
    scroll.setMinimumWidth(min_width)
    scroll.setMaximumWidth(max_width)
    return scroll


def spin(minimum: int, maximum: int, value: int, step: int = 1) -> QSpinBox:
    w = QSpinBox()
    w.setRange(minimum, maximum)
    w.setValue(value)
    w.setSingleStep(step)
    w.setGroupSeparatorShown(False)
    w.setAccelerated(True)
    w.setMinimumWidth(90)
    return w


def dspin(minimum: float, maximum: float, value: float, step: float = 0.1,
          decimals: int = 2) -> QDoubleSpinBox:
    from PySide6.QtCore import QLocale
    w = QDoubleSpinBox()
    w.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))  # punto decimal en toda la app
    w.setDecimals(decimals)
    w.setRange(minimum, maximum)
    w.setValue(value)
    w.setSingleStep(step)
    w.setCorrectionMode(QAbstractSpinBox.CorrectToNearestValue)
    w.setMinimumWidth(90)
    return w


def button(kind: str | None = None) -> QPushButton:
    b = QPushButton()
    if kind:
        b.setProperty("kind", kind)
    b.setCursor(Qt.PointingHandCursor)
    return b


def muted_label(role: str = "muted") -> QLabel:
    lab = QLabel()
    lab.setWordWrap(True)
    lab.setProperty("role", role)
    return lab


def fmt(value: Any, decimals: int = 3) -> str:
    """Formato numérico uniforme (punto decimal) para tablas y etiquetas."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return tr("bool.yes") if value else tr("bool.no")
    if isinstance(value, int):
        return str(value)
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if f != f:  # NaN
        return "—"
    if f.is_integer() and abs(f) < 1e9 and decimals == 0:
        return str(int(f))
    return f"{f:.{decimals}f}"


def fill_table(table: QTableWidget, rows: list[list[Any]], align_right_from: int = 1) -> None:
    table.setRowCount(len(rows))
    for i, row in enumerate(rows):
        for j, value in enumerate(row):
            item = QTableWidgetItem(value if isinstance(value, str) else fmt(value))
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if j >= align_right_from and not isinstance(value, str):
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            table.setItem(i, j, item)


def make_table(columns: int, stretch_last: bool = True) -> QTableWidget:
    t = QTableWidget(0, columns)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setVisible(False)
    t.setSelectionBehavior(QTableWidget.SelectRows)
    t.setEditTriggers(QTableWidget.NoEditTriggers)
    t.horizontalHeader().setStretchLastSection(stretch_last)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
    t.horizontalHeader().setMinimumSectionSize(48)
    t.setWordWrap(False)
    return t


def fit_columns(table: QTableWidget) -> None:
    """Ajusta el ancho de las columnas al contenido y a los encabezados (sin recortes)."""
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
    header.setStretchLastSection(True)


class TranslatedToolbar(NavigationToolbar2QT):
    """
    Barra de navegación de matplotlib reducida y traducida.

    Conserva inicio, atrás, adelante, desplazar y zoom. Se omiten los diálogos
    de configuración y guardado de matplotlib (solo en inglés); la exportación
    se ofrece con el botón traducido «Exportar figura…» de cada panel.
    """

    toolitems = [t for t in NavigationToolbar2QT.toolitems
                 if t[0] in ("Home", "Back", "Forward", "Pan", "Zoom")]
    _TIPS = {"home": "nav.home", "back": "nav.back", "forward": "nav.forward",
             "pan": "nav.pan", "zoom": "nav.zoom"}

    def __init__(self, canvas, parent) -> None:
        super().__init__(canvas, parent, coordinates=False)
        self.retranslate()

    def retranslate(self) -> None:
        for name, action in getattr(self, "_actions", {}).items():
            if name in self._TIPS:
                action.setToolTip(tr(self._TIPS[name]))
                action.setText(tr(self._TIPS[name]))


class FigurePanel(QWidget):
    """Figura de matplotlib incrustada, con barra de herramientas (zoom, desplazamiento, guardar)."""

    def __init__(self, width: float = 9.0, height: float = 5.5, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = new_figure(width, height)
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setMinimumHeight(260)
        self.toolbar = TranslatedToolbar(self.canvas, self)
        self.export_button = button()
        self.export_button.clicked.connect(self._export)
        top = QHBoxLayout()
        top.setContentsMargins(0, 0, 0, 0)
        top.addWidget(self.toolbar)
        top.addStretch(1)
        top.addWidget(self.export_button)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addLayout(top)
        lay.addWidget(self.canvas, 1)
        self.default_name = "figure.png"
        self.retranslate()

    def retranslate(self) -> None:
        self.toolbar.retranslate()
        self.export_button.setText(tr("btn.export_figure"))

    def _export(self) -> None:
        path = ask_save(self, "filter.png", self.default_name)
        if not path:
            return
        try:
            self.save(path)
        except OSError as exc:
            log.error("No se pudo exportar la figura: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return
        log.info("Figura exportada: %s", path)
        info(self, tr("msg.figure_exported", file=path))

    def draw(self, plot_fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        try:
            plot_fn(self.figure, *args, **kwargs)
        except Exception:  # noqa: BLE001 - una figura fallida no debe cerrar la aplicación
            log.exception("Error al dibujar la figura %s", getattr(plot_fn, "__name__", plot_fn))
            self.figure.clear()
        self.canvas.draw_idle()

    def clear(self) -> None:
        self.figure.clear()
        self.canvas.draw_idle()

    def save(self, path: str | Path, dpi: int = 200) -> None:
        self.figure.savefig(path, dpi=dpi, facecolor=self.figure.get_facecolor(), bbox_inches="tight")


# ----------------------------------------------------------------------------- mensajes

def _box(parent, icon, title_key: str, text: str) -> None:
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(tr(title_key))
    box.setText(text)
    box.setStandardButtons(QMessageBox.Ok)
    box.button(QMessageBox.Ok).setText(tr("btn.ok"))
    box.exec()
    box.deleteLater()


def info(parent, text: str) -> None:
    _box(parent, QMessageBox.Information, "dlg.info", text)


def warn(parent, text: str) -> None:
    _box(parent, QMessageBox.Warning, "dlg.warning", text)


def error(parent, text: str) -> None:
    _box(parent, QMessageBox.Critical, "dlg.error", text)


def unexpected_error(parent) -> None:
    from meritum_cat.utils.paths import cache_dir
    error(parent, tr("err.unexpected", log=str(cache_dir() / "logs" / "meritum_cat.log")))


def confirm(parent, text: str) -> bool:
    box = QMessageBox(parent)
    box.setIcon(QMessageBox.Question)
    box.setWindowTitle(tr("dlg.confirm"))
    box.setText(text)
    box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    box.button(QMessageBox.Yes).setText(tr("btn.yes"))
    box.button(QMessageBox.No).setText(tr("btn.no"))
    box.setDefaultButton(QMessageBox.No)
    answer = box.exec() == QMessageBox.Yes
    box.deleteLater()
    return answer


def ask_open(parent, filter_key: str) -> str | None:
    path, _ = QFileDialog.getOpenFileName(parent, "", str(Path.home()), tr(filter_key))
    return path or None


def ask_save(parent, filter_key: str, default_name: str) -> str | None:
    path, _ = QFileDialog.getSaveFileName(parent, "", str(Path.home() / default_name), tr(filter_key))
    return path or None


def ask_folder(parent) -> str | None:
    path = QFileDialog.getExistingDirectory(parent, tr("dlg.choose_folder"), str(Path.home()))
    return path or None


def io_error_text(exc: Exception) -> str:
    """Traduce un error de E/S con código a un mensaje amigable."""
    code = getattr(exc, "code", None)
    if code is not None:
        return tr(f"ioerr.{code}", **getattr(exc, "params", {}))
    if isinstance(exc, OSError):
        return tr("err.write_failed", file=getattr(exc, "filename", "") or "")
    return str(exc)
