"""
Motor de una sesión de Computerized Adaptive Testing (CAT).

Implementa el ciclo adaptativo estándar:

    1. Seleccionar el siguiente ítem (con posible balanceo de contenido).
    2. Administrar el ítem y observar (o simular) la respuesta.
    3. Reestimar la habilidad y su error estándar.
    4. Evaluar el criterio de terminación.

En modo simulación las respuestas se generan a partir de la habilidad verdadera
del examinado y del modelo IRT (respuesta correcta con probabilidad P(theta)).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from meritum_cat.models import ItemBank, CATResult
from meritum_cat.core.irt.information import test_information
from meritum_cat.core.estimation.base import AbilityEstimator
from meritum_cat.core.selection.base import ItemSelector
from meritum_cat.core.stopping.rules import StoppingRule, CATState
from meritum_cat.core.balancing.content import ContentBalancer


@dataclass
class CATConfig:
    """Configuración de una sesión CAT."""

    estimator: AbilityEstimator
    selector: ItemSelector
    stopping_rule: StoppingRule
    initial_theta: float = 0.0
    balancer: ContentBalancer | None = None
    theta_bounds: tuple[float, float] = (-4.0, 4.0)


def _simulate_response(theta_true: float, a: float, b: float, c: float,
                       rng: np.random.Generator) -> int:
    """Simula una respuesta dicotómica dada la habilidad verdadera."""
    z = float(a) * (theta_true - float(b))
    # Logística escalar estable: evita overflow de exp para |z| grande.
    if z >= 0:
        logistic = 1.0 / (1.0 + math.exp(-z))
    else:
        ez = math.exp(z)
        logistic = ez / (1.0 + ez)
    p = float(c) + (1.0 - float(c)) * logistic
    return int(rng.random() < p)


def simulate_cat(
    theta_true: float,
    bank: ItemBank,
    config: CATConfig,
    rng: np.random.Generator,
    true_bank: ItemBank | None = None,
) -> CATResult:
    """
    Ejecuta una sesión CAT simulada para un examinado de habilidad ``theta_true``.

    Args:
        theta_true: Habilidad verdadera del examinado simulado.
        bank: Banco con los parámetros que el CAT usa para seleccionar y estimar.
        config: Configuración del CAT.
        rng: Generador pseudoaleatorio (reproducibilidad).
        true_bank: Banco con los parámetros verdaderos usados para generar las
            respuestas (mismo orden de ítems). Si es ``None`` se usa ``bank``.
            Permite estudiar la robustez ante errores de calibración.

    Devuelve un :class:`CATResult` con la estimación final y las trazas de theta,
    error estándar e información acumulada tras cada ítem.
    """
    a, b, c = bank.a, bank.b, bank.c
    n = bank.n_items
    if n == 0:
        raise ValueError("El banco no tiene ítems activos.")
    gen = true_bank if true_bank is not None else bank
    if gen.n_items != n:
        raise ValueError("El banco verdadero y el estimado deben tener los mismos ítems.")
    ta, tb, tc = gen.a, gen.b, gen.c

    available = np.ones(n, dtype=bool)
    administered: list[int] = []
    responses: list[int] = []
    admin_categories: list[str] = []
    theta_hist: list[float] = []
    se_hist: list[float] = []
    info_hist: list[float] = []

    theta_hat = config.initial_theta
    se = float("inf")
    stop_reason = "bank_exhausted"

    # Selectores con estado por examinado (p. ej. Sympson-Hetter) se reinician.
    start_session = getattr(config.selector, "start_session", None)
    if start_session is not None:
        start_session()

    while True:
        # Balanceo de contenido: restringe la disponibilidad si está activo.
        selectable = available
        if config.balancer is not None:
            selectable = config.balancer.restrict(available, admin_categories)

        idx = config.selector.select(theta_hat, a, b, c, selectable, rng)

        resp = _simulate_response(theta_true, ta[idx], tb[idx], tc[idx], rng)
        administered.append(idx)
        responses.append(resp)
        admin_categories.append(bank.category_of(idx))
        available[idx] = False

        adm = np.array(administered)
        theta_hat, se = config.estimator.estimate(
            np.array(responses, dtype=float), a[adm], b[adm], c[adm]
        )
        info = test_information(theta_hat, a[adm], b[adm], c[adm])

        theta_hist.append(theta_hat)
        se_hist.append(se)
        info_hist.append(info)

        n_remaining = int(np.sum(available))
        state = CATState(
            n_administered=len(administered),
            standard_error=se,
            information=info,
            n_remaining=n_remaining,
        )
        stop, reason = config.stopping_rule.should_stop(state)
        if stop:
            stop_reason = reason
            break
        if n_remaining == 0:
            stop_reason = "bank_exhausted"
            break

    return CATResult(
        theta_true=theta_true,
        theta_estimate=theta_hat,
        standard_error=se,
        administered_items=administered,
        responses=responses,
        theta_history=theta_hist,
        se_history=se_hist,
        information_history=info_hist,
        stop_reason=stop_reason,
    )


def simulate_cat_with_true_params(
    theta_true: float,
    true_bank: ItemBank,
    estimated_bank: ItemBank,
    config: CATConfig,
    rng: np.random.Generator,
) -> CATResult:
    """CAT cuyas respuestas provienen de ``true_bank`` y cuya selección/estimación usa ``estimated_bank``."""
    return simulate_cat(theta_true, estimated_bank, config, rng, true_bank=true_bank)


def run_fixed_test(
    theta_true: float,
    bank: ItemBank,
    estimator: AbilityEstimator,
    n_items: int,
    rng: np.random.Generator,
) -> CATResult:
    """
    Ejecuta un test de longitud fija (no adaptativo) para comparación.

    Administra ``n_items`` ítems elegidos al azar del banco y estima la habilidad
    al final. Sirve de referencia frente al CAT (experimento CAT vs Fixed).
    """
    a, b, c = bank.a, bank.b, bank.c
    n = bank.n_items
    k = min(n_items, n)
    idx = rng.choice(n, size=k, replace=False)

    responses = [_simulate_response(theta_true, a[i], b[i], c[i], rng) for i in idx]
    theta_hat, se = estimator.estimate(np.array(responses, dtype=float), a[idx], b[idx], c[idx])
    info = test_information(theta_hat, a[idx], b[idx], c[idx])

    return CATResult(
        theta_true=theta_true,
        theta_estimate=theta_hat,
        standard_error=se,
        administered_items=list(idx),
        responses=responses,
        theta_history=[theta_hat],
        se_history=[se],
        information_history=[info],
        stop_reason="fixed_length",
    )
