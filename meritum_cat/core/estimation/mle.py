"""
Estimación por Máxima Verosimilitud (Maximum Likelihood Estimation, MLE).

Busca el valor de theta que maximiza la log-verosimilitud del patrón de
respuestas. Cuando el patrón es degenerado (todas correctas o todas
incorrectas) el máximo tiende a +/- infinito; en ese caso se devuelve el límite
correspondiente del rango admisible. El error estándar se obtiene de la
información de Fisher del test evaluada en la estimación.
"""
from __future__ import annotations

import numpy as np
from scipy import optimize

from meritum_cat.core.estimation.base import AbilityEstimator, EstimationMethod
from meritum_cat.core.irt.models import log_likelihood
from meritum_cat.core.irt.information import standard_error


class MLEEstimator(AbilityEstimator):
    """Estimador de máxima verosimilitud (MLE)."""

    method = EstimationMethod.MLE

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
        n_correct = float(np.sum(responses))

        # Patrones degenerados: la verosimilitud es monótona; el óptimo está en
        # el borde del rango admisible.
        if n_correct == 0:
            theta = lo
        elif n_correct == len(responses):
            theta = hi
        else:
            neg_ll = lambda t: -log_likelihood(t, responses, a, b, c)
            result = optimize.minimize_scalar(
                neg_ll, bounds=(lo, hi), method="bounded",
                options={"xatol": 1e-4},
            )
            theta = float(result.x)

        se = standard_error(theta, a, b, c)
        return theta, se
