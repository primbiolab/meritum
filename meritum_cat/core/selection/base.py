"""
Interfaz común de los selectores de ítems y fábrica de selectores.

Un selector recibe la estimación actual de habilidad, los parámetros de todos
los ítems del banco y una máscara booleana de disponibilidad (True = el ítem aún
no se ha administrado y está permitido) y devuelve el índice del ítem elegido.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

import numpy as np


class SelectionMethod(str, Enum):
    """Algoritmos de selección de ítems soportados."""

    MAX_INFO = "Maximum Information"
    RANDOM = "Random"
    RANDOMESQUE = "Randomesque"
    KL = "Kullback-Leibler"
    SYMPSON_HETTER = "Sympson-Hetter"


class ItemSelector(ABC):
    """Clase base abstracta de los selectores de ítems."""

    method: SelectionMethod

    @abstractmethod
    def select(
        self,
        theta: float,
        a: np.ndarray,
        b: np.ndarray,
        c: np.ndarray,
        available: np.ndarray,
        rng: np.random.Generator,
    ) -> int:
        """Devuelve el índice (en el banco) del ítem seleccionado."""
        raise NotImplementedError

    @staticmethod
    def _available_indices(available: np.ndarray) -> np.ndarray:
        idx = np.flatnonzero(available)
        if idx.size == 0:
            raise ValueError("No quedan ítems disponibles para seleccionar.")
        return idx


def make_selector(method: SelectionMethod | str, **kwargs) -> ItemSelector:
    """Fábrica de selectores a partir del nombre del método."""
    method = SelectionMethod(method)
    from meritum_cat.core.selection.maximum_information import MaximumInformationSelector
    from meritum_cat.core.selection.random_selection import RandomSelector
    from meritum_cat.core.selection.randomesque import RandomesqueSelector
    from meritum_cat.core.selection.kullback_leibler import KullbackLeiblerSelector
    from meritum_cat.core.selection.sympson_hetter import SympsonHetterSelector

    if method == SelectionMethod.MAX_INFO:
        return MaximumInformationSelector(**kwargs)
    if method == SelectionMethod.RANDOM:
        return RandomSelector(**kwargs)
    if method == SelectionMethod.RANDOMESQUE:
        return RandomesqueSelector(**kwargs)
    if method == SelectionMethod.KL:
        return KullbackLeiblerSelector(**kwargs)
    if method == SelectionMethod.SYMPSON_HETTER:
        return SympsonHetterSelector(**kwargs)
    raise ValueError(f"Método de selección no soportado: {method}")  # pragma: no cover
