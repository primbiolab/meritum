"""
Control probabilístico de exposición de Sympson-Hetter (Sympson & Hetter, 1985).

Cada ítem i tiene un parámetro de control de exposición K_i en (0, 1]. En cada
paso del CAT se ordenan los ítems disponibles por información de Fisher; el más
informativo se "selecciona" y pasa un sorteo: se administra con probabilidad K_i;
si no, queda bloqueado para ese examinado y se sortea el siguiente. La tasa de
exposición resultante es P(A_i) = P(S_i) * K_i, donde P(S_i) es la probabilidad de
que el ítem sea seleccionado.

Los K_i se calibran iterativamente mediante simulaciones (ver
:func:`calibrate_sympson_hetter`) para que ninguna tasa de exposición supere el
máximo objetivo r:

    K_i <- r / P(S_i)   si P(S_i) > r
    K_i <- 1            en otro caso
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from meritum_cat.core.selection.base import ItemSelector, SelectionMethod
from meritum_cat.core.irt.information import item_information


class SympsonHetterSelector(ItemSelector):
    """Máxima información con control de exposición de Sympson-Hetter."""

    method = SelectionMethod.SYMPSON_HETTER

    def __init__(self, k_params: np.ndarray | None = None, n_items: int | None = None) -> None:
        if k_params is None:
            if n_items is None:
                raise ValueError("Se requiere k_params o n_items.")
            k_params = np.ones(n_items)
        k_params = np.asarray(k_params, dtype=float)
        if np.any(k_params <= 0) or np.any(k_params > 1):
            raise ValueError("Los parámetros K deben estar en (0, 1].")
        self.k = k_params
        self.selected_counts = np.zeros(k_params.size)
        self._blocked: set[int] = set()

    def start_session(self) -> None:
        """Inicia un nuevo examinado: limpia los bloqueos de la sesión anterior."""
        self._blocked = set()

    def reset_counts(self) -> None:
        self.selected_counts[:] = 0

    def select(self, theta, a, b, c, available, rng):
        mask = available.copy()
        if self._blocked:
            mask[list(self._blocked)] = False
        idx = np.flatnonzero(mask)
        if idx.size == 0:
            # Todos los disponibles bloqueados: se relaja el control para no
            # interrumpir el test (caso límite con bancos pequeños).
            idx = self._available_indices(available)
            info = item_information(theta, a[idx], b[idx], c[idx])
            return int(idx[int(np.argmax(info))])

        info = item_information(theta, a[idx], b[idx], c[idx])
        order = idx[np.argsort(-info)]
        for item in order:
            self.selected_counts[item] += 1
            if rng.random() <= self.k[item]:
                return int(item)
            self._blocked.add(int(item))
        # Ningún ítem superó el sorteo: se administra el último candidato.
        return int(order[-1])


def calibrate_sympson_hetter(
    run_population: Callable[[SympsonHetterSelector], tuple[np.ndarray, int]],
    n_items: int,
    r_max: float = 0.25,
    n_iterations: int = 10,
) -> tuple[np.ndarray, list[float]]:
    """
    Calibra los parámetros K de Sympson-Hetter.

    Args:
        run_population: Función que simula una población con el selector dado y
            devuelve (conteos de administración por ítem, número de examinados).
        n_items: Número de ítems del banco.
        r_max: Tasa máxima de exposición objetivo (0 < r_max <= 1).
        n_iterations: Número de iteraciones de calibración.

    Devuelve (K calibrados, historial de la exposición máxima por iteración).
    """
    if not 0 < r_max <= 1:
        raise ValueError("r_max debe estar en (0, 1].")
    k = np.ones(n_items)
    history: list[float] = []
    for _ in range(n_iterations):
        selector = SympsonHetterSelector(k_params=k.copy())
        admin_counts, n_examinees = run_population(selector)
        p_admin = admin_counts / n_examinees
        history.append(float(np.max(p_admin)))
        p_select = selector.selected_counts / n_examinees
        k = np.where(p_select > r_max, r_max / np.maximum(p_select, 1e-12), 1.0)
        k = np.clip(k, 1e-3, 1.0)
    return k, history
