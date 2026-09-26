"""Información de Fisher: fórmulas cerradas, derivada numérica independiente y propiedades."""
from __future__ import annotations

import numpy as np
import pytest

from meritum_cat.core.irt.information import item_information, standard_error
from meritum_cat.core.irt.information import test_information as tif
from meritum_cat.core.irt.models import probability_3pl


def numerical_fisher(theta: float, a: float, b: float, c: float, h: float = 1e-5) -> float:
    """I(θ) = P'(θ)² / [P(θ)(1 − P(θ))], con derivada por diferencias centrales."""
    p = float(probability_3pl(theta, a, b, c))
    dp = (float(probability_3pl(theta + h, a, b, c)) - float(probability_3pl(theta - h, a, b, c))) / (2 * h)
    return dp * dp / (p * (1 - p))


@pytest.mark.parametrize("theta,a,b,c", [(0.0, 1.0, 0.0, 0.0), (0.7, 1.8, -0.3, 0.0), (-1.0, 0.6, 0.5, 0.2),
                                         (1.5, 2.2, 1.0, 0.25), (-2.5, 1.3, -2.0, 0.15)])
def test_information_matches_numerical_derivative(theta, a, b, c):
    assert item_information(theta, a, b, c) == pytest.approx(numerical_fisher(theta, a, b, c), rel=1e-5)


def test_2pl_closed_form():
    theta = np.linspace(-3, 3, 61)
    a, b = 1.7, 0.4
    p = probability_3pl(theta, a, b, 0.0)
    assert np.allclose(item_information(theta, a, b, 0.0), a ** 2 * p * (1 - p))


def test_2pl_maximum_at_difficulty():
    a, b = 2.0, 0.5
    grid = np.linspace(-4, 4, 8001)
    info = item_information(grid, a, b, 0.0)
    assert grid[np.argmax(info)] == pytest.approx(b, abs=1e-3)
    assert info.max() == pytest.approx(a ** 2 / 4, rel=1e-6)


def test_3pl_maximum_location_birnbaum():
    # Máximo de la información 3PL (Birnbaum): θ* = b + (1/a) ln[(1 + sqrt(1 + 8c)) / 2].
    a, b, c = 1.5, 0.2, 0.25
    grid = np.linspace(-4, 4, 80001)
    theta_star = b + np.log((1 + np.sqrt(1 + 8 * c)) / 2) / a
    assert grid[np.argmax(item_information(grid, a, b, c))] == pytest.approx(theta_star, abs=1e-3)


def test_guessing_reduces_information():
    assert item_information(0.0, 1.2, 0.0, 0.25) < item_information(0.0, 1.2, 0.0, 0.0)


def test_information_non_negative_everywhere():
    grid = np.linspace(-8, 8, 400)
    for a, b, c in [(0.3, -2, 0), (2.5, 1, 0.3), (1.0, 0.0, 0.9)]:
        assert np.all(item_information(grid, a, b, c) >= 0)


def test_test_information_is_sum_and_se():
    a = np.array([1.0, 1.4, 0.8])
    b = np.array([-0.5, 0.0, 0.7])
    c = np.array([0.0, 0.1, 0.2])
    total = tif(0.2, a, b, c)
    assert total == pytest.approx(sum(item_information(0.2, a[i], b[i], c[i]) for i in range(3)))
    assert standard_error(0.2, a, b, c) == pytest.approx(1 / np.sqrt(total))


def test_standard_error_empty_is_infinite():
    assert standard_error(0.0, np.array([]), np.array([]), np.array([])) == float("inf")
