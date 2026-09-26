"""
Estimación Máxima A Posteriori (Maximum A Posteriori, MAP).

Maximiza el logaritmo de la densidad posterior, es decir la log-verosimilitud
más el log de una densidad previa (prior) normal N(prior_mean, prior_sd^2) sobre
theta. A diferencia de MLE, la prior regulariza la estimación y produce valores
finitos incluso con patrones de respuesta degenerados. El error estándar se
obtiene de la información posterior: I_test(theta) + 1 / prior_sd^2.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize

from meritum_cat.core.estimation.base import AbilityEstimator, EstimationMethod
from meritum_cat.core.irt.models import log_likelihood
from meritum_cat.core.irt.information import test_information


class MAPEstimator(AbilityEstimator):
    """Estimador Máxima A Posteriori (MAP) con prior normal."""

    method = EstimationMethod.MAP

    def __init__(
        self,
        prior_mean: float = 0.0,
        prior_sd: float = 1.0,
        theta_bounds: tuple[float, float] = (-4.0, 4.0),
    ) -> None:
        super().__init__(theta_bounds)
        if prior_sd <= 0.0:
            raise ValueError("prior_sd debe ser positivo.")
        self.prior_mean = prior_mean
        self.prior_sd = prior_sd

    def _neg_log_posterior(self, theta, responses, a, b, c) -> float:
        ll = log_likelihood(theta, responses, a, b, c)
        log_prior = -0.5 * ((theta - self.prior_mean) / self.prior_sd) ** 2
        return -(ll + log_prior)

    def estimate(
        self,
        responses: np.ndarray,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
    ) -> tuple[float, float]:
        responses = np.asarray(responses, dtype=float)
        a = np.asarray(a, dtype=float)
        b = np.asarray(b, dtype=float)
        c = np.asarray(c, dtype=float)

        lo, hi = self.theta_bounds
        result = optimize.minimize_scalar(
            lambda t: self._neg_log_posterior(t, responses, a, b, c),
            bounds=(lo, hi), method="bounded", options={"xatol": 1e-4},
        )
        theta = float(result.x)

        posterior_info = test_information(theta, a, b, c) + 1.0 / (self.prior_sd ** 2)
        se = float(1.0 / np.sqrt(posterior_info)) if posterior_info > 0 else float("inf")
        return theta, se
