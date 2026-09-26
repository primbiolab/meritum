"""
Métricas de recuperación de la habilidad y de desempeño de la estimación.

Comparan la habilidad verdadera (theta_true) con la estimada (theta_est) a lo
largo de una muestra de examinados simulados.
"""
from __future__ import annotations

import numpy as np
from scipy import stats as _sps


def bias(theta_true, theta_est) -> float:
    """Sesgo medio: media de (estimado - verdadero)."""
    t, e = np.asarray(theta_true, float), np.asarray(theta_est, float)
    return float(np.mean(e - t))


def mae(theta_true, theta_est) -> float:
    """Error absoluto medio (Mean Absolute Error)."""
    t, e = np.asarray(theta_true, float), np.asarray(theta_est, float)
    return float(np.mean(np.abs(e - t)))


def mse(theta_true, theta_est) -> float:
    """Error cuadrático medio (Mean Squared Error)."""
    t, e = np.asarray(theta_true, float), np.asarray(theta_est, float)
    return float(np.mean((e - t) ** 2))


def rmse(theta_true, theta_est) -> float:
    """Raíz del error cuadrático medio (Root Mean Squared Error)."""
    return float(np.sqrt(mse(theta_true, theta_est)))


def pearson(theta_true, theta_est) -> float:
    """Correlación de Pearson entre verdadero y estimado."""
    t, e = np.asarray(theta_true, float), np.asarray(theta_est, float)
    if t.size < 2 or np.std(t) == 0 or np.std(e) == 0:
        return float("nan")
    return float(_sps.pearsonr(t, e)[0])


def spearman(theta_true, theta_est) -> float:
    """Correlación de rangos de Spearman entre verdadero y estimado."""
    t, e = np.asarray(theta_true, float), np.asarray(theta_est, float)
    if t.size < 2:
        return float("nan")
    return float(_sps.spearmanr(t, e)[0])


def coverage_probability(theta_true, theta_est, se, level: float = 0.95) -> float:
    """
    Probabilidad de cobertura: proporción de examinados cuyo intervalo de
    confianza (theta_est +/- z * SE) contiene la habilidad verdadera.
    """
    t = np.asarray(theta_true, float)
    e = np.asarray(theta_est, float)
    s = np.asarray(se, float)
    z = float(_sps.norm.ppf(0.5 + level / 2.0))
    inside = np.abs(e - t) <= z * s
    return float(np.mean(inside))


def recovery_metrics(theta_true, theta_est, se=None) -> dict[str, float]:
    """Calcula de una vez el conjunto de métricas de recuperación de habilidad."""
    metrics = {
        "bias": bias(theta_true, theta_est),
        "mae": mae(theta_true, theta_est),
        "mse": mse(theta_true, theta_est),
        "rmse": rmse(theta_true, theta_est),
        "pearson": pearson(theta_true, theta_est),
        "spearman": spearman(theta_true, theta_est),
    }
    if se is not None:
        metrics["coverage_95"] = coverage_probability(theta_true, theta_est, se, 0.95)
    return metrics
