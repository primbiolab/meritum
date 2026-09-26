"""Pestaña «Test adaptativo (CAT)»: sesión CAT paso a paso con visualización en vivo."""
from __future__ import annotations

import csv

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QSplitter,
    QVBoxLayout, QWidget,
)

from meritum_cat.core.balancing.content import ContentBalancer
from meritum_cat.core.estimation.base import make_estimator
from meritum_cat.core.irt.models import apply_model
from meritum_cat.core.selection.base import make_selector, SelectionMethod
from meritum_cat.core.simulation.cat import CATConfig
from meritum_cat.core.simulation.session import CATSession
from meritum_cat.core.stopping.rules import make_stopping_rule
from meritum_cat.plotting import plot_cat_trace
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.gui.common import (
    side_panel, fit_columns, Binder, FigurePanel, ask_save, button, dspin, error, fill_table, info, make_form, make_table,
    muted_label, param_row, spin, tr, warn,
)
from meritum_cat.gui.config_widgets import AlgorithmControls, StoppingControls
from meritum_cat.gui.state import AppState

log = get_logger("gui.cat")

STATE_KEYS = ["cat.theta0", "cat.theta_now", "cat.se_now", "cat.n_items", "cat.info",
              "cat.correct", "cat.incorrect", "cat.status"]


