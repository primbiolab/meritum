"""
Interfaz común de los estimadores de habilidad y fábrica de estimadores.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import numpy as np


class EstimationMethod(str, Enum):
    """Métodos de estimación de habilidad soportados."""

    MLE = "MLE"
    MAP = "MAP"
    EAP = "EAP"


class AbilityEstimator(ABC):
    """
    Clase base abstracta de los estimadores de habilidad.

    Toda subclase implementa :meth:`estimate`, que recibe el patrón de respuestas
    y los parámetros de los ítems administrados y devuelve la pareja
    ``(theta_estimada, error_estandar)``.
    """

    method: EstimationMethod

    def __init__(self, theta_bounds: tuple[float, float] = (-4.0, 4.0)) -> None:
        self.theta_bounds = theta_bounds

    @abstractmethod
    def estimate(
        self,
        responses: np.ndarray,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
    ) -> tuple[float, float]:
        """Estima la habilidad. Devuelve (theta, error estándar)."""
        raise NotImplementedError


def make_estimator(method: EstimationMethod | str, **kwargs) -> AbilityEstimator:
    """
    Fábrica de estimadores a partir del nombre del método.

    Args:
        method: 'MLE', 'MAP' o 'EAP'.
        **kwargs: Parámetros específicos del estimador (p. ej. prior_mean,
            prior_sd para MAP/EAP; n_points para EAP).
    """
    method = EstimationMethod(method)
    # Importaciones diferidas para evitar dependencias circulares.
    from meritum_cat.core.estimation.mle import MLEEstimator
    from meritum_cat.core.estimation.map import MAPEstimator
    from meritum_cat.core.estimation.eap import EAPEstimator

    if method == EstimationMethod.MLE:
        return MLEEstimator(**kwargs)
    if method == EstimationMethod.MAP:
        return MAPEstimator(**kwargs)
    if method == EstimationMethod.EAP:
        return EAPEstimator(**kwargs)
    raise ValueError(f"Método de estimación no soportado: {method}")  # pragma: no cover
