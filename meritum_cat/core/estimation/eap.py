"""
Estimación Esperada A Posteriori (Expected A Posteriori, EAP).

Calcula la media de la distribución posterior de theta mediante cuadratura
numérica sobre una malla de puntos (Bock & Mislevy, 1982):

    theta_EAP = sum_k [ X_k * L(X_k) * W(X_k) ] / sum_k [ L(X_k) * W(X_k) ]

donde X_k son los nodos de cuadratura, W(X_k) los pesos de la prior normal y
L(X_k) la verosimilitud del patrón de respuestas. El error estándar es la raíz
de la varianza posterior. EAP no requiere optimización iterativa, es estable con
pocos ítems y es el estimador por defecto durante el CAT.
"""
from __future__ import annotations

import numpy as np

from meritum_cat.core.estimation.base import AbilityEstimator, EstimationMethod
from meritum_cat.core.irt.models import probability_3pl


class EAPEstimator(AbilityEstimator):
    """Estimador Esperado A Posteriori (EAP) por cuadratura."""

    def __init__(
        self,
        prior_mean: float = 0.0,
        prior_sd: float = 1.0,
        n_points: int = 61,
        theta_bounds: tuple[float, float] = (-4.0, 4.0),
    ) -> None:
        super().__init__(theta_bounds)
        if prior_sd <= 0.0:
            raise ValueError("prior_sd debe ser positivo.")
        if n_points < 3:
            raise ValueError("n_points debe ser al menos 3.")
        self.prior_mean = prior_mean
        self.prior_sd = prior_sd
        self.n_points = n_points

        lo, hi = self.theta_bounds
        self.nodes = np.linspace(lo, hi, n_points)
        # Pesos de cuadratura = densidad de la prior normal (normalizada luego).
        w = np.exp(-0.5 * ((self.nodes - prior_mean) / prior_sd) ** 2)
        self.weights = w / np.sum(w)

    method = EstimationMethod.EAP

    def estimate(
        self,
        responses: np.ndarray,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
    ) -> tuple[float, float]:
        responses = np.asarray(responses, dtype=float).reshape(-1, 1)
        a = np.asarray(a, dtype=float).reshape(-1, 1)
        b = np.asarray(b, dtype=float).reshape(-1, 1)
        c = np.asarray(c, dtype=float).reshape(-1, 1)

        # Matriz de probabilidades: filas = ítems, columnas = nodos de theta.
        nodes = self.nodes.reshape(1, -1)
        p = probability_3pl(nodes, a, b, c)
        eps = 1e-12
        p = np.clip(p, eps, 1.0 - eps)

        # Verosimilitud por nodo (producto sobre ítems) en escala log para estabilidad.
        log_like = np.sum(responses * np.log(p) + (1.0 - responses) * np.log(1.0 - p), axis=0)
        log_like -= np.max(log_like)  # normalización para evitar underflow
        like = np.exp(log_like)

        posterior = like * self.weights
        total = np.sum(posterior)
        if total <= 0.0:  # pragma: no cover - salvaguarda numérica
            return self.prior_mean, float(self.prior_sd)
        posterior /= total

        theta = float(np.sum(self.nodes * posterior))
        variance = float(np.sum(((self.nodes - theta) ** 2) * posterior))
        se = float(np.sqrt(variance))
        return theta, se
