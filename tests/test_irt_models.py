"""Modelos IRT 1PL, 2PL y 3PL: valores analíticos, dominio y propiedades."""
from __future__ import annotations

import math

import numpy as np
import pytest

from meritum_cat.core.irt.models import (
    IRTModel, apply_model, log_likelihood, probability, probability_1pl, probability_2pl, probability_3pl,
)
from meritum_cat.datasets import generate_synthetic_bank

THETA = np.linspace(-10, 10, 2001)


def ref_3pl(theta: float, a: float, b: float, c: float) -> float:
    """Implementación escalar independiente (math) del modelo 3PL."""
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))


@pytest.mark.parametrize("theta,b,expected", [(0, 0, 0.5), (1, 0, 1 / (1 + math.exp(-1))),
                                              (-2, 1, 1 / (1 + math.exp(3)))])
def test_1pl_analytic(theta, b, expected):
    assert probability_1pl(theta, b) == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize("theta,a,b", [(0.3, 1.7, -0.4), (2.0, 0.5, 1.0), (-1.2, 2.3, 0.8)])
def test_2pl_matches_reference(theta, a, b):
    assert probability_2pl(theta, a, b) == pytest.approx(ref_3pl(theta, a, b, 0.0), abs=1e-12)


@pytest.mark.parametrize("theta,a,b,c", [(0.3, 1.7, -0.4, 0.2), (2.0, 0.5, 1.0, 0.25), (-3, 2.3, 0.8, 0.1)])
def test_3pl_matches_reference(theta, a, b, c):
    assert probability_3pl(theta, a, b, c) == pytest.approx(ref_3pl(theta, a, b, c), abs=1e-12)


def test_p_equals_half_at_difficulty():
    assert probability_2pl(0.7, 1.9, 0.7) == pytest.approx(0.5)
    # En 3PL, P(b) = (1 + c) / 2.
    assert probability_3pl(0.7, 1.9, 0.7, 0.2) == pytest.approx(0.6)


@pytest.mark.parametrize("model", ["1PL", "2PL", "3PL"])
def test_probability_in_unit_interval_and_monotone(model):
    p = probability(THETA, a=1.8, b=0.3, c=0.2, model=model)
    assert np.all(p >= 0.0) and np.all(p <= 1.0)
    assert np.all(np.diff(p) >= 0.0)  # creciente en theta (a > 0)


def test_extreme_values_are_stable():
    p = probability_3pl(np.array([-1e6, -800.0, 0.0, 800.0, 1e6]), 3.0, 0.0, 0.2)
    assert np.all(np.isfinite(p))
    assert p[0] == pytest.approx(0.2) and p[-1] == pytest.approx(1.0)


def test_lower_asymptote_is_guessing():
    assert probability_3pl(-50, 1.0, 0.0, 0.25) == pytest.approx(0.25, abs=1e-12)


def test_symmetry_2pl():
    # P(b + d) = 1 - P(b - d) en el modelo 2PL.
    for d in (0.3, 1.1, 2.5):
        assert probability_2pl(1 + d, 1.4, 1) == pytest.approx(1 - probability_2pl(1 - d, 1.4, 1))


def test_vectorized_broadcasting():
    theta = np.linspace(-2, 2, 5).reshape(-1, 1)
    a = np.array([[0.8, 1.2, 2.0]])
    p = probability_2pl(theta, a, 0.0)
    assert p.shape == (5, 3)
    assert p[2, 1] == pytest.approx(0.5)


def test_model_selection_ignores_parameters():
    assert probability(0.5, a=3.0, b=0.0, c=0.3, model="1PL") == pytest.approx(probability_1pl(0.5, 0.0))
    assert probability(0.5, a=3.0, b=0.0, c=0.3, model="2PL") == pytest.approx(probability_2pl(0.5, 3.0, 0.0))
    assert IRTModel("1PL") is IRTModel.RASCH


def test_apply_model_constrains_parameters():
    bank = generate_synthetic_bank(50, model="3PL", seed=1)
    b1 = apply_model(bank, "1PL")
    b2 = apply_model(bank, "2PL")
    assert np.allclose(b1.a, 1.0) and np.allclose(b1.c, 0.0) and np.allclose(b1.b, bank.b)
    assert np.allclose(b2.a, bank.a) and np.allclose(b2.c, 0.0)
    assert apply_model(bank, "3PL") is bank
    assert not np.allclose(bank.c, 0.0)  # el original no se modifica


def test_log_likelihood_matches_reference():
    a, b, c = np.array([1.0, 1.5, 0.7]), np.array([-0.5, 0.2, 1.1]), np.array([0.0, 0.2, 0.1])
    x = np.array([1, 0, 1])
    theta = 0.4
    ref = sum(math.log(ref_3pl(theta, ai, bi, ci)) if xi else math.log(1 - ref_3pl(theta, ai, bi, ci))
              for xi, ai, bi, ci in zip(x, a, b, c))
    assert log_likelihood(theta, x, a, b, c) == pytest.approx(ref, abs=1e-10)
