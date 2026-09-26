"""
Catálogo bilingüe (español, inglés) de todas las cadenas visibles de Meritum_CAT.

``STRINGS``: clave -> (español, inglés).
``PARAM_HELP``: parámetros científicos con nombre descriptivo, símbolo, ayuda
contextual y rango válido en ambos idiomas.

Las pruebas automatizadas (tests/test_i18n.py) verifican que toda clave usada en
la interfaz y en las figuras exista aquí y tenga texto en ambos idiomas.
"""
from __future__ import annotations

S: dict[str, tuple[str, str]] = {}


def _add(entries: dict[str, tuple[str, str]]) -> None:
    S.update(entries)


# ----------------------------------------------------------------------------- aplicación
_add({
    "app.title": ("Meritum_CAT {version}", "Meritum_CAT {version}"),
    "app.subtitle": (
        "Plataforma científica para test adaptativo computarizado, modelamiento psicométrico y simulación de evaluaciones",
        "Scientific Platform for Computerized Adaptive Testing, Psychometric Modeling and Assessment Simulation",
    ),
    "menu.file": ("&Archivo", "&File"),
    "menu.language": ("&Idioma", "&Language"),
    "menu.help": ("A&yuda", "&Help"),
    "action.import_bank": ("Importar banco de ítems (CSV/JSON)…", "Import item bank (CSV/JSON)…"),
    "action.export_bank_csv": ("Exportar banco a CSV…", "Export bank to CSV…"),
    "action.export_bank_json": ("Exportar banco a JSON…", "Export bank to JSON…"),
    "action.load_config": ("Cargar configuración de experimento…", "Load experiment configuration…"),
    "action.save_config": ("Guardar configuración de experimento…", "Save experiment configuration…"),
    "action.exit": ("Salir", "Exit"),
    "action.lang_es": ("Español", "Español"),
    "action.lang_en": ("English", "English"),
    "action.quick_start": ("Guía rápida de uso", "Quick start guide"),
    "action.glossary": ("Glosario de parámetros", "Parameter glossary"),
    "action.open_logs": ("Abrir carpeta de registros (logs)", "Open log folder"),
    "action.about": ("Acerca de Meritum_CAT", "About Meritum_CAT"),
    "lang.toggle_tooltip": ("Cambiar el idioma de la interfaz", "Change the interface language"),
    "tab.home": ("Inicio", "Home"),
    "tab.bank": ("Banco de ítems", "Item bank"),
    "tab.irt": ("Modelos IRT", "IRT models"),
    "tab.cat": ("Test adaptativo (CAT)", "Adaptive test (CAT)"),
    "tab.mc": ("Simulación Monte Carlo", "Monte Carlo simulation"),
    "tab.exp": ("Experimentos científicos", "Scientific experiments"),
    "status.bank": ("Banco: {name} · {n} ítems activos", "Bank: {name} · {n} active items"),
    "status.no_bank": ("Sin banco cargado", "No bank loaded"),
    "status.ready": ("Listo", "Ready"),
    "status.language": ("Idioma: Español", "Language: English"),
    "btn.ok": ("Aceptar", "OK"),
    "btn.cancel": ("Cancelar", "Cancel"),
    "btn.yes": ("Sí", "Yes"),
    "btn.no": ("No", "No"),
    "btn.close": ("Cerrar", "Close"),
    "btn.go": ("Ir", "Go"),
    "btn.export_figure": ("Exportar figura…", "Export figure…"),
    "nav.home": ("Restablecer la vista", "Reset view"),
    "nav.back": ("Vista anterior", "Previous view"),
    "nav.forward": ("Vista siguiente", "Next view"),
    "nav.pan": ("Desplazar (arrastrar con el ratón)", "Pan (drag with the mouse)"),
    "nav.zoom": ("Zoom a un rectángulo", "Zoom to rectangle"),
    "dlg.error": ("Error", "Error"),
    "dlg.warning": ("Advertencia", "Warning"),
    "dlg.info": ("Información", "Information"),
    "dlg.confirm": ("Confirmar", "Confirm"),
    "close.running": (
        "Hay una tarea en ejecución. ¿Desea detenerla y salir?",
        "A task is running. Do you want to stop it and exit?",
    ),
    "filter.bank": ("Bancos de ítems (*.csv *.json)", "Item banks (*.csv *.json)"),
    "filter.csv": ("Archivo CSV (*.csv)", "CSV file (*.csv)"),
    "filter.json": ("Archivo JSON (*.json)", "JSON file (*.json)"),
    "filter.png": ("Imagen PNG (*.png)", "PNG image (*.png)"),
    "filter.config": ("Configuración de experimento (*.json)", "Experiment configuration (*.json)"),
    "dlg.choose_folder": ("Seleccione la carpeta de destino", "Select the destination folder"),
    "msg.figure_exported": ("Figura exportada a {file}.", "Figure exported to {file}."),
    "msg.file_written": ("Archivo guardado: {file}", "File saved: {file}"),
})

# ----------------------------------------------------------------------------- errores
_add({
    "err.unexpected": (
        "Ocurrió un error inesperado. La operación no se completó.\n\nLos detalles técnicos se guardaron en el registro:\n{log}",
        "An unexpected error occurred. The operation was not completed.\n\nTechnical details were saved to the log:\n{log}",
    ),
    "err.invalid_input": ("Revise los siguientes parámetros:", "Please review the following parameters:"),
    "err.write_failed": (
        "No se pudo escribir el archivo {file}. Verifique que la carpeta exista y que tenga permisos de escritura.",
        "Could not write the file {file}. Check that the folder exists and that you have write permission.",
    ),
    "err.bank_invalid": (
        "El banco actual tiene {n} errores de validación. Corríjalos en la pestaña «Banco de ítems» antes de continuar.",
        "The current bank has {n} validation errors. Fix them in the “Item bank” tab before continuing.",
    ),
    "err.no_bank": ("No hay un banco de ítems cargado.", "No item bank is loaded."),
    "err.bank_too_small": (
        "El banco tiene {n} ítems activos; esta operación necesita al menos {m}.",
        "The bank has {n} active items; this operation needs at least {m}.",
    ),
    "valerr.must_be_positive_int": ("{field}: debe ser un número entero mayor o igual que 1.",
                                    "{field}: must be an integer greater than or equal to 1."),
    "valerr.must_be_positive": ("{field}: debe ser mayor que 0.", "{field}: must be greater than 0."),
    "valerr.min_lt_max": ("{field}: el mínimo debe ser menor que el máximo.",
                          "{field}: the minimum must be less than the maximum."),
    "valerr.invalid_choice": ("{field}: la opción seleccionada no es válida.",
                              "{field}: the selected option is not valid."),
    "valerr.need_stopping_rule": ("Active al menos un criterio de terminación.",
                                  "Enable at least one stopping rule."),
    "valerr.fixed_needs_length": ("El test de longitud fija requiere un número máximo de ítems.",
                                  "A fixed-length test requires a maximum number of items."),
    "valerr.invalid_seed": ("{field}: la semilla debe ser un entero no negativo.",
                            "{field}: the seed must be a non-negative integer."),
    "valerr.must_be_probability": ("{field}: debe ser mayor que 0 y menor o igual que 1.",
                                   "{field}: must be greater than 0 and at most 1."),
    "valerr.a_positive": ("La discriminación (a) debe ser mayor que 0.", "Discrimination (a) must be greater than 0."),
    "valerr.c_range": ("El pseudo-azar (c) debe cumplir 0 ≤ c < 1.", "Guessing (c) must satisfy 0 ≤ c < 1."),
    "ioerr.file_not_found": ("No se encuentra el archivo: {path}", "File not found: {path}"),
    "ioerr.missing_column": (
        "No se puede importar el banco porque falta la columna «{column}».",
        "Cannot import the item bank because the “{column}” column is missing.",
    ),
    "ioerr.missing_difficulty": (
        "No se puede importar el banco porque falta la columna de dificultad «b» (también se acepta «difficulty» o «dificultad»).",
        "Cannot import the item bank because the difficulty column “b” is missing (“difficulty” is also accepted).",
    ),
    "ioerr.missing_value": (
        "No se puede importar el ítem «{item_id}»: falta el valor de la columna «{column}».",
        "Cannot import item “{item_id}”: the “{column}” value is missing.",
    ),
    "ioerr.non_numeric": (
        "No se puede importar el ítem «{item_id}»: el valor «{value}» de la columna «{column}» no es numérico.",
        "Cannot import item “{item_id}”: the value “{value}” in column “{column}” is not numeric.",
    ),
    "ioerr.no_items": ("El archivo no contiene ítems válidos.", "The file does not contain any valid items."),
    "ioerr.json_invalid": ("El archivo JSON no es válido: {msg} (línea {line}).",
                           "The JSON file is not valid: {msg} (line {line})."),
    "ioerr.json_structure": (
        "El JSON debe contener una lista de ítems o un objeto con la clave «items».",
        "The JSON must contain a list of items or an object with an “items” key.",
    ),
    "ioerr.encoding": ("No se pudo leer el archivo: la codificación no es UTF-8.",
                       "Could not read the file: the encoding is not UTF-8."),
    "ioerr.invalid_json": ("El archivo de configuración no es un JSON válido: {msg} (línea {line}).",
                           "The configuration file is not valid JSON: {msg} (line {line})."),
    "ioerr.not_config": ("El archivo no es una configuración de experimento de Meritum_CAT.",
                         "The file is not a Meritum_CAT experiment configuration."),
    "ioerr.invalid_value": ("La configuración contiene un valor inválido en «{field}».",
                            "The configuration contains an invalid value in “{field}”."),
})

