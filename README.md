# Meritum_CAT 1.0.0

**Scientific Platform for Computerized Adaptive Testing, Psychometric Modeling and Assessment Simulation**

*Plataforma científica para test adaptativo computarizado, modelamiento psicométrico y simulación de evaluaciones*

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Platform](https://img.shields.io/badge/Windows-x64-lightgrey)

Meritum_CAT es un software científico de escritorio, bilingüe (español / inglés), para investigar el
**test adaptativo computarizado (CAT)** basado en la **Teoría de Respuesta al Ítem (IRT)**. Permite
modelar ítems, simular poblaciones de examinados, comparar algoritmos de estimación y de selección,
cuantificar precisión y exposición de ítems, visualizar, exportar y **reproducir exactamente** cada
experimento. Todo el procesamiento es local y funciona sin conexión a Internet.

*Meritum_CAT is a bilingual (Spanish/English) desktop scientific platform for research on computerized
adaptive testing based on item response theory: modeling, Monte Carlo simulation, method comparison,
visualization, export and exact reproducibility, fully offline.*

## Características / Features

| Área | Capacidades |
|---|---|
| Modelos IRT | Rasch/1PL, 2PL, 3PL (vectorizados y numéricamente estables); información del ítem y del test; ICC, IIC, TIF y función de error estándar |
| Estimación | MLE, MAP y EAP, con manejo de patrones degenerados y error estándar |
| Selección de ítems | Máxima información de Fisher, aleatoria (línea base), Randomesque, Kullback-Leibler, Sympson-Hetter |
| Terminación | Máximo de ítems, umbral de error estándar, información objetivo, mínimo de ítems (combinables) |
| Exposición y contenido | Tasas de exposición, exposición máxima/media, ítems no usados, χ² de uniformidad; control Randomesque y Sympson-Hetter con calibración iterativa; balanceo de contenido |
| Simulación Monte Carlo | 1 a 1 000 000 examinados, poblaciones normal o uniforme, CAT o test fijo, comparación CAT vs test fijo, barra de progreso y botón Detener funcional |
| Métricas | Sesgo, MAE, MSE, RMSE, Pearson, Spearman, cobertura del IC 95 %, EE medio, longitud, exposición, tiempo; sesgo y RMSE condicionales; precisión vs número de ítems |
| Experimentos | 10 experimentos científicos predefinidos y reproducibles |
| Banco de ítems | Crear, editar, duplicar, eliminar, importar/exportar CSV y JSON, validación automática; bancos sintéticos de 100, 500 y 1000 ítems |
| Reproducibilidad | `experiment_config.json` con versión, fecha, entorno, configuración, banco (huella SHA-256) y resultados; verificación automática al reproducir |
| Interfaz | PySide6, bilingüe con cambio ES \| EN en vivo, ayuda contextual «?» y tooltips con rango válido en cada parámetro, guía rápida, glosario, «Acerca de», registro (logs) |

## Aplicación para Windows / Windows application

Descargue `Meritum_CAT_1.0.0_Windows_x64.zip` desde la sección
[Releases](https://github.com/primbiolab/Meritum_CAT/releases), descomprímalo en cualquier carpeta y abra
`Meritum_CAT\Meritum_CAT.exe` con doble clic. No requiere instalar Python ni librerías y funciona sin
conexión a Internet. Windows puede mostrar «Windows protegió su PC» porque el ejecutable no está firmado
digitalmente: elija «Más información» → «Ejecutar de todas formas». Verifique la integridad del zip con el
SHA-256 publicado en la release:

```powershell
Get-FileHash .\Meritum_CAT_1.0.0_Windows_x64.zip -Algorithm SHA256
```

El programa guarda su registro (`logs/meritum_cat.log`), sus preferencias y la caché de matplotlib en la
subcarpeta `cache` de su propia carpeta; si esa carpeta no admite escritura, usa
`Documentos\Meritum_CAT\cache`. No escribe en AppData.

## Ejecución desde el código fuente / Running from source

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m meritum_cat            # interfaz gráfica
.venv\Scripts\python.exe -m meritum_cat --lang en  # interfaz en inglés
```

## Pruebas / Tests

```bash
.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.venv\Scripts\python.exe -m pytest
```

Las pruebas automatizadas cubren los modelos IRT (frente a soluciones analíticas), la información, los
estimadores MLE/MAP/EAP, los algoritmos de selección, las reglas de terminación, la exposición y el balanceo
de contenido, la simulación Monte Carlo y su reproducibilidad exacta, la importación y validación de bancos,
los diez experimentos, la traducción completa ES/EN, las figuras y la interfaz gráfica.

La autoprueba de la interfaz recorre la aplicación real (pestañas, idiomas, bancos, CAT, Monte Carlo,
Detener, reproducción, experimentos, importación/exportación y ayuda) y guarda una matriz PASS/FAIL:

```bash
.venv\Scripts\python.exe -m meritum_cat --self-test salida_autoprueba
Meritum_CAT\Meritum_CAT.exe --self-test salida_autoprueba
```

## Compilación del ejecutable / Building the executable

```bash
powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
```

El script instala las dependencias fijadas, corre las pruebas, construye con PyInstaller la carpeta de
aplicación `dist\Meritum_CAT\` (con `Meritum_CAT.exe`) y la comprime en
`dist\Meritum_CAT_1.0.0_Windows_x64.zip` con su suma SHA-256 (`packaging/make_zip.py`). El icono se
regenera con `python packaging/make_icon.py`.

## Flujo científico / Scientific workflow

1. **Banco de ítems:** genere un banco sintético o importe el suyo (CSV/JSON) y valídelo.
2. **Modelos IRT:** explore ICC, IIC y la información del banco.
3. **Test adaptativo:** observe un CAT paso a paso (respuestas simuladas o manuales).
4. **Simulación Monte Carlo:** elija modelo, estimador, selección, criterio de terminación, población y
   semilla; ejecute, analice sesgo, RMSE y exposición, compare con un test fijo y exporte.
5. **Reproducibilidad:** guarde la configuración; al recargarla y ejecutar, Meritum_CAT verifica que los
   resultados coinciden exactamente.
6. **Experimentos científicos:** ejecute los diez experimentos predefinidos.

## Uso como biblioteca / Library usage

```python
from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo
from meritum_cat.persistence import load_bank

bank = load_bank("resources/datasets/synthetic_bank_500_2PL.csv")
config = MonteCarloConfig(n_examinees=1000, model="2PL", estimation_method="EAP",
                          selection_method="Maximum Information", max_items=20, seed=12345)
result = run_monte_carlo(bank, config)
print(result.metrics["rmse"], result.metrics["bias"], result.exposure.max_rate)
```

Más ejemplos en [`examples/`](examples/).

## Experimentos / Experiments

| # | Experimento | Factor |
|---|---|---|
| 1 | Recuperación de la habilidad | 1PL, 2PL, 3PL |
| 2 | Estimadores | MLE, MAP, EAP |
| 3 | Selección de ítems | 5 algoritmos |
| 4 | CAT vs test fijo | longitudes 10, 20, 30 |
| 5 | Tamaño del banco | 50 a 1000 ítems |
| 6 | Longitud máxima | 5 a 40 ítems |
| 7 | Robustez | error de calibración de a, b, c |
| 8 | Exposición | 5 algoritmos |
| 9 | Poblaciones | 5 distribuciones de θ |
| 10 | Semillas | variabilidad y reproducibilidad |

Cada experimento se ejecuta desde la pestaña «Experimentos» y exporta su tabla (CSV), su figura (PNG) y su
configuración (JSON).

## Estructura / Structure

```
meritum_cat/
  core/            núcleo científico: irt, estimation, selection, stopping, exposure,
                   balancing, simulation, statistics, validation
  datasets/        generación de bancos sintéticos reproducibles
  experiments/     diez experimentos predefinidos
  persistence/     CSV/JSON de bancos, experiment_config.json, exportación de resultados
  plotting/        gráficas científicas (matplotlib)
  i18n/            catálogo bilingüe ES/EN y ayuda de parámetros
  gui/             interfaz PySide6 (pestañas, diálogos, hilos de trabajo, autoprueba)
  utils/           rutas de recursos, carpeta de caché y registro
tests/             pruebas automatizadas (pytest)
examples/          ejemplos de uso de la API y banco de ejemplo
scripts/           generación de los bancos sintéticos incluidos
resources/         bancos sintéticos e icono
packaging/         especificación de PyInstaller, construcción del ejecutable y del zip
```

## Documentación / Documentation

La descripción del software, el manual técnico y el manual de usuario se distribuyen por separado del
código fuente; en el repositorio están en la carpeta `manuales/`.

## Datos / Data

Los bancos incluidos en `resources/datasets/` son **datos sintéticos** generados por simulación
(semilla 2026) con fines de experimentación. No son ítems reales ni provienen de ninguna prueba o
institución. Para trabajar con datos reales, importe su propio banco calibrado.

## Cómo citar / How to cite

Gómez Otero, K. L., Burgos Flórez, F. J., & Popayán Hernández, J. G. (2026). *Meritum_CAT: Scientific Platform for Computerized
Adaptive Testing, Psychometric Modeling and Assessment Simulation* (versión 1.0.0) [Software].
https://github.com/primbiolab/Meritum_CAT

Ver [`CITATION.cff`](CITATION.cff).

## Autores / Authors

Keidy Lucía Gómez Otero, Francisco Javier Burgos Flórez y Juan Guillermo Popayán Hernández.
Contacto: fjburgosf@gmail.com

## Componentes de terceros / Third-party components

Usa NumPy, SciPy y Matplotlib (licencias BSD/compatibles) y PySide6 (Qt for Python, LGPLv3), cada uno bajo su
propia licencia.
