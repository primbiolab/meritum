"""
Estructura común de los experimentos científicos.

Cada experimento produce un :class:`ExperimentResult` con una tabla de
resultados cuyas columnas usan códigos neutrales de idioma (``rmse``,
``pearson``, ``model``...). Títulos, descripciones, encabezados e
interpretaciones se obtienen del módulo :mod:`meritum_cat.i18n` en el idioma
activo, de modo que interfaz, scripts e informes consumen el mismo resultado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


class ExperimentCancelled(Exception):
    """Se lanza cuando el usuario detiene un experimento en curso."""


@dataclass
class ExperimentResult:
    """Resultado estandarizado de un experimento."""

    key: str
    columns: list[str]
    rows: list[dict[str, Any]]
    config: dict[str, Any] = field(default_factory=dict)
    summary_params: dict[str, Any] = field(default_factory=dict)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "columns": self.columns,
            "rows": self.rows,
            "config": self.config,
            "summary_params": self.summary_params,
            "elapsed_seconds": self.elapsed_seconds,
        }

    def as_text_table(self, header: Callable[[str], str] | None = None) -> str:
        """Tabla en texto plano; ``header`` traduce los códigos de columna."""
        names = {c: (header(c) if header else c) for c in self.columns}
        widths = {
            c: max([len(names[c])] + [len(str(r.get(c, ""))) for r in self.rows])
            for c in self.columns
        }
        lines = [
            " | ".join(names[c].ljust(widths[c]) for c in self.columns),
            "-+-".join("-" * widths[c] for c in self.columns),
        ]
        for r in self.rows:
            lines.append(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in self.columns))
        return "\n".join(lines)

    def as_markdown_table(self, header: Callable[[str], str] | None = None) -> str:
        """Tabla en formato Markdown; ``header`` traduce los códigos de columna."""
        names = [(header(c) if header else c) for c in self.columns]
        lines = ["| " + " | ".join(names) + " |", "|" + "|".join("---" for _ in names) + "|"]
        for r in self.rows:
            lines.append("| " + " | ".join(str(r.get(c, "")) for c in self.columns) + " |")
        return "\n".join(lines)