# ----------------------------------------------------------------------------- inicio
_add({
    "home.title": ("Bienvenido a Meritum_CAT", "Welcome to Meritum_CAT"),
    "home.intro": (
        "Meritum_CAT es una plataforma científica de escritorio para estudiar el test adaptativo computarizado (CAT) "
        "basado en la Teoría de Respuesta al Ítem (IRT). Permite modelar ítems, simular poblaciones de examinados, "
        "comparar algoritmos de estimación y de selección, cuantificar la precisión y la exposición de ítems, "
        "visualizar los resultados, exportarlos y reproducir exactamente cada experimento.",
        "Meritum_CAT is a scientific desktop platform for studying computerized adaptive testing (CAT) based on "
        "Item Response Theory (IRT). It lets you model items, simulate populations of examinees, compare estimation "
        "and selection algorithms, quantify precision and item exposure, visualize the results, export them and "
        "reproduce every experiment exactly.",
    ),
    "home.workflow": ("Flujo de trabajo recomendado", "Recommended workflow"),
    "home.step1": ("1. Seleccione o genere un banco de ítems.", "1. Select or generate an item bank."),
    "home.step2": ("2. Explore el modelo IRT (curvas ICC e información).", "2. Explore the IRT model (ICC and information curves)."),
    "home.step3": ("3. Pruebe un CAT paso a paso con un examinado.", "3. Try a step-by-step CAT with one examinee."),
    "home.step4": (
        "4. Configure una simulación Monte Carlo: modelo, estimador, selección, criterio de terminación, población y semilla.",
        "4. Configure a Monte Carlo simulation: model, estimator, selection, stopping rule, population and seed.",
    ),
    "home.step5": ("5. Ejecute, analice las métricas y las figuras, y exporte.", "5. Run, analyse the metrics and figures, and export."),
    "home.step6": (
        "6. Guarde la configuración para reproducir el experimento o ejecute los experimentos científicos predefinidos.",
        "6. Save the configuration to reproduce the experiment, or run the predefined scientific experiments.",
    ),
    "home.bank_group": ("Banco de ítems actual", "Current item bank"),
    "home.synthetic_note": (
        "Los bancos incluidos son DATOS SINTÉTICOS generados por simulación con fines de experimentación. "
        "No son ítems reales ni provienen de ninguna prueba o institución. Para trabajar con datos reales, "
        "importe su propio banco calibrado (CSV o JSON).",
        "The included banks are SYNTHETIC DATA generated by simulation for experimentation. They are not real "
        "items and do not come from any real test or institution. To work with real data, import your own "
        "calibrated bank (CSV or JSON).",
    ),
    "home.offline": (
        "Todo el procesamiento científico se ejecuta localmente y sin conexión a Internet.",
        "All scientific processing runs locally and without an Internet connection.",
    ),
})

# ----------------------------------------------------------------------------- banco
_add({
    "bank.gen_group": ("Generador de banco sintético", "Synthetic bank generator"),
    "bank.generate": ("Generar banco sintético", "Generate synthetic bank"),
    "bank.examples_group": ("Bancos de ejemplo incluidos (sintéticos)", "Included example banks (synthetic)"),
    "bank.example_item": ("{n} ítems · {model}", "{n} items · {model}"),
    "bank.load_example": ("Cargar ejemplo", "Load example"),
    "bank.io_group": ("Importar / exportar", "Import / export"),
    "bank.import": ("Importar CSV/JSON…", "Import CSV/JSON…"),
    "bank.export_csv": ("Exportar CSV…", "Export CSV…"),
    "bank.export_json": ("Exportar JSON…", "Export JSON…"),
    "bank.format_help": (
        "Formato: una fila por ítem. Columnas obligatorias: item_id y b (dificultad). Opcionales: a, c, category, "
        "subcategory, tags (separadas por ;), question, alternatives (separadas por |), correct, source, active, notes.",
        "Format: one row per item. Required columns: item_id and b (difficulty). Optional: a, c, category, "
        "subcategory, tags (separated by ;), question, alternatives (separated by |), correct, source, active, notes.",
    ),
    "bank.edit_group": ("Edición de ítems", "Item editing"),
    "bank.add": ("Agregar ítem", "Add item"),
    "bank.edit": ("Editar ítem", "Edit item"),
    "bank.duplicate": ("Duplicar", "Duplicate"),
    "bank.delete": ("Eliminar", "Delete"),
    "bank.validate": ("Validar banco", "Validate bank"),
    "bank.summary": (
        "{name}: {n} ítems ({active} activos) · {ncat} categorías · media a = {a:.2f}, b = {b:.2f}, c = {c:.2f}",
        "{name}: {n} items ({active} active) · {ncat} categories · mean a = {a:.2f}, b = {b:.2f}, c = {c:.2f}",
    ),
    "bank.empty": ("No hay banco cargado.", "No bank loaded."),
    "bank.edit_hint": ("Doble clic en una fila para editar el ítem.", "Double-click a row to edit the item."),
    "col.item_id": ("ID", "ID"),
    "col.a": ("Discriminación (a)", "Discrimination (a)"),
    "col.b": ("Dificultad (b)", "Difficulty (b)"),
    "col.c": ("Pseudo-azar (c)", "Guessing (c)"),
    "col.category": ("Categoría", "Category"),
    "col.subcategory": ("Subcategoría", "Subcategory"),
    "col.tags": ("Etiquetas", "Tags"),
    "col.active": ("Activo", "Active"),
    "col.source": ("Fuente", "Source"),
    "col.question": ("Pregunta", "Question"),
    "col.notes": ("Observaciones", "Notes"),
    "val.title": ("Resultados de la validación", "Validation results"),
    "val.col_severity": ("Severidad", "Severity"),
    "val.col_item": ("Ítem", "Item"),
    "val.col_field": ("Campo", "Field"),
    "val.col_message": ("Mensaje", "Message"),
    "val.ok": ("Validación superada: no se encontraron problemas.", "Validation passed: no problems were found."),
    "val.summary": ("{errors} errores y {warnings} advertencias.", "{errors} errors and {warnings} warnings."),
    "val.not_run": ("Presione «Validar banco» para revisar el banco.", "Press “Validate bank” to check the bank."),
    "severity.error": ("Error", "Error"),
    "severity.warning": ("Advertencia", "Warning"),
    "val.missing_id": ("El ítem no tiene identificador.", "The item has no identifier."),
    "val.duplicate_id": ("ID duplicado: «{item_id}».", "Duplicate ID: “{item_id}”."),
    "val.a_nan": ("La discriminación (a) no es un número válido.", "Discrimination (a) is not a valid number."),
    "val.a_nonpositive": ("La discriminación (a = {value:g}) debe ser positiva.", "Discrimination (a = {value:g}) must be positive."),
    "val.a_high": ("La discriminación (a = {value:g}) es atípicamente alta (> 3).", "Discrimination (a = {value:g}) is unusually high (> 3)."),
    "val.b_nan": ("La dificultad (b) no es un número válido.", "Difficulty (b) is not a valid number."),
    "val.b_extreme": ("La dificultad (b = {value:g}) es extrema (|b| > 4).", "Difficulty (b = {value:g}) is extreme (|b| > 4)."),
    "val.c_nan": ("El pseudo-azar (c) no es un número válido.", "Guessing (c) is not a valid number."),
    "val.c_negative": ("El pseudo-azar (c = {value:g}) no puede ser negativo.", "Guessing (c = {value:g}) cannot be negative."),
    "val.c_ge_one": ("El pseudo-azar (c = {value:g}) debe ser menor que 1.", "Guessing (c = {value:g}) must be less than 1."),
    "val.c_high": ("El pseudo-azar (c = {value:g}) es atípicamente alto (> 0.5).", "Guessing (c = {value:g}) is unusually high (> 0.5)."),
    "val.missing_category": ("El ítem no tiene categoría de contenido.", "The item has no content category."),
    "val.bank_empty": ("El banco no contiene ítems.", "The bank contains no items."),
    "val.bank_no_active": ("El banco no tiene ítems activos.", "The bank has no active items."),
    "dlg.item_new": ("Nuevo ítem", "New item"),
    "dlg.item_edit": ("Editar ítem «{id}»", "Edit item “{id}”"),
    "field.item_id": ("Identificador del ítem (ID)", "Item identifier (ID)"),
    "field.question": ("Enunciado de la pregunta", "Question text"),
    "field.alternatives": ("Alternativas (una por línea)", "Alternatives (one per line)"),
    "field.correct": ("Respuesta correcta", "Correct answer"),
    "field.category": ("Categoría de contenido", "Content category"),
    "field.subcategory": ("Subcategoría", "Subcategory"),
    "field.tags": ("Etiquetas (separadas por ;)", "Tags (separated by ;)"),
    "field.source": ("Fuente", "Source"),
    "field.active": ("Ítem activo (disponible para administración)", "Active item (available for administration)"),
    "field.notes": ("Observaciones", "Notes"),
    "msg.select_item": ("Seleccione primero uno o más ítems en la tabla.", "First select one or more items in the table."),
    "msg.id_required": ("El ID del ítem es obligatorio.", "The item ID is required."),
    "msg.id_duplicate": ("Ya existe un ítem con el ID «{id}».", "An item with ID “{id}” already exists."),
    "msg.confirm_delete": ("¿Eliminar {n} ítem(s) seleccionado(s)?", "Delete {n} selected item(s)?"),
    "msg.bank_generated": ("Banco sintético generado: {n} ítems ({model}, semilla {seed}).",
                           "Synthetic bank generated: {n} items ({model}, seed {seed})."),
    "msg.bank_imported": ("Banco importado: {n} ítems desde {file}.", "Bank imported: {n} items from {file}."),
    "msg.bank_exported": ("Banco exportado a {file}.", "Bank exported to {file}."),
    "msg.bank_import_warnings": (
        "El banco se importó, pero la validación encontró {errors} errores y {warnings} advertencias. Revíselos en la tabla de validación.",
        "The bank was imported, but validation found {errors} errors and {warnings} warnings. Review them in the validation table.",
    ),
})