class CATTab(QWidget):
    """Administración interactiva de un CAT con un examinado."""

    def __init__(self, state: AppState) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        self.session: CATSession | None = None
        b = self.binder

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        help_lbl = muted_label("note")
        b.text(help_lbl, "cat.help")
        ll.addWidget(help_lbl)

        cfg = QGroupBox()
        b.title(cfg, "cat.config_group")
        form = make_form()
        self.algo = AlgorithmControls(b, include_sh=False)
        self.algo.add_model(form, b)
        self.algo.add_estimation(form, b)
        self.algo.add_selection(form, b)
        self.initial_theta = dspin(-4.0, 4.0, 0.0, 0.1)
        param_row(form, b, "initial_theta", self.initial_theta)
        self.balancing = QCheckBox()
        b.text(self.balancing, "mc.content_balancing")
        param_row(form, b, "content_balancing", self.balancing)
        cfg.setLayout(form)
        ll.addWidget(cfg)

        stop = QGroupBox()
        b.title(stop, "cat.stop_group")
        sform = make_form()
        self.stopping = StoppingControls()
        self.stopping.add(sform, b)
        stop.setLayout(sform)
        ll.addWidget(stop)

        ex = QGroupBox()
        b.title(ex, "cat.examinee_group")
        eform = make_form()
        self.mode = QComboBox()
        b.combo(self.mode, [("sim", "cat.mode_sim"), ("manual", "cat.mode_manual")])
        mode_label = QLabel()
        b.text(mode_label, "cat.mode")
        eform.addRow(mode_label, self.mode)
        self.theta_true = dspin(-4.0, 4.0, 1.0, 0.1)
        param_row(eform, b, "theta_true", self.theta_true)
        self.seed = spin(0, 2_147_483_647, 12345)
        param_row(eform, b, "seed", self.seed)
        ex.setLayout(eform)
        ll.addWidget(ex)
        ll.addStretch(1)
        scroll = side_panel(left, 370, 450)

        # --- controles y estado ----------------------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        btns = QHBoxLayout()
        self.btn_start = button("primary")
        b.text(self.btn_start, "cat.start")
        self.btn_next = button()
        b.text(self.btn_next, "cat.next")
        self.btn_correct = button()
        b.text(self.btn_correct, "cat.answer_correct")
        self.btn_incorrect = button()
        b.text(self.btn_incorrect, "cat.answer_incorrect")
        self.btn_run = button()
        b.text(self.btn_run, "cat.run_all")
        self.btn_reset = button("danger")
        b.text(self.btn_reset, "cat.reset")
        self.btn_export = button()
        b.text(self.btn_export, "cat.export_trace")
        for w in (self.btn_start, self.btn_next, self.btn_correct, self.btn_incorrect, self.btn_run,
                  self.btn_reset, self.btn_export):
            btns.addWidget(w)
        btns.addStretch(1)
        rl.addLayout(btns)

        st = QGroupBox()
        b.title(st, "cat.state_group")
        grid = QGridLayout(st)
        self.state_labels: dict[str, QLabel] = {}
        for i, key in enumerate(STATE_KEYS):
            name = QLabel()
            b.text(name, key)
            name.setProperty("role", "muted")
            val = QLabel("—")
            val.setProperty("role", "metric")
            self.state_labels[key] = val
            grid.addWidget(name, (i // 4) * 2, i % 4)
            grid.addWidget(val, (i // 4) * 2 + 1, i % 4)
        self.pending_label = muted_label()
        grid.addWidget(self.pending_label, 4, 0, 1, 4)
        rl.addWidget(st)

        self.figure = FigurePanel(9, 6)
        self.figure.default_name = "cat_session_trace.png"
        self.table = make_table(9)
        b.headers(self.table, ["col.step", "col.item_id", "col.a", "col.b", "col.c", "col.response",
                               "col.theta_after", "col.se_after", "col.info_after"])
        fit_columns(self.table)
        split = QSplitter(Qt.Vertical)
        split.addWidget(self.figure)
        split.addWidget(self.table)
        split.setStretchFactor(0, 3)
        split.setStretchFactor(1, 1)
        rl.addWidget(split, 1)

        outer = QHBoxLayout(self)
        outer.addWidget(scroll)
        outer.addWidget(right, 1)

        self.btn_start.clicked.connect(self.start)
        self.btn_next.clicked.connect(self.next_simulated)
        self.btn_correct.clicked.connect(lambda: self.answer(1))
        self.btn_incorrect.clicked.connect(lambda: self.answer(0))
        self.btn_run.clicked.connect(self.run_all)
        self.btn_reset.clicked.connect(self.reset)
        self.btn_export.clicked.connect(self.export_trace)
        self.mode.currentIndexChanged.connect(self._update_buttons)
        b.call(self.refresh_view)

    # ------------------------------------------------------------------ sesión
    def _build_session(self) -> CATSession | None:
        bank = self.state.bank
        if bank is None or bank.n_items == 0:
            warn(self, tr("err.no_bank"))
            return None
        n_err = self.state.bank_error_count()
        if n_err:
            warn(self, tr("err.bank_invalid", n=n_err))
            return None
        stop = self.stopping.values()
        if stop["max_items"] is None and stop["se_threshold"] is None and stop["target_information"] is None:
            warn(self, tr("err.invalid_input") + "\n• " + tr("valerr.need_stopping_rule"))
            return None
        model = self.algo.model.currentData()
        mb = apply_model(bank, model)
        est_method = self.algo.estimator.currentData()
        kwargs = {}
        if est_method in ("MAP", "EAP"):
            kwargs = {"prior_mean": self.algo.prior_mean.value(), "prior_sd": self.algo.prior_sd.value()}
        estimator = make_estimator(est_method, **kwargs)
        sel = self.algo.selector.currentData()
        selector = (make_selector(sel, bin_size=self.algo.randomesque_bin.value())
                    if sel == SelectionMethod.RANDOMESQUE.value else make_selector(sel))
        stopping = make_stopping_rule(**stop)
        balancer = None
        if self.balancing.isChecked() and mb.categories:
            balancer = ContentBalancer([it.category for it in mb.active_items],
                                       {c: 1.0 for c in mb.categories})
        config = CATConfig(estimator=estimator, selector=selector, stopping_rule=stopping,
                           initial_theta=self.initial_theta.value(), balancer=balancer)
        theta_true = self.theta_true.value() if self.mode.currentData() == "sim" else None
        log.info("Sesión CAT: modelo=%s estimador=%s selección=%s semilla=%d θ*=%s",
                 model, est_method, sel, self.seed.value(), theta_true)
        return CATSession(mb, config, np.random.default_rng(self.seed.value()), theta_true=theta_true)

    def start(self) -> None:
        try:
            self.session = self._build_session()
        except ValueError as exc:
            log.error("No se pudo iniciar la sesión CAT: %s", exc)
            error(self, str(exc))
            self.session = None
        if self.session is not None and self.mode.currentData() == "manual":
            self.session.next_item()
        self.refresh_view()

    def next_simulated(self) -> None:
        if self.session is None or self.session.finished:
            return
        self.session.step()
        self.refresh_view()

    def answer(self, response: int) -> None:
        s = self.session
        if s is None or s.finished or s.pending is None:
            return
        s.answer(response)
        if not s.finished:
            s.next_item()
        self.refresh_view()

    def run_all(self) -> None:
        s = self.session
        if s is None or s.finished or self.mode.currentData() != "sim":
            return
        s.run_to_end()
        self.refresh_view()

    def reset(self) -> None:
        self.session = None
        self.refresh_view()

    # ------------------------------------------------------------------ vista
    def _update_buttons(self, *_args) -> None:
        s = self.session
        active = s is not None and not s.finished
        sim = self.mode.currentData() == "sim"
        self.btn_next.setEnabled(active and sim)
        self.btn_run.setEnabled(active and sim)
        self.btn_correct.setEnabled(active and not sim and s is not None and s.pending is not None)
        self.btn_incorrect.setEnabled(active and not sim and s is not None and s.pending is not None)
        self.btn_export.setEnabled(s is not None and len(s.administered) > 0)
        self.btn_reset.setEnabled(s is not None)
        self.mode.setEnabled(s is None)

    def refresh_view(self) -> None:
        s = self.session
        L = self.state_labels
        if s is None:
            for key in STATE_KEYS:
                L[key].setText("—")
            L["cat.status"].setText(tr("cat.not_started"))
            self.pending_label.setText("")
            self.table.setRowCount(0)
            self.figure.clear()
            self._update_buttons()
            return
        n = len(s.administered)
        L["cat.theta0"].setText(f"{s.config.initial_theta:.3f}")
        L["cat.theta_now"].setText(f"{s.theta:.3f}")
        L["cat.se_now"].setText("∞" if not np.isfinite(s.se) else f"{s.se:.3f}")
        L["cat.n_items"].setText(str(n))
        L["cat.info"].setText(f"{s.info:.3f}")
        L["cat.correct"].setText(str(int(sum(s.responses))))
        L["cat.incorrect"].setText(str(n - int(sum(s.responses))))
        L["cat.status"].setText(tr("cat.finished", reason=tr(f"stop.{s.stop_reason}")) if s.finished
                                else tr("cat.in_progress"))
        if s.pending is not None and not s.finished:
            it = s.bank.active_items[s.pending]
            self.pending_label.setText(tr("cat.pending_item", id=it.item_id, a=it.a, b=it.b, c=it.c))
        else:
            self.pending_label.setText("")
        rows = []
        for k, idx in enumerate(s.administered):
            it = s.bank.active_items[idx]
            rows.append([k + 1, it.item_id, it.a, it.b, it.c,
                         tr("response.correct") if s.responses[k] else tr("response.incorrect"),
                         s.theta_history[k], s.se_history[k], s.info_history[k]])
        fill_table(self.table, rows)
        fit_columns(self.table)
        if n:
            self.table.scrollToBottom()
            b_sel = [float(s.bank.b[i]) for i in s.administered]
            self.figure.draw(plot_cat_trace, s.theta_history, s.se_history, s.info_history, b_sel, tr,
                             theta_true=s.theta_true, initial_theta=s.config.initial_theta)
        else:
            self.figure.clear()
        self._update_buttons()

    def export_trace(self) -> None:
        s = self.session
        if s is None or not s.administered:
            return
        path = ask_save(self, "filter.csv", "cat_session_trace.csv")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["step", "item_id", "a", "b", "c", "response", "theta_estimate",
                            "standard_error", "cumulative_information"])
                for k, idx in enumerate(s.administered):
                    it = s.bank.active_items[idx]
                    w.writerow([k + 1, it.item_id, it.a, it.b, it.c, s.responses[k],
                                f"{s.theta_history[k]:.6f}", f"{s.se_history[k]:.6f}",
                                f"{s.info_history[k]:.6f}"])
        except OSError as exc:
            log.error("No se pudo exportar la traza: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return
        log.info("Traza CAT exportada: %s", path)
        info(self, tr("msg.file_written", file=path))

    def retranslate(self) -> None:
        self.binder.retranslate()
        self.figure.retranslate()
