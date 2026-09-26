"""Pestaña «Simulación Monte Carlo»: configuración, ejecución, análisis, exportación y reproducción."""
from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGroupBox, QHBoxLayout, QLabel, QProgressBar, QSplitter,
    QTabWidget, QTableWidgetItem, QVBoxLayout, QWidget, QHeaderView,
)

from meritum_cat.core.simulation.monte_carlo import MonteCarloConfig, MonteCarloResult, run_monte_carlo
from meritum_cat.core.selection.base import SelectionMethod
from meritum_cat.i18n import get_translator
from meritum_cat.i18n.strings import PARAM_HELP
from meritum_cat.persistence import (
    ConfigIOError, bank_fingerprint, bank_from_payload, load_experiment_config,
    monte_carlo_config_from_dict, save_experiment_config, save_results_csv,
)
from meritum_cat.plotting import (
    plot_bias_rmse_by_theta, plot_cat_vs_fixed, plot_error_distribution, plot_exposure,
    plot_precision_by_items, plot_recovery, plot_test_length,
)
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.gui.common import (
    side_panel, Binder, FigurePanel, ask_folder, ask_open, ask_save, button, confirm, dspin, error, fmt, info,
    io_error_text, make_form, make_table, muted_label, param_row, spin, tr, unexpected_error, warn,
)
from meritum_cat.gui.config_widgets import AlgorithmControls, StoppingControls
from meritum_cat.gui.state import AppState
from meritum_cat.gui.workers import TaskRunner

log = get_logger("gui.mc")

METRIC_ROWS = ["n_examinees", "mean_test_length", "bias", "mae", "mse", "rmse", "pearson", "spearman",
               "coverage95", "mean_se", "max_exposure_rate", "mean_exposure_rate", "unused_items",
               "elapsed_seconds"]
_METRIC_SOURCE = {"coverage95": "coverage_95"}
LARGE_N = 20000


def metric_value(result: MonteCarloResult, key: str):
    if key == "n_examinees":
        return int(result.config.n_examinees)
    if key == "sh_max_exposure_final":
        return result.sh_history[-1] if result.sh_history else None
    value = result.metrics.get(_METRIC_SOURCE.get(key, key))
    if key == "unused_items" and value is not None:
        return int(value)
    return value


def simulation_task(bank, config: MonteCarloConfig, compare_fixed: bool, progress=None, cancel_check=None):
    """Tarea de fondo: CAT y, opcionalmente, test fijo de igual longitud media."""
    scale = 1000
    share = 0.5 if compare_fixed else 1.0

    def p_cat(done, total):
        if progress:
            progress(int(done / total * scale * share), scale)

    res = run_monte_carlo(bank, config, progress_callback=p_cat, cancel_check=cancel_check)
    if res is None:
        return None
    fixed = None
    if compare_fixed:
        length = max(1, int(round(res.mean_test_length)))
        fcfg = replace(config, fixed_test=True, max_items=length, se_threshold=None,
                       target_information=None)

        def p_fixed(done, total):
            if progress:
                progress(int(scale * share + done / total * scale * share), scale)

        fixed = run_monte_carlo(bank, fcfg, progress_callback=p_fixed, cancel_check=cancel_check)
        if fixed is None:
            return None
    return {"cat": res, "fixed": fixed}