# ----------------------------------------------------------------------------- IRT
_add({
    "irt.params_group": ("Parámetros del ítem", "Item parameters"),
    "irt.add_curve": ("Añadir a la comparación", "Add to comparison"),
    "irt.clear": ("Limpiar comparación", "Clear comparison"),
    "irt.curves_note": (
        "La curva actual se actualiza al mover los parámetros. Puede fijar hasta 7 curvas para compararlas.",
        "The current curve updates as you change the parameters. You can pin up to 7 curves to compare them.",
    ),
    "irt.results_group": ("Información del ítem", "Item information"),
    "irt.max_info": ("Información máxima: {imax:.3f} en θ = {theta:.2f}", "Maximum information: {imax:.3f} at θ = {theta:.2f}"),
    "irt.region": (
        "Región más informativa (≥ 50 % del máximo): θ ∈ [{lo:.2f}, {hi:.2f}]",
        "Most informative region (≥ 50 % of maximum): θ ∈ [{lo:.2f}, {hi:.2f}]",
    ),
    "irt.info_at": ("En θ = {theta:.2f}: información = {info:.3f}; P(correcta) = {p:.3f}",
                    "At θ = {theta:.2f}: information = {info:.3f}; P(correct) = {p:.3f}"),
    "irt.subtab_item": ("Curvas del ítem (ICC / IIC)", "Item curves (ICC / IIC)"),
    "irt.subtab_test": ("Información del banco (TIF / EE)", "Bank information (TIF / SE)"),
    "irt.test_note": (
        "Calculada con los ítems activos del banco actual bajo el modelo IRT seleccionado.",
        "Computed from the active items of the current bank under the selected IRT model.",
    ),
    "irt.current_curve": ("actual", "current"),
    "irt.curve_label": ("a={a:.2f}, b={b:.2f}, c={c:.2f}", "a={a:.2f}, b={b:.2f}, c={c:.2f}"),
    "irt.model_note_1pl": ("En 1PL/Rasch se usan a = 1 y c = 0.", "In 1PL/Rasch, a = 1 and c = 0 are used."),
    "irt.model_note_2pl": ("En 2PL se usa c = 0.", "In 2PL, c = 0 is used."),
    "irt.model_note_3pl": ("En 3PL se usan a, b y c.", "In 3PL, a, b and c are used."),
})

# ----------------------------------------------------------------------------- CAT
_add({
    "cat.config_group": ("Configuración del CAT", "CAT configuration"),
    "cat.examinee_group": ("Examinado", "Examinee"),
    "cat.stop_group": ("Criterios de terminación", "Stopping rules"),
    "cat.mode": ("Modo de respuesta", "Response mode"),
    "cat.mode_sim": ("Simulada desde la θ verdadera", "Simulated from the true θ"),
    "cat.mode_manual": ("Manual (usted responde)", "Manual (you answer)"),
    "cat.start": ("Iniciar sesión", "Start session"),
    "cat.next": ("Siguiente ítem", "Next item"),
    "cat.answer_correct": ("Correcta", "Correct"),
    "cat.answer_incorrect": ("Incorrecta", "Incorrect"),
    "cat.run_all": ("Ejecutar hasta terminar", "Run to completion"),
    "cat.reset": ("Reiniciar", "Reset"),
    "cat.export_trace": ("Exportar traza CSV…", "Export trace CSV…"),
    "cat.state_group": ("Estado de la sesión", "Session state"),
    "cat.theta0": ("θ inicial", "Initial θ"),
    "cat.theta_now": ("θ actual", "Current θ"),
    "cat.se_now": ("Error estándar actual (EE)", "Current standard error (SE)"),
    "cat.n_items": ("Ítems administrados", "Items administered"),
    "cat.info": ("Información acumulada", "Cumulative information"),
    "cat.correct": ("Respuestas correctas", "Correct responses"),
    "cat.incorrect": ("Respuestas incorrectas", "Incorrect responses"),
    "cat.status": ("Estado", "Status"),
    "cat.not_started": ("Sin iniciar", "Not started"),
    "cat.in_progress": ("En curso", "In progress"),
    "cat.finished": ("Finalizada: {reason}", "Finished: {reason}"),
    "cat.pending_item": ("Ítem presentado: {id} (a = {a:.2f}, b = {b:.2f}, c = {c:.2f}). Responda con los botones.",
                         "Item presented: {id} (a = {a:.2f}, b = {b:.2f}, c = {c:.2f}). Answer with the buttons."),
    "cat.help": (
        "Inicie la sesión y avance ítem por ítem para observar cómo el algoritmo selecciona ítems, actualiza θ y reduce el error estándar.",
        "Start the session and advance item by item to see how the algorithm selects items, updates θ and reduces the standard error.",
    ),
    "col.step": ("Paso", "Step"),
    "col.response": ("Respuesta", "Response"),
    "col.theta_after": ("θ estimada", "Estimated θ"),
    "col.se_after": ("EE", "SE"),
    "col.info_after": ("Información", "Information"),
    "response.correct": ("Correcta", "Correct"),
    "response.incorrect": ("Incorrecta", "Incorrect"),
    "stop.max_items": ("se alcanzó el número máximo de ítems", "maximum number of items reached"),
    "stop.se_threshold": ("se alcanzó el error estándar objetivo", "target standard error reached"),
    "stop.target_information": ("se alcanzó la información objetivo", "target information reached"),
    "stop.bank_exhausted": ("se agotó el banco", "item bank exhausted"),
    "stop.fixed_length": ("longitud fija completada", "fixed length completed"),
})

