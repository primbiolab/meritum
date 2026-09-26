"""Utilidades transversales: logging y rutas de recursos."""
from __future__ import annotations

from meritum_cat.utils.paths import resource_path, cache_dir
from meritum_cat.utils.logging_setup import setup_logging, get_logger

__all__ = ["resource_path", "cache_dir", "setup_logging", "get_logger"]
