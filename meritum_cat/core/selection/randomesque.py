"""
Selección Randomesque (Kingsbury & Zara, 1989).

Estrategia de control de exposición: en lugar de administrar siempre el ítem más
informativo, selecciona aleatoriamente entre los ``bin_size`` ítems más
informativos disponibles. Reduce la sobre-exposición de los ítems más
informativos manteniendo una eficiencia estadística cercana a la máxima.
"""
from __future__ import annotations

import numpy as np

from meritum_cat.core.selection.base import ItemSelector, SelectionMethod
from meritum_cat.core.irt.information import item_information


class RandomesqueSelector(ItemSelector):
    """Selecciona al azar entre los N ítems más informativos."""

    method = SelectionMethod.RANDOMESQUE

    def __init__(self, bin_size: int = 5) -> None:
        if bin_size < 1:
            raise ValueError("bin_size debe ser al menos 1.")
        self.bin_size = bin_size

    def select(self, theta, a, b, c, available, rng):
        idx = self._available_indices(available)
        info = item_information(theta, a[idx], b[idx], c[idx])
        k = min(self.bin_size, idx.size)
        # Índices (dentro de idx) de los k ítems más informativos.
        top_local = np.argpartition(info, -k)[-k:]
        chosen = idx[top_local]
        return int(rng.choice(chosen))
