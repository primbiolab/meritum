"""Pestaña «Experimentos científicos»: los diez experimentos predefinidos y reproducibles."""
from __future__ import annotations

import json
import time

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QSplitter, QVBoxLayout, QWidget,
)

from meritum_cat import __version__
from meritum_cat.experiments import EXPERIMENTS
from meritum_cat.experiments.base import ExperimentResult
from meritum_cat.persistence import save_experiment_result_csv
from meritum_cat.plotting import plot_experiment
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.gui.common import (
    side_panel, fit_columns, Binder, FigurePanel, ask_save, button, error, fill_table, info, make_form, make_table,
    muted_label, param_row, spin, tr, unexpected_error, warn,
)
from meritum_cat.gui.state import AppState
from meritum_cat.gui.workers import TaskRunner

log = get_logger("gui.experiments")

# Experimentos que generan sus propios bancos (el factor estudiado es el banco o el modelo).
OWN_BANK = {"ability_recovery", "bank_size"}
TEXT_COLUMNS = {"model", "estimator", "selector", "test_type", "population"}


def display_value(column: str, value):
    """Traduce los valores categóricos de las tablas de resultados."""
    if column == "selector":
        return tr(f"sel.{value}")
    if column == "test_type":
        return tr(f"testtype.{value}")
    return value


def experiment_summary(result: ExperimentResult) -> str:
    params = dict(result.summary_params)
    if "reproducible" in params:
        params["reproducible"] = tr(f"exp.reproducible.{str(params['reproducible']).lower()}")
    return tr(f"exp.{result.key}.summary", **params)


