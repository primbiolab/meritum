"""Pestaña «Modelos IRT»: curvas ICC/IIC de ítems e información del banco."""
from __future__ import annotations

import numpy as np
from PySide6.QtWidgets import QComboBox, QGroupBox, QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from meritum_cat.core.irt.models import apply_model, probability_3pl
from meritum_cat.core.irt.information import item_information
from meritum_cat.plotting import plot_icc_iic, plot_test_information
from meritum_cat.plotting.charts import THETA_GRID
from meritum_cat.gui.common import side_panel, Binder, FigurePanel, button, dspin, make_form, muted_label, param_row, tr
from meritum_cat.gui.state import AppState

MAX_CURVES = 7


def informative_region(a: float, b: float, c: float) -> tuple[float, float, float, float]:
    """Devuelve (theta de máxima información, información máxima, límite inferior, límite superior)."""
    info = item_information(THETA_GRID, a, b, c)
    k = int(np.argmax(info))
    imax = float(info[k])
    mask = info >= 0.5 * imax
    region = THETA_GRID[mask]
    return float(THETA_GRID[k]), imax, float(region.min()), float(region.max())


class IRTTab(QWidget):
    """Explorador interactivo de los modelos 1PL, 2PL y 3PL."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        self.pinned: list[dict] = []
        b = self.binder

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        params = QGroupBox()
        b.title(params, "irt.params_group")
        form = make_form()
        self.model = QComboBox()
        b.combo(self.model, [("1PL", "model.1PL"), ("2PL", "model.2PL"), ("3PL", "model.3PL")])
        self.model.setCurrentIndex(2)
        self.a = dspin(0.05, 4.0, 1.2, 0.05)
        self.b = dspin(-4.0, 4.0, 0.0, 0.1)
        self.c = dspin(0.0, 0.95, 0.2, 0.01)
        self.theta = dspin(-4.0, 4.0, 0.0, 0.1)
        param_row(form, b, "model", self.model)
        param_row(form, b, "a", self.a)
        param_row(form, b, "b", self.b)
        param_row(form, b, "c", self.c)
        param_row(form, b, "theta_eval", self.theta)
        self.model_note = muted_label()
        pl = QVBoxLayout(params)
        pl.addLayout(form)
        pl.addWidget(self.model_note)
        row = QHBoxLayout()
        self.btn_add = button()
        b.text(self.btn_add, "irt.add_curve")
        self.btn_add.clicked.connect(self.add_curve)
        self.btn_clear = button()
        b.text(self.btn_clear, "irt.clear")
        self.btn_clear.clicked.connect(self.clear_curves)
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_clear)
        pl.addLayout(row)
        note = muted_label()
        b.text(note, "irt.curves_note")
        pl.addWidget(note)
        ll.addWidget(params)

        res = QGroupBox()
        b.title(res, "irt.results_group")
        rl = QVBoxLayout(res)
        self.lbl_max = QLabel()
        self.lbl_region = QLabel()
        self.lbl_at = QLabel()
        for lab in (self.lbl_max, self.lbl_region, self.lbl_at):
            lab.setWordWrap(True)
            rl.addWidget(lab)
        ll.addWidget(res)
        ll.addStretch(1)
        scroll = side_panel(left, 370, 450)

        self.subtabs = QTabWidget()
        self.fig_item = FigurePanel()
        self.fig_item.default_name = "irt_icc_iic.png"
        test_page = QWidget()
        tl = QVBoxLayout(test_page)
        self.test_note = muted_label()
        b.text(self.test_note, "irt.test_note")
        self.fig_test = FigurePanel()
        self.fig_test.default_name = "bank_test_information.png"
        tl.addWidget(self.test_note)
        tl.addWidget(self.fig_test, 1)
        self.subtabs.addTab(self.fig_item, "")
        self.subtabs.addTab(test_page, "")
        b.tab(self.subtabs, self.fig_item, "irt.subtab_item")
        b.tab(self.subtabs, test_page, "irt.subtab_test")

        outer = QHBoxLayout(self)
        outer.addWidget(scroll)
        outer.addWidget(self.subtabs, 1)

        for w in (self.a, self.b, self.c, self.theta):
            w.valueChanged.connect(self.update_item)
        self.model.currentIndexChanged.connect(self.on_model_changed)
        state.bank_changed.connect(self.update_test)
        b.call(self.on_model_changed)

    # ------------------------------------------------------------------ lógica
    def effective_params(self) -> tuple[float, float, float]:
        model = self.model.currentData() or "3PL"
        a = 1.0 if model == "1PL" else self.a.value()
        c = self.c.value() if model == "3PL" else 0.0
        return a, self.b.value(), c

    def on_model_changed(self, *_args) -> None:
        model = self.model.currentData() or "3PL"
        self.a.setEnabled(model != "1PL")
        self.c.setEnabled(model == "3PL")
        self.model_note.setText(tr({"1PL": "irt.model_note_1pl", "2PL": "irt.model_note_2pl",
                                    "3PL": "irt.model_note_3pl"}[model]))
        self.update_item()
        self.update_test()

    def add_curve(self) -> None:
        a, b, c = self.effective_params()
        if len(self.pinned) >= MAX_CURVES - 1:
            self.pinned.pop(0)
        self.pinned.append({"a": a, "b": b, "c": c})
        self.update_item()

    def clear_curves(self) -> None:
        self.pinned.clear()
        self.update_item()

    def update_item(self, *_args) -> None:
        a, b, c = self.effective_params()
        theta_max, imax, lo, hi = informative_region(a, b, c)
        th = self.theta.value()
        info = float(item_information(th, a, b, c))
        p = float(probability_3pl(th, a, b, c))
        self.lbl_max.setText(tr("irt.max_info", imax=imax, theta=theta_max))
        self.lbl_region.setText(tr("irt.region", lo=lo, hi=hi))
        self.lbl_at.setText(tr("irt.info_at", theta=th, info=info, p=p))
        curves = [dict(cv, label=tr("irt.curve_label", **cv)) for cv in self.pinned]
        curves.append({"a": a, "b": b, "c": c,
                       "label": tr("irt.curve_label", a=a, b=b, c=c) + f" ({tr('irt.current_curve')})"})
        self.fig_item.draw(plot_icc_iic, curves, tr)

    def update_test(self, *_args) -> None:
        bank = self.state.bank
        if bank is None or bank.n_items == 0:
            self.fig_test.clear()
            return
        model = self.model.currentData() or "3PL"
        mb = apply_model(bank, model)
        self.fig_test.draw(plot_test_information, mb.a, mb.b, mb.c, tr, tr(f"model.{model}"))

    def retranslate(self) -> None:
        self.binder.retranslate()
        self.fig_item.retranslate()
        self.fig_test.retranslate()
