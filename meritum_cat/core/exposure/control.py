"""
Análisis de exposición de ítems.

La tasa de exposición de un ítem es la proporción de examinados a los que se les
administró. Un banco bien utilizado reparte la exposición; una concentración
excesiva en pocos ítems compromete la seguridad de la prueba. El control de
exposición por randomización (Randomesque) se implementa a nivel de selección
(ver :mod:`meritum_cat.core.selection.randomesque`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ExposureStats:
    """Estadísticos de exposición de un banco tras una simulación."""

    exposure_rates: np.ndarray  # tasa por ítem (proporción de examinados)
    counts: np.ndarray          # veces administrado por ítem
    n_examinees: int

    @property
    def max_rate(self) -> float:
        """Máxima tasa de exposición."""
        return float(np.max(self.exposure_rates)) if self.exposure_rates.size else 0.0

    @property
    def mean_rate(self) -> float:
        """Tasa media de exposición (sobre todos los ítems del banco)."""
        return float(np.mean(self.exposure_rates)) if self.exposure_rates.size else 0.0

    @property
    def unused_items(self) -> int:
        """Número de ítems nunca administrados."""
        return int(np.sum(self.counts == 0))

    @property
    def overexposed_items(self) -> int:
        """Ítems con exposición > 0.2 (umbral habitual de referencia)."""
        return int(np.sum(self.exposure_rates > 0.2))

    def chi_square_uniformity(self) -> float:
        """
        Estadístico chi-cuadrado de desviación respecto a la exposición uniforme.
        Valores mayores indican reparto más desigual de la exposición.
        """
        n_items = self.counts.size
        if n_items == 0 or self.n_examinees == 0:
            return 0.0
        expected = self.counts.sum() / n_items
        if expected <= 0:
            return 0.0
        return float(np.sum((self.counts - expected) ** 2) / expected)


def compute_exposure(administered_indices: list[list[int]], n_items: int) -> ExposureStats:
    """
    Calcula los estadísticos de exposición a partir de las listas de ítems
    administrados a cada examinado.

    Args:
        administered_indices: Lista (por examinado) de índices de ítems administrados.
        n_items: Número de ítems del banco.
    """
    counts = np.zeros(n_items, dtype=float)
    for items in administered_indices:
        for idx in items:
            counts[idx] += 1.0
    n_examinees = len(administered_indices)
    rates = counts / n_examinees if n_examinees > 0 else counts
    return ExposureStats(exposure_rates=rates, counts=counts, n_examinees=n_examinees)