class ExperimentsTab(QWidget):
    """Ejecución y análisis de experimentos científicos predefinidos."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        self.runner = TaskRunner(self)
        self.result: ExperimentResult | None = None
        self._t0 = 0.0
        self._status: tuple[str, dict] | None = None
        b = self.binder

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        lst = QGroupBox()
        b.title(lst, "exp.list_group")
        lstl = QVBoxLayout(lst)
        self.list = QListWidget()
        for key in EXPERIMENTS:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, key)
            self.list.addItem(item)
        self.list.setCurrentRow(0)
        lstl.addWidget(self.list)
        ll.addWidget(lst, 1)

        prm = QGroupBox()
        b.title(prm, "exp.params_group")
        form = make_form()
        self.n_examinees = spin(10, 100_000, 1000, 100)
        self.seed = spin(0, 2_147_483_647, 2026)
        param_row(form, b, "exp_examinees", self.n_examinees)
        param_row(form, b, "seed", self.seed)
        self.use_bank = QCheckBox()
        b.text(self.use_bank, "exp.use_bank")
        form.addRow(self.use_bank)
        prm.setLayout(form)
        ll.addWidget(prm)

        desc = QGroupBox()
        b.title(desc, "exp.description")
        dl = QVBoxLayout(desc)
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.bank_note = muted_label()
        dl.addWidget(self.desc_label)
        dl.addWidget(self.bank_note)
        ll.addWidget(desc)

        scroll = side_panel(left, 370, 450)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        row = QHBoxLayout()
        self.btn_run = button("primary")
        b.text(self.btn_run, "exp.run")
        self.btn_run.clicked.connect(self.run)
        self.btn_stop = button("danger")
        b.text(self.btn_stop, "exp.stop")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        self.btn_csv = button()
        b.text(self.btn_csv, "exp.export_csv")
        self.btn_csv.clicked.connect(self.export_csv)
        self.btn_json = button()
        b.text(self.btn_json, "exp.export_json")
        self.btn_json.clicked.connect(self.export_json)
        for w in (self.btn_run, self.btn_stop, self.btn_csv, self.btn_json):
            row.addWidget(w)
        row.addStretch(1)
        rl.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setFormat("%p %")
        self.status = muted_label()
        rl.addWidget(self.progress)
        rl.addWidget(self.status)

        self.table = make_table(1)
        interp_box = QGroupBox()
        b.title(interp_box, "exp.interpretation")
        il = QVBoxLayout(interp_box)
        self.interp = QLabel()
        self.interp.setWordWrap(True)
        il.addWidget(self.interp)
        top = QWidget()
        tl = QVBoxLayout(top)
        tl.setContentsMargins(0, 0, 0, 0)
        tl.addWidget(self.table, 1)
        tl.addWidget(interp_box)
        self.figure = FigurePanel(10, 4.8)
        split = QSplitter(Qt.Vertical)
        split.addWidget(top)
        split.addWidget(self.figure)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        self.table.setMinimumHeight(215)
        split.setSizes([330, 520])
        rl.addWidget(split, 1)

        outer = QHBoxLayout(self)
        outer.addWidget(scroll)
        outer.addWidget(right, 1)

        self.list.currentRowChanged.connect(self.on_selection)
        self.runner.progress.connect(self.on_progress)
        self.runner.finished.connect(self.on_finished)
        self.runner.failed.connect(self.on_failed)
        self.runner.cancelled.connect(self.on_cancelled)
        b.call(self.refresh_all)

    def _set_status(self, key: str | None, **params) -> None:
        """Guarda el estado como clave + parámetros para retraducirlo al cambiar de idioma."""
        self._status = (key, params) if key else None
        self.status.setText(tr(key, **params) if key else "")

    # ------------------------------------------------------------------ vista
    def current_key(self) -> str:
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item else next(iter(EXPERIMENTS))

    def select(self, key: str) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == key:
                self.list.setCurrentRow(i)
                return

    def on_selection(self, *_args) -> None:
        key = self.current_key()
        self.desc_label.setText(tr(f"exp.{key}.desc"))
        own = key in OWN_BANK
        self.bank_note.setText(tr("exp.bank_own") if own else "")
        self.use_bank.setEnabled(not own and not self.runner.running)

    def refresh_all(self) -> None:
        for i in range(self.list.count()):
            item = self.list.item(i)
            item.setText(tr(f"exp.{item.data(Qt.UserRole)}.title"))
        self.on_selection()
        if self._status is None and not self.runner.running and self.result is None:
            self._set_status("exp.status_idle")
        elif self._status is not None:
            self._set_status(self._status[0], **self._status[1])
        self._show_result()

    def _show_result(self) -> None:
        r = self.result
        self.figure.retranslate()
        if r is None:
            self.table.setColumnCount(1)
            self.table.setRowCount(0)
            self.table.setHorizontalHeaderLabels([""])
            self.interp.setText("")
            self.figure.clear()
            return
        self.table.setColumnCount(len(r.columns))
        self.table.setHorizontalHeaderLabels([tr(f"col.{c}") for c in r.columns])
        rows = [[display_value(c, row.get(c)) for c in r.columns] for row in r.rows]
        fill_table(self.table, rows, align_right_from=0)
        fit_columns(self.table)
        self.interp.setText(tr(f"exp.{r.key}.title") + " — " + experiment_summary(r))
        self.figure.default_name = f"experiment_{r.key}.png"
        self.figure.draw(plot_experiment, r, tr)

    # ------------------------------------------------------------------ ejecución
    def run(self, _checked: bool = False) -> bool:
        if self.runner.running:
            return False
        key = self.current_key()
        bank = None
        if self.use_bank.isChecked() and key not in OWN_BANK:
            bank = self.state.bank
            if bank is None or bank.n_items == 0:
                warn(self, tr("err.no_bank"))
                return False
            n_err = self.state.bank_error_count()
            if n_err:
                warn(self, tr("err.bank_invalid", n=n_err))
                return False
            if bank.n_items < 20:
                warn(self, tr("err.bank_too_small", n=bank.n_items, m=20))
                return False
        n, seed = self.n_examinees.value(), self.seed.value()
        log.info("Experimento iniciado: %s N=%d semilla=%d banco=%s", key, n, seed,
                 bank.name if bank else "sintético")
        self._t0 = time.perf_counter()
        self.progress.setValue(0)
        self._set_running(True)
        self._set_status("exp.status_running", pct=0, elapsed=0.0)
        self.runner.start(EXPERIMENTS[key], n_examinees=n, seed=seed, bank=bank)
        return True

    def stop(self) -> None:
        if self.runner.running:
            self.runner.cancel()
            self.btn_stop.setEnabled(False)

    def _set_running(self, running: bool) -> None:
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        self.btn_csv.setEnabled(not running)
        self.btn_json.setEnabled(not running)
        self.list.setEnabled(not running)
        self.use_bank.setEnabled(not running and self.current_key() not in OWN_BANK)

    def on_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)
        pct = int(round(100 * done / total)) if total else 0
        self._set_status("exp.status_running", pct=pct, elapsed=time.perf_counter() - self._t0)

    def on_finished(self, result: ExperimentResult) -> None:
        self._set_running(False)
        self.progress.setValue(self.progress.maximum())
        self.result = result
        self._set_status("exp.status_done", sec=result.elapsed_seconds)
        log.info("Experimento %s completado en %.2f s", result.key, result.elapsed_seconds)
        self._show_result()

    def on_failed(self, _detail: str) -> None:
        self._set_running(False)
        self._set_status(None)
        unexpected_error(self)

    def on_cancelled(self) -> None:
        self._set_running(False)
        self.progress.setValue(0)
        self._set_status("exp.status_cancelled")
        log.info("Experimento detenido por el usuario.")

    # ------------------------------------------------------------------ exportación
    def export_csv(self) -> None:
        if self.result is None:
            warn(self, tr("exp.need_result"))
            return
        path = ask_save(self, "filter.csv", f"experiment_{self.result.key}.csv")
        if path:
            self.export_csv_to(path)

    def export_csv_to(self, path: str, silent: bool = False) -> bool:
        try:
            save_experiment_result_csv(self.result, path)
        except OSError as exc:
            log.error("Exportación fallida: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return False
        log.info("Resultado de experimento exportado: %s", path)
        if not silent:
            info(self, tr("exp.result_exported", file=path))
        return True

    def export_json(self) -> None:
        if self.result is None:
            warn(self, tr("exp.need_result"))
            return
        path = ask_save(self, "filter.json", f"experiment_{self.result.key}.json")
        if not path:
            return
        payload = {"software": "Meritum_CAT", "meritum_cat_version": __version__, **self.result.to_dict()}
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2, default=str)
        except OSError as exc:
            log.error("Exportación fallida: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return
        log.info("Resultado de experimento exportado: %s", path)
        info(self, tr("exp.result_exported", file=path))

    def retranslate(self) -> None:
        self.binder.retranslate()
