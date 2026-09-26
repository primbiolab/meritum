"""
Modelos logísticos IRT: Rasch/1PL, 2PL y 3PL.

Todas las funciones están vectorizadas con NumPy y son numéricamente estables
(la logística se evalúa con ``scipy.special.expit``, sin overflow). Aceptan
escalares o arreglos tanto en la habilidad ``theta`` como en los parámetros del
ítem, aplicando *broadcasting* de NumPy.

Modelos (P es la probabilidad de respuesta correcta):

    1PL / Rasch:  P = 1 / (1 + exp[-(theta - b)])
    2PL:          P = 1 / (1 + exp[-a (theta - b)])
    3PL:          P = c + (1 - c) / (1 + exp[-a (theta - b)])

donde theta = habilidad, a = discriminación, b = dificultad, c = pseudo-azar.
"""
from __future__ import annotations

from enum import Enum

import numpy as np
from scipy.special import expit

class IRTModel(str, Enum):
    """Modelos IRT soportados."""

    RASCH = "1PL"
    ONE_PL = "1PL"
    TWO_PL = "2PL"
    THREE_PL = "3PL"


def _logistic(z):
    """
    Función logística estándar 1/(1+exp(-z)).

    Se usa ``scipy.special.expit``, que es numéricamente estable para cualquier
    valor de z (no produce overflow ni NaN en los extremos).
    """
    return expit(z)


def probability_1pl(theta, b):
    """Probabilidad de respuesta correcta bajo el modelo Rasch / 1PL."""
    theta = np.asarray(theta, dtype=float)
    b = np.asarray(b, dtype=float)
    return _logistic(theta - b)


def probability_2pl(theta, a, b):
    """Probabilidad de respuesta correcta bajo el modelo 2PL."""
    theta = np.asarray(theta, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    return _logistic(a * (theta - b))


def probability_3pl(theta, a, b, c):
    """Probabilidad de respuesta correcta bajo el modelo 3PL."""
    theta = np.asarray(theta, dtype=float)
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    c = np.asarray(c, dtype=float)
    return c + (1.0 - c) * _logistic(a * (theta - b))


def probability(theta, a=1.0, b=0.0, c=0.0, model: IRTModel | str = IRTModel.TWO_PL):
    """
    Probabilidad de respuesta correcta bajo el modelo IRT indicado.

    Punto de entrada unificado. Según ``model`` ignora los parámetros que no
    apliquen (p. ej. en 1PL se ignoran ``a`` y ``c``; en 2PL se ignora ``c``).

    Devuelve un valor (o arreglo) en el intervalo cerrado [0, 1].
    """
    model = IRTModel(model)
    if model in (IRTModel.RASCH, IRTModel.ONE_PL):
        p = probability_1pl(theta, b)
    elif model == IRTModel.TWO_PL:
        p = probability_2pl(theta, a, b)
    elif model == IRTModel.THREE_PL:
        p = probability_3pl(theta, a, b, c)
    else:  # pragma: no cover - IRTModel garantiza el dominio
        raise ValueError(f"Modelo IRT no soportado: {model}")
    return np.clip(p, 0.0, 1.0)


def apply_model(bank, model: IRTModel | str):
    """
    Devuelve una copia del banco interpretada bajo el modelo IRT indicado.

    * 1PL / Rasch: a = 1 y c = 0 para todos los ítems (solo varía b).
    * 2PL: c = 0 (varían a y b).
    * 3PL: se conservan a, b y c.

    Así, seleccionar un modelo en la interfaz determina de forma explícita qué
    parámetros intervienen tanto en la generación de respuestas como en la
    estimación. El banco original no se modifica.
    """
    from dataclasses import replace
    from meritum_cat.models import ItemBank

    model = IRTModel(model)
    if model == IRTModel.THREE_PL:
        return bank
    if model in (IRTModel.RASCH, IRTModel.ONE_PL):
        items = [replace(it, a=1.0, c=0.0) for it in bank.items]
    else:
        items = [replace(it, c=0.0) for it in bank.items]
    return ItemBank(items=items, name=bank.name)


def log_likelihood(theta, responses, a, b, c) -> float:
    """
    Log-verosimilitud de un patrón de respuestas para una habilidad ``theta``.

    Args:
        theta: Habilidad (escalar).
        responses: Vector de respuestas observadas (1 correcto, 0 incorrecto).
        a, b, c: Vectores de parámetros de los ítems administrados.

    Se acota P a (eps, 1-eps) para evitar log(0).
    """
    responses = np.asarray(responses, dtype=float)
    p = probability_3pl(theta, a, b, c)
    eps = 1e-12
    p = np.clip(p, eps, 1.0 - eps)
    return float(np.sum(responses * np.log(p) + (1.0 - responses) * np.log(1.0 - p)))