# ----------------------------------------------------------------------------- Monte Carlo
_add({
    "mc.group_bank": ("1. Banco de ítems", "1. Item bank"),
    "mc.bank_current": ("{name} — {n} ítems activos", "{name} — {n} active items"),
    "mc.change_bank": ("Cambiar banco…", "Change bank…"),
    "mc.group_model": ("2. Modelo IRT", "2. IRT model"),
    "mc.group_estimation": ("3. Estimación de la habilidad", "3. Ability estimation"),
    "mc.group_selection": ("4. Selección de ítems", "4. Item selection"),
    "mc.group_stopping": ("5. Criterio de terminación", "5. Stopping rule"),
    "mc.group_population": ("6. Población simulada", "6. Simulated population"),
    "mc.group_repro": ("7. Reproducibilidad y tipo de prueba", "7. Reproducibility and test type"),
    "mc.new_seed": ("Nueva semilla", "New seed"),
    "mc.compare_fixed": ("Comparar también con un test fijo de igual longitud",
                         "Also compare with a fixed test of the same length"),
    "mc.run": ("Ejecutar", "Run"),
    "mc.stop": ("Detener", "Stop"),
    "mc.reset": ("Restablecer valores", "Reset values"),
    "mc.save_config": ("Guardar configuración…", "Save configuration…"),
    "mc.load_config": ("Cargar configuración…", "Load configuration…"),
    "mc.export_results": ("Exportar resultados CSV…", "Export results CSV…"),
    "mc.export_figures": ("Exportar figuras PNG…", "Export figures PNG…"),
    "mc.status_idle": ("Configure la simulación y presione «Ejecutar».", "Configure the simulation and press “Run”."),
    "mc.status_running": ("Simulando… {pct} % · {elapsed:.1f} s", "Simulating… {pct} % · {elapsed:.1f} s"),
    "mc.status_running_fixed": ("Simulando test fijo… {pct} % · {elapsed:.1f} s",
                                "Simulating fixed test… {pct} % · {elapsed:.1f} s"),
    "mc.status_done": ("Simulación completada en {sec:.1f} s.", "Simulation completed in {sec:.1f} s."),
    "mc.status_cancelled": ("Simulación detenida por el usuario. No se generaron resultados.",
                            "Simulation stopped by the user. No results were produced."),
    "mc.results_group": ("Resultados", "Results"),
    "mc.no_results": ("Aún no hay resultados. Ejecute una simulación.", "No results yet. Run a simulation."),
    "col.metric": ("Métrica", "Metric"),
    "col.value": ("Valor", "Value"),
    "col.cat": ("CAT", "CAT"),
    "col.fixed": ("Test fijo", "Fixed test"),
    "mc.subtab_recovery": ("θ real vs estimada", "True vs estimated θ"),
    "mc.subtab_error": ("Error", "Error"),
    "mc.subtab_conditional": ("Sesgo/RMSE por θ", "Bias/RMSE by θ"),
    "mc.subtab_precision": ("Precisión por ítems", "Precision by items"),
    "mc.subtab_exposure": ("Exposición", "Exposure"),
    "mc.subtab_length": ("Longitud", "Length"),
    "mc.subtab_compare": ("CAT vs fijo", "CAT vs fixed"),
    "mc.repro_ok": (
        "Reproducción verificada: los resultados coinciden exactamente con los guardados en la configuración.",
        "Reproduction verified: the results match exactly those stored in the configuration.",
    ),
    "mc.repro_diff": (
        "Atención: los resultados difieren de los guardados (diferencia máxima {d:.3g}).",
        "Warning: the results differ from the stored ones (maximum difference {d:.3g}).",
    ),
    "mc.config_loaded": (
        "Configuración cargada desde {file}. Presione «Ejecutar» para reproducir el experimento.",
        "Configuration loaded from {file}. Press “Run” to reproduce the experiment.",
    ),
    "mc.bank_restored": (
        "Se restauró el banco guardado en la configuración ({n} ítems; huella SHA-256 verificada).",
        "The bank stored in the configuration was restored ({n} items; SHA-256 fingerprint verified).",
    ),
    "mc.config_version_note": ("Creada con Meritum_CAT {v}.", "Created with Meritum_CAT {v}."),
    "mc.config_saved": ("Configuración guardada en {file}.", "Configuration saved to {file}."),
    "mc.results_exported": ("Resultados por examinado exportados a {file}.", "Per-examinee results exported to {file}."),
    "mc.figures_exported": ("{n} figuras exportadas a {folder}.", "{n} figures exported to {folder}."),
    "mc.need_results": ("Primero ejecute una simulación.", "Run a simulation first."),
    "mc.large_confirm": (
        "Simular {n} examinados puede tardar varios minutos (la interfaz seguirá respondiendo y podrá detenerla). ¿Continuar?",
        "Simulating {n} examinees may take several minutes (the interface stays responsive and you can stop it). Continue?",
    ),
    "mc.sh_note": (
        "Sympson-Hetter calibra primero los parámetros de control de exposición mediante simulaciones previas (incluidas en la barra de progreso).",
        "Sympson-Hetter first calibrates the exposure-control parameters through preliminary simulations (included in the progress bar).",
    ),
    "mc.content_balancing": ("Activar (proporciones iguales por categoría)",
                             "Enable (equal proportions per category)"),
})

# ----------------------------------------------------------------------------- métricas
METRICS = {
    "bias": (("Sesgo", "Bias"), ("Sesgo medio (Bias)", "Mean bias"),
             ("Media de (θ estimada − θ verdadera). Valores cercanos a 0 indican ausencia de error sistemático.",
              "Mean of (estimated θ − true θ). Values close to 0 indicate no systematic error.")),
    "mae": (("MAE", "MAE"), ("Error absoluto medio (MAE)", "Mean absolute error (MAE)"),
            ("Media de |θ estimada − θ verdadera|.", "Mean of |estimated θ − true θ|.")),
    "mse": (("MSE", "MSE"), ("Error cuadrático medio (MSE)", "Mean squared error (MSE)"),
            ("Media de (θ estimada − θ verdadera)². Combina varianza y sesgo al cuadrado.",
             "Mean of (estimated θ − true θ)². Combines variance and squared bias.")),
    "rmse": (("RMSE", "RMSE"), ("Raíz del error cuadrático medio (RMSE)", "Root mean squared error (RMSE)"),
             ("Raíz cuadrada del MSE, en unidades de θ (logits). Menor es mejor.",
              "Square root of the MSE, in θ units (logits). Lower is better.")),
    "pearson": (("Pearson r", "Pearson r"), ("Correlación de Pearson (r)", "Pearson correlation (r)"),
                ("Correlación lineal entre θ verdadera y estimada.", "Linear correlation between true and estimated θ.")),
    "spearman": (("Spearman ρ", "Spearman ρ"), ("Correlación de Spearman (ρ)", "Spearman correlation (ρ)"),
                 ("Correlación de rangos entre θ verdadera y estimada (conservación del orden).",
                  "Rank correlation between true and estimated θ (order preservation).")),
    "coverage95": (("Cobertura IC 95 %", "95 % CI coverage"), ("Cobertura del intervalo de confianza del 95 %", "95 % confidence-interval coverage"),
                   ("Proporción de examinados cuyo intervalo θ̂ ± 1.96·EE contiene la θ verdadera. El valor nominal es 0.95.",
                    "Proportion of examinees whose interval θ̂ ± 1.96·SE contains the true θ. The nominal value is 0.95.")),
    "mean_se": (("EE medio", "Mean SE"), ("Error estándar medio", "Mean standard error"),
                ("Promedio del error estándar final reportado por el estimador.", "Average of the final standard error reported by the estimator.")),
    "mean_test_length": (("Longitud media", "Mean length"), ("Longitud media del test (ítems)", "Mean test length (items)"),
                         ("Número promedio de ítems administrados por examinado.", "Average number of items administered per examinee.")),
    "max_exposure_rate": (("Exposición máx.", "Max. exposure"), ("Tasa máxima de exposición", "Maximum exposure rate"),
                          ("Mayor proporción de examinados a quienes se administró un mismo ítem.",
                           "Largest proportion of examinees who received the same item.")),
    "mean_exposure_rate": (("Exposición media", "Mean exposure"), ("Tasa media de exposición", "Mean exposure rate"),
                           ("Promedio de las tasas de exposición de todos los ítems del banco.",
                            "Average exposure rate over all items in the bank.")),
    "unused_items": (("Ítems no usados", "Unused items"), ("Ítems nunca administrados", "Items never administered"),
                     ("Número de ítems del banco que no se administraron a ningún examinado.",
                      "Number of bank items never administered to any examinee.")),
    "elapsed_seconds": (("Tiempo (s)", "Time (s)"), ("Tiempo de cómputo (s)", "Computation time (s)"),
                        ("Tiempo de ejecución de la simulación en segundos.", "Simulation run time in seconds.")),
    "n_examinees": (("N", "N"), ("Examinados simulados", "Simulated examinees"),
                    ("Número de examinados virtuales de la simulación.", "Number of virtual examinees in the simulation.")),
    "sh_max_exposure_final": (("Exposición máx. (calibración SH)", "Max. exposure (SH calibration)"),
                              ("Exposición máxima en la última iteración de calibración Sympson-Hetter", "Maximum exposure in the last Sympson-Hetter calibration iteration"),
                              ("Valor alcanzado en la última iteración de calibración de los parámetros K.",
                               "Value reached in the last calibration iteration of the K parameters.")),
}
for _k, (_short, _long, _help) in METRICS.items():
    S[f"metric.{_k}"] = _short
    S[f"metric_long.{_k}"] = _long
    S[f"metric_help.{_k}"] = _help

# ----------------------------------------------------------------------------- columnas de experimentos y valores
_add({
    "col.model": ("Modelo IRT", "IRT model"),
    "col.estimator": ("Estimador", "Estimator"),
    "col.selector": ("Selección de ítems", "Item selection"),
    "col.test_type": ("Tipo de prueba", "Test type"),
    "col.test_length": ("Longitud del test (ítems)", "Test length (items)"),
    "col.bank_size": ("Tamaño del banco (ítems)", "Bank size (items)"),
    "col.param_noise": ("Error de calibración (DE del ruido)", "Calibration error (noise SD)"),
    "col.population": ("Población de θ", "θ population"),
    "col.seed": ("Semilla", "Seed"),
    "col.bias": ("Sesgo", "Bias"),
    "col.mae": ("MAE", "MAE"),
    "col.mse": ("MSE", "MSE"),
    "col.rmse": ("RMSE", "RMSE"),
    "col.pearson": ("Pearson r", "Pearson r"),
    "col.spearman": ("Spearman ρ", "Spearman ρ"),
    "col.coverage95": ("Cobertura IC 95 %", "95 % CI coverage"),
    "col.mean_se": ("EE medio", "Mean SE"),
    "col.max_exposure": ("Exposición máx.", "Max. exposure"),
    "col.mean_exposure": ("Exposición media", "Mean exposure"),
    "col.overexposed_items": ("Ítems con exposición > 0.2", "Items with exposure > 0.2"),
    "col.unused_items": ("Ítems no usados", "Unused items"),
    "col.chi2_uniformity": ("χ² de uniformidad", "χ² uniformity"),
    "testtype.cat": ("CAT (adaptativo)", "CAT (adaptive)"),
    "testtype.fixed": ("Fijo (aleatorio)", "Fixed (random)"),
    "sel.Maximum Information": ("Máxima información", "Maximum information"),
    "sel.Random": ("Aleatoria", "Random"),
    "sel.Randomesque": ("Randomesque", "Randomesque"),
    "sel.Kullback-Leibler": ("Kullback-Leibler", "Kullback-Leibler"),
    "sel.Sympson-Hetter": ("Sympson-Hetter", "Sympson-Hetter"),
    "est.MLE": ("MLE — Máxima verosimilitud", "MLE — Maximum likelihood"),
    "est.MAP": ("MAP — Máximo a posteriori", "MAP — Maximum a posteriori"),
    "est.EAP": ("EAP — Esperado a posteriori", "EAP — Expected a posteriori"),
    "model.1PL": ("1PL / Rasch — solo dificultad (b)", "1PL / Rasch — difficulty only (b)"),
    "model.2PL": ("2PL — discriminación (a) y dificultad (b)", "2PL — discrimination (a) and difficulty (b)"),
    "model.3PL": ("3PL — a, b y pseudo-azar (c)", "3PL — a, b and guessing (c)"),
    "dist.normal": ("Normal", "Normal"),
    "dist.uniform": ("Uniforme", "Uniform"),
    "mode.cat": ("Adaptativa (CAT)", "Adaptive (CAT)"),
    "mode.fixed": ("Longitud fija (no adaptativa)", "Fixed length (non-adaptive)"),
    "bool.yes": ("Sí", "Yes"),
    "bool.no": ("No", "No"),
})

