"""Reproducibilidad por semilla y experimentos científicos predefinidos."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from meritum_cat.core.selection import SelectionMethod
from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo
from meritum_cat.experiments import EXPERIMENTS, ExperimentCancelled, run_experiment


@pytest.mark.parametrize("selector", [s.value for s in SelectionMethod])
def test_same_seed_same_results(bank_2pl, selector):
    cfg = MonteCarloConfig(n_examinees=60, selection_method=selector, max_items=8, seed=2024,
                           sh_iterations=2, sh_calibration_examinees=60)
    r1 = run_monte_carlo(bank_2pl, cfg)
    r2 = run_monte_carlo(bank_2pl, cfg)
    assert np.array_equal(r1.theta_true, r2.theta_true)
    assert np.array_equal(r1.theta_est, r2.theta_est)
    assert r1.administered == r2.administered


def test_different_seed_different_results(bank_2pl):
    cfg = MonteCarloConfig(n_examinees=60, max_items=8, seed=1)
    r1 = run_monte_carlo(bank_2pl, cfg)
    r2 = run_monte_carlo(bank_2pl, replace(cfg, seed=2))
    assert not np.array_equal(r1.theta_true, r2.theta_true)


def test_progress_does_not_change_results(bank_2pl):
    cfg = MonteCarloConfig(n_examinees=50, max_items=6, seed=9)
    r1 = run_monte_carlo(bank_2pl, cfg)
    r2 = run_monte_carlo(bank_2pl, cfg, progress_callback=lambda d, t: None, cancel_check=lambda: False)
    assert np.array_equal(r1.theta_est, r2.theta_est)


@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_each_experiment_runs(key):
    res = run_experiment(key, n_examinees=40, seed=5)
    assert res.key == key and res.rows
    for row in res.rows:
        assert set(res.columns) <= set(row)


def test_experiment_scientific_expectations():
    cvf = run_experiment("cat_vs_fixed", n_examinees=300, seed=11)
    for length in (10, 20, 30):
        cat = next(r for r in cvf.rows if r["test_type"] == "cat" and r["test_length"] == length)
        fixed = next(r for r in cvf.rows if r["test_type"] == "fixed" and r["test_length"] == length)
        assert cat["rmse"] < fixed["rmse"]
    tl = run_experiment("test_length", n_examinees=300, seed=11)
    rmses = [r["rmse"] for r in tl.rows]
    assert rmses[0] > rmses[-1]
    seeds = run_experiment("seeds", n_examinees=100, seed=11)
    assert seeds.summary_params["reproducible"] is True


def test_experiment_reproducible():
    a = run_experiment("estimators", n_examinees=80, seed=3)
    b = run_experiment("estimators", n_examinees=80, seed=3)
    assert a.rows == b.rows


def test_experiment_cancellation():
    with pytest.raises(ExperimentCancelled):
        run_experiment("bank_size", n_examinees=100, seed=1, cancel_check=lambda: True)
    with pytest.raises(ExperimentCancelled):
        run_experiment("robustness", n_examinees=100, seed=1, cancel_check=lambda: True)


def test_unknown_experiment():
    with pytest.raises(ValueError):
        run_experiment("nope")
