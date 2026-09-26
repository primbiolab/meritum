"""
Diez experimentos científicos predefinidos y reproducibles.

Cada experimento ejecuta varias simulaciones Monte Carlo variando un único factor
de interés (modelo, estimador, selector, tamaño del banco, longitud, error de
calibración, población o semilla) y mantiene fijos los demás. Todos aceptan:

    * ``n_examinees``: examinados simulados por condición;
    * ``seed``: semilla (reproducibilidad);
    * ``bank``: banco opcional del usuario (si no se da, se genera un banco
      sintético reproducible; los experimentos 1 y 5 siempre generan sus bancos
      porque el factor estudiado es el propio banco);
    * ``progress``: función (hechos, total) para informar avance;
    * ``cancel_check``: función que devuelve True para detener el experimento.
"""
from __future__ import annotations

import time
from typing import Any, Callable

import numpy as np

from meritum_cat.datasets import generate_synthetic_bank
from meritum_cat.models import Item, ItemBank
from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo
from meritum_cat.core.simulation.cat import CATConfig, simulate_cat_with_true_params
from meritum_cat.core.simulation.monte_carlo import sample_population
from meritum_cat.core.statistics.metrics import recovery_metrics
from meritum_cat.core.estimation.base import EstimationMethod
from meritum_cat.core.selection.base import SelectionMethod
from meritum_cat.experiments.base import ExperimentResult, ExperimentCancelled

Progress = Callable[[int, int], None] | None
CancelCheck = Callable[[], bool] | None

DEFAULT_MAX_ITEMS = 20


def _r(x: float, n: int = 3) -> float | None:
    x = float(x)
    return None if np.isnan(x) else round(x, n)


class _Runner:
    """Ejecuta las condiciones de un experimento con progreso global y cancelación."""

    def __init__(self, n_conditions: int, progress: Progress, cancel_check: CancelCheck) -> None:
        self.n_conditions = n_conditions
        self.progress = progress
        self.cancel_check = cancel_check
        self.done = 0
        self.scale = 1000  # resolución del progreso global

    def run(self, bank: ItemBank, **cfg_kwargs: Any):
        # Calibración de Sympson-Hetter proporcional al tamaño del experimento (máx. 1000 por iteración).
        cfg_kwargs.setdefault("sh_calibration_examinees", min(int(cfg_kwargs.get("n_examinees", 1000)), 1000))
        cfg = MonteCarloConfig(**cfg_kwargs)
        base = self.done

        def sub_progress(done: int, total: int) -> None:
            if self.progress:
                frac = (base + done / total) / self.n_conditions
                self.progress(int(frac * self.scale), self.scale)

        res = run_monte_carlo(bank, cfg, progress_callback=sub_progress,
                              cancel_check=self.cancel_check)
        if res is None:
            raise ExperimentCancelled()
        self.done += 1
        return res


def _default_bank(bank: ItemBank | None, seed: int, n_items: int = 500) -> ItemBank:
    return bank if bank is not None else generate_synthetic_bank(n_items, model="2PL", seed=seed)


def _bank_info(bank: ItemBank) -> dict[str, Any]:
    return {"bank_name": bank.name, "bank_items": bank.n_items}