# ----------------------------------------------------------------------------- experimentos
_add({
    "exp.list_group": ("Experimentos disponibles", "Available experiments"),
    "exp.params_group": ("Parámetros del experimento", "Experiment parameters"),
    "exp.use_bank": ("Usar el banco actual cuando el experimento lo admite",
                     "Use the current bank when the experiment allows it"),
    "exp.run": ("Ejecutar experimento", "Run experiment"),
    "exp.stop": ("Detener", "Stop"),
    "exp.export_csv": ("Exportar tabla CSV…", "Export table CSV…"),
    "exp.export_json": ("Exportar resultado JSON…", "Export result JSON…"),
    "exp.description": ("Descripción y diseño", "Description and design"),
    "exp.interpretation": ("Interpretación", "Interpretation"),
    "exp.status_idle": ("Seleccione un experimento y presione «Ejecutar experimento».",
                        "Select an experiment and press “Run experiment”."),
    "exp.status_running": ("Ejecutando… {pct} % · {elapsed:.1f} s", "Running… {pct} % · {elapsed:.1f} s"),
    "exp.status_done": ("Experimento completado en {sec:.1f} s.", "Experiment completed in {sec:.1f} s."),
    "exp.status_cancelled": ("Experimento detenido por el usuario. No se generaron resultados.",
                             "Experiment stopped by the user. No results were produced."),
    "exp.bank_own": ("Este experimento genera sus propios bancos sintéticos, porque el factor estudiado es el banco o el modelo.",
                     "This experiment generates its own synthetic banks, because the factor studied is the bank or the model."),
    "exp.result_exported": ("Resultado exportado a {file}.", "Result exported to {file}."),
    "exp.need_result": ("Primero ejecute el experimento.", "Run the experiment first."),
    "exp.conditions": ("Condiciones: {n}", "Conditions: {n}"),
})

EXPERIMENT_TEXT = {
    "ability_recovery": (
        ("Experimento 1 — Recuperación de la habilidad", "Experiment 1 — Ability recovery"),
        ("Compara la θ verdadera con la θ estimada bajo los modelos 1PL, 2PL y 3PL. Cada modelo usa un banco sintético de 500 ítems generado con ese modelo; estimador EAP, selección por máxima información y 20 ítems.",
         "Compares true and estimated θ under the 1PL, 2PL and 3PL models. Each model uses a 500-item synthetic bank simulated under that model; EAP estimator, maximum-information selection and 20 items."),
        ("Un sesgo cercano a 0, RMSE bajo y correlaciones altas indican buena recuperación. La cobertura debería aproximarse a 0.95.",
         "A bias close to 0, a low RMSE and high correlations indicate good recovery. Coverage should be close to 0.95."),
    ),
    "estimators": (
        ("Experimento 2 — Comparación de estimadores", "Experiment 2 — Estimator comparison"),
        ("Compara MLE, MAP y EAP con el mismo banco, el mismo selector (máxima información), la misma población y 20 ítems (modelo 2PL).",
         "Compares MLE, MAP and EAP with the same bank, the same selector (maximum information), the same population and 20 items (2PL model)."),
        ("MAP y EAP incorporan una distribución previa que regulariza la estimación; suelen mostrar menor RMSE que MLE, a costa de cierto sesgo hacia la media de la previa en los extremos.",
         "MAP and EAP include a prior that regularizes the estimate; they usually show a lower RMSE than MLE, at the cost of some bias towards the prior mean at the extremes."),
    ),
    "selection": (
        ("Experimento 3 — Comparación de la selección de ítems", "Experiment 3 — Item selection comparison"),
        ("Compara máxima información, selección aleatoria, Randomesque, Kullback-Leibler y Sympson-Hetter (2PL, EAP, 20 ítems).",
         "Compares maximum information, random selection, Randomesque, Kullback-Leibler and Sympson-Hetter (2PL, EAP, 20 items)."),
        ("La selección aleatoria es la línea base: menor precisión y exposición uniforme. Los métodos basados en información mejoran la precisión; el control de exposición reduce la exposición máxima con un pequeño costo en RMSE.",
         "Random selection is the baseline: lower precision and uniform exposure. Information-based methods improve precision; exposure control reduces maximum exposure at a small cost in RMSE."),
    ),
    "cat_vs_fixed": (
        ("Experimento 4 — CAT vs test fijo", "Experiment 4 — CAT vs fixed test"),
        ("Compara un CAT (máxima información) con un test de longitud fija formado por ítems aleatorios del mismo banco, para longitudes de 10, 20 y 30 ítems.",
         "Compares a CAT (maximum information) with a fixed-length test made of random items from the same bank, for lengths of 10, 20 and 30 items."),
        ("A igual número de ítems, el CAT debería alcanzar menor RMSE y menor error estándar, porque adapta la dificultad a cada examinado.",
         "For the same number of items, the CAT should achieve a lower RMSE and standard error, because it adapts difficulty to each examinee."),
    ),
    "bank_size": (
        ("Experimento 5 — Tamaño del banco", "Experiment 5 — Bank size"),
        ("Evalúa bancos sintéticos de 50, 100, 250, 500 y 1000 ítems (2PL, EAP, máxima información, 20 ítems).",
         "Evaluates synthetic banks of 50, 100, 250, 500 and 1000 items (2PL, EAP, maximum information, 20 items)."),
        ("Bancos mayores ofrecen ítems más informativos en todo el rango de θ, por lo que la precisión mejora y se estabiliza; con máxima información la exposición máxima permanece alta.",
         "Larger banks offer more informative items across the θ range, so precision improves and levels off; with maximum information the maximum exposure remains high."),
    ),
    "test_length": (
        ("Experimento 6 — Longitud máxima del test", "Experiment 6 — Maximum test length"),
        ("Varía el número máximo de ítems: 5, 10, 15, 20, 30 y 40 (2PL, EAP, máxima información).",
         "Varies the maximum number of items: 5, 10, 15, 20, 30 and 40 (2PL, EAP, maximum information)."),
        ("El RMSE y el error estándar deberían disminuir al aumentar la longitud, con rendimientos decrecientes.",
         "RMSE and standard error should decrease as length increases, with diminishing returns."),
    ),
    "robustness": (
        ("Experimento 7 — Robustez ante errores de calibración", "Experiment 7 — Robustness to calibration error"),
        ("Las respuestas se generan con los parámetros verdaderos de un banco 3PL, pero el CAT selecciona y estima con parámetros perturbados con ruido gaussiano (DE 0, 0.1, 0.2, 0.3, 0.5 en a y b).",
         "Responses are simulated from the true parameters of a 3PL bank, but the CAT selects and estimates with parameters perturbed by Gaussian noise (SD 0, 0.1, 0.2, 0.3, 0.5 on a and b)."),
        ("Al aumentar el error de calibración, la precisión se degrada y la cobertura del intervalo cae por debajo del valor nominal: el error estándar reportado deja de reflejar la incertidumbre real.",
         "As calibration error increases, precision degrades and interval coverage falls below its nominal value: the reported standard error no longer reflects the true uncertainty."),
    ),
    "exposure": (
        ("Experimento 8 — Control de exposición", "Experiment 8 — Exposure control"),
        ("Compara la exposición de los ítems entre algoritmos de selección con un banco de 300 ítems (2PL, EAP, 20 ítems).",
         "Compares item exposure across selection algorithms with a 300-item bank (2PL, EAP, 20 items)."),
        ("Máxima información y KL concentran la exposición en pocos ítems. Randomesque la reduce moderadamente y Sympson-Hetter la limita cerca del máximo objetivo (0.25), con un aumento moderado del RMSE.",
         "Maximum information and KL concentrate exposure on a few items. Randomesque reduces it moderately and Sympson-Hetter keeps it near the target maximum (0.25), with a moderate RMSE increase."),
    ),
    "populations": (
        ("Experimento 9 — Poblaciones de habilidad", "Experiment 9 — Ability populations"),
        ("Evalúa el CAT con distintas distribuciones de θ verdadera: N(0.1), N(−1.1), N(1.1), N(0, 1.5) y U(−3.3).",
         "Evaluates the CAT with different true-θ distributions: N(0,1), N(−1,1), N(1,1), N(0, 1.5) and U(−3,3)."),
        ("Cuando la población se aleja de la previa del estimador o de la zona donde el banco es informativo, aumentan el sesgo y el RMSE.",
         "When the population moves away from the estimator's prior or from the region where the bank is informative, bias and RMSE increase."),
    ),
    "seeds": (
        ("Experimento 10 — Semillas y reproducibilidad", "Experiment 10 — Seeds and reproducibility"),
        ("Ejecuta la misma configuración con cinco semillas distintas y repite la primera para verificar la reproducibilidad exacta.",
         "Runs the same configuration with five different seeds and repeats the first one to verify exact reproducibility."),
        ("RMSE medio = {rmse_mean}; desviación estándar entre semillas = {rmse_sd} (variabilidad Monte Carlo). Reproducibilidad exacta con la misma semilla: {reproducible}.",
         "Mean RMSE = {rmse_mean}; standard deviation across seeds = {rmse_sd} (Monte Carlo variability). Exact reproducibility with the same seed: {reproducible}."),
    ),
}
for _k, (_title, _desc, _summary) in EXPERIMENT_TEXT.items():
    S[f"exp.{_k}.title"] = _title
    S[f"exp.{_k}.desc"] = _desc
    S[f"exp.{_k}.summary"] = _summary
