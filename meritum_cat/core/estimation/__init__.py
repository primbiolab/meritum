"""
Estimación de la habilidad (theta) bajo modelos IRT.

Métodos soportados:
    * MLE — Maximum Likelihood Estimation.
    * MAP — Maximum A Posteriori.
    * EAP — Expected A Posteriori.
"""
from __future__ import annotations

from meritum_cat.core.estimation.base import (
    AbilityEstimator,
    EstimationMethod,
    make_estimator,
)
from meritum_cat.core.estimation.mle import MLEEstimator
from meritum_cat.core.estimation.map import MAPEstimator
from meritum_cat.core.estimation.eap import EAPEstimator

__all__ = [
    "AbilityEstimator",
    "EstimationMethod",
    "make_estimator",
    "MLEEstimator",
    "MAPEstimator",
    "EAPEstimator",
]
