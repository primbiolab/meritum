"""Figuras científicas de Meritum_CAT (matplotlib, API orientada a objetos)."""
from __future__ import annotations

import os

from meritum_cat.utils.paths import cache_dir

# matplotlib guarda su configuración y la caché de fuentes en la carpeta de caché del programa.
os.environ.setdefault("MPLCONFIGDIR", str(cache_dir() / "matplotlib"))


from meritum_cat.plotting.charts import (
    new_figure,
    plot_icc_iic,
    plot_test_information,
    plot_cat_trace,
    plot_recovery,
    plot_error_distribution,
    plot_bias_rmse_by_theta,
    plot_precision_by_items,
    plot_exposure,
    plot_test_length,
    plot_cat_vs_fixed,
    plot_experiment,
)

__all__ = [
    "new_figure",
    "plot_icc_iic",
    "plot_test_information",
    "plot_cat_trace",
    "plot_recovery",
    "plot_error_distribution",
    "plot_bias_rmse_by_theta",
    "plot_precision_by_items",
    "plot_exposure",
    "plot_test_length",
    "plot_cat_vs_fixed",
    "plot_experiment",
]