S["exp.reproducible.true"] = ("CONFIRMADA", "CONFIRMED")
S["exp.reproducible.false"] = ("NO CONFIRMADA", "NOT CONFIRMED")

# ----------------------------------------------------------------------------- ayuda y acerca de
_add({
    "help.valid_range": ("Rango válido", "Valid range"),
    "help.button_tooltip": ("Mostrar la ayuda de este parámetro", "Show help for this parameter"),
    "help.title": ("Ayuda: {name}", "Help: {name}"),
    "help.symbol": ("Símbolo", "Symbol"),
    "qs.title": ("Guía rápida de Meritum_CAT", "Meritum_CAT quick start guide"),
    "qs.body": (
        "<h3>Ejemplo: simulación Monte Carlo reproducible</h3><ol>"
        "<li>En <b>Banco de ítems</b>, genere un banco sintético (p. ej. 500 ítems, 2PL, semilla 2026) o importe el suyo (CSV/JSON) y presione <b>Validar banco</b>.</li>"
        "<li>En <b>Modelos IRT</b>, explore las curvas ICC e IIC y la información del banco.</li>"
        "<li>En <b>Simulación Monte Carlo</b>, elija el modelo (2PL), el estimador (EAP) y la selección (Máxima información).</li>"
        "<li>Defina el criterio de terminación (p. ej. 20 ítems máximo) y la población (p. ej. 5000 examinados, Normal(0,1)).</li>"
        "<li>Escriba una semilla (p. ej. 12345) y presione <b>Ejecutar</b>. Puede <b>Detener</b> en cualquier momento.</li>"
        "<li>Analice sesgo, RMSE, cobertura y exposición en la tabla y en las pestañas de figuras.</li>"
        "<li>Marque <b>Comparar también con un test fijo</b> para contrastar CAT y test fijo.</li>"
        "<li>Exporte resultados (CSV), figuras (PNG) y la configuración (JSON).</li>"
        "<li>Para reproducir: <b>Archivo → Cargar configuración</b> y <b>Ejecutar</b>. Meritum_CAT restaura el banco, verifica su huella y compara los resultados con los guardados.</li></ol>"
        "<p>Cada parámetro tiene una ayuda (<b>?</b>) con su significado y su rango válido.</p>",
        "<h3>Example: reproducible Monte Carlo simulation</h3><ol>"
        "<li>In <b>Item bank</b>, generate a synthetic bank (e.g. 500 items, 2PL, seed 2026) or import your own (CSV/JSON) and press <b>Validate bank</b>.</li>"
        "<li>In <b>IRT models</b>, explore the ICC and IIC curves and the bank information.</li>"
        "<li>In <b>Monte Carlo simulation</b>, choose the model (2PL), the estimator (EAP) and the selection (Maximum information).</li>"
        "<li>Set the stopping rule (e.g. at most 20 items) and the population (e.g. 5000 examinees, Normal(0,1)).</li>"
        "<li>Type a seed (e.g. 12345) and press <b>Run</b>. You can <b>Stop</b> at any time.</li>"
        "<li>Analyse bias, RMSE, coverage and exposure in the table and the figure tabs.</li>"
        "<li>Tick <b>Also compare with a fixed test</b> to contrast CAT and fixed test.</li>"
        "<li>Export results (CSV), figures (PNG) and the configuration (JSON).</li>"
        "<li>To reproduce: <b>File → Load configuration</b> and <b>Run</b>. Meritum_CAT restores the bank, verifies its fingerprint and compares the results with the stored ones.</li></ol>"
        "<p>Every parameter has a help button (<b>?</b>) with its meaning and valid range.</p>",
    ),
    "gl.title": ("Glosario de parámetros científicos", "Scientific parameter glossary"),
    "gl.col_param": ("Parámetro", "Parameter"),
    "gl.col_symbol": ("Símbolo", "Symbol"),
    "gl.col_desc": ("Descripción", "Description"),
    "gl.col_range": ("Rango válido", "Valid range"),
    "about.title": ("Acerca de Meritum_CAT", "About Meritum_CAT"),
    "about.version": ("Versión {v}", "Version {v}"),
    "about.author": ("Autores: {a}", "Authors: {a}"),
    "about.description": (
        "Software científico para la investigación en psicometría, Teoría de Respuesta al Ítem, test adaptativo computarizado y simulación Monte Carlo de evaluaciones. Funciona sin conexión a Internet.",
        "Scientific software for research in psychometrics, Item Response Theory, computerized adaptive testing and Monte Carlo simulation of assessments. Works without an Internet connection.",
    ),
    "about.components": ("Componentes de código abierto", "Open-source components"),
    "about.data_note": (
        "Los bancos de ejemplo incluidos son datos sintéticos, no datos reales.",
        "The included example banks are synthetic data, not real data.",
    ),
})

