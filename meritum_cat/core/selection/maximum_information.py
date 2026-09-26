"""
Selección por Máxima Información de Fisher.

Selecciona, entre los ítems disponibles, aquel cuya información de Fisher es
máxima en la estimación actual de habilidad. Es el criterio clásico de máxima
eficiencia estadística en CAT (Lord, 1980).
"""
from __future__ import annotations

import numpy as np

from meritum_cat.core.selection.base import ItemSelector, SelectionMethod
from meritum_cat.core.irt.information import item_information


class MaximumInformationSelector(ItemSelector):
    """Selecciona el ítem disponible con mayor información en theta."""

    method = SelectionMethod.MAX_INFO

    def select(self, theta, a, b, c, available, rng):
        idx = self._available_indices(available)
        info = item_information(theta, a[idx], b[idx], c[idx])
        best = idx[int(np.argmax(info))]
        return int(best)