class MonteCarloTab(QWidget):
    """Simulación Monte Carlo configurable y reproducible."""

    def __init__(self, state: AppState, go_to_bank) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        self.runner = TaskRunner(self)
        self.result: MonteCarloResult | None = None
        self.fixed_result: MonteCarloResult | None = None
        self.expected_metrics: dict | None = None
        self.repro_message = ""
        self._t0 = 0.0
        self._compare_running = False
        self._status: tuple[str, dict] | None = None
        b = self.binder

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)

        g1 = QGroupBox()
        b.title(g1, "mc.group_bank")
        l1 = QVBoxLayout(g1)
        self.bank_label = QLabel()
        self.bank_label.setWordWrap(True)
        self.btn_bank = button()
        b.text(self.btn_bank, "mc.change_bank")
        self.btn_bank.clicked.connect(go_to_bank)
        l1.addWidget(self.bank_label)
        l1.addWidget(self.btn_bank)
        ll.addWidget(g1)

        self.algo = AlgorithmControls(b, include_sh=True)
        g2 = QGroupBox()
        b.title(g2, "mc.group_model")
        f2 = make_form()
        self.algo.add_model(f2, b)
        g2.setLayout(f2)
        ll.addWidget(g2)

        g3 = QGroupBox()
        b.title(g3, "mc.group_estimation")
        f3 = make_form()
        self.algo.add_estimation(f3, b)
        self.initial_theta = dspin(-4.0, 4.0, 0.0, 0.1)
        param_row(f3, b, "initial_theta", self.initial_theta)
        g3.setLayout(f3)
        ll.addWidget(g3)

        g4 = QGroupBox()
        b.title(g4, "mc.group_selection")
        f4 = make_form()
        self.algo.add_selection(f4, b)
        self.balancing = QCheckBox()
        b.text(self.balancing, "mc.content_balancing")
        param_row(f4, b, "content_balancing", self.balancing)
        sh_note = muted_label()
        b.text(sh_note, "mc.sh_note")
        v4 = QVBoxLayout(g4)
        v4.addLayout(f4)
        v4.addWidget(sh_note)
        ll.addWidget(g4)

        g5 = QGroupBox()
        b.title(g5, "mc.group_stopping")
        f5 = make_form()
        self.stopping = StoppingControls()
        self.stopping.add(f5, b)
        g5.setLayout(f5)
        ll.addWidget(g5)

        g6 = QGroupBox()
        b.title(g6, "mc.group_population")
        f6 = make_form()
        self.n_examinees = spin(1, 1_000_000, 1000, 100)
        self.distribution = QComboBox()
        b.combo(self.distribution, [("normal", "dist.normal"), ("uniform", "dist.uniform")])
        self.theta_mean = dspin(-4.0, 4.0, 0.0, 0.1)
        self.theta_sd = dspin(0.01, 5.0, 1.0, 0.1)
        self.theta_min = dspin(-6.0, 6.0, -3.0, 0.1)
        self.theta_max = dspin(-6.0, 6.0, 3.0, 0.1)
        param_row(f6, b, "n_examinees", self.n_examinees)
        param_row(f6, b, "theta_distribution", self.distribution)
        param_row(f6, b, "theta_mean", self.theta_mean)
        param_row(f6, b, "theta_sd", self.theta_sd)
        param_row(f6, b, "theta_min", self.theta_min)
        param_row(f6, b, "theta_max", self.theta_max)
        g6.setLayout(f6)
        ll.addWidget(g6)
        self.distribution.currentIndexChanged.connect(self._update_dist_enabled)

        g7 = QGroupBox()
        b.title(g7, "mc.group_repro")
        f7 = make_form()
        seed_row = QWidget()
        sr = QHBoxLayout(seed_row)
        sr.setContentsMargins(0, 0, 0, 0)
        self.seed = spin(0, 2_147_483_647, 12345)
        self.btn_new_seed = button()
        b.text(self.btn_new_seed, "mc.new_seed")
        self.btn_new_seed.clicked.connect(self.new_seed)
        sr.addWidget(self.seed, 1)
        sr.addWidget(self.btn_new_seed)
        param_row(f7, b, "seed", seed_row)
        self.test_mode = QComboBox()
        b.combo(self.test_mode, [("cat", "mode.cat"), ("fixed", "mode.fixed")])
        param_row(f7, b, "test_mode", self.test_mode)
        self.compare_fixed = QCheckBox()
        b.text(self.compare_fixed, "mc.compare_fixed")
        f7.addRow(self.compare_fixed)
        g7.setLayout(f7)
        ll.addWidget(g7)
        self.test_mode.currentIndexChanged.connect(self._update_mode_enabled)

        io_row = QHBoxLayout()
        self.btn_save_cfg = button()
        b.text(self.btn_save_cfg, "mc.save_config")
        self.btn_save_cfg.clicked.connect(self.save_config)
        self.btn_load_cfg = button()
        b.text(self.btn_load_cfg, "mc.load_config")
        self.btn_load_cfg.clicked.connect(self.load_config)
        io_row.addWidget(self.btn_save_cfg)
        io_row.addWidget(self.btn_load_cfg)
        ll.addLayout(io_row)
        self.btn_reset = button()
        b.text(self.btn_reset, "mc.reset")
        self.btn_reset.clicked.connect(self.reset_values)
        ll.addWidget(self.btn_reset)
        ll.addStretch(1)

        scroll = side_panel(left, 390, 470)

        # --- ejecución y resultados ------------------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        run_row = QHBoxLayout()
        self.btn_run = button("primary")
        b.text(self.btn_run, "mc.run")
        self.btn_run.clicked.connect(self.run)
        self.btn_stop = button("danger")
        b.text(self.btn_stop, "mc.stop")
        self.btn_stop.clicked.connect(self.stop)
        self.btn_stop.setEnabled(False)
        self.btn_export_csv = button()
        b.text(self.btn_export_csv, "mc.export_results")
        self.btn_export_csv.clicked.connect(self.export_results)
        self.btn_export_figs = button()
        b.text(self.btn_export_figs, "mc.export_figures")
        self.btn_export_figs.clicked.connect(self.export_figures)
        for w in (self.btn_run, self.btn_stop, self.btn_export_csv, self.btn_export_figs):
            run_row.addWidget(w)
        run_row.addStretch(1)
        rl.addLayout(run_row)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p %")
        self.status = muted_label()
        rl.addWidget(self.progress)
        rl.addWidget(self.status)

        res_box = QGroupBox()
        b.title(res_box, "mc.results_group")
        resl = QVBoxLayout(res_box)
        self.metrics_table = make_table(3)
        self.metrics_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.repro_label = muted_label("note")
        self.repro_label.setVisible(False)
        resl.addWidget(self.repro_label)
        resl.addWidget(self.metrics_table)

        self.fig_tabs = QTabWidget()
        self.figs: dict[str, FigurePanel] = {}
        for key in ("recovery", "error", "conditional", "precision", "exposure", "length", "compare"):
            panel = FigurePanel()
            panel.default_name = f"monte_carlo_{key}.png"
            self.figs[key] = panel
            self.fig_tabs.addTab(panel, "")
            b.tab(self.fig_tabs, panel, f"mc.subtab_{key}")

        split = QSplitter(Qt.Horizontal)
        split.addWidget(res_box)
        split.addWidget(self.fig_tabs)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 5)
        split.setSizes([500, 800])
        self.metrics_table.setMinimumWidth(380)
        self.metrics_table.setWordWrap(True)
        rl.addWidget(split, 1)

        outer = QHBoxLayout(self)
        outer.addWidget(scroll)
        outer.addWidget(right, 1)

        self.runner.progress.connect(self.on_progress)
        self.runner.finished.connect(self.on_finished)
        self.runner.failed.connect(self.on_failed)
        self.runner.cancelled.connect(self.on_cancelled)
        state.bank_changed.connect(self.update_bank_label)
        self._update_dist_enabled()
        self._update_mode_enabled()
        b.call(self.refresh_all)

    # ------------------------------------------------------------------ configuración
    def _update_dist_enabled(self, *_args) -> None:
        normal = self.distribution.currentData() == "normal"
        self.theta_mean.setEnabled(normal)
        self.theta_sd.setEnabled(normal)
        self.theta_min.setEnabled(not normal)
        self.theta_max.setEnabled(not normal)

    def _update_mode_enabled(self, *_args) -> None:
        cat = self.test_mode.currentData() == "cat"
        self.compare_fixed.setEnabled(cat)
        if not cat:
            self.compare_fixed.setChecked(False)

    def update_bank_label(self) -> None:
        bank = self.state.bank
        self.bank_label.setText(tr("status.no_bank") if bank is None else
                                tr("mc.bank_current", name=bank.name, n=bank.n_items))

    def new_seed(self) -> None:
        self.seed.setValue(int(np.random.default_rng().integers(0, 2_147_483_647)))

    def current_config(self) -> MonteCarloConfig:
        stop = self.stopping.values()
        bank = self.state.bank
        targets = None
        if self.balancing.isChecked() and bank is not None and bank.categories:
            targets = {c: 1.0 for c in bank.categories}
        return MonteCarloConfig(
            n_examinees=self.n_examinees.value(),
            theta_distribution=self.distribution.currentData(),
            theta_mean=self.theta_mean.value(), theta_sd=self.theta_sd.value(),
            theta_min=self.theta_min.value(), theta_max=self.theta_max.value(),
            model=self.algo.model.currentData(),
            estimation_method=self.algo.estimator.currentData(),
            selection_method=self.algo.selector.currentData(),
            max_items=stop["max_items"], se_threshold=stop["se_threshold"],
            target_information=stop["target_information"], min_items=stop["min_items"],
            initial_theta=self.initial_theta.value(),
            randomesque_bin=self.algo.randomesque_bin.value(),
            sh_r_max=self.algo.sh_r_max.value(), sh_iterations=self.algo.sh_iterations.value(),
            sh_calibration_examinees=self.algo.sh_calibration_examinees.value(),
            prior_mean=self.algo.prior_mean.value(), prior_sd=self.algo.prior_sd.value(),
            content_targets=targets,
            fixed_test=self.test_mode.currentData() == "fixed",
            seed=self.seed.value(),
        )

    def set_config(self, cfg: MonteCarloConfig) -> None:
        self.n_examinees.setValue(int(cfg.n_examinees))
        self.algo.set_combo(self.distribution, cfg.theta_distribution)
        self.theta_mean.setValue(cfg.theta_mean)
        self.theta_sd.setValue(cfg.theta_sd)
        self.theta_min.setValue(cfg.theta_min)
        self.theta_max.setValue(cfg.theta_max)
        self.algo.set_combo(self.algo.model, cfg.model)
        self.algo.set_combo(self.algo.estimator, cfg.estimation_method)
        self.algo.set_combo(self.algo.selector, cfg.selection_method)
        self.stopping.max_items.set_value(cfg.max_items)
        self.stopping.se_threshold.set_value(cfg.se_threshold)
        self.stopping.target_information.set_value(cfg.target_information)
        self.stopping.min_items.setValue(int(cfg.min_items))
        self.initial_theta.setValue(cfg.initial_theta)
        self.algo.randomesque_bin.setValue(int(cfg.randomesque_bin))
        self.algo.sh_r_max.setValue(cfg.sh_r_max)
        self.algo.sh_iterations.setValue(int(cfg.sh_iterations))
        self.algo.sh_calibration_examinees.setValue(int(cfg.sh_calibration_examinees))
        self.algo.prior_mean.setValue(cfg.prior_mean)
        self.algo.prior_sd.setValue(cfg.prior_sd)
        self.balancing.setChecked(bool(cfg.content_targets))
        self.algo.set_combo(self.test_mode, "fixed" if cfg.fixed_test else "cat")
        self.seed.setValue(int(cfg.seed))

    def reset_values(self) -> None:
        self.set_config(MonteCarloConfig())
        self.compare_fixed.setChecked(False)
        self.expected_metrics = None

    def _validation_messages(self, cfg: MonteCarloConfig) -> list[str]:
        t = get_translator()
        msgs = []
        for field, code in cfg.validate():
            name = t.param_label(field) if field in PARAM_HELP else field
            msgs.append(tr(f"valerr.{code}", field=name))
        return msgs

    def _set_status(self, key: str | None, **params) -> None:
        """Guarda el estado como clave + parámetros para retraducirlo al cambiar de idioma."""
        self._status = (key, params) if key else None
        self.status.setText(tr(key, **params) if key else "")

    # ------------------------------------------------------------------ ejecución
    def run(self, _checked: bool = False, skip_confirm: bool = False) -> bool:
        if self.runner.running:
            return False
        bank = self.state.bank
        if bank is None or bank.n_items == 0:
            warn(self, tr("err.no_bank"))
            return False
        n_err = self.state.bank_error_count()
        if n_err:
            warn(self, tr("err.bank_invalid", n=n_err))
            return False
        cfg = self.current_config()
        msgs = self._validation_messages(cfg)
        if msgs:
            warn(self, tr("err.invalid_input") + "\n\n• " + "\n• ".join(msgs))
            return False
        if cfg.n_examinees > LARGE_N and not skip_confirm:
            if not confirm(self, tr("mc.large_confirm", n=cfg.n_examinees)):
                return False
        compare = self.compare_fixed.isChecked() and not cfg.fixed_test
        log.info("Simulación Monte Carlo iniciada: N=%d modelo=%s estimador=%s selección=%s "
                 "max_items=%s se=%s info=%s semilla=%d fijo=%s comparar=%s banco=%s(%d)",
                 cfg.n_examinees, cfg.model, cfg.estimation_method, cfg.selection_method,
                 cfg.max_items, cfg.se_threshold, cfg.target_information, cfg.seed, cfg.fixed_test,
                 compare, bank.name, bank.n_items)
        self._t0 = time.perf_counter()
        self._compare_running = compare
        self.progress.setValue(0)
        self._set_running(True)
        self._set_status("mc.status_running", pct=0, elapsed=0.0)
        self.runner.start(simulation_task, bank, cfg, compare)
        return True

    def stop(self) -> None:
        if self.runner.running:
            self.runner.cancel()
            self.btn_stop.setEnabled(False)

    def _set_running(self, running: bool) -> None:
        self.btn_run.setEnabled(not running)
        self.btn_stop.setEnabled(running)
        for w in (self.btn_export_csv, self.btn_export_figs, self.btn_save_cfg, self.btn_load_cfg,
                  self.btn_reset, self.btn_bank):
            w.setEnabled(not running)

    def on_progress(self, done: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(done)
        pct = int(round(100 * done / total)) if total else 0
        key = "mc.status_running_fixed" if (self._compare_running and done > total / 2) else "mc.status_running"
        self._set_status(key, pct=pct, elapsed=time.perf_counter() - self._t0)

    def on_finished(self, payload) -> None:
        self._set_running(False)
        self.progress.setValue(self.progress.maximum())
        self.result = payload["cat"]
        self.fixed_result = payload["fixed"]
        sec = time.perf_counter() - self._t0
        self._set_status("mc.status_done", sec=sec)
        log.info("Simulación completada en %.2f s. Métricas: %s", sec,
                 {k: round(v, 4) for k, v in self.result.metrics.items() if isinstance(v, float)})
        self._check_reproduction()
        self.refresh_all()

    def on_failed(self, _detail: str) -> None:
        self._set_running(False)
        self._set_status(None)
        unexpected_error(self)

    def on_cancelled(self) -> None:
        self._set_running(False)
        self.progress.setValue(0)
        self._set_status("mc.status_cancelled")
        log.info("Simulación detenida por el usuario.")

    def _check_reproduction(self) -> None:
        self.repro_message = ""
        if not self.expected_metrics or self.result is None:
            return
        diffs = []
        for k, v in self.expected_metrics.items():
            if k == "elapsed_seconds" or v is None:
                continue
            new = self.result.metrics.get(k)
            if new is None or (isinstance(new, float) and np.isnan(new)):
                continue
            diffs.append(abs(float(new) - float(v)))
        d = max(diffs) if diffs else 0.0
        self.repro_message = "ok" if d <= 1e-9 else f"diff:{d}"
        log.info("Verificación de reproducción: diferencia máxima = %.3g", d)
        self.expected_metrics = None

    # ------------------------------------------------------------------ vista
    def refresh_all(self) -> None:
        self.update_bank_label()
        self._update_mode_enabled()
        if self._status is None and not self.runner.running and self.result is None:
            self._set_status("mc.status_idle")
        elif self._status is not None:
            self._set_status(self._status[0], **self._status[1])
        self._fill_metrics()
        self._draw_figures()
        if self.repro_message == "ok":
            self.repro_label.setText(tr("mc.repro_ok"))
            self.repro_label.setVisible(True)
        elif self.repro_message.startswith("diff:"):
            self.repro_label.setText(tr("mc.repro_diff", d=float(self.repro_message[5:])))
            self.repro_label.setVisible(True)
        else:
            self.repro_label.setText("")
            self.repro_label.setVisible(False)

    def _fill_metrics(self) -> None:
        table = self.metrics_table
        has_fixed = self.fixed_result is not None
        table.setColumnCount(3 if has_fixed else 2)
        headers = [tr("col.metric"), tr("col.cat") if has_fixed else tr("col.value")]
        if has_fixed:
            headers.append(tr("col.fixed"))
        table.setHorizontalHeaderLabels(headers)
        if self.result is None:
            table.clearSpans()
            table.setRowCount(1)
            item = QTableWidgetItem(tr("mc.no_results"))
            table.setItem(0, 0, item)
            table.setSpan(0, 0, 1, table.columnCount())
            return
        table.clearSpans()
        keys = list(METRIC_ROWS)
        if self.result.sh_history:
            keys.append("sh_max_exposure_final")
        table.setRowCount(len(keys))
        for i, key in enumerate(keys):
            name = QTableWidgetItem(tr(f"metric_long.{key}"))
            name.setToolTip(tr(f"metric_help.{key}"))
            table.setItem(i, 0, name)
            for j, res in enumerate([self.result] + ([self.fixed_result] if has_fixed else [])):
                v = metric_value(res, key)
                decimals = 2 if key == "elapsed_seconds" else (2 if key == "mean_test_length" else 4)
                cell = QTableWidgetItem(fmt(v, decimals))
                cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(i, j + 1, cell)
        table.resizeColumnsToContents()
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, table.columnCount()):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        table.resizeRowsToContents()

    def _draw_figures(self) -> None:
        r = self.result
        for panel in self.figs.values():
            panel.retranslate()
        if r is None:
            for panel in self.figs.values():
                panel.clear()
            return
        self.figs["recovery"].draw(plot_recovery, r.theta_true, r.theta_est, tr)
        self.figs["error"].draw(plot_error_distribution, r.theta_true, r.theta_est, tr)
        self.figs["conditional"].draw(plot_bias_rmse_by_theta, r.theta_true, r.theta_est, tr)
        k, rmse_k, se_k = r.precision_by_item_number()
        self.figs["precision"].draw(plot_precision_by_items, k, rmse_k, se_k, tr)
        r_max = r.config.sh_r_max if r.config.selection_method == SelectionMethod.SYMPSON_HETTER.value else None
        self.figs["exposure"].draw(plot_exposure, r.exposure.exposure_rates, tr, r_max)
        self.figs["length"].draw(plot_test_length, r.test_lengths, tr)
        f = self.fixed_result
        idx = self.fig_tabs.indexOf(self.figs["compare"])
        self.fig_tabs.setTabEnabled(idx, f is not None)
        if f is not None:
            self.figs["compare"].draw(plot_cat_vs_fixed, r.theta_true, r.theta_est, f.theta_true,
                                      f.theta_est, tr)
        else:
            self.figs["compare"].clear()

    # ------------------------------------------------------------------ archivos
    def save_config(self) -> None:
        path = ask_save(self, "filter.config", "experiment_config.json")
        if path:
            self.save_config_to(path)

    def save_config_to(self, path: str, silent: bool = False) -> bool:
        bank = self.state.bank
        if bank is None:
            warn(self, tr("err.no_bank"))
            return False
        cfg = self.current_config()
        metrics = elapsed = None
        if self.result is not None and self.result.config == cfg:
            metrics, elapsed = self.result.metrics, self.result.elapsed_seconds
        try:
            save_experiment_config(path, cfg, bank, metrics=metrics, elapsed_seconds=elapsed,
                                   extra={"compare_fixed": self.compare_fixed.isChecked()})
        except OSError as exc:
            log.error("No se pudo guardar la configuración: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return False
        log.info("Configuración guardada: %s (con resultados: %s)", path, metrics is not None)
        if not silent:
            info(self, tr("mc.config_saved", file=path))
        return True

    def load_config(self) -> None:
        path = ask_open(self, "filter.config")
        if path:
            self.load_config_from(path)

    def load_config_from(self, path: str, silent: bool = False) -> bool:
        try:
            data = load_experiment_config(path)
            cfg = monte_carlo_config_from_dict(data["config"])
        except ConfigIOError as exc:
            log.warning("Configuración no válida (%s): %s", path, exc)
            error(self, io_error_text(exc))
            return False
        messages = [tr("mc.config_loaded", file=Path(path).name)]
        if data.get("meritum_cat_version"):
            messages.append(tr("mc.config_version_note", v=data["meritum_cat_version"]))
        bank = bank_from_payload(data)
        if bank is not None:
            stored = data["bank"].get("sha256")
            if stored and bank_fingerprint(bank) == stored:
                self.state.set_bank(bank)
                messages.append(tr("mc.bank_restored", n=bank.n_total))
        self.set_config(cfg)
        self.compare_fixed.setChecked(bool(data.get("extra", {}).get("compare_fixed", False)))
        results = data.get("results") or {}
        self.expected_metrics = results.get("metrics")
        self.repro_message = ""
        log.info("Configuración cargada: %s (versión %s)", path, data.get("meritum_cat_version"))
        self.refresh_all()
        if not silent:
            info(self, "\n\n".join(messages))
        return True

    def export_results(self) -> None:
        if self.result is None:
            warn(self, tr("mc.need_results"))
            return
        path = ask_save(self, "filter.csv", "monte_carlo_results.csv")
        if path:
            self.export_results_to(path)

    def export_results_to(self, path: str, silent: bool = False) -> bool:
        try:
            save_results_csv(self.result, path)
        except OSError as exc:
            log.error("No se pudieron exportar los resultados: %s", exc)
            error(self, tr("err.write_failed", file=path))
            return False
        log.info("Resultados exportados: %s", path)
        if not silent:
            info(self, tr("mc.results_exported", file=path))
        return True

    def export_figures(self) -> None:
        if self.result is None:
            warn(self, tr("mc.need_results"))
            return
        folder = ask_folder(self)
        if folder:
            self.export_figures_to(folder)

    def export_figures_to(self, folder: str, silent: bool = False) -> int:
        n = 0
        for key, panel in self.figs.items():
            if key == "compare" and self.fixed_result is None:
                continue
            path = Path(folder) / f"monte_carlo_{key}.png"
            try:
                panel.save(path)
                n += 1
            except OSError as exc:
                log.error("No se pudo exportar %s: %s", path, exc)
                error(self, tr("err.write_failed", file=str(path)))
                return n
        log.info("%d figuras exportadas a %s", n, folder)
        if not silent:
            info(self, tr("mc.figures_exported", n=n, folder=folder))
        return n

    def retranslate(self) -> None:
        self.binder.retranslate()
