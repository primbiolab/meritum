# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de PyInstaller para generar la carpeta de aplicación de Meritum_CAT para Windows x64.

Uso (desde la raíz del repositorio):
    python -m PyInstaller packaging/meritum_cat.spec --noconfirm --clean
Resultado:
    dist/Meritum_CAT/Meritum_CAT.exe  (con sus bibliotecas en dist/Meritum_CAT/_internal)
"""
from pathlib import Path

ROOT = Path(SPECPATH).parent

import PySide6
QT_TRANSLATIONS = Path(PySide6.__file__).parent / "translations"

datas = [
    (str(ROOT / "resources" / "datasets"), "resources/datasets"),
    (str(ROOT / "resources" / "icons"), "resources/icons"),
]
# Traducciones propias de Qt (menús contextuales y diálogos estándar en español).
for name in ("qtbase_es.qm", "qtbase_en.qm"):
    if (QT_TRANSLATIONS / name).exists():
        datas.append((str(QT_TRANSLATIONS / name), "PySide6/translations"))

excludes = [
    "tkinter", "PyQt5", "PyQt6", "IPython", "jupyter", "notebook", "pandas", "pytest", "sphinx",
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngineQuick",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtQuick3D",
    "PySide6.QtMultimedia", "PySide6.QtBluetooth", "PySide6.QtPositioning", "PySide6.QtCharts",
    "PySide6.QtDataVisualization", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtNetworkAuth",
    "PySide6.QtPdf", "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtRemoteObjects",
    "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtOpenGL", "PySide6.QtOpenGLWidgets",
    "PySide6.QtSvgWidgets", "PySide6.QtXml", "PySide6.QtWebSockets", "PySide6.QtSpatialAudio",
    "PySide6.QtTextToSpeech", "PySide6.QtGraphs", "PySide6.QtHttpServer",
]

a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["matplotlib.backends.backend_qtagg"],
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)
# El programa guarda la configuración de matplotlib en su propia carpeta de caché
# (ver meritum_cat.utils.paths.cache_dir); se omite el gancho que la crea en la carpeta temporal.
a.scripts = [s for s in a.scripts if s[0] != "pyi_rth_mplconfig"]
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Meritum_CAT",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=True,
    icon=str(ROOT / "resources" / "icons" / "meritum_cat.ico"),
    version=str(ROOT / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Meritum_CAT",
)
