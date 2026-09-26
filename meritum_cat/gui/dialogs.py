"""Diálogos de la interfaz: edición de ítems, guía rápida, glosario y «Acerca de»."""
from __future__ import annotations

import platform

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QDialogButtonBox, QLabel, QLineEdit, QPlainTextEdit, QTextBrowser,
    QVBoxLayout, QHBoxLayout, QHeaderView,
)

from meritum_cat import (__app_name__, __app_subtitle__, __authors__, __license__,
                         __organization__, __version__)
from meritum_cat.models import Item
from meritum_cat.i18n import get_translator
from meritum_cat.i18n.strings import PARAM_HELP
from meritum_cat.gui.common import Binder, dspin, fill_table, make_form, make_table, param_row, tr, warn


def _buttons(dialog: QDialog, ok: bool = True) -> QDialogButtonBox:
    box = QDialogButtonBox((QDialogButtonBox.Ok | QDialogButtonBox.Cancel) if ok else QDialogButtonBox.Close)
    if ok:
        box.button(QDialogButtonBox.Ok).setText(tr("btn.ok"))
        box.button(QDialogButtonBox.Cancel).setText(tr("btn.cancel"))
        box.accepted.connect(dialog.accept)
        box.rejected.connect(dialog.reject)
    else:
        box.button(QDialogButtonBox.Close).setText(tr("btn.close"))
        box.rejected.connect(dialog.reject)
    return box


class ItemDialog(QDialog):
    """Formulario para crear o editar un ítem, con validación de parámetros."""

    def __init__(self, parent, item: Item | None, existing_ids: set[str]) -> None:
        super().__init__(parent)
        self.setMinimumWidth(560)
        self._original_id = item.item_id if item else None
        self._existing = existing_ids
        self.result_item: Item | None = None
        self.setWindowTitle(tr("dlg.item_edit", id=item.item_id) if item else tr("dlg.item_new"))
        b = Binder()
        form = make_form()

        self.item_id = QLineEdit(item.item_id if item else "")
        form.addRow(tr("field.item_id"), self.item_id)
        self.a = dspin(0.01, 10.0, item.a if item else 1.0, 0.05, 3)
        self.b = dspin(-10.0, 10.0, item.b if item else 0.0, 0.1, 3)
        self.c = dspin(0.0, 0.99, item.c if item else 0.0, 0.01, 3)
        param_row(form, b, "a", self.a)
        param_row(form, b, "b", self.b)
        param_row(form, b, "c", self.c)
        self.category = QLineEdit(item.category if item else "")
        self.subcategory = QLineEdit(item.subcategory if item else "")
        self.tags = QLineEdit(";".join(item.tags) if item else "")
        self.question = QPlainTextEdit(item.question if item else "")
        self.question.setFixedHeight(70)
        self.alternatives = QPlainTextEdit("\n".join(item.alternatives) if item else "")
        self.alternatives.setFixedHeight(70)
        self.correct = QLineEdit(item.correct if item else "")
        self.source = QLineEdit(item.source if item else "")
        self.notes = QLineEdit(item.notes if item else "")
        self.active = QCheckBox(tr("field.active"))
        self.active.setChecked(item.active if item else True)
        for key, widget in (("field.category", self.category), ("field.subcategory", self.subcategory),
                            ("field.tags", self.tags), ("field.question", self.question),
                            ("field.alternatives", self.alternatives), ("field.correct", self.correct),
                            ("field.source", self.source), ("field.notes", self.notes)):
            form.addRow(tr(key), widget)
        form.addRow("", self.active)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(_buttons(self))

    def accept(self) -> None:
        iid = self.item_id.text().strip()
        if not iid:
            warn(self, tr("msg.id_required"))
            return
        if iid != self._original_id and iid in self._existing:
            warn(self, tr("msg.id_duplicate", id=iid))
            return
        self.result_item = Item(
            item_id=iid, a=round(self.a.value(), 4), b=round(self.b.value(), 4), c=round(self.c.value(), 4),
            category=self.category.text().strip(), subcategory=self.subcategory.text().strip(),
            tags=tuple(t.strip() for t in self.tags.text().split(";") if t.strip()),
            question=self.question.toPlainText().strip(),
            alternatives=tuple(x.strip() for x in self.alternatives.toPlainText().splitlines() if x.strip()),
            correct=self.correct.text().strip(), source=self.source.text().strip(),
            active=self.active.isChecked(), notes=self.notes.text().strip(),
        )
        super().accept()


class QuickStartDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("qs.title"))
        self.resize(720, 520)
        text = QTextBrowser()
        text.setHtml(tr("qs.body"))
        lay = QVBoxLayout(self)
        lay.addWidget(text)
        lay.addWidget(_buttons(self, ok=False))


class GlossaryDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("gl.title"))
        self.resize(980, 600)
        t = get_translator()
        table = make_table(4)
        table.setHorizontalHeaderLabels([tr("gl.col_param"), tr("gl.col_symbol"), tr("gl.col_desc"),
                                         tr("gl.col_range")])
        rows = []
        for key in PARAM_HELP:
            p = t.param(key)
            rows.append([p["name"], p["symbol"] or "—", p["help"], p["range"] or "—"])
        fill_table(table, rows, align_right_from=99)
        table.setWordWrap(True)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.resizeRowsToContents()
        lay = QVBoxLayout(self)
        lay.addWidget(table)
        lay.addWidget(_buttons(self, ok=False))


class AboutDialog(QDialog):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setMinimumWidth(560)
        import matplotlib
        import numpy
        import scipy
        import PySide6
        components = (f"Python {platform.python_version()} · NumPy {numpy.__version__} · "
                      f"SciPy {scipy.__version__} · Matplotlib {matplotlib.__version__} · "
                      f"PySide6 (Qt for Python, LGPLv3) {PySide6.__version__}")
        html = (
            f"<h2 style='margin-bottom:0'>{__app_name__}</h2>"
            f"<p style='margin-top:2px'><b>{tr('about.version', v=__version__)}</b></p>"
            f"<p><i>{__app_subtitle__}</i></p>"
            f"<p>{tr('about.description')}</p>"
            f"<p>{tr('about.author', a=' · '.join(__authors__))}<br>{__organization__}<br>"
            f"{tr('about.license', l=__license__)}</p>"
            f"<p><b>{tr('about.components')}:</b><br>{components}</p>"
            f"<p style='color:#52514e'>{tr('about.data_note')}</p>"
        )
        label = QLabel(html)
        label.setTextFormat(Qt.RichText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        lay = QVBoxLayout(self)
        lay.addWidget(label)
        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(_buttons(self, ok=False))
        lay.addLayout(row)
