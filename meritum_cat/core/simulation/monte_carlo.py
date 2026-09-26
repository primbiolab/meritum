"""
Simulación Monte Carlo de poblaciones de examinados.

Genera una población de habilidades verdaderas a partir de una distribución
configurable, ejecuta un CAT (o un test fijo) para cada examinado y agrega los
resultados: métricas de recuperación de habilidad, trayectorias de estimación y
estadísticos de exposición de ítems.

Reproducibilidad: todo el azar (población, respuestas simuladas y selección
aleatorizada) proviene de un único generador ``numpy.random.default_rng(seed)``.
Con la misma configuración, el mismo banco y la misma semilla, los resultados
son idénticos.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

import numpy as np

from meritum_cat.models import ItemBank
from meritum_cat.core.irt.models import apply_model, IRTModel
from meritum_cat.core.estimation.base import make_estimator, EstimationMethod
from meritum_cat.core.selection.base import make_selector, SelectionMethod
from meritum_cat.core.stopping.rules import make_stopping_rule
from meritum_cat.core.balancing.content import ContentBalancer
from meritum_cat.core.simulation.cat import CATConfig, simulate_cat, run_fixed_test
from meritum_cat.core.exposure.control import compute_exposure, ExposureStats
from meritum_cat.core.statistics.metrics import recovery_metrics

DISTRIBUTIONS = ("normal", "uniform")


@dataclass
class MonteCarloConfig:
    """
    Configuración de una simulación Monte Carlo.

    Reúne los parámetros poblacionales (distribución de theta) y algorítmicos
    (modelo IRT, estimador, selector, criterios de terminación, semilla).
    """

    n_examinees: int = 1000
    theta_distribution: str = "normal"  # "normal" | "uniform"
    theta_mean: float = 0.0
    theta_sd: float = 1.0
    theta_min: float = -3.0
    theta_max: float = 3.0

    model: str = IRTModel.TWO_PL.value
    estimation_method: str = EstimationMethod.EAP.value
    selection_method: str = SelectionMethod.MAX_INFO.value

    max_items: int | None = 20
    se_threshold: float | None = None
    target_information: float | None = None
    min_items: int = 1

    initial_theta: float = 0.0
    randomesque_bin: int = 5
    sh_r_max: float = 0.25          # Sympson-Hetter: exposición máxima objetivo
    sh_iterations: int = 8          # Sympson-Hetter: iteraciones de calibración
    sh_calibration_examinees: int = 1000  # Sympson-Hetter: examinados por iteración
    prior_mean: float = 0.0
    prior_sd: float = 1.0
    content_targets: dict[str, float] | None = None

    fixed_test: bool = False  # True: test de longitud fija (max_items) sin adaptación
    seed: int = 12345
    theta_bounds: tuple[float, float] = (-4.0, 4.0)

    def validate(self) -> list[tuple[str, str]]:
        """
        Valida la configuración. Devuelve una lista de pares (campo, código de
        error); lista vacía si es válida. Los códigos se traducen en la GUI.
        """
        errors: list[tuple[str, str]] = []
        if not isinstance(self.n_examinees, (int, np.integer)) or self.n_examinees < 1:
            errors.append(("n_examinees", "must_be_positive_int"))
        if self.theta_distribution not in DISTRIBUTIONS:
            errors.append(("theta_distribution", "invalid_choice"))
        if self.theta_distribution == "normal" and not (self.theta_sd > 0):
            errors.append(("theta_sd", "must_be_positive"))
        if self.theta_distribution == "uniform" and not (self.theta_min < self.theta_max):
            errors.append(("theta_min", "min_lt_max"))
        if self.model not in [m.value for m in (IRTModel.ONE_PL, IRTModel.TWO_PL, IRTModel.THREE_PL)]:
            errors.append(("model", "invalid_choice"))
        if self.estimation_method not in [m.value for m in EstimationMethod]:
            errors.append(("estimation_method", "invalid_choice"))
        if self.selection_method not in [m.value for m in SelectionMethod]:
            errors.append(("selection_method", "invalid_choice"))
        if self.max_items is not None and self.max_items < 1:
            errors.append(("max_items", "must_be_positive_int"))
        if self.se_threshold is not None and not (self.se_threshold > 0):
            errors.append(("se_threshold", "must_be_positive"))
        if self.target_information is not None and not (self.target_information > 0):
            errors.append(("target_information", "must_be_positive"))
        if self.max_items is None and self.se_threshold is None and self.target_information is None:
            errors.append(("max_items", "need_stopping_rule"))
        if self.fixed_test and self.max_items is None:
            errors.append(("max_items", "fixed_needs_length"))
        if not (self.prior_sd > 0):
            errors.append(("prior_sd", "must_be_positive"))
        if self.randomesque_bin < 1:
            errors.append(("randomesque_bin", "must_be_positive_int"))
        if not (0 < self.sh_r_max <= 1):
            errors.append(("sh_r_max", "must_be_probability"))
        if self.sh_iterations < 1:
            errors.append(("sh_iterations", "must_be_positive_int"))
        if self.sh_calibration_examinees < 1:
            errors.append(("sh_calibration_examinees", "must_be_positive_int"))
        if not isinstance(self.seed, (int, np.integer)) or self.seed < 0:
            errors.append(("seed", "invalid_seed"))
        lo, hi = self.theta_bounds
        if not lo < hi:
            errors.append(("theta_bounds", "min_lt_max"))
        return errors

    def build_estimator(self):
        kwargs: dict = {"theta_bounds": tuple(self.theta_bounds)}
        if self.estimation_method in (EstimationMethod.MAP.value, EstimationMethod.EAP.value):
            kwargs["prior_mean"] = self.prior_mean
            kwargs["prior_sd"] = self.prior_sd
        return make_estimator(self.estimation_method, **kwargs)

    def build_selector(self, n_items: int | None = None, k_params: np.ndarray | None = None):
        if self.selection_method == SelectionMethod.RANDOMESQUE.value:
            return make_selector(self.selection_method, bin_size=self.randomesque_bin)
        if self.selection_method == SelectionMethod.SYMPSON_HETTER.value:
            return make_selector(self.selection_method, k_params=k_params, n_items=n_items)
        return make_selector(self.selection_method)

    def build_stopping_rule(self):
        return make_stopping_rule(
            max_items=self.max_items,
            se_threshold=self.se_threshold,
            target_information=self.target_information,
            min_items=self.min_items,
        )


@dataclass
class MonteCarloResult:
    """Resultado agregado de una simulación Monte Carlo."""

    theta_true: np.ndarray
    theta_est: np.ndarray
    se: np.ndarray
    test_lengths: np.ndarray
    administered: list[list[int]]
    stop_reasons: list[str]
    exposure: ExposureStats
    metrics: dict[str, float]
    config: MonteCarloConfig
    elapsed_seconds: float
    n_items_bank: int = 0
    theta_histories: list[list[float]] = field(default_factory=list)
    se_histories: list[list[float]] = field(default_factory=list)
    b_administered: list[list[float]] = field(default_factory=list)
    sh_k: np.ndarray | None = None
    sh_history: list[float] = field(default_factory=list)

    @property
    def mean_test_length(self) -> float:
        return float(np.mean(self.test_lengths)) if self.test_lengths.size else 0.0

    def precision_by_item_number(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Precisión en función del número de ítems administrados.

        Para k = 1..L_max devuelve el RMSE de la estimación tras k ítems y el
        error estándar medio tras k ítems. Los examinados que terminaron antes de
        k ítems conservan su estimación final (el test ya había concluido).
        Devuelve (k, rmse_k, mean_se_k).
        """
        if not self.theta_histories:
            return np.zeros(0), np.zeros(0), np.zeros(0)
        max_len = max(len(h) for h in self.theta_histories)
        n = len(self.theta_histories)
        th = np.empty((n, max_len))
        se = np.empty((n, max_len))
        for i, (h, s) in enumerate(zip(self.theta_histories, self.se_histories)):
            th[i, :len(h)] = h
            th[i, len(h):] = h[-1]
            se[i, :len(s)] = s
            se[i, len(s):] = s[-1]
        err = th - self.theta_true.reshape(-1, 1)
        rmse_k = np.sqrt(np.mean(err ** 2, axis=0))
        se = np.where(np.isfinite(se), se, np.nan)
        mean_se_k = np.nanmean(se, axis=0)
        return np.arange(1, max_len + 1), rmse_k, mean_se_k


