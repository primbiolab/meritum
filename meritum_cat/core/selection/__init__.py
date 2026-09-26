"""
Algoritmos de selección de ítems para CAT.

Métodos soportados:
    * Maximum Fisher Information (máxima información).
    * Random (aleatorio, baseline).
    * Randomesque (aleatorización entre los más informativos).
    * Kullback-Leibler (información KL global).
    * Sympson-Hetter (máxima información con control probabilístico de exposición).
"""
from __future__ import annotations

from meritum_cat.core.selection.base import (
    ItemSelector,
    SelectionMethod,
    make_selector,
)
from meritum_cat.core.selection.maximum_information import MaximumInformationSelector
from meritum_cat.core.selection.random_selection import RandomSelector
from meritum_cat.core.selection.randomesque import RandomesqueSelector
from meritum_cat.core.selection.kullback_leibler import KullbackLeiblerSelector
from meritum_cat.core.selection.sympson_hetter import (
    SympsonHetterSelector,
    calibrate_sympson_hetter,
)

__all__ = [
    "ItemSelector",
    "SelectionMethod",
    "make_selector",
    "MaximumInformationSelector",
    "RandomSelector",
    "RandomesqueSelector",
    "KullbackLeiblerSelector",
    "SympsonHetterSelector",
    "calibrate_sympson_hetter",
]
