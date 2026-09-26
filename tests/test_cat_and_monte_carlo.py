"""Motor CAT, sesión paso a paso y simulación Monte Carlo."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from meritum_cat.core.estimation import EAPEstimator, MLEEstimator
from meritum_cat.core.selection import MaximumInformationSelector, RandomSelector
from meritum_cat.core.simulation import CATConfig, CATSession, MonteCarloConfig, run_monte_carlo, simulate_cat
from meritum_cat.core.simulation.cat import run_fixed_test, simulate_cat_with_true_params
from meritum_cat.core.stopping import MaxItemsRule, make_stopping_rule
from meritum_cat.models import Item, ItemBank


def test_cat_basic_result(bank_2pl, rng):
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(12))
    r = simulate_cat(0.5, bank_2pl, cfg, rng)
    assert r.test_length == 12 and len(set(r.administered_items)) == 12
    assert len(r.theta_history) == len(r.se_history) == len(r.information_history) == 12
    assert r.stop_reason == "max_items"
    assert np.all(np.diff(r.information_history) > -1.0)  # la información se acumula
    assert r.se_history[-1] < r.se_history[0]


def test_cat_exhausts_small_bank(rng):
    bank = ItemBank([Item(f"I{i}", 1.0, b, 0.0) for i, b in enumerate([-1, 0, 1])])
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(10))
    r = simulate_cat(0.0, bank, cfg, rng)
    assert r.test_length == 3 and r.stop_reason == "bank_exhausted"


def test_inactive_items_never_administered(rng):
    items = [Item(f"I{i}", 1.0, float(i) / 10, 0.0, active=(i % 2 == 0)) for i in range(20)]
    bank = ItemBank(items)
    assert bank.n_items == 10 and bank.n_total == 20
    cfg = CATConfig(EAPEstimator(), RandomSelector(), MaxItemsRule(10))
    r = simulate_cat(0.0, bank, cfg, rng)
    ids = {bank.active_items[i].item_id for i in r.administered_items}
    assert all(int(x[1:]) % 2 == 0 for x in ids)


def test_session_equals_batch_engine(bank_2pl):
    cfg = CATConfig(EAPEstimator(), RandomSelector(), make_stopping_rule(max_items=15))
    batch = simulate_cat(0.7, bank_2pl, cfg, np.random.default_rng(42))
    s = CATSession(bank_2pl, cfg, np.random.default_rng(42), theta_true=0.7)
    s.run_to_end()
    assert s.administered == batch.administered_items
    assert s.responses == batch.responses
    assert s.theta == pytest.approx(batch.theta_estimate)


def test_session_manual_answers(bank_2pl, rng):
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(3))
    s = CATSession(bank_2pl, cfg, rng)
    for resp in (1, 1, 1):
        s.next_item()
        s.answer(resp)
    assert s.finished and s.stop_reason == "max_items" and s.theta > 0
    with pytest.raises(RuntimeError):
        s.next_item()


def test_true_params_vs_estimated_params(bank_2pl, rng):
    shifted = ItemBank([replace(it, b=it.b + 1.0) for it in bank_2pl.items])
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(30))
    ests = [simulate_cat_with_true_params(0.0, bank_2pl, shifted, cfg, rng).theta_estimate for _ in range(40)]
    # Los ítems parecen 1 logit más difíciles de lo que son: se sobreestima la habilidad.
    assert np.mean(ests) > 0.5


def test_fixed_test(bank_2pl, rng):
    r = run_fixed_test(0.0, bank_2pl, EAPEstimator(), 25, rng)
    assert r.test_length == 25 and r.stop_reason == "fixed_length"


def test_monte_carlo_shapes_and_metrics(bank_2pl):
    res = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=200, max_items=15, seed=1))
    assert res.theta_true.shape == res.theta_est.shape == (200,)
    assert res.mean_test_length == 15
    m = res.metrics
    assert abs(m["bias"]) < 0.15 and m["rmse"] < 0.5 and m["pearson"] > 0.85
    assert 0.8 < m["coverage_95"] <= 1.0
    k, rmse_k, se_k = res.precision_by_item_number()
    assert len(k) == 15 and rmse_k[-1] < rmse_k[0] and se_k[-1] < se_k[0]


def test_cat_beats_fixed(bank_2pl):
    cat = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=400, max_items=15, seed=3))
    fixed = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=400, max_items=15, seed=3, fixed_test=True))
    assert cat.metrics["rmse"] < fixed.metrics["rmse"]


def test_uniform_population_bounds(bank_2pl):
    res = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=300, theta_distribution="uniform",
                                                     theta_min=-1, theta_max=2, max_items=5, seed=2))
    assert res.theta_true.min() >= -1 and res.theta_true.max() <= 2


def test_progress_and_cancellation(bank_2pl):
    calls = []
    run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=50, max_items=5),
                    progress_callback=lambda d, t: calls.append((d, t)))
    assert calls[-1] == (50, 50)
    assert run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=50, max_items=5),
                           cancel_check=lambda: True) is None


def test_sympson_hetter_monte_carlo(bank_2pl):
    base = MonteCarloConfig(n_examinees=300, max_items=15, seed=4)
    mi = run_monte_carlo(bank_2pl, base)
    sh = run_monte_carlo(bank_2pl, replace(base, selection_method="Sympson-Hetter", sh_r_max=0.25,
                                            sh_iterations=6, sh_calibration_examinees=300))
    assert sh.exposure.max_rate < mi.exposure.max_rate
    assert sh.exposure.max_rate < 0.45
    assert len(sh.sh_history) == 6


@pytest.mark.parametrize("field,value,code", [
    ("n_examinees", 0, "must_be_positive_int"), ("theta_sd", 0.0, "must_be_positive"),
    ("theta_distribution", "gamma", "invalid_choice"), ("model", "4PL", "invalid_choice"),
    ("estimation_method", "X", "invalid_choice"), ("selection_method", "X", "invalid_choice"),
    ("max_items", 0, "must_be_positive_int"), ("se_threshold", -0.1, "must_be_positive"),
    ("prior_sd", 0.0, "must_be_positive"), ("seed", -1, "invalid_seed"),
    ("randomesque_bin", 0, "must_be_positive_int"), ("sh_r_max", 1.5, "must_be_probability"),
])
def test_config_validation(field, value, code):
    cfg = replace(MonteCarloConfig(), **{field: value})
    assert (field, code) in cfg.validate()


def test_config_needs_stopping_rule(bank_2pl):
    cfg = MonteCarloConfig(max_items=None)
    assert ("max_items", "need_stopping_rule") in cfg.validate()
    with pytest.raises(ValueError):
        run_monte_carlo(bank_2pl, cfg)


def test_uniform_bounds_validation():
    cfg = MonteCarloConfig(theta_distribution="uniform", theta_min=1.0, theta_max=1.0)
    assert ("theta_min", "min_lt_max") in cfg.validate()


def test_mle_monte_carlo_runs(bank_2pl):
    res = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=100, estimation_method="MLE", max_items=10))
    assert np.all(np.abs(res.theta_est) <= 4)
    assert isinstance(MonteCarloConfig(estimation_method="MLE").build_estimator(), MLEEstimator)
