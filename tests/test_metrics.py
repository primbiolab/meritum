"""Métricas de recuperación frente a valores calculados a mano e implementaciones de referencia."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from meritum_cat.core.statistics import (
    bias, coverage_probability, mae, mse, pearson, recovery_metrics, rmse, spearman,
)

T = np.array([0.0, 1.0, -1.0, 2.0])
E = np.array([0.5, 1.0, -2.0, 2.5])  # errores: 0.5, 0, -1, 0.5


def test_hand_computed_values():
    assert bias(T, E) == pytest.approx(0.0)
    assert mae(T, E) == pytest.approx(0.5)
    assert mse(T, E) == pytest.approx((0.25 + 0 + 1 + 0.25) / 4)
    assert rmse(T, E) == pytest.approx(np.sqrt(0.375))


def test_correlations_match_scipy():
    rng = np.random.default_rng(1)
    t = rng.normal(size=200)
    e = t + rng.normal(scale=0.4, size=200)
    assert pearson(t, e) == pytest.approx(stats.pearsonr(t, e)[0])
    assert pearson(t, e) == pytest.approx(np.corrcoef(t, e)[0, 1])
    assert spearman(t, e) == pytest.approx(stats.spearmanr(t, e)[0])


def test_degenerate_correlation_is_nan():
    assert np.isnan(pearson([1, 1, 1], [1, 2, 3]))
    assert np.isnan(pearson([1], [1]))


def test_coverage_probability():
    t = np.zeros(4)
    e = np.array([0.1, 0.5, 2.0, -0.3])
    se = np.full(4, 0.5)  # intervalo ±0.98
    assert coverage_probability(t, e, se) == pytest.approx(0.75)


def test_coverage_nominal_under_correct_model():
    rng = np.random.default_rng(3)
    t = rng.normal(size=20000)
    se = np.full_like(t, 0.3)
    e = t + rng.normal(scale=0.3, size=t.size)
    assert coverage_probability(t, e, se) == pytest.approx(0.95, abs=0.01)


def test_recovery_metrics_keys():
    m = recovery_metrics(T, E, np.ones(4))
    assert set(m) == {"bias", "mae", "mse", "rmse", "pearson", "spearman", "coverage_95"}
    assert m["rmse"] ** 2 == pytest.approx(m["mse"])
