"""
Balanceo de contenido (content balancing).

Permite imponer una distribución objetivo de categorías de contenido a lo largo
del test adaptativo. La estrategia implementada es la del *déficit máximo*
(constrained CAT, Kingsbury & Zara, 1989): en cada paso se prioriza la categoría
cuya proporción administrada está más por debajo de su proporción objetivo,
restringiendo los ítems disponibles a esa categoría. Dentro de la categoría
elegida, la selección de ítems opera normalmente por información.
"""
from __future__ import annotations

import numpy as np


class ContentBalancer:
    """
    Balanceador de contenido por déficit máximo.

    Args:
        categories: Categoría de cada ítem del banco (misma longitud que el banco).
        targets: Diccionario {categoría: proporción objetivo}. Las proporciones se
            normalizan automáticamente. Si es ``None`` no se aplica balanceo.
    """

    def __init__(self, categories: list[str], targets: dict[str, float] | None = None) -> None:
        self.categories = np.asarray(categories, dtype=object)
        self.enabled = bool(targets)
        if targets:
            total = sum(targets.values())
            if total <= 0:
                raise ValueError("La suma de proporciones objetivo debe ser positiva.")
            self.targets = {k: v / total for k, v in targets.items()}
        else:
            self.targets = {}

    def restrict(self, available: np.ndarray, administered_categories: list[str]) -> np.ndarray:
        """
        Restringe la máscara de disponibilidad a la categoría con mayor déficit.

        Args:
            available: Máscara booleana de ítems disponibles.
            administered_categories: Categorías ya administradas en esta sesión.

        Devuelve una máscara booleana. Si el balanceo está desactivado o la
        categoría prioritaria no tiene ítems disponibles, devuelve ``available``
        sin cambios.
        """
        if not self.enabled:
            return available

        n_admin = len(administered_categories)
        # Proporción administrada actual por categoría.
        current: dict[str, float] = {cat: 0.0 for cat in self.targets}
        if n_admin > 0:
            for cat in administered_categories:
                if cat in current:
                    current[cat] += 1.0 / n_admin

        # Déficit = objetivo - actual. Se elige la categoría de mayor déficit que
        # tenga ítems disponibles.
        deficits = sorted(self.targets, key=lambda cat: self.targets[cat] - current[cat], reverse=True)
        for cat in deficits:
            cat_mask = available & (self.categories == cat)
            if np.any(cat_mask):
                return cat_mask
        return available
