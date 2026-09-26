"""
Información de Fisher del ítem y del test bajo modelos IRT logísticos.

La información del ítem cuantifica cuánta precisión aporta un ítem para estimar
la habilidad ``theta`` en un punto dado. Para el modelo 3PL (Birnbaum, 1968;
Lord, 1980):

    I_i(theta) = a_i^2 * [(P_i - c_i)^2 / (1 - c_i)^2] * [(1 - P_i) / P_i]

que se reduce a a^2 * P * (1 - P) cuando c = 0 (2PL), y a P * (1 - P) cuando
además a = 1 (1PL / Rasch). La información del test es la suma de las
informaciones de los ítems administrados, y el error estándar de la estimación
de máxima verosimilitud es SE(theta) = 1 / sqrt(I_test(theta)).
"""
from __future__ import annotations

import numpy as np

from meritum_cat.core.irt.models import probability_3pl


def item_information(theta, a=1.0, b=0.0, c=0.0):
    """
    Información de Fisher de uno o varios ítems en la habilidad ``theta``.

    Acepta escalares o arreglos (broadcasting NumPy). Devuelve la información de
    cada ítem evaluada en ``theta``.
    """
    theta = np.asarray(theta, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    c = np.asarray(c, dtype=float)

    p = probability_3pl(theta, a, b, c)
    eps = 1e-12
    p = np.clip(p, eps, 1.0 - eps)

    numerator = (p - c) ** 2
    denominator = (1.0 - c) ** 2
    # Evita división por cero cuando c -> 1 (ítem degenerado).
    denominator = np.where(denominator < eps, eps, denominator)
    info = (a ** 2) * (numerator / denominator) * ((1.0 - p) / p)
    return info


def test_information(theta, a, b, c) -> float:
    """
    Información del test: suma de la información de los ítems administrados.

    ``a``, ``b`` y ``c`` son vectores de los ítems administrados; ``theta`` es
    escalar. Devuelve un escalar.
    """
    info = item_information(theta, a, b, c)
    return float(np.sum(info))


def standard_error(theta, a, b, c) -> float:
    """
    Error estándar de la estimación de habilidad en ``theta``.

    SE(theta) = 1 / sqrt(I_test(theta)). Si la información es cero (no hay
    ítems o son no informativos), devuelve ``inf``.
    """
    info = test_information(theta, a, b, c)
    if info <= 0.0:
        return float("inf")
    return float(1.0 / np.sqrt(info))
