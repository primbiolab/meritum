"""
Punto de entrada de la aplicación de escritorio Meritum_CAT.

Uso:
    python -m meritum_cat                  # abre la interfaz gráfica
    python -m meritum_cat --lang en        # abre la interfaz en inglés
    python -m meritum_cat --self-test DIR  # autoprueba de extremo a extremo de la GUI

La opción ``--self-test`` recorre la interfaz real (las mismas ventanas, botones
y tareas que usa una persona) y guarda la matriz de verificación en ``DIR``.
Sirve también para verificar el ejecutable empaquetado.
"""
from __future__ import annotations

import argparse
import os
import platform
import sys
import threading
import traceback
from typing import Callable

from meritum_cat import __app_name__, __version__


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="Meritum_CAT", add_help=True)
    parser.add_argument("--lang", choices=["es", "en"], default=None)
    parser.add_argument("--self-test", dest="self_test", default=None, metavar="DIR")
    args, _unknown = parser.parse_known_args(argv)
    return args


def main(argv: list[str] | None = None, on_ready: Callable | None = None) -> int:
    """
    Abre la aplicación. ``on_ready`` (opcional) recibe la ventana principal una vez visible,
    debe devolver ``True`` si su recorrido terminó bien, y al terminar se cierra la aplicación.
    """
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    from meritum_cat.utils.paths import cache_dir
    os.environ.setdefault("MPLCONFIGDIR", str(cache_dir() / "matplotlib"))

    from meritum_cat.utils.logging_setup import setup_logging
    log = setup_logging()
    log.info("Inicio de %s %s (Python %s, %s)", __app_name__, __version__,
             platform.python_version(), platform.platform())

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Primbiolab")
    app.setFont(QFont("Segoe UI", 9))

    from meritum_cat.gui.style import apply_theme
    from meritum_cat.utils.paths import resource_path
    apply_theme(app)
    icon_path = resource_path("resources/icons/meritum_cat.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from meritum_cat.i18n import get_translator
    from meritum_cat.gui.state import load_settings
    language = args.lang or load_settings().get("language", "es")
    get_translator().set_language(language if language in ("es", "en") else "es")

    from meritum_cat.gui.main_window import MainWindow
    window = MainWindow()

    def excepthook(exc_type, exc, tb) -> None:
        log.error("Excepción no controlada:\n%s", "".join(traceback.format_exception(exc_type, exc, tb)))
        if getattr(app, "_automation", False):
            return
        try:
            from meritum_cat.gui.common import unexpected_error
            unexpected_error(window)
        except Exception:  # noqa: BLE001
            pass

    sys.excepthook = excepthook
    threading.excepthook = lambda a: excepthook(a.exc_type, a.exc_value, a.exc_traceback)

    window.show()

    exit_code = {"value": 0}
    if args.self_test and on_ready is None:
        from meritum_cat.gui import automation

        def on_ready(win) -> bool:
            return automation.run_self_test(win, args.self_test)

    if on_ready is not None:
        app._automation = True  # type: ignore[attr-defined]

        def run_automation() -> None:
            try:
                ok = on_ready(window)
                exit_code["value"] = 0 if ok else 1
            except Exception:  # noqa: BLE001
                log.error("Fallo en la automatización:\n%s", traceback.format_exc())
                exit_code["value"] = 2
            window._force_close = True  # type: ignore[attr-defined]
            window.close()
            app.quit()

        QTimer.singleShot(800, run_automation)

    code = app.exec()
    log.info("Fin de %s (código %s)", __app_name__, exit_code["value"] or code)
    return exit_code["value"] or code


if __name__ == "__main__":
    sys.exit(main())