def sample_population(config: MonteCarloConfig, rng: np.random.Generator) -> np.ndarray:
    """Genera el vector de habilidades verdaderas de la población."""
    if config.theta_distribution == "normal":
        return rng.normal(config.theta_mean, config.theta_sd, config.n_examinees)
    if config.theta_distribution == "uniform":
        return rng.uniform(config.theta_min, config.theta_max, config.n_examinees)
    raise ValueError(f"Distribución no soportada: {config.theta_distribution}")


def run_monte_carlo(
    bank: ItemBank,
    config: MonteCarloConfig,
    progress_callback: Callable[[int, int], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> MonteCarloResult | None:
    """
    Ejecuta la simulación Monte Carlo.

    El banco se interpreta bajo el modelo IRT de la configuración (ver
    :func:`meritum_cat.core.irt.models.apply_model`): en 1PL se usan a = 1 y
    c = 0; en 2PL, c = 0; en 3PL, los parámetros completos. El mismo modelo
    genera las respuestas simuladas y se usa para estimar.

    Args:
        bank: Banco de ítems.
        config: Configuración de la simulación.
        progress_callback: Función opcional llamada con (hechos, total).
        cancel_check: Función opcional; si devuelve True la simulación se cancela
            de forma limpia y se devuelve ``None``.
    """
    errors = config.validate()
    if errors:
        raise ValueError("Configuración inválida: " + ", ".join(f"{f}:{c}" for f, c in errors))
    model_bank = apply_model(bank, config.model)
    if model_bank.n_items == 0:
        raise ValueError("El banco no tiene ítems activos.")

    t0 = time.perf_counter()
    rng = np.random.default_rng(config.seed)
    theta_true = sample_population(config, rng)

    estimator = config.build_estimator()
    stopping = config.build_stopping_rule()
    balancer = None
    if config.content_targets:
        cats = [it.category for it in model_bank.active_items]
        balancer = ContentBalancer(cats, config.content_targets)

    def make_cat_config(selector) -> CATConfig:
        return CATConfig(
            estimator=estimator,
            selector=selector,
            stopping_rule=stopping,
            initial_theta=config.initial_theta,
            balancer=balancer,
            theta_bounds=tuple(config.theta_bounds),
        )

    n = config.n_examinees
    sh_k = None
    sh_history: list[float] = []
    is_sh = (config.selection_method == SelectionMethod.SYMPSON_HETTER.value
             and not config.fixed_test)
    n_cal = config.sh_calibration_examinees if is_sh else 0
    total_work = n + n_cal * config.sh_iterations
    work_done = [0]
    report_every = max(1, total_work // 200)

    def tick() -> None:
        work_done[0] += 1
        if progress_callback is not None and (
                work_done[0] % report_every == 0 or work_done[0] == total_work):
            progress_callback(work_done[0], total_work)

    if is_sh:
        # Calibración con un flujo aleatorio independiente pero determinado por la
        # semilla, de modo que la simulación principal sea reproducible.
        cal_config = MonteCarloConfig(**{**config.__dict__, "n_examinees": n_cal})
        cal_rng = np.random.default_rng([config.seed, 7919])
        cancelled = [False]

        def run_population(selector):
            counts = np.zeros(model_bank.n_items)
            thetas = sample_population(cal_config, cal_rng)
            cfg = make_cat_config(selector)
            for t in thetas:
                if cancel_check is not None and cancel_check():
                    cancelled[0] = True
                    return counts, max(1, len(thetas))
                r = simulate_cat(t, model_bank, cfg, cal_rng)
                counts[r.administered_items] += 1
                tick()
            return counts, len(thetas)

        from meritum_cat.core.selection.sympson_hetter import calibrate_sympson_hetter
        sh_k, sh_history = calibrate_sympson_hetter(
            run_population, model_bank.n_items, config.sh_r_max, config.sh_iterations)
        if cancelled[0]:
            return None

    selector = config.build_selector(n_items=model_bank.n_items, k_params=sh_k)
    cat_config = make_cat_config(selector)

    theta_est = np.zeros(n)
    se = np.zeros(n)
    lengths = np.zeros(n, dtype=int)
    administered: list[list[int]] = []
    stop_reasons: list[str] = []
    theta_hist: list[list[float]] = []
    se_hist: list[list[float]] = []
    b_adm: list[list[float]] = []

    for i in range(n):
        if cancel_check is not None and cancel_check():
            return None

        if config.fixed_test:
            result = run_fixed_test(theta_true[i], model_bank, estimator, int(config.max_items), rng)
        else:
            result = simulate_cat(theta_true[i], model_bank, cat_config, rng)

        theta_est[i] = result.theta_estimate
        se[i] = result.standard_error
        lengths[i] = result.test_length
        administered.append(result.administered_items)
        stop_reasons.append(result.stop_reason)
        theta_hist.append(result.theta_history)
        se_hist.append(result.se_history)
        b_adm.append([float(model_bank.b[j]) for j in result.administered_items])
        tick()

    exposure = compute_exposure(administered, model_bank.n_items)
    metrics = recovery_metrics(theta_true, theta_est, se)
    metrics["mean_se"] = float(np.mean(se[np.isfinite(se)])) if np.any(np.isfinite(se)) else float("nan")
    metrics["mean_test_length"] = float(np.mean(lengths))
    metrics["max_exposure_rate"] = exposure.max_rate
    metrics["mean_exposure_rate"] = exposure.mean_rate
    metrics["unused_items"] = float(exposure.unused_items)

    elapsed = time.perf_counter() - t0
    metrics["elapsed_seconds"] = elapsed
    return MonteCarloResult(
        theta_true=theta_true,
        theta_est=theta_est,
        se=se,
        test_lengths=lengths,
        administered=administered,
        stop_reasons=stop_reasons,
        exposure=exposure,
        metrics=metrics,
        config=config,
        elapsed_seconds=elapsed,
        n_items_bank=model_bank.n_items,
        theta_histories=theta_hist,
        se_histories=se_hist,
        b_administered=b_adm,
        sh_k=sh_k,
        sh_history=sh_history,
    )
