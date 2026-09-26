"""
Validación del banco de ítems.

Detecta problemas frecuentes en los parámetros IRT y en la estructura de los
ítems. Cada hallazgo lleva un código (``code``) y sus parámetros (``params``),
que la interfaz traduce a un mensaje comprensible en el idioma activo; el campo
``message`` contiene además una versión en español para uso fuera de la GUI.
La severidad distingue errores (invalidan el ítem) de advertencias (parámetros
atípicos que conviene revisar).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from meritum_cat.models import ItemBank

# Umbrales de parámetros atípicos (advertencias, no errores).
A_HIGH = 3.0
B_EXTREME = 4.0
C_HIGH = 0.5

# Plantillas en español (la GUI usa las traducciones del módulo i18n).
_MESSAGES_ES: dict[str, str] = {
    "missing_id": "El ítem no tiene identificador.",
    "duplicate_id": "ID duplicado: '{item_id}'.",
    "a_nan": "Discriminación (a) no es un número válido.",
    "a_nonpositive": "Discriminación (a={value:g}) debe ser positiva.",
    "a_high": "Discriminación (a={value:g}) es atípicamente alta (>3).",
    "b_nan": "Dificultad (b) no es un número válido.",
    "b_extreme": "Dificultad (b={value:g}) es extrema (|b|>4).",
    "c_nan": "Pseudo-azar (c) no es un número válido.",
    "c_negative": "Pseudo-azar (c={value:g}) no puede ser negativo.",
    "c_ge_one": "Pseudo-azar (c={value:g}) debe ser menor que 1.",
    "c_high": "Pseudo-azar (c={value:g}) es atípicamente alto (>0.5).",
    "missing_category": "El ítem no tiene categoría de contenido.",
    "bank_empty": "El banco no contiene ítems.",
    "bank_no_active": "El banco no tiene ítems activos administrables.",
}


@dataclass
class ValidationIssue:
    """Un hallazgo de la validación del banco."""

    item_id: str
    severity: str  # "error" | "warning"
    field: str
    code: str
    params: dict[str, Any] = field(default_factory=dict)

    @property
    def message(self) -> str:
        """Mensaje en español (para scripts y logs)."""
        return _MESSAGES_ES[self.code].format(**self.params)


def _is_nan(x: Any) -> bool:
    try:
        return math.isnan(float(x))
    except (TypeError, ValueError):
        return True


def validate_bank(bank: ItemBank) -> list[ValidationIssue]:
    """
    Valida un banco de ítems y devuelve la lista de hallazgos.

    Comprueba IDs vacíos o duplicados, valores NaN, discriminaciones no
    positivas, c fuera de [0, 1), parámetros extremos y categorías faltantes.
    """
    issues: list[ValidationIssue] = []
    seen_ids: set[str] = set()

    def add(iid: str, severity: str, fld: str, code: str, **params: Any) -> None:
        issues.append(ValidationIssue(iid, severity, fld, code, params))

    for item in bank.items:
        iid = item.item_id or "—"

        if not item.item_id:
            add(iid, "error", "item_id", "missing_id")
        elif item.item_id in seen_ids:
            add(iid, "error", "item_id", "duplicate_id", item_id=item.item_id)
        else:
            seen_ids.add(item.item_id)

        if _is_nan(item.a):
            add(iid, "error", "a", "a_nan")
        elif item.a <= 0:
            add(iid, "error", "a", "a_nonpositive", value=item.a)
        elif item.a > A_HIGH:
            add(iid, "warning", "a", "a_high", value=item.a)

        if _is_nan(item.b):
            add(iid, "error", "b", "b_nan")
        elif abs(item.b) > B_EXTREME:
            add(iid, "warning", "b", "b_extreme", value=item.b)

        if _is_nan(item.c):
            add(iid, "error", "c", "c_nan")
        elif item.c < 0:
            add(iid, "error", "c", "c_negative", value=item.c)
        elif item.c >= 1:
            add(iid, "error", "c", "c_ge_one", value=item.c)
        elif item.c > C_HIGH:
            add(iid, "warning", "c", "c_high", value=item.c)

        if not item.category:
            add(iid, "warning", "category", "missing_category")

    if bank.n_total == 0:
        add("—", "error", "items", "bank_empty")
    elif bank.n_items == 0:
        add("—", "error", "items", "bank_no_active")

    return issues


def has_errors(issues: list[ValidationIssue]) -> bool:
    """Indica si la lista de hallazgos contiene al menos un error."""
    return any(i.severity == "error" for i in issues)
