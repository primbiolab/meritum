"""Permite ejecutar la aplicación con ``python -m meritum_cat``."""
from __future__ import annotations

import sys

from meritum_cat.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
