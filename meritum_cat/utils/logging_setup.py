"""
Configuración del sistema de logging de Meritum_CAT.

Registra el inicio y cierre de la aplicación, los experimentos, las
importaciones/exportaciones y los errores en ``logs/meritum_cat.log`` dentro de la
carpeta de caché del programa (ver :func:`meritum_cat.utils.paths.cache_dir`). Nunca registra datos sensibles.
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from meritum_cat.utils.paths import cache_dir

_CONFIGURED = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configura el logger raíz de la aplicación (idempotente)."""
    global _CONFIGURED
    logger = logging.getLogger("meritum_cat")
    if _CONFIGURED:
        return logger

    logger.setLevel(level)
    log_dir = cache_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "meritum_cat.log"

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    file_handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3,
                                       encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # En el ejecutable con ventana (sin consola) sys.stderr es None: solo archivo.
    import sys
    if sys.stderr is not None:
        stream = logging.StreamHandler()
        stream.setFormatter(fmt)
        logger.addHandler(stream)

    _CONFIGURED = True
    logger.info("Logging inicializado. Archivo: %s", log_file)
    return logger


def get_logger(name: str = "meritum_cat") -> logging.Logger:
    """Devuelve un logger hijo del logger de la aplicación."""
    return logging.getLogger(name if name.startswith("meritum_cat") else f"meritum_cat.{name}")
