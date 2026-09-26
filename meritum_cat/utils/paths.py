"""
Resolución de rutas de recursos y de datos del usuario.

Funciona tanto en ejecución desde el código fuente como dentro del ejecutable
empaquetado con PyInstaller (que extrae los recursos a ``sys._MEIPASS``).
"""
from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Indica si el programa corre como ejecutable empaquetado (PyInstaller)."""
    return getattr(sys, "frozen", False)


def resource_path(relative: str) -> Path:
    """
    Devuelve la ruta absoluta de un recurso empaquetado.

    En modo empaquetado usa ``sys._MEIPASS``; en desarrollo usa la raíz del
    proyecto (dos niveles por encima de este archivo).
    """
    if is_frozen():
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).resolve().parents[2]
    return base / relative


def app_dir() -> Path:
    """Carpeta de la aplicación: la del ejecutable o, desde el código fuente, la raíz del proyecto."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _writable(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


_CACHE: Path | None = None


def cache_dir(app_name: str = "Meritum_CAT") -> Path:
    """
    Carpeta de caché del programa (registro, preferencias y configuración de matplotlib).

    Es la subcarpeta ``cache`` de la propia aplicación; si esa carpeta no admite
    escritura (por ejemplo, instalada en una ruta protegida), se usa
    ``Documentos/<app_name>/cache``.
    """
    global _CACHE
    if _CACHE is None:
        path = app_dir() / "cache"
        if not _writable(path):
            path = Path.home() / "Documents" / app_name / "cache"
            path.mkdir(parents=True, exist_ok=True)
        _CACHE = path
    return _CACHE
