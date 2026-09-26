"""Estimadores MLE, MAP y EAP frente a implementaciones independientes y casos límite."""
from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import integrate

from meritum_cat.core.estimation import EAPEstimator, MAPEstimator, MLEEstimator, make_estimator
from meritum_cat.core.irt.information import test_information as tif

A = np.array([1.2, 0.8, 1.5, 1.0, 2.0, 0.9, 1.3])
B = np.array([-1.0, -0.5, 0.0, 0.3, 0.8, 1.2, -0.2])
C = np.array([0.0, 0.1, 0.2, 0.0, 0.15, 0.05, 0.0])
X = np.array([1, 1, 1, 0, 0, 1, 0])


def ref_loglik(theta: float) -> float:
    total = 0.0
    for a, b, c, x in zip(A, B, C, X):
        p = c + (1 - c) / (1 + math.exp(-a * (theta - b)))
        total += math.log(p) if x else math.log(1 - p)
    return total


def test_mle_matches_grid_search():
    grid = np.linspace(-4, 4, 80001)
    ref = grid[np.argmax([ref_loglik(t) for t in grid])]
    theta, se = MLEEstimator().estimate(X, A, B, C)
    assert theta == pytest.approx(ref, abs=2e-3)
    assert se == pytest.approx(1 / math.sqrt(tif(theta, A, B, C)), rel=1e-6)


def test_mle_degenerate_patterns_hit_bounds():
    est = MLEEstimator(theta_bounds=(-4, 4))
    assert est.estimate(np.ones(5), A[:5], B[:5], C[:5])[0] == 4
    assert est.estimate(np.zeros(5), A[:5], B[:5], C[:5])[0] == -4


def test_map_matches_grid_posterior_mode():
    grid = np.linspace(-4, 4, 80001)
    logpost = [ref_loglik(t) - 0.5 * ((t - 0.2) / 0.8) ** 2 for t in grid]
    ref = grid[int(np.argmax(logpost))]
    theta, se = MAPEstimator(prior_mean=0.2, prior_sd=0.8).estimate(X, A, B, C)
    assert theta == pytest.approx(ref, abs=2e-3)
    assert se == pytest.approx(1 / math.sqrt(tif(theta, A, B, C) + 1 / 0.8 ** 2), rel=1e-6)


def test_eap_matches_numerical_integration():
    def post(t, k):
        return t ** k * math.exp(ref_loglik(t)) * math.exp(-0.5 * t * t)
    z = integrate.quad(lambda t: post(t, 0), -4, 4)[0]
    mean = integrate.quad(lambda t: post(t, 1), -4, 4)[0] / z
    second = integrate.quad(lambda t: post(t, 2), -4, 4)[0] / z
    sd = math.sqrt(second - mean ** 2)
    theta, se = EAPEstimator(n_points=401).estimate(X, A, B, C)
    assert theta == pytest.approx(mean, abs=2e-3)
    assert se == pytest.approx(sd, abs=2e-3)


def test_eap_with_no_items_returns_prior():
    theta, se = EAPEstimator(prior_mean=0.5, prior_sd=1.0, n_points=201).estimate(
        np.array([]), np.array([]), np.array([]), np.array([]))
    assert theta == pytest.approx(0.5, abs=1e-3)
    assert se == pytest.approx(1.0, abs=0.02)


def test_bayesian_estimators_finite_with_degenerate_patterns():
    for est in (MAPEstimator(), EAPEstimator()):
        theta, se = est.estimate(np.ones(3), A[:3], B[:3], C[:3])
        assert -4 < theta < 4 and 0 < se < 2


def test_map_shrinks_towards_prior():
    theta_mle, _ = MLEEstimator().estimate(X, A, B, C)
    theta_map, _ = MAPEstimator(prior_mean=-2.0, prior_sd=0.5).estimate(X, A, B, C)
    assert theta_map < theta_mle


@pytest.mark.parametrize("method", ["MLE", "MAP", "EAP"])
def test_consistency_with_long_test(method):
    rng = np.random.default_rng(5)
    n = 400
    a = rng.lognormal(0, 0.25, n)
    b = rng.normal(0, 1, n)
    c = np.zeros(n)
    theta_true = 0.8
    p = 1 / (1 + np.exp(-a * (theta_true - b)))
    x = (rng.random(n) < p).astype(float)
    theta, se = make_estimator(method).estimate(x, a, b, c)
    assert abs(theta - theta_true) < 3 * se
    assert se < 0.15


def test_invalid_estimator_parameters():
    with pytest.raises(ValueError):
        MAPEstimator(prior_sd=0)
    with pytest.raises(ValueError):
        EAPEstimator(prior_sd=-1)
    with pytest.raises(ValueError):
        EAPEstimator(n_points=2)
    with pytest.raises(ValueError):
        make_estimator("XYZ")