# ----------------------------------------------------------------------------- figuras
_add({
    "plot.theta": ("Habilidad θ (logits)", "Ability θ (logits)"),
    "plot.theta_true": ("θ verdadera (logits)", "True θ (logits)"),
    "plot.theta_est": ("θ estimada (logits)", "Estimated θ (logits)"),
    "plot.icc.title": ("Curva característica del ítem (ICC)", "Item characteristic curve (ICC)"),
    "plot.icc.y": ("Probabilidad de respuesta correcta P(θ)", "Probability of a correct response P(θ)"),
    "plot.iic.title": ("Curva de información del ítem (IIC)", "Item information curve (IIC)"),
    "plot.iic.y": ("Información de Fisher I(θ)", "Fisher information I(θ)"),
    "plot.tif.title": ("Función de información del test (TIF)", "Test information function (TIF)"),
    "plot.tif.y": ("Información de Fisher I(θ)", "Fisher information I(θ)"),
    "plot.sef.title": ("Función de error estándar", "Standard error function"),
    "plot.se.y": ("Error estándar EE(θ) (logits)", "Standard error SE(θ) (logits)"),
    "plot.bank_info.suptitle": ("Información del banco ({n} ítems activos)", "Bank information ({n} active items)"),
    "plot.item_number": ("Número de ítems administrados", "Number of items administered"),
    "plot.cat.theta.title": ("Estimación de θ por ítem", "θ estimate by item"),
    "plot.cat.se.title": ("Error estándar por ítem", "Standard error by item"),
    "plot.cat.info.title": ("Información acumulada", "Cumulative information"),
    "plot.cat.b.title": ("Dificultad del ítem seleccionado", "Difficulty of the selected item"),
    "plot.cat.band": ("IC 95 % (θ̂ ± 1.96·EE)", "95 % CI (θ̂ ± 1.96·SE)"),
    "plot.cat.theta_hat": ("θ estimada", "Estimated θ"),
    "plot.cat.theta_true": ("θ verdadera", "True θ"),
    "plot.cat.b_selected": ("Dificultad b del ítem", "Item difficulty b"),
    "plot.b_axis": ("Escala θ / b (logits)", "θ / b scale (logits)"),
    "plot.examinees": ("Examinados", "Examinees"),
    "plot.identity": ("Identidad (θ̂ = θ)", "Identity (θ̂ = θ)"),
    "plot.recovery.title": ("θ verdadera vs θ estimada", "True θ vs estimated θ"),
    "plot.error.title": ("Distribución del error de estimación", "Distribution of estimation error"),
    "plot.error.x": ("Error θ̂ − θ (logits)", "Error θ̂ − θ (logits)"),
    "plot.mean_error": ("Error medio = {v:.3f}", "Mean error = {v:.3f}"),
    "plot.count": ("Frecuencia (examinados)", "Frequency (examinees)"),
    "plot.cond_bias.title": ("Sesgo condicional por θ", "Conditional bias by θ"),
    "plot.cond_rmse.title": ("RMSE condicional por θ", "Conditional RMSE by θ"),
    "plot.bias.y": ("Sesgo (logits)", "Bias (logits)"),
    "plot.rmse.y": ("RMSE (logits)", "RMSE (logits)"),
    "plot.rmse_items.title": ("RMSE vs número de ítems", "RMSE vs number of items"),
    "plot.se_items.title": ("Error estándar medio vs número de ítems", "Mean standard error vs number of items"),
    "plot.exposure.sorted.title": ("Tasa de exposición por ítem (ordenada)", "Exposure rate by item (sorted)"),
    "plot.exposure.hist.title": ("Histograma de tasas de exposición", "Histogram of exposure rates"),
    "plot.exposure.rank": ("Ítems ordenados por exposición", "Items ranked by exposure"),
    "plot.exposure.y": ("Tasa de exposición (proporción)", "Exposure rate (proportion)"),
    "plot.exposure.target": ("Máximo objetivo r = {v:.2f}", "Target maximum r = {v:.2f}"),
    "plot.n_items": ("Número de ítems", "Number of items"),
    "plot.length.title": ("Distribución de la longitud del test", "Test length distribution"),
    "plot.length.x": ("Ítems administrados", "Items administered"),
    "plot.cat_label": ("CAT", "CAT"),
    "plot.fixed_label": ("Test fijo", "Fixed test"),
    "plot.cat_vs_fixed.suptitle": ("CAT vs test fijo de igual longitud", "CAT vs fixed test of equal length"),
    "plot.cat_vs_fixed.global": ("Error global", "Overall error"),
    "plot.value_theta": ("Valor (logits)", "Value (logits)"),
    "plot.correlation": ("Correlación", "Correlation"),
    "plot.nominal95": ("Nominal 0.95", "Nominal 0.95"),
    "plot.mean": ("Media", "Mean"),
    "plot.exp.error_by_model": ("Error por modelo", "Error by model"),
    "plot.exp.corr_by_model": ("Correlación por modelo", "Correlation by model"),
    "plot.exp.error_by_estimator": ("Error por estimador", "Error by estimator"),
    "plot.exp.bias_by_estimator": ("Sesgo por estimador", "Bias by estimator"),
    "plot.exp.rmse_by_selector": ("RMSE por método de selección", "RMSE by selection method"),
    "plot.exp.exposure_by_selector": ("Exposición máxima por método", "Maximum exposure by method"),
    "plot.exp.rmse_by_length": ("RMSE vs longitud del test", "RMSE vs test length"),
    "plot.exp.se_by_length": ("EE medio vs longitud del test", "Mean SE vs test length"),
    "plot.exp.rmse_by_bank": ("RMSE vs tamaño del banco", "RMSE vs bank size"),
    "plot.exp.exposure_by_bank": ("Exposición máxima vs tamaño del banco", "Maximum exposure vs bank size"),
    "plot.exp.rmse_by_noise": ("RMSE vs error de calibración", "RMSE vs calibration error"),
    "plot.exp.coverage_by_noise": ("Cobertura vs error de calibración", "Coverage vs calibration error"),
    "plot.exp.rmse_by_population": ("RMSE por población", "RMSE by population"),
    "plot.exp.bias_by_population": ("Sesgo por población", "Bias by population"),
    "plot.exp.rmse_by_seed": ("RMSE por semilla", "RMSE by seed"),
})

STRINGS = S

