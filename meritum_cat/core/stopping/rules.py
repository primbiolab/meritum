"""
Criterios de terminación del test adaptativo.

Cada regla implementa :meth:`should_stop`, que recibe el estado actual del CAT
(número de ítems administrados, error estándar actual, información acumulada y el
número de ítems restantes en el banco) y decide si el test debe finalizar,
devolviendo también una etiqueta con el motivo.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CATState:
    """Estado del CAT evaluado por las reglas de terminación."""

    n_administered: int
    standard_error: float
    information: float
    n_remaining: int


class StoppingRule(ABC):
    """Clase base abstracta de las reglas de terminación."""

    @abstractmethod
    def should_stop(self, state: CATState) -> tuple[bool, str]:
        """Devuelve (detener, motivo)."""
        raise NotImplementedError


class MaxItemsRule(StoppingRule):
    """Detiene el test al alcanzar un número máximo de ítems."""

    def __init__(self, max_items: int = 20) -> None:
        if max_items < 1:
            raise ValueError("max_items debe ser al menos 1.")
        self.max_items = max_items

    def should_stop(self, state: CATState) -> tuple[bool, str]:
        if state.n_administered >= self.max_items:
            return True, "max_items"
        return False, ""


class StandardErrorRule(StoppingRule):
    """Detiene el test cuando el error estándar cae por debajo de un umbral."""

    def __init__(self, se_threshold: float = 0.3, min_items: int = 1) -> None:
        if se_threshold <= 0.0:
            raise ValueError("se_threshold debe ser positivo.")
        self.se_threshold = se_threshold
        self.min_items = min_items

    def should_stop(self, state: CATState) -> tuple[bool, str]:
        if state.n_administered >= self.min_items and state.standard_error <= self.se_threshold:
            return True, "se_threshold"
        return False, ""


class MinInformationRule(StoppingRule):
    """
    Detiene el test cuando la máxima información disponible ya no aporta.

    Se detiene si la información acumulada del test alcanza un objetivo (que
    equivale a un error estándar objetivo, dado que SE = 1/sqrt(I)).
    """

    def __init__(self, target_information: float = 11.0, min_items: int = 1) -> None:
        if target_information <= 0.0:
            raise ValueError("target_information debe ser positivo.")
        self.target_information = target_information
        self.min_items = min_items

    def should_stop(self, state: CATState) -> tuple[bool, str]:
        if state.n_administered >= self.min_items and state.information >= self.target_information:
            return True, "target_information"
        return False, ""


class CompositeRule(StoppingRule):
    """
    Combina varias reglas: el test se detiene cuando CUALQUIERA de ellas lo pide
    (además de detenerse siempre si se agota el banco, gestionado por el motor).
    """

    def __init__(self, rules: list[StoppingRule]) -> None:
        if not rules:
            raise ValueError("Se requiere al menos una regla.")
        self.rules = rules

    def should_stop(self, state: CATState) -> tuple[bool, str]:
        for rule in self.rules:
            stop, reason = rule.should_stop(state)
            if stop:
                return True, reason
        return False, ""


def make_stopping_rule(
    max_items: int | None = 20,
    se_threshold: float | None = None,
    target_information: float | None = None,
    min_items: int = 1,
) -> StoppingRule:
    """
    Construye una regla de terminación (posiblemente compuesta) a partir de los
    criterios activos. Los criterios con valor ``None`` se omiten.
    """
    rules: list[StoppingRule] = []
    if max_items is not None:
        rules.append(MaxItemsRule(max_items))
    if se_threshold is not None:
        rules.append(StandardErrorRule(se_threshold, min_items=min_items))
    if target_information is not None:
        rules.append(MinInformationRule(target_information, min_items=min_items))
    if not rules:
        raise ValueError("Debe activarse al menos un criterio de terminación.")
    if len(rules) == 1:
        return rules[0]
    return CompositeRule(rules)
