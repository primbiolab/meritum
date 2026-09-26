"""
Comprime la carpeta de aplicación ``dist/Meritum_CAT`` en ``dist/Meritum_CAT_<versión>_Windows_x64.zip``
y escribe su suma SHA-256 en un archivo ``.sha256`` junto al zip.

No incluye la carpeta ``cache`` que el programa crea al ejecutarse.

Uso (desde la raíz del repositorio):
    python packaging/make_zip.py
"""
from __future__ import annotations

import hashlib
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meritum_cat import __app_name__, __version__  # noqa: E402


def main() -> None:
    app = ROOT / "dist" / __app_name__
    if not (app / f"{__app_name__}.exe").exists():
        raise SystemExit(f"No se encontró {app / (__app_name__ + '.exe')}; construya primero la aplicación.")
    zip_path = ROOT / "dist" / f"{__app_name__}_{__version__}_Windows_x64.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for path in sorted(app.rglob("*")):
            rel = path.relative_to(app)
            if rel.parts[0] == "cache" or path.is_dir():
                continue
            z.write(path, f"{__app_name__}/{rel.as_posix()}")
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    (zip_path.parent / (zip_path.name + ".sha256")).write_text(f"{digest}  {zip_path.name}\n", encoding="ascii")
    print(f"Zip:     {zip_path}")
    print(f"SHA-256: {digest}")


if __name__ == "__main__":
    main()
