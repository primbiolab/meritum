"""
Modelos de datos centrales de Meritum_CAT.

Define las estructuras de datos inmutables (dataclasses) usadas de forma
transversal por el núcleo científico: el ítem psicométrico, el banco de ítems,
y los resultados de una sesión CAT.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

import numpy as np


@dataclass(frozen=True)
class Item:
    """
    Ítem psicométrico calibrado bajo un modelo IRT (Item Response Theory).

    Atributos:
        item_id: Identificador único del ítem.
        a: Discriminación del ítem (a). Pendiente de la curva característica.
        b: Dificultad del ítem (b), en la escala de habilidad theta.
        c: Pseudo-azar / guessing (c), probabilidad de acierto por azar (0 <= c < 1).
        category: Categoría de contenido (para content balancing).
        subcategory: Subcategoría de contenido.
        tags: Etiquetas descriptivas adicionales.
        question: Enunciado del ítem (opcional; el núcleo científico solo usa a, b, c).
        alternatives: Alternativas de respuesta (opcional).
        correct: Índice o clave de la respuesta correcta (opcional).
        source: Fuente u origen del ítem.
        active: Si el ítem está activo y disponible para administración.
        notes: Observaciones libres.
    """

    item_id: str
    a: float = 1.0
    b: float = 0.0
    c: float = 0.0
    category: str = ""
    subcategory: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)
    question: str = ""
    alternatives: tuple[str, ...] = field(default_factory=tuple)
    correct: str = ""
    source: str = ""
    active: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tags"] = list(self.tags)
        d["alternatives"] = list(self.alternatives)
        return d


@dataclass
class ItemBank:
    """
    Banco de ítems. Contenedor de una colección de :class:`Item` que además
    expone los parámetros IRT como arreglos NumPy vectorizados para el motor.
    """

    items: list[Item] = field(default_factory=list)
    name: str = "item_bank"

    def __post_init__(self) -> None:
        self._rebuild_cache()

    def _rebuild_cache(self) -> None:
        active = [it for it in self.items if it.active]
        self._active_items = active
        if active:
            self._a = np.array([it.a for it in active], dtype=float)
            self._b = np.array([it.b for it in active], dtype=float)
            self._c = np.array([it.c for it in active], dtype=float)
        else:
            self._a = np.zeros(0)
            self._b = np.zeros(0)
            self._c = np.zeros(0)

    @property
    def active_items(self) -> list[Item]:
        """Ítems activos (los administrables)."""
        return self._active_items

    @property
    def a(self) -> np.ndarray:
        """Vector de discriminaciones (a) de los ítems activos."""
        return self._a

    @property
    def b(self) -> np.ndarray:
        """Vector de dificultades (b) de los ítems activos."""
        return self._b

    @property
    def c(self) -> np.ndarray:
        """Vector de pseudo-azar (c) de los ítems activos."""
        return self._c

    @property
    def n_items(self) -> int:
        """Número de ítems activos."""
        return len(self._active_items)

    @property
    def n_total(self) -> int:
        """Número total de ítems (activos e inactivos)."""
        return len(self.items)

    @property
    def categories(self) -> list[str]:
        """Categorías de contenido presentes en el banco (ítems activos)."""
        cats = {it.category for it in self._active_items if it.category}
        return sorted(cats)

    def category_of(self, index: int) -> str:
        """Categoría del ítem activo en la posición ``index``."""
        return self._active_items[index].category

    def refresh(self) -> None:
        """Reconstruye la caché vectorizada tras modificar la lista de ítems."""
        self._rebuild_cache()


@dataclass
class CATResult:
    """
    Resultado de una única sesión de Computerized Adaptive Testing.

    Atributos:
        theta_true: Habilidad verdadera del examinado (si es simulación).
        theta_estimate: Estimación final de la habilidad (theta).
        standard_error: Error estándar final de la estimación.
        administered_items: Índices (en el banco activo) de los ítems administrados.
        responses: Respuestas observadas (1 = correcto, 0 = incorrecto).
        theta_history: Evolución de la estimación de theta tras cada ítem.
        se_history: Evolución del error estándar tras cada ítem.
        information_history: Información acumulada tras cada ítem.
        stop_reason: Motivo de terminación del test.
    """

    theta_true: float | None
    theta_estimate: float
    standard_error: float
    administered_items: list[int]
    responses: list[int]
    theta_history: list[float]
    se_history: list[float]
    information_history: list[float]
    stop_reason: str

    @property
    def test_length(self) -> int:
        """Número de ítems administrados."""
        return len(self.administered_items)

    @property
    def n_correct(self) -> int:
        """Número de respuestas correctas."""
        return int(sum(self.responses))

    @property
    def error(self) -> float | None:
        """Error de estimación (theta_estimate - theta_true), si hay verdad."""
        if self.theta_true is None:
            return None
        return self.theta_estimate - self.theta_true
