"""
Selección por información de Kullback-Leibler (Chang & Ying, 1996).

A diferencia de la información de Fisher (local, evaluada en un punto), la
información KL integra la divergencia entre las distribuciones de respuesta en un
entorno de la estimación actual de theta, lo que la hace más robusta cuando la
estimación aún es imprecisa (pocos ítems administrados):

    KL_i(theta_hat) = integral sobre [theta_hat - d, theta_hat + d] de
        P_i(theta_hat) * log( P_i(theta_hat) / P_i(theta) )
      + (1 - P_i(theta_hat)) * log( (1 - P_i(theta_hat)) / (1 - P_i(theta)) )  d theta

La integral se aproxima numéricamente sobre una malla del entorno.
"""
from __future__ import annotations

import numpy as np

from meritum_cat.core.selection.base import ItemSelector, SelectionMethod
from meritum_cat.core.irt.models import probability_3pl

# np.trapezoid (NumPy >= 2.0) reemplaza a np.trapz (NumPy < 2.0). Se usa el disponible.
_trapezoid = np.trapezoid if hasattr(np, "trapezoid") else np.trapz


class KullbackLeiblerSelector(ItemSelector):
    """Selecciona el ítem con mayor información KL global."""

    method = SelectionMethod.KL

    def __init__(self, delta: float = 1.0, n_points: int = 21) -> None:
        if delta <= 0.0:
            raise ValueError("delta debe ser positivo.")
        if n_points < 3:
            raise ValueError("n_points debe ser al menos 3.")
        self.delta = delta
        self.n_points = n_points

    def select(self, theta, a, b, c, available, rng):
        idx = self._available_indices(available)
        grid = np.linspace(theta - self.delta, theta + self.delta, self.n_points)

        eps = 1e-12
        # P en el punto estimado (vector por ítem disponible).
        p_hat = np.clip(probability_3pl(theta, a[idx], b[idx], c[idx]), eps, 1 - eps)
        p_hat = p_hat.reshape(-1, 1)

        # P sobre la malla: filas = ítems disponibles, columnas = nodos.
        p_grid = probability_3pl(
            grid.reshape(1, -1),
            a[idx].reshape(-1, 1),
            b[idx].reshape(-1, 1),
            c[idx].reshape(-1, 1),
        )
        p_grid = np.clip(p_grid, eps, 1 - eps)

        kl = p_hat * np.log(p_hat / p_grid) + (1 - p_hat) * np.log((1 - p_hat) / (1 - p_grid))
        # Integral aproximada por regla del trapecio sobre la malla.
        kl_info = _trapezoid(kl, grid, axis=1)
        best = idx[int(np.argmax(kl_info))]
        return int(best)
