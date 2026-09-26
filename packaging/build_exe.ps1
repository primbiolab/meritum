# Construye la carpeta de aplicación de Meritum_CAT para Windows x64 y la comprime en un zip listo para usar.
# Uso (PowerShell, desde la raíz del repositorio):
#   powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
# Resultado:
#   dist\Meritum_CAT\Meritum_CAT.exe
#   dist\Meritum_CAT_1.0.0_Windows_x64.zip  (y su suma SHA-256 en .sha256)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
if (-not (Test-Path ".venv")) { python -m venv .venv }
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Las pruebas automáticas fallaron; no se construye el ejecutable." }
.\.venv\Scripts\python.exe -m PyInstaller packaging\meritum_cat.spec --noconfirm --clean --distpath dist --workpath build
if ($LASTEXITCODE -ne 0) { throw "PyInstaller terminó con errores." }
.\.venv\Scripts\python.exe packaging\make_zip.py
if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el zip de la aplicación." }
Write-Output "Aplicación: dist\Meritum_CAT\Meritum_CAT.exe"
