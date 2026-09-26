"""
Generación de bancos de ítems SINTÉTICOS y reproducibles.

Los parámetros IRT se muestrean de distribuciones habituales en la literatura
psicométrica (van der Linden & Glas, 2010):

    * discriminación a ~ LogNormal (media ~1, positiva);
    * dificultad b ~ Normal(0, 1);
    * pseudo-azar c ~ Beta (concentrada en valores bajos), solo en 3PL.

IMPORTANTE: estos bancos son DATOS SIMULADOS con fines de experimentación y
demostración. No representan ítems reales ni provienen de ninguna prueba o
institución real.
"""
from __future__ import annotations

import numpy as np

from meritum_cat.models import Item, ItemBank

# Códigos de categoría neutrales respecto al idioma (dominios de contenido simulados).
DEFAULT_CATEGORIES = ["D1", "D2", "D3", "D4"]


def generate_synthetic_bank(
    n_items: int = 500,
    model: str = "2PL",
    seed: int = 2026,
    categories: list[str] | None = None,
    name: str | None = None,
) -> ItemBank:
    """
    Genera un banco de ítems sintético reproducible.

    Args:
        n_items: Número de ítems.
        model: "1PL", "2PL" o "3PL" (determina qué parámetros varían).
        seed: Semilla para reproducibilidad.
        categories: Lista de categorías de contenido a repartir cíclicamente.
        name: Nombre del banco.
    """
    if n_items < 1:
        raise ValueError("n_items debe ser al menos 1.")
    rng = np.random.default_rng(seed)
    cats = categories or DEFAULT_CATEGORIES
    model = model.upper()

    if model == "1PL":
        a = np.ones(n_items)
        c = np.zeros(n_items)
    elif model == "2PL":
        a = rng.lognormal(mean=0.0, sigma=0.3, size=n_items)
        c = np.zeros(n_items)
    elif model == "3PL":
        a = rng.lognormal(mean=0.0, sigma=0.3, size=n_items)
        c = rng.beta(a=5.0, b=17.0, size=n_items)  # media ~0.23
    else:
        raise ValueError(f"Modelo no soportado: {model}")

    b = rng.normal(loc=0.0, scale=1.0, size=n_items)

    items: list[Item] = []
    width = len(str(n_items))
    for i in range(n_items):
        items.append(
            Item(
                item_id=f"SYN-{model}-{i + 1:0{width}d}",
                a=round(float(a[i]), 4),
                b=round(float(b[i]), 4),
                c=round(float(c[i]), 4),
                category=cats[i % len(cats)],
                subcategory="",
                source="SYN",
                active=True,
                notes="",
            )
        )

    return ItemBank(items=items, name=name or f"synthetic_{model}_{n_items}")