# ----------------------------------------------------------------------------- parámetros científicos
PARAM_HELP: dict[str, dict] = {
    "a": {
        "name": ("Discriminación del ítem", "Item discrimination"), "symbol": "a",
        "help": ("Determina qué tan fuertemente el ítem diferencia a examinados con habilidades cercanas a su dificultad. Es la pendiente de la curva característica: valores mayores producen curvas más empinadas y más información concentrada.",
                 "Determines how strongly the item differentiates examinees whose abilities are close to its difficulty. It is the slope of the characteristic curve: larger values produce steeper curves and more concentrated information."),
        "range": ("a > 0 (habitual: 0.3 a 2.5)", "a > 0 (typical: 0.3 to 2.5)"),
    },
    "b": {
        "name": ("Dificultad del ítem", "Item difficulty"), "symbol": "b",
        "help": ("Punto de la escala de habilidad en el que la curva característica alcanza su punto de inflexión (P = 0.5 en 1PL/2PL). Valores mayores indican ítems más difíciles.",
                 "Point on the ability scale where the characteristic curve reaches its inflection point (P = 0.5 in 1PL/2PL). Larger values indicate harder items."),
        "range": ("Número real, en logits (habitual: −3 a 3)", "Real number, in logits (typical: −3 to 3)"),
    },
    "c": {
        "name": ("Pseudo-azar (adivinación)", "Pseudo-guessing"), "symbol": "c",
        "help": ("Asíntota inferior de la curva característica: probabilidad de que un examinado de habilidad muy baja responda correctamente (por ejemplo, adivinando). Solo interviene en el modelo 3PL.",
                 "Lower asymptote of the characteristic curve: probability that an examinee with very low ability answers correctly (e.g. by guessing). Only used in the 3PL model."),
        "range": ("0 ≤ c < 1 (habitual: 0 a 0.35)", "0 ≤ c < 1 (typical: 0 to 0.35)"),
    },
    "theta_eval": {
        "name": ("Habilidad a evaluar", "Ability to evaluate"), "symbol": "θ",
        "help": ("Valor de habilidad en el que se calculan la probabilidad de acierto y la información del ítem.",
                 "Ability value at which the probability of a correct response and the item information are computed."),
        "range": ("−4 a 4 logits", "−4 to 4 logits"),
    },
    "model": {
        "name": ("Modelo IRT", "IRT model"), "symbol": "",
        "help": ("Modelo logístico de Teoría de Respuesta al Ítem. 1PL/Rasch usa solo la dificultad; 2PL añade la discriminación; 3PL añade el pseudo-azar. El modelo elegido determina qué parámetros del banco intervienen en la simulación y en la estimación.",
                 "Logistic Item Response Theory model. 1PL/Rasch uses difficulty only; 2PL adds discrimination; 3PL adds pseudo-guessing. The chosen model determines which bank parameters are used in simulation and estimation."),
        "range": ("1PL, 2PL o 3PL", "1PL, 2PL or 3PL"),
    },
    "estimator": {
        "name": ("Método de estimación de la habilidad", "Ability estimation method"), "symbol": "θ̂",
        "help": ("MLE maximiza la verosimilitud (sin previa; puede ser extremo con pocos ítems). MAP maximiza la posterior con una previa normal. EAP calcula la media posterior por cuadratura; es estable desde el primer ítem.",
                 "MLE maximizes the likelihood (no prior; can be extreme with few items). MAP maximizes the posterior with a normal prior. EAP computes the posterior mean by quadrature; it is stable from the first item."),
        "range": ("MLE, MAP o EAP", "MLE, MAP or EAP"),
    },
    "selector": {
        "name": ("Algoritmo de selección de ítems", "Item selection algorithm"), "symbol": "",
        "help": ("Máxima información elige el ítem más informativo en la θ actual. Aleatoria es la línea base. Randomesque elige al azar entre los k más informativos. Kullback-Leibler usa información global alrededor de θ. Sympson-Hetter limita probabilísticamente la exposición.",
                 "Maximum information picks the most informative item at the current θ. Random is the baseline. Randomesque picks at random among the k most informative. Kullback-Leibler uses global information around θ. Sympson-Hetter limits exposure probabilistically."),
        "range": ("Una de las cinco opciones", "One of the five options"),
    },
    "max_items": {
        "name": ("Número máximo de ítems", "Maximum number of items"), "symbol": ("Lmáx", "Lmax"),
        "help": ("El test termina al administrar este número de ítems. En el test de longitud fija es la longitud exacta.",
                 "The test ends after administering this number of items. In a fixed-length test it is the exact length."),
        "range": ("Entero ≥ 1 (sin superar el banco)", "Integer ≥ 1 (not exceeding the bank)"),
    },
    "se_threshold": {
        "name": ("Umbral de error estándar", "Standard error threshold"), "symbol": ("EE*", "SE*"),
        "help": ("El test termina cuando el error estándar de la estimación es menor o igual que este valor. Un umbral de 0.30 equivale aproximadamente a una fiabilidad de 0.91 en una población N(0.1).",
                 "The test ends when the standard error of the estimate is less than or equal to this value. A threshold of 0.30 corresponds approximately to a reliability of 0.91 in an N(0,1) population."),
        "range": ("> 0 (habitual: 0.20 a 0.50)", "> 0 (typical: 0.20 to 0.50)"),
    },
    "target_information": {
        "name": ("Información mínima objetivo", "Minimum target information"), "symbol": "I*",
        "help": ("El test termina cuando la información acumulada del test alcanza este valor. Como EE = 1/√I, una información de 11.1 equivale a un EE de 0.30.",
                 "The test ends when the cumulative test information reaches this value. Since SE = 1/√I, an information of 11.1 corresponds to an SE of 0.30."),
        "range": ("> 0", "> 0"),
    },
    "min_items": {
        "name": ("Número mínimo de ítems", "Minimum number of items"), "symbol": ("Lmín", "Lmin"),
        "help": ("Número mínimo de ítems antes de aplicar los criterios de error estándar o de información.",
                 "Minimum number of items before the standard-error or information criteria are applied."),
        "range": ("Entero ≥ 1", "Integer ≥ 1"),
    },
    "n_examinees": {
        "name": ("Número de examinados simulados", "Number of simulated examinees"), "symbol": "N",
        "help": ("Cantidad de sujetos virtuales generados durante la simulación Monte Carlo. Valores mayores producen estimaciones estadísticas más estables, pero requieren mayor tiempo de procesamiento.",
                 "Number of virtual subjects generated during the Monte Carlo simulation. Larger values produce more stable statistical estimates but require more processing time."),
        "range": ("Entero de 1 a 1 000 000", "Integer from 1 to 1,000,000"),
    },
    "theta_distribution": {
        "name": ("Distribución de la habilidad", "Ability distribution"), "symbol": "",
        "help": ("Distribución de la que se muestrean las habilidades verdaderas de los examinados simulados.",
                 "Distribution from which the true abilities of the simulated examinees are sampled."),
        "range": ("Normal o uniforme", "Normal or uniform"),
    },
    "theta_mean": {
        "name": ("Media de la habilidad", "Mean ability"), "symbol": "μθ",
        "help": ("Media de la distribución normal de la habilidad verdadera.", "Mean of the normal distribution of true ability."),
        "range": ("−4 a 4 logits", "−4 to 4 logits"),
    },
    "theta_sd": {
        "name": ("Desviación estándar de la habilidad", "Ability standard deviation"), "symbol": "σθ",
        "help": ("Dispersión de la distribución normal de la habilidad verdadera.", "Spread of the normal distribution of true ability."),
        "range": ("> 0 (habitual: 1)", "> 0 (typical: 1)"),
    },
    "theta_min": {
        "name": ("Límite inferior de la habilidad", "Ability lower bound"), "symbol": ("θmín", "θmin"),
        "help": ("Límite inferior de la distribución uniforme de la habilidad verdadera.", "Lower bound of the uniform distribution of true ability."),
        "range": ("Menor que el límite superior", "Less than the upper bound"),
    },
    "theta_max": {
        "name": ("Límite superior de la habilidad", "Ability upper bound"), "symbol": ("θmáx", "θmax"),
        "help": ("Límite superior de la distribución uniforme de la habilidad verdadera.", "Upper bound of the uniform distribution of true ability."),
        "range": ("Mayor que el límite inferior", "Greater than the lower bound"),
    },
    "seed": {
        "name": ("Semilla aleatoria", "Random seed"), "symbol": "",
        "help": ("Valor utilizado para inicializar el generador pseudoaleatorio. Permite reproducir exactamente un experimento: la misma configuración con la misma semilla produce los mismos resultados.",
                 "Value used to initialize the pseudo-random generator. It allows an experiment to be reproduced exactly: the same configuration with the same seed produces the same results."),
        "range": ("Entero de 0 a 2 147 483 647", "Integer from 0 to 2,147,483,647"),
    },
    "prior_mean": {
        "name": ("Media de la distribución previa", "Prior mean"), "symbol": "μ₀",
        "help": ("Media de la distribución previa normal de θ usada por los estimadores MAP y EAP.",
                 "Mean of the normal prior distribution of θ used by the MAP and EAP estimators."),
        "range": ("−4 a 4 logits (habitual: 0)", "−4 to 4 logits (typical: 0)"),
    },
    "prior_sd": {
        "name": ("Desviación estándar de la previa", "Prior standard deviation"), "symbol": "σ₀",
        "help": ("Dispersión de la previa normal de θ en MAP y EAP. Valores pequeños acercan más las estimaciones a la media previa.",
                 "Spread of the normal prior of θ in MAP and EAP. Small values pull estimates more strongly towards the prior mean."),
        "range": ("> 0 (habitual: 1)", "> 0 (typical: 1)"),
    },
    "randomesque_bin": {
        "name": ("Tamaño del grupo Randomesque", "Randomesque group size"), "symbol": "k",
        "help": ("Número de ítems más informativos entre los que Randomesque elige al azar. k = 1 equivale a máxima información.",
                 "Number of most informative items among which Randomesque picks at random. k = 1 is equivalent to maximum information."),
        "range": ("Entero ≥ 1 (habitual: 3 a 10)", "Integer ≥ 1 (typical: 3 to 10)"),
    },
    "sh_r_max": {
        "name": ("Exposición máxima objetivo (Sympson-Hetter)", "Target maximum exposure (Sympson-Hetter)"), "symbol": "r",
        "help": ("Tasa máxima de exposición que el procedimiento de Sympson-Hetter intenta no superar para ningún ítem.",
                 "Maximum exposure rate that the Sympson-Hetter procedure tries not to exceed for any item."),
        "range": ("0 < r ≤ 1 (habitual: 0.2 a 0.3)", "0 < r ≤ 1 (typical: 0.2 to 0.3)"),
    },
    "sh_iterations": {
        "name": ("Iteraciones de calibración (Sympson-Hetter)", "Calibration iterations (Sympson-Hetter)"), "symbol": "",
        "help": ("Número de simulaciones previas usadas para ajustar los parámetros K de control de exposición.",
                 "Number of preliminary simulations used to adjust the exposure-control K parameters."),
        "range": ("Entero ≥ 1 (habitual: 5 a 15)", "Integer ≥ 1 (typical: 5 to 15)"),
    },
    "sh_calibration_examinees": {
        "name": ("Examinados por iteración de calibración", "Examinees per calibration iteration"), "symbol": "",
        "help": ("Número de examinados simulados en cada iteración de calibración de Sympson-Hetter.",
                 "Number of simulated examinees in each Sympson-Hetter calibration iteration."),
        "range": ("Entero ≥ 1 (habitual: 500 a 2000)", "Integer ≥ 1 (typical: 500 to 2000)"),
    },
    "initial_theta": {
        "name": ("Habilidad inicial", "Initial ability"), "symbol": "θ₀",
        "help": ("Estimación de habilidad usada para seleccionar el primer ítem, antes de observar respuestas.",
                 "Ability estimate used to select the first item, before any response is observed."),
        "range": ("−4 a 4 logits (habitual: 0)", "−4 to 4 logits (typical: 0)"),
    },
    "theta_true": {
        "name": ("Habilidad verdadera del examinado", "True ability of the examinee"), "symbol": "θ*",
        "help": ("Habilidad real del examinado simulado. Las respuestas se generan con probabilidad P(θ*) según el modelo IRT.",
                 "Actual ability of the simulated examinee. Responses are simulated with probability P(θ*) under the IRT model."),
        "range": ("−4 a 4 logits", "−4 to 4 logits"),
    },
    "test_mode": {
        "name": ("Tipo de prueba", "Test type"), "symbol": "",
        "help": ("Adaptativa: cada ítem se elige según las respuestas previas. Longitud fija: se administran ítems aleatorios del banco sin adaptación (referencia de comparación).",
                 "Adaptive: each item is chosen from previous responses. Fixed length: random bank items are administered without adaptation (comparison reference)."),
        "range": ("CAT o longitud fija", "CAT or fixed length"),
    },
    "content_balancing": {
        "name": ("Balanceo de contenido", "Content balancing"), "symbol": "",
        "help": ("Si se activa, en cada paso se prioriza la categoría de contenido cuya proporción administrada está más por debajo de su objetivo (proporciones iguales entre las categorías del banco).",
                 "If enabled, at each step the content category whose administered proportion is furthest below its target is prioritized (equal proportions across the bank categories)."),
        "range": ("Activado o desactivado", "On or off"),
    },
    "bank_size": {
        "name": ("Número de ítems del banco", "Number of items in the bank"), "symbol": "",
        "help": ("Cantidad de ítems sintéticos que se generarán.", "Number of synthetic items to generate."),
        "range": ("Entero de 1 a 20 000", "Integer from 1 to 20,000"),
    },
    "bank_model": {
        "name": ("Modelo de generación", "Generating model"), "symbol": "",
        "help": ("Modelo IRT con el que se generan los parámetros: 1PL (a = 1, c = 0), 2PL (a lognormal, c = 0) o 3PL (a lognormal, c beta). b sigue una normal estándar.",
                 "IRT model used to generate the parameters: 1PL (a = 1, c = 0), 2PL (lognormal a, c = 0) or 3PL (lognormal a, beta c). b follows a standard normal."),
        "range": ("1PL, 2PL o 3PL", "1PL, 2PL or 3PL"),
    },
    "bank_seed": {
        "name": ("Semilla del banco", "Bank seed"), "symbol": "",
        "help": ("Semilla con la que se generan los parámetros del banco sintético. La misma semilla produce el mismo banco.",
                 "Seed used to generate the synthetic bank parameters. The same seed produces the same bank."),
        "range": ("Entero de 0 a 2 147 483 647", "Integer from 0 to 2,147,483,647"),
    },
    "exp_examinees": {
        "name": ("Examinados por condición", "Examinees per condition"), "symbol": "N",
        "help": ("Número de examinados simulados en cada condición del experimento. El tiempo total crece con N y con el número de condiciones.",
                 "Number of simulated examinees in each experimental condition. Total time grows with N and with the number of conditions."),
        "range": ("Entero de 10 a 100 000", "Integer from 10 to 100,000"),
    },
}
