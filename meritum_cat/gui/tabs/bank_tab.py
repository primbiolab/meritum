"""Pestaña «Banco de ítems»: generación, importación, edición, exportación y validación."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import (
    QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QSplitter, QTableView,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView,
)

from meritum_cat.datasets import generate_synthetic_bank
from meritum_cat.models import ItemBank
from meritum_cat.core.validation import validate_bank
from meritum_cat.persistence import BankIOError, load_bank, save_bank_csv, save_bank_json
from meritum_cat.utils.paths import resource_path
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.gui.common import (
    side_panel, fit_columns, Binder, ask_open, ask_save, button, confirm, error, fill_table, info, io_error_text,
    make_form, make_table, muted_label, param_row, spin, tr, warn,
)
from meritum_cat.gui.dialogs import ItemDialog
from meritum_cat.gui.state import AppState

log = get_logger("gui.bank")

COLUMNS = ["item_id", "a", "b", "c", "category", "subcategory", "tags", "active", "source",
           "question", "notes"]


def example_manifest() -> list[dict]:
    """Lista de bancos de ejemplo incluidos (resources/datasets/datasets.json)."""
    path = resource_path("resources/datasets/datasets.json")
    try:
        return json.loads(path.read_text(encoding="utf-8"))["datasets"]
    except (OSError, ValueError, KeyError):
        log.warning("No se encontró el manifiesto de bancos de ejemplo: %s", path)
        return []


class BankTableModel(QAbstractTableModel):
    """Modelo de tabla sobre la lista de ítems del banco (eficiente con bancos grandes)."""

    def __init__(self) -> None:
        super().__init__()
        self.bank: ItemBank | None = None

    def set_bank(self, bank: ItemBank | None) -> None:
        self.beginResetModel()
        self.bank = bank
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:  # noqa: N802 (API de Qt)
        return 0 if self.bank is None or parent.isValid() else len(self.bank.items)

    def columnCount(self, parent=QModelIndex()) -> int:  # noqa: N802
        return len(COLUMNS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or self.bank is None:
            return None
        item = self.bank.items[index.row()]
        col = COLUMNS[index.column()]
        value = getattr(item, col)
        if role == Qt.DisplayRole:
            if col in ("a", "b", "c"):
                return f"{value:.3f}"
            if col == "active":
                return tr("bool.yes") if value else tr("bool.no")
            if col == "tags":
                return "; ".join(value)
            if col == "question":
                return (value[:80] + "…") if len(value) > 80 else value
            return str(value)
        if role == Qt.EditRole:  # usado para ordenar numéricamente
            return value if col in ("a", "b", "c") else str(value)
        if role == Qt.TextAlignmentRole and col in ("a", "b", "c"):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):  # noqa: N802
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return tr(f"col.{COLUMNS[section]}")
        return None

    def retranslate(self) -> None:
        self.headerDataChanged.emit(Qt.Horizontal, 0, len(COLUMNS) - 1)
        if self.rowCount():
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, len(COLUMNS) - 1))


class BankTab(QWidget):
    """Gestión completa del banco de ítems."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        self.issues = []
        self.validated = False
        b = self.binder

        # --- panel izquierdo ---------------------------------------------------------
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)

        gen = QGroupBox()
        b.title(gen, "bank.gen_group")
        gf = make_form()
        self.gen_n = spin(1, 20000, 500, 50)
        self.gen_model = QComboBox()
        b.combo(self.gen_model, [("1PL", "model.1PL"), ("2PL", "model.2PL"), ("3PL", "model.3PL")])
        self.gen_model.setCurrentIndex(1)
        self.gen_seed = spin(0, 2_147_483_647, 2026)
        param_row(gf, b, "bank_size", self.gen_n)
        param_row(gf, b, "bank_model", self.gen_model)
        param_row(gf, b, "bank_seed", self.gen_seed)
        self.btn_generate = button("primary")
        b.text(self.btn_generate, "bank.generate")
        self.btn_generate.clicked.connect(self.generate)
        gl = QVBoxLayout(gen)
        gl.addLayout(gf)
        gl.addWidget(self.btn_generate)
        ll.addWidget(gen)

        ex = QGroupBox()
        b.title(ex, "bank.examples_group")
        el = QVBoxLayout(ex)
        self.examples = QComboBox()
        self.manifest = example_manifest()
        b.call(self._fill_examples)
        self.btn_example = button()
        b.text(self.btn_example, "bank.load_example")
        self.btn_example.clicked.connect(self.load_example)
        el.addWidget(self.examples)
        el.addWidget(self.btn_example)
        ll.addWidget(ex)

        io = QGroupBox()
        b.title(io, "bank.io_group")
        il = QGridLayout(io)
        self.btn_import = button()
        b.text(self.btn_import, "bank.import")
        self.btn_import.clicked.connect(self.import_bank)
        self.btn_export_csv = button()
        b.text(self.btn_export_csv, "bank.export_csv")
        self.btn_export_csv.clicked.connect(lambda: self.export_bank("csv"))
        self.btn_export_json = button()
        b.text(self.btn_export_json, "bank.export_json")
        self.btn_export_json.clicked.connect(lambda: self.export_bank("json"))
        fmt_help = muted_label()
        b.text(fmt_help, "bank.format_help")
        il.addWidget(self.btn_import, 0, 0, 1, 2)
        il.addWidget(self.btn_export_csv, 1, 0)
        il.addWidget(self.btn_export_json, 1, 1)
        il.addWidget(fmt_help, 2, 0, 1, 2)
        ll.addWidget(io)

        ed = QGroupBox()
        b.title(ed, "bank.edit_group")
        edl = QGridLayout(ed)
        self.btn_add = button()
        b.text(self.btn_add, "bank.add")
        self.btn_add.clicked.connect(self.add_item)
        self.btn_edit = button()
        b.text(self.btn_edit, "bank.edit")
        self.btn_edit.clicked.connect(self.edit_item)
        self.btn_dup = button()
        b.text(self.btn_dup, "bank.duplicate")
        self.btn_dup.clicked.connect(self.duplicate_items)
        self.btn_delete = button("danger")
        b.text(self.btn_delete, "bank.delete")
        self.btn_delete.clicked.connect(self.delete_items)
        self.btn_validate = button("primary")
        b.text(self.btn_validate, "bank.validate")
        self.btn_validate.clicked.connect(self.validate)
        edl.addWidget(self.btn_add, 0, 0)
        edl.addWidget(self.btn_edit, 0, 1)
        edl.addWidget(self.btn_dup, 1, 0)
        edl.addWidget(self.btn_delete, 1, 1)
        edl.addWidget(self.btn_validate, 2, 0, 1, 2)
        hint = muted_label()
        b.text(hint, "bank.edit_hint")
        edl.addWidget(hint, 3, 0, 1, 2)
        ll.addWidget(ed)
        ll.addStretch(1)

        scroll = side_panel(left, 370, 450)

        # --- panel derecho -----------------------------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        self.summary.setProperty("role", "metric")
        rl.addWidget(self.summary)

        self.model = BankTableModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortRole(Qt.EditRole)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.doubleClicked.connect(lambda _: self.edit_item())

        val = QGroupBox()
        b.title(val, "val.title")
        vl = QVBoxLayout(val)
        self.val_summary = QLabel()
        self.val_summary.setWordWrap(True)
        self.val_table = make_table(4)
        b.headers(self.val_table, ["val.col_severity", "val.col_item", "val.col_field", "val.col_message"])
        vl.addWidget(self.val_summary)
        vl.addWidget(self.val_table)

        split = QSplitter(Qt.Vertical)
        split.addWidget(self.table)
        split.addWidget(val)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        rl.addWidget(split, 1)

        outer = QHBoxLayout(self)
        outer.addWidget(scroll)
        outer.addWidget(right, 1)

        state.bank_changed.connect(self.on_bank_changed)
        b.call(self._retranslate_dynamic)

    # ------------------------------------------------------------------ utilidades
    def _fill_examples(self) -> None:
        current = self.examples.currentIndex()
        self.examples.clear()
        for ds in self.manifest:
            self.examples.addItem(tr("bank.example_item", n=ds["n_items"], model=ds["model"]), ds["file"])
        if current >= 0:
            self.examples.setCurrentIndex(current)

    def _retranslate_dynamic(self) -> None:
        self.model.retranslate()
        self._update_summary()
        self._show_issues()

    def retranslate(self) -> None:
        self.binder.retranslate()

    def _update_summary(self) -> None:
        bank = self.state.bank
        if bank is None:
            self.summary.setText(tr("bank.empty"))
            return
        a = float(np.mean(bank.a)) if bank.n_items else 0.0
        bb = float(np.mean(bank.b)) if bank.n_items else 0.0
        c = float(np.mean(bank.c)) if bank.n_items else 0.0
        self.summary.setText(tr("bank.summary", name=bank.name, n=bank.n_total, active=bank.n_items,
                                ncat=len(bank.categories), a=a, b=bb, c=c))

    def on_bank_changed(self) -> None:
        self.model.set_bank(self.state.bank)
        self.table.resizeColumnsToContents()
        for col in (COLUMNS.index("question"), COLUMNS.index("notes")):
            self.table.setColumnWidth(col, 260)
        self._update_summary()
        self.validate(silent=True)

    def _selected_rows(self) -> list[int]:
        rows = {self.proxy.mapToSource(ix).row() for ix in self.table.selectionModel().selectedRows()}
        return sorted(rows)

    def _existing_ids(self) -> set[str]:
        bank = self.state.bank
        return {it.item_id for it in bank.items} if bank else set()

    def _ensure_bank(self) -> ItemBank:
        if self.state.bank is None:
            self.state.set_bank(ItemBank(items=[], name="new_bank"))
        return self.state.bank

    # ------------------------------------------------------------------ acciones
    def generate(self) -> None:
        n, model, seed = self.gen_n.value(), self.gen_model.currentData(), self.gen_seed.value()
        bank = generate_synthetic_bank(n, model=model, seed=seed, name=f"synthetic_{model}_{n}_seed{seed}")
        self.state.set_bank(bank)
        log.info("Banco sintético generado: n=%d modelo=%s semilla=%d", n, model, seed)
        info(self, tr("msg.bank_generated", n=n, model=model, seed=seed))

    def load_example(self, _checked: bool = False, silent: bool = False) -> None:
        file = self.examples.currentData()
        if not file:
            return
        path = resource_path(f"resources/datasets/{file}")
        try:
            bank = load_bank(path)
        except BankIOError as exc:
            log.error("No se pudo cargar el banco de ejemplo %s: %s", path, exc)
            error(self, io_error_text(exc))
            return
        self.state.set_bank(bank)
        log.info("Banco de ejemplo cargado: %s", path.name)
        if not silent:
            info(self, tr("msg.bank_imported", n=bank.n_total, file=path.name))

    def import_bank(self) -> None:
        path = ask_open(self, "filter.bank")
        if not path:
            return
        self.import_path(path)

    def import_path(self, path: str, silent: bool = False) -> bool:
        try:
            bank = load_bank(path)
        except BankIOError as exc:
            log.warning("Importación fallida (%s): %s", path, exc)
            error(self, io_error_text(exc))
            return False
        self.state.set_bank(bank)
        log.info("Banco importado: %s (%d ítems)", path, bank.n_total)
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        if not silent:
            if errors or warnings:
                warn(self, tr("msg.bank_import_warnings", errors=errors, warnings=warnings))
            else:
                info(self, tr("msg.bank_imported", n=bank.n_total, file=Path(path).name))
        return True

    def export_bank(self, kind: str) -> None:
        bank = self.state.bank
        if bank is None:
            warn(self, tr("err.no_bank"))
            return
        path = ask_save(self, "filter.csv" if kind == "csv" else "filter.json", f"{bank.name}.{kind}")
        if not path:
            return
        self.export_to(path, kind)

    def export_to(self, path: str, kind: str, silent: bool = False) -> bool:
        bank = self.state.bank
        try:
            (save_bank_csv if kind == "csv" else save_bank_json)(bank, path)
        except OSError as exc:
            log.error("Exportación fallida (%s): %s", path, exc)
            error(self, tr("err.write_failed", file=path))
            return False
        log.info("Banco exportado: %s", path)
        if not silent:
            info(self, tr("msg.bank_exported", file=path))
        return True

    def add_item(self) -> None:
        dlg = ItemDialog(self, None, self._existing_ids())
        try:
            if dlg.exec() and dlg.result_item is not None:
                bank = self._ensure_bank()
                bank.items.append(dlg.result_item)
                self.state.notify_bank_edited()
                log.info("Ítem agregado: %s", dlg.result_item.item_id)
        finally:
            dlg.deleteLater()

    def edit_item(self) -> None:
        rows = self._selected_rows()
        if not rows:
            warn(self, tr("msg.select_item"))
            return
        bank = self.state.bank
        row = rows[0]
        dlg = ItemDialog(self, bank.items[row], self._existing_ids())
        try:
            if dlg.exec() and dlg.result_item is not None:
                bank.items[row] = dlg.result_item
                self.state.notify_bank_edited()
                log.info("Ítem editado: %s", dlg.result_item.item_id)
        finally:
            dlg.deleteLater()

    def duplicate_items(self) -> None:
        rows = self._selected_rows()
        if not rows:
            warn(self, tr("msg.select_item"))
            return
        from dataclasses import replace
        bank = self.state.bank
        ids = self._existing_ids()
        for row in rows:
            base = bank.items[row].item_id
            k = 1
            new_id = f"{base}_copy"
            while new_id in ids:
                k += 1
                new_id = f"{base}_copy{k}"
            ids.add(new_id)
            bank.items.append(replace(bank.items[row], item_id=new_id))
        self.state.notify_bank_edited()
        log.info("Ítems duplicados: %d", len(rows))

    def delete_items(self) -> None:
        rows = self._selected_rows()
        if not rows:
            warn(self, tr("msg.select_item"))
            return
        if not confirm(self, tr("msg.confirm_delete", n=len(rows))):
            return
        bank = self.state.bank
        for row in sorted(rows, reverse=True):
            del bank.items[row]
        self.state.notify_bank_edited()
        log.info("Ítems eliminados: %d", len(rows))

    def validate(self, _checked: bool = False, silent: bool = False) -> None:
        bank = self.state.bank
        self.issues = validate_bank(bank) if bank is not None else []
        self.validated = bank is not None
        self._show_issues()
        if bank is not None and not silent:
            log.info("Validación del banco: %d hallazgos", len(self.issues))

    def _show_issues(self) -> None:
        if not self.validated:
            self.val_summary.setText(tr("val.not_run"))
            self.val_table.setRowCount(0)
            return
        errors = sum(1 for i in self.issues if i.severity == "error")
        warnings = sum(1 for i in self.issues if i.severity == "warning")
        self.val_summary.setText(tr("val.ok") if not self.issues else
                                 tr("val.summary", errors=errors, warnings=warnings))
        rows = [[tr(f"severity.{i.severity}"), i.item_id, i.field, tr(f"val.{i.code}", **i.params)]
                for i in self.issues[:5000]]
        fill_table(self.val_table, rows, align_right_from=99)
        fit_columns(self.val_table)
