"""
Selección aleatoria de ítems (baseline).

Selecciona uniformemente al azar entre los ítems disponibles. Sirve como línea
base para comparar el desempeño de los algoritmos adaptativos.
"""
from __future__ import annotations

from meritum_cat.core.selection.base import ItemSelector, SelectionMethod


class RandomSelector(ItemSelector):
    """Selecciona un ítem disponible de forma uniformemente aleatoria."""

    method = SelectionMethod.RANDOM

    def select(self, theta, a, b, c, available, rng):
        idx = self._available_indices(available)
        return int(rng.choice(idx))