def experiment_ability_recovery(n_examinees=1000, seed=2026, bank=None, progress=None,
                                cancel_check=None) -> ExperimentResult:
    """Experimento 1 — Recuperación de habilidad (theta real vs estimada) en 1PL, 2PL y 3PL."""
    t0 = time.perf_counter()
    models = ["1PL", "2PL", "3PL"]
    run = _Runner(len(models), progress, cancel_check)
    rows = []
    for model in models:
        b = generate_synthetic_bank(500, model=model, seed=seed)
        m = run.run(b, n_examinees=n_examinees, model=model, estimation_method="EAP",
                    selection_method=SelectionMethod.MAX_INFO.value,
                    max_items=DEFAULT_MAX_ITEMS, seed=seed).metrics
        rows.append({"model": model, "bias": _r(m["bias"]), "mae": _r(m["mae"]),
                     "mse": _r(m["mse"]), "rmse": _r(m["rmse"]), "pearson": _r(m["pearson"]),
                     "spearman": _r(m["spearman"]), "coverage95": _r(m["coverage_95"])})
    return ExperimentResult(
        key="ability_recovery",
        columns=["model", "bias", "mae", "mse", "rmse", "pearson", "spearman", "coverage95"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "estimator": "EAP",
                "selector": SelectionMethod.MAX_INFO.value, "max_items": DEFAULT_MAX_ITEMS,
                "bank_items": 500},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_estimators(n_examinees=1000, seed=2026, bank=None, progress=None,
                          cancel_check=None) -> ExperimentResult:
    """Experimento 2 — Comparación de estimadores MLE, MAP y EAP."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    methods = [m.value for m in EstimationMethod]
    run = _Runner(len(methods), progress, cancel_check)
    rows = []
    for method in methods:
        m = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method=method,
                    selection_method=SelectionMethod.MAX_INFO.value,
                    max_items=DEFAULT_MAX_ITEMS, seed=seed).metrics
        rows.append({"estimator": method, "bias": _r(m["bias"]), "rmse": _r(m["rmse"]),
                     "mae": _r(m["mae"]), "pearson": _r(m["pearson"]),
                     "mean_se": _r(m["mean_se"]), "coverage95": _r(m["coverage_95"])})
    return ExperimentResult(
        key="estimators",
        columns=["estimator", "bias", "rmse", "mae", "pearson", "mean_se", "coverage95"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL",
                "max_items": DEFAULT_MAX_ITEMS, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_selection(n_examinees=1000, seed=2026, bank=None, progress=None,
                         cancel_check=None) -> ExperimentResult:
    """Experimento 3 — Comparación de algoritmos de selección de ítems."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    selectors = [s.value for s in SelectionMethod]
    run = _Runner(len(selectors), progress, cancel_check)
    rows = []
    for sel in selectors:
        m = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                    selection_method=sel, max_items=DEFAULT_MAX_ITEMS, seed=seed).metrics
        rows.append({"selector": sel, "rmse": _r(m["rmse"]), "bias": _r(m["bias"]),
                     "pearson": _r(m["pearson"]), "max_exposure": _r(m["max_exposure_rate"]),
                     "unused_items": int(m["unused_items"])})
    return ExperimentResult(
        key="selection",
        columns=["selector", "rmse", "bias", "pearson", "max_exposure", "unused_items"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_cat_vs_fixed(n_examinees=1000, seed=2026, bank=None, progress=None,
                            cancel_check=None) -> ExperimentResult:
    """Experimento 4 — CAT frente a test de longitud fija, para varias longitudes."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    lengths = [10, 20, 30]
    run = _Runner(2 * len(lengths), progress, cancel_check)
    rows = []
    for length in lengths:
        cat = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                      selection_method=SelectionMethod.MAX_INFO.value, max_items=length,
                      seed=seed).metrics
        fixed = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                        max_items=length, fixed_test=True, seed=seed).metrics
        for kind, m in (("cat", cat), ("fixed", fixed)):
            rows.append({"test_type": kind, "test_length": length, "rmse": _r(m["rmse"]),
                         "bias": _r(m["bias"]), "pearson": _r(m["pearson"]),
                         "mean_se": _r(m["mean_se"])})
    return ExperimentResult(
        key="cat_vs_fixed",
        columns=["test_type", "test_length", "rmse", "bias", "pearson", "mean_se"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "lengths": lengths, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_bank_size(n_examinees=1000, seed=2026, bank=None, progress=None,
                         cancel_check=None) -> ExperimentResult:
    """Experimento 5 — Efecto del tamaño del banco en precisión y exposición."""
    t0 = time.perf_counter()
    sizes = [50, 100, 250, 500, 1000]
    run = _Runner(len(sizes), progress, cancel_check)
    rows = []
    for size in sizes:
        b = generate_synthetic_bank(size, model="2PL", seed=seed)
        m = run.run(b, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                    selection_method=SelectionMethod.MAX_INFO.value,
                    max_items=DEFAULT_MAX_ITEMS, seed=seed).metrics
        rows.append({"bank_size": size, "rmse": _r(m["rmse"]), "pearson": _r(m["pearson"]),
                     "max_exposure": _r(m["max_exposure_rate"]),
                     "unused_items": int(m["unused_items"])})
    return ExperimentResult(
        key="bank_size",
        columns=["bank_size", "rmse", "pearson", "max_exposure", "unused_items"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, "sizes": sizes},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_test_length(n_examinees=1000, seed=2026, bank=None, progress=None,
                           cancel_check=None) -> ExperimentResult:
    """Experimento 6 — Efecto de la longitud máxima del test."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    lengths = [5, 10, 15, 20, 30, 40]
    run = _Runner(len(lengths), progress, cancel_check)
    rows = []
    for length in lengths:
        m = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                    selection_method=SelectionMethod.MAX_INFO.value, max_items=length,
                    seed=seed).metrics
        rows.append({"test_length": length, "rmse": _r(m["rmse"]), "bias": _r(m["bias"]),
                     "pearson": _r(m["pearson"]), "mean_se": _r(m["mean_se"])})
    return ExperimentResult(
        key="test_length",
        columns=["test_length", "rmse", "bias", "pearson", "mean_se"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "lengths": lengths, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def _perturb(bank: ItemBank, noise: float, rng: np.random.Generator) -> ItemBank:
    """Añade ruido gaussiano a a, b y c (errores de calibración), respetando dominios."""
    items = []
    for it in bank.items:
        items.append(Item(
            item_id=it.item_id,
            a=float(max(0.05, it.a + rng.normal(0.0, noise))),
            b=float(it.b + rng.normal(0.0, noise)),
            c=float(np.clip(it.c + rng.normal(0.0, noise / 4.0), 0.0, 0.5)) if it.c > 0 else 0.0,
            category=it.category, source=it.source, active=it.active,
        ))
    return ItemBank(items=items, name=f"{bank.name}_noise{noise}")


def experiment_robustness(n_examinees=1000, seed=2026, bank=None, progress=None,
                          cancel_check=None) -> ExperimentResult:
    """
    Experimento 7 — Robustez ante errores de calibración.

    Las respuestas se generan con los parámetros VERDADEROS del banco, pero el CAT
    selecciona y estima con parámetros PERTURBADOS (a, b y c con ruido
    gaussiano), como ocurre cuando los ítems están mal calibrados.
    """
    t0 = time.perf_counter()
    true_bank = bank if bank is not None else generate_synthetic_bank(500, model="3PL", seed=seed)
    noise_levels = [0.0, 0.1, 0.2, 0.3, 0.5]
    rows = []
    for k, noise in enumerate(noise_levels):
        rng_noise = np.random.default_rng(seed + 1000 + k)
        est_bank = true_bank if noise == 0.0 else _perturb(true_bank, noise, rng_noise)
        cfg = MonteCarloConfig(n_examinees=n_examinees, model="3PL", estimation_method="EAP",
                               selection_method=SelectionMethod.MAX_INFO.value,
                               max_items=DEFAULT_MAX_ITEMS, seed=seed)
        rng = np.random.default_rng(seed)
        theta_true = sample_population(cfg, rng)
        cat_cfg = CATConfig(estimator=cfg.build_estimator(), selector=cfg.build_selector(),
                            stopping_rule=cfg.build_stopping_rule())
        est = np.zeros(n_examinees)
        se = np.zeros(n_examinees)
        for i in range(n_examinees):
            if cancel_check is not None and cancel_check():
                raise ExperimentCancelled()
            r = simulate_cat_with_true_params(theta_true[i], true_bank, est_bank, cat_cfg, rng)
            est[i], se[i] = r.theta_estimate, r.standard_error
            if progress and (i % max(1, n_examinees // 100) == 0):
                progress(int((k + (i + 1) / n_examinees) / len(noise_levels) * 1000), 1000)
        m = recovery_metrics(theta_true, est, se)
        rows.append({"param_noise": noise, "rmse": _r(m["rmse"]), "bias": _r(m["bias"]),
                     "pearson": _r(m["pearson"]), "coverage95": _r(m["coverage_95"])})
    if progress:
        progress(1000, 1000)
    return ExperimentResult(
        key="robustness",
        columns=["param_noise", "rmse", "bias", "pearson", "coverage95"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "3PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, "noise_levels": noise_levels,
                **_bank_info(true_bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_exposure(n_examinees=1000, seed=2026, bank=None, progress=None,
                        cancel_check=None) -> ExperimentResult:
    """Experimento 8 — Exposición de ítems según el algoritmo de selección."""
    t0 = time.perf_counter()
    bank = bank if bank is not None else generate_synthetic_bank(300, model="2PL", seed=seed)
    selectors = [SelectionMethod.MAX_INFO.value, SelectionMethod.KL.value,
                 SelectionMethod.RANDOMESQUE.value, SelectionMethod.SYMPSON_HETTER.value,
                 SelectionMethod.RANDOM.value]
    run = _Runner(len(selectors), progress, cancel_check)
    rows = []
    for sel in selectors:
        res = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                      selection_method=sel, max_items=DEFAULT_MAX_ITEMS, seed=seed)
        rows.append({"selector": sel, "max_exposure": _r(res.exposure.max_rate),
                     "mean_exposure": _r(res.exposure.mean_rate),
                     "overexposed_items": res.exposure.overexposed_items,
                     "unused_items": res.exposure.unused_items,
                     "chi2_uniformity": _r(res.exposure.chi_square_uniformity(), 1),
                     "rmse": _r(res.metrics["rmse"])})
    return ExperimentResult(
        key="exposure",
        columns=["selector", "max_exposure", "mean_exposure", "overexposed_items",
                 "unused_items", "chi2_uniformity", "rmse"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_populations(n_examinees=1000, seed=2026, bank=None, progress=None,
                           cancel_check=None) -> ExperimentResult:
    """Experimento 9 — Desempeño bajo distintas distribuciones de habilidad."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    pops = [
        ("N(0,1)", dict(theta_distribution="normal", theta_mean=0.0, theta_sd=1.0)),
        ("N(-1,1)", dict(theta_distribution="normal", theta_mean=-1.0, theta_sd=1.0)),
        ("N(1,1)", dict(theta_distribution="normal", theta_mean=1.0, theta_sd=1.0)),
        ("N(0,1.5)", dict(theta_distribution="normal", theta_mean=0.0, theta_sd=1.5)),
        ("U(-3,3)", dict(theta_distribution="uniform", theta_min=-3.0, theta_max=3.0)),
    ]
    run = _Runner(len(pops), progress, cancel_check)
    rows = []
    for label, params in pops:
        m = run.run(bank, n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                    selection_method=SelectionMethod.MAX_INFO.value,
                    max_items=DEFAULT_MAX_ITEMS, seed=seed, **params).metrics
        rows.append({"population": label, "rmse": _r(m["rmse"]), "bias": _r(m["bias"]),
                     "pearson": _r(m["pearson"]), "coverage95": _r(m["coverage_95"])})
    return ExperimentResult(
        key="populations",
        columns=["population", "rmse", "bias", "pearson", "coverage95"],
        rows=rows,
        config={"n_examinees": n_examinees, "seed": seed, "model": "2PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, **_bank_info(bank)},
        elapsed_seconds=time.perf_counter() - t0,
    )


def experiment_seeds(n_examinees=1000, seed=2026, bank=None, progress=None,
                     cancel_check=None) -> ExperimentResult:
    """Experimento 10 — Variabilidad Monte Carlo entre semillas y reproducibilidad."""
    t0 = time.perf_counter()
    bank = _default_bank(bank, seed)
    seeds = [seed + k for k in range(5)]
    run = _Runner(len(seeds) + 1, progress, cancel_check)
    rows = []
    rmses = []
    common = dict(n_examinees=n_examinees, model="2PL", estimation_method="EAP",
                  selection_method=SelectionMethod.MAX_INFO.value, max_items=DEFAULT_MAX_ITEMS)
    first = None
    for s in seeds:
        res = run.run(bank, seed=s, **common)
        if first is None:
            first = res
        m = res.metrics
        rmses.append(m["rmse"])
        rows.append({"seed": s, "rmse": _r(m["rmse"]), "bias": _r(m["bias"]),
                     "pearson": _r(m["pearson"])})
    repeat = run.run(bank, seed=seeds[0], **common)
    identical = bool(np.array_equal(first.theta_est, repeat.theta_est)
                     and np.array_equal(first.theta_true, repeat.theta_true))
    return ExperimentResult(
        key="seeds",
        columns=["seed", "rmse", "bias", "pearson"],
        rows=rows,
        config={"n_examinees": n_examinees, "seeds": seeds, "model": "2PL", "estimator": "EAP",
                "max_items": DEFAULT_MAX_ITEMS, **_bank_info(bank)},
        summary_params={"rmse_mean": _r(np.mean(rmses), 4), "rmse_sd": _r(np.std(rmses, ddof=1), 4),
                        "reproducible": identical},
        elapsed_seconds=time.perf_counter() - t0,
    )


EXPERIMENTS: dict[str, Callable[..., ExperimentResult]] = {
    "ability_recovery": experiment_ability_recovery,
    "estimators": experiment_estimators,
    "selection": experiment_selection,
    "cat_vs_fixed": experiment_cat_vs_fixed,
    "bank_size": experiment_bank_size,
    "test_length": experiment_test_length,
    "robustness": experiment_robustness,
    "exposure": experiment_exposure,
    "populations": experiment_populations,
    "seeds": experiment_seeds,
}


def run_experiment(key: str, **kwargs: Any) -> ExperimentResult:
    """Ejecuta un experimento por su clave."""
    if key not in EXPERIMENTS:
        raise ValueError(f"Experimento desconocido: {key}")
    return EXPERIMENTS[key](**kwargs)
