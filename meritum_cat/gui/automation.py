"""
Autoprueba de la interfaz real.

:func:`run_self_test` recorre la GUI de extremo a extremo (pestañas, idiomas,
bancos, modelos, estimadores, selectores, CAT, Monte Carlo, detención,
reproducción, experimentos, importación/exportación y ayuda) accionando los
mismos botones que usa una persona, y genera una matriz de verificación
(PASS/FAIL) en JSON y Markdown.

Los cuadros de diálogo modales se responden automáticamente y su texto queda
registrado, para que la ejecución no se bloquee.
"""
from __future__ import annotations

import csv
import json
import re
import time
import traceback
from pathlib import Path
from typing import Any, Callable

import numpy as np
from PySide6.QtCore import QCoreApplication, QEvent, QEventLoop, Qt
from PySide6.QtWidgets import (
    QAbstractButton, QComboBox, QGroupBox, QLabel, QMessageBox, QTabWidget, QTableView, QTableWidget,
    QWidget, QMenu,
)

from meritum_cat import __version__
from meritum_cat.i18n import get_translator
from meritum_cat.i18n.strings import PARAM_HELP, STRINGS
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.utils.paths import resource_path, cache_dir

log = get_logger("automation")


# ----------------------------------------------------------------------------- utilidades
def pump(seconds: float = 0.2) -> None:
    """
    Procesa eventos durante ``seconds``. También ejecuta las eliminaciones diferidas
    (deleteLater), que processEvents no ejecuta por sí solo; así el estado de la
    interfaz coincide con el de un uso real, en el que el control vuelve al bucle principal.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        QCoreApplication.processEvents(QEventLoop.AllEvents, 30)
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        time.sleep(0.005)


class DialogRecorder:
    """Sustituye QMessageBox.exec: registra el texto y responde automáticamente."""

    def __init__(self) -> None:
        self.messages: list[str] = []
        self.answer_yes = True
        self._original = QMessageBox.exec

    def install(self) -> None:
        recorder = self

        def fake_exec(box: QMessageBox) -> int:
            recorder.handle(box)
            return int(QMessageBox.Yes if recorder.answer_yes else QMessageBox.No)

        QMessageBox.exec = fake_exec  # type: ignore[method-assign]

    def handle(self, box: QMessageBox) -> None:
        """Registra el texto del cuadro de diálogo."""
        self.messages.append(re.sub("<[^>]+>", " ", box.text()))

    def uninstall(self) -> None:
        QMessageBox.exec = self._original  # type: ignore[method-assign]

    def last(self) -> str:
        return self.messages[-1] if self.messages else ""


class Report:
    """Matriz de QA: pantalla, control, acción, esperado, observado, estado."""

    def __init__(self, outdir: Path) -> None:
        self.outdir = outdir
        self.rows: list[dict[str, str]] = []

    def check(self, screen: str, control: str, action: str, expected: str,
              fn: Callable[[], tuple[bool, str]]) -> bool:
        try:
            ok, observed = fn()
        except Exception as exc:  # noqa: BLE001 - toda excepción es un FAIL documentado
            ok, observed = False, f"Excepción: {exc!r}"
            log.error("Fallo en verificación %s/%s:\n%s", screen, control, traceback.format_exc())
        self.rows.append({"screen": screen, "control": control, "action": action,
                          "expected": expected, "observed": observed,
                          "status": "PASS" if ok else "FAIL"})
        log.info("[%s] %s · %s → %s", "PASS" if ok else "FAIL", screen, control, observed)
        return ok

    @property
    def all_passed(self) -> bool:
        return all(r["status"] == "PASS" for r in self.rows)

    def write(self, name: str = "self_test_report") -> None:
        n_pass = sum(r["status"] == "PASS" for r in self.rows)
        payload = {"meritum_cat_version": __version__,
                   "created": time.strftime("%Y-%m-%d %H:%M:%S"),
                   "total": len(self.rows), "passed": n_pass, "failed": len(self.rows) - n_pass,
                   "checks": self.rows}
        (self.outdir / f"{name}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                                  encoding="utf-8")
        lines = [f"# Matriz de QA de interfaz — Meritum_CAT {__version__}", "",
                 f"Total: {len(self.rows)} · PASS: {n_pass} · FAIL: {len(self.rows) - n_pass}", "",
                 "| # | Pantalla | Control | Acción | Resultado esperado | Resultado observado | Estado |",
                 "|---|---|---|---|---|---|---|"]
        for i, r in enumerate(self.rows, 1):
            cells = [str(i)] + [r[k].replace("|", "/").replace("\n", " ") for k in
                                ("screen", "control", "action", "expected", "observed", "status")]
            lines.append("| " + " | ".join(cells) + " |")
        (self.outdir / f"{name}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _strip(text: str) -> str:
    return re.sub("<[^>]+>", "", text or "").strip()


def collect_texts(window: QWidget) -> list[str]:
    """Todos los textos visibles o potencialmente visibles de la interfaz."""
    texts: list[str] = []
    for w in window.findChildren(QWidget):
        if isinstance(w, QLabel):
            texts.append(_strip(w.text()))
        elif isinstance(w, QAbstractButton):
            texts.append(w.text())
        elif isinstance(w, QGroupBox):
            texts.append(w.title())
        elif isinstance(w, QTabWidget):
            texts.extend(w.tabText(i) for i in range(w.count()))
        elif isinstance(w, QComboBox):
            texts.extend(w.itemText(i) for i in range(w.count()))
        elif isinstance(w, QTableWidget):
            for c in range(w.columnCount()):
                it = w.horizontalHeaderItem(c)
                if it is not None:
                    texts.append(it.text())
        elif isinstance(w, QTableView):
            model = w.model()
            if model is not None:
                texts.extend(str(model.headerData(c, Qt.Horizontal)) for c in range(model.columnCount()))
        elif isinstance(w, QMenu):
            texts.append(w.title())
            texts.extend(a.text() for a in w.actions())
        tip = _strip(w.toolTip())
        if tip:
            texts.append(tip)
    return [t for t in texts if t and t.strip()]


def language_problems(window: QWidget, language: str) -> list[str]:
    """
    Detecta claves sin traducir y textos del otro idioma: un texto de la GUI que
    coincide exactamente con la versión del idioma contrario (y que difiere entre
    idiomas) indica mezcla de idiomas.
    """
    other = 1 if language == "es" else 0
    foreign = {v[other] for v in STRINGS.values() if v[0] != v[1] and len(v[other]) > 3}
    for p in PARAM_HELP.values():
        for field in ("name", "help"):
            if p[field][0] != p[field][1]:
                foreign.add(p[field][other])
    keys = set(STRINGS)
    # Plantillas con parámetros ({n}, {sec:.1f}...) del otro idioma, como expresiones regulares.
    templates = []
    for es_en in STRINGS.values():
        text = es_en[other]
        if es_en[0] != es_en[1] and "{" in text:
            parts = re.split(r"\{[^{}]*\}", text)
            if sum(len(p.strip()) for p in parts) >= 8:
                templates.append(re.compile("^" + ".+?".join(re.escape(p) for p in parts) + "$", re.S))
    problems = []
    for t in collect_texts(window):
        if t in keys:
            problems.append(f"clave sin traducir: {t}")
        elif t in foreign or any(rx.match(t) for rx in templates):
            problems.append(f"texto del otro idioma: {t[:60]}")
        elif "Traceback" in t:
            problems.append("traza técnica visible")
    return sorted(set(problems))


def wait_runner(runner, timeout_s: float = 600.0) -> bool:
    return runner.wait(int(timeout_s * 1000))


def set_combo(combo: QComboBox, data: Any) -> None:
    idx = combo.findData(data)
    if idx < 0:
        raise ValueError(f"Opción no encontrada: {data}")
    combo.setCurrentIndex(idx)


# ----------------------------------------------------------------------------- escenarios
def configure_mc(mc, model="2PL", estimator="EAP", selector="Maximum Information", n=1000,
                 seed=12345, max_items=20, se=None, compare=False, mode="cat") -> None:
    mc.reset_values()
    set_combo(mc.algo.model, model)
    set_combo(mc.algo.estimator, estimator)
    set_combo(mc.algo.selector, selector)
    mc.n_examinees.setValue(n)
    mc.seed.setValue(seed)
    mc.stopping.max_items.set_value(max_items)
    mc.stopping.se_threshold.set_value(se)
    set_combo(mc.test_mode, mode)
    mc.compare_fixed.setChecked(compare)


def run_mc(mc, timeout_s: float = 600.0) -> bool:
    started = mc.run(skip_confirm=True)
    if not started:
        return False
    wait_runner(mc.runner, timeout_s)
    pump(0.3)
    return mc.result is not None


def metrics_summary(result) -> dict[str, float]:
    keys = ["bias", "mae", "mse", "rmse", "pearson", "spearman", "coverage_95", "mean_se",
            "mean_test_length", "max_exposure_rate", "mean_exposure_rate", "unused_items",
            "elapsed_seconds"]
    return {k: round(float(result.metrics[k]), 4) for k in keys if k in result.metrics}


# ----------------------------------------------------------------------------- self-test
def run_self_test(window, outdir: str) -> bool:
    out = Path(outdir)
    files_dir = out / "files"
    for d in (out, files_dir):
        d.mkdir(parents=True, exist_ok=True)
    rec = DialogRecorder()
    rec.install()
    rep = Report(out)
    t = get_translator()
    window.resize(1600, 950)
    pump(1.0)
    W = window
    try:
        _self_test_body(W, rep, rec, t, files_dir)
    finally:
        rec.uninstall()
        rep.write()
    log.info("Autoprueba finalizada: %d verificaciones, todas PASS: %s", len(rep.rows), rep.all_passed)
    return rep.all_passed


def _self_test_body(W, rep: Report, rec: DialogRecorder, t, files: Path) -> None:
    from meritum_cat.gui import dialogs
    from meritum_cat.persistence import bank_fingerprint

    # ---------------------------------------------------------------- arranque
    rep.check("Ventana principal", "Inicio de la aplicación", "Abrir Meritum_CAT",
              "Ventana visible con versión 1.0.0",
              lambda: (W.isVisible() and __version__ in W.windowTitle(), W.windowTitle()[:40]))
    rep.check("Ventana principal", "Banco inicial", "Arranque",
              "Banco sintético de 500 ítems cargado",
              lambda: (W.state.bank is not None and W.state.bank.n_items == 500,
                       f"{W.state.bank.name if W.state.bank else None}"))

    # ---------------------------------------------------------------- idioma
    W.set_language("es")
    pump(0.5)
    for i in range(W.tabs.count()):
        W.tabs.setCurrentIndex(i)
        pump(0.4)
    rep.check("Ventana principal", "Idioma ES", "Seleccionar Español",
              "Sin claves sin traducir ni textos en inglés",
              lambda: (lambda p: (not p, "; ".join(p[:5]) or "0 problemas"))(language_problems(W, "es")))
    W.btn_en.click()
    pump(0.5)
    rep.check("Ventana principal", "Botón EN", "Clic en EN",
              "Interfaz en inglés (pestaña 'Item bank')",
              lambda: (W.tabs.tabText(1) == "Item bank" and t.language == "en", W.tabs.tabText(1)))
    for i in range(W.tabs.count()):
        W.tabs.setCurrentIndex(i)
        pump(0.4)
    rep.check("Ventana principal", "Idioma EN", "Recorrer todas las pestañas",
              "Sin claves sin traducir ni textos en español",
              lambda: (lambda p: (not p, "; ".join(p[:5]) or "0 problemas"))(language_problems(W, "en")))
    W.act_es.trigger()
    pump(0.5)
    rep.check("Menú Idioma", "Español", "Idioma → Español",
              "Interfaz en español (pestaña 'Banco de ítems')",
              lambda: (W.tabs.tabText(1) == "Banco de ítems", W.tabs.tabText(1)))
    rep.check("Menús", "Archivo / Idioma / Ayuda", "Revisar menús",
              "Menús traducidos y con acciones",
              lambda: (W.menu_file.title() == "&Archivo" and len(W.menu_help.actions()) >= 4
                       and len(W.menu_file.actions()) >= 6,
                       f"{W.menu_file.title()}, {W.menu_lang.title()}, {W.menu_help.title()}"))

    # ---------------------------------------------------------------- banco
    bt = W.bank_tab
    W.tabs.setCurrentIndex(W.TAB_BANK)
    for n, model in ((100, "1PL"), (500, "2PL"), (1000, "3PL")):
        def gen(n=n, model=model):
            bt.gen_n.setValue(n)
            set_combo(bt.gen_model, model)
            bt.gen_seed.setValue(2026)
            bt.btn_generate.click()
            pump(0.3)
            b = W.state.bank
            ok = b.n_items == n and (model != "1PL" or np.allclose(b.a, 1.0)) and \
                (model == "3PL" or np.allclose(b.c, 0.0))
            return ok, f"{b.name}: {b.n_items} ítems"
        rep.check("Banco de ítems", "Generar banco sintético", f"n={n}, modelo {model}, semilla 2026",
                  f"Banco de {n} ítems {model}", gen)
    pump(0.4)

    def load_examples():
        names = []
        for i in range(bt.examples.count()):
            bt.examples.setCurrentIndex(i)
            bt.btn_example.click()
            pump(0.2)
            names.append(f"{W.state.bank.n_items}")
        return len(names) == bt.examples.count() >= 5, "ítems: " + ", ".join(names)
    rep.check("Banco de ítems", "Cargar ejemplo", "Cargar los bancos incluidos",
              "Los 5 bancos sintéticos se cargan", load_examples)

    def validate_clean():
        bt.btn_validate.click()
        pump(0.2)
        errs = sum(1 for i in bt.issues if i.severity == "error")
        return errs == 0, f"{errs} errores, {len(bt.issues)} hallazgos"
    rep.check("Banco de ítems", "Validar banco", "Clic en Validar banco", "0 errores", validate_clean)

    def roundtrip(kind):
        def fn():
            before = bank_fingerprint(W.state.bank)
            path = files / f"bank_export.{kind}"
            ok_exp = bt.export_to(str(path), kind, silent=True)
            ok_imp = bt.import_path(str(path), silent=True)
            after = bank_fingerprint(W.state.bank)
            return ok_exp and ok_imp and before == after, f"huella idéntica: {before == after}"
        return fn
    rep.check("Banco de ítems", "Exportar/Importar CSV", "Exportar y reimportar",
              "Banco idéntico (misma huella SHA-256)", roundtrip("csv"))
    rep.check("Banco de ítems", "Exportar/Importar JSON", "Exportar y reimportar",
              "Banco idéntico (misma huella SHA-256)", roundtrip("json"))

    def import_missing_column():
        path = files / "bank_missing_b.csv"
        path.write_text("item_id,a,c\nX1,1.0,0.1\n", encoding="utf-8")
        n_before = len(rec.messages)
        ok = bt.import_path(str(path), silent=True)
        msg = rec.last() if len(rec.messages) > n_before else ""
        return (not ok) and ("falta la columna" in msg), msg[:90]
    rep.check("Banco de ítems", "Importar CSV", "Importar CSV sin columna de dificultad",
              "Mensaje amigable, sin traza técnica", import_missing_column)

    def import_invalid_params():
        path = files / "bank_invalid.csv"
        path.write_text("item_id,a,b,c,category\nI1,1.2,0.1,0.2,D1\nI2,-0.5,0.3,0.1,D1\n"
                        "I3,1.0,0.0,1.2,D2\nI1,0.8,5.5,0.0,\n", encoding="utf-8")
        bt.import_path(str(path), silent=True)
        pump(0.2)
        codes = sorted({i.code for i in bt.issues})
        expected = {"a_nonpositive", "c_ge_one", "duplicate_id", "b_extreme", "missing_category"}
        return expected.issubset(codes), ", ".join(codes)
    rep.check("Banco de ítems", "Validación automática", "Importar banco con parámetros inválidos",
              "Detecta a≤0, c≥1, ID duplicado, b extremo, categoría faltante", import_invalid_params)
    pump(0.4)

    def mc_blocked_invalid():
        W.tabs.setCurrentIndex(W.TAB_MC)
        n_before = len(rec.messages)
        started = W.mc_tab.run(skip_confirm=True)
        msg = rec.last() if len(rec.messages) > n_before else ""
        return (not started) and ("errores de validación" in msg), msg[:80]
    rep.check("Simulación Monte Carlo", "Ejecutar", "Ejecutar con banco inválido",
              "La simulación se bloquea con mensaje claro", mc_blocked_invalid)

    # edición de ítems (el diálogo se completa automáticamente)
    W.tabs.setCurrentIndex(W.TAB_BANK)
    bt.examples.setCurrentIndex(bt.examples.findData("synthetic_bank_100_2PL.csv"))
    bt.btn_example.click()
    pump(0.2)
    original_exec = dialogs.ItemDialog.exec

    def auto_exec(dlg, fill: dict):
        for k, v in fill.items():
            w = getattr(dlg, k)
            if hasattr(w, "setValue"):
                w.setValue(v)
            else:
                w.setText(v)
        dlg.accept()
        return 1 if dlg.result_item is not None else 0

    try:
        def add_item():
            n0 = W.state.bank.n_total
            dialogs.ItemDialog.exec = lambda dlg: auto_exec(dlg, {"item_id": "NEW-1", "a": 1.3, "b": 0.4,
                                                                   "c": 0.15, "category": "D1"})
            bt.btn_add.click()
            pump(0.2)
            last = W.state.bank.items[-1]
            return W.state.bank.n_total == n0 + 1 and last.item_id == "NEW-1" and abs(last.c - 0.15) < 1e-9, \
                f"{n0} → {W.state.bank.n_total}"
        rep.check("Banco de ítems", "Agregar ítem", "Agregar ítem NEW-1", "El banco crece en 1", add_item)

        def edit_item():
            bt.table.clearSelection()
            bt.table.selectRow(0)
            row = bt._selected_rows()[0]
            iid = W.state.bank.items[row].item_id
            dialogs.ItemDialog.exec = lambda dlg: auto_exec(dlg, {"b": -1.25})
            bt.btn_edit.click()
            pump(0.2)
            item = W.state.bank.items[row]
            return item.item_id == iid and abs(item.b + 1.25) < 1e-9, f"{iid}: b = {item.b}"
        rep.check("Banco de ítems", "Editar ítem", "Cambiar b = −1.25", "Parámetro actualizado", edit_item)

        def duplicate_item():
            n0 = W.state.bank.n_total
            bt.table.clearSelection()
            bt.table.selectRow(0)
            bt.btn_dup.click()
            pump(0.2)
            return W.state.bank.n_total == n0 + 1 and W.state.bank.items[-1].item_id.endswith("_copy"), \
                W.state.bank.items[-1].item_id
        rep.check("Banco de ítems", "Duplicar", "Duplicar ítem seleccionado", "Copia con ID nuevo", duplicate_item)

        def dup_id_rejected():
            n_before = len(rec.messages)
            existing = W.state.bank.items[1].item_id
            dialogs.ItemDialog.exec = lambda dlg: (auto_exec(dlg, {"item_id": existing}), 0)[1]
            bt.btn_add.click()
            pump(0.2)
            msg = rec.last() if len(rec.messages) > n_before else ""
            return existing in msg, msg[:80]
        rep.check("Banco de ítems", "Agregar ítem", "Agregar ítem con ID existente",
                  "Advertencia de ID duplicado", dup_id_rejected)
    finally:
        dialogs.ItemDialog.exec = original_exec

    def delete_item():
        n0 = W.state.bank.n_total
        bt.table.clearSelection()
        bt.table.selectRow(0)
        rec.answer_yes = True
        bt.btn_delete.click()
        pump(0.2)
        return W.state.bank.n_total == n0 - 1, f"{n0} → {W.state.bank.n_total}"
    rep.check("Banco de ítems", "Eliminar", "Eliminar con confirmación", "El banco decrece en 1", delete_item)

    bt.examples.setCurrentIndex(bt.examples.findData("synthetic_bank_500_2PL.csv"))
    bt.btn_example.click()
    pump(0.3)

    # ---------------------------------------------------------------- IRT
    it = W.irt_tab
    W.tabs.setCurrentIndex(W.TAB_IRT)
    for model in ("1PL", "2PL", "3PL"):
        def irt_model(model=model):
            set_combo(it.model, model)
            pump(0.3)
            n_axes = len(it.fig_item.figure.axes)
            return n_axes == 2 and len(it.fig_test.figure.axes) == 2, f"{n_axes} ejes ICC/IIC"
        rep.check("Modelos IRT", f"Modelo {model}", f"Seleccionar {model}", "Figuras ICC/IIC y TIF/EE dibujadas",
                  irt_model)

    def irt_analytic():
        set_combo(it.model, "2PL")
        it.a.setValue(2.0)
        it.b.setValue(0.5)
        pump(0.2)
        text = it.lbl_max.text()
        nums = [float(x) for x in re.findall(r"-?\d+\.\d+", text)]
        return abs(nums[0] - 1.0) < 1e-3 and abs(nums[1] - 0.5) < 0.03, text
    rep.check("Modelos IRT", "Información máxima", "2PL con a=2, b=0.5",
              "I_max = a²/4 = 1.000 en θ = b = 0.5 (solución analítica)", irt_analytic)

    def irt_curves():
        it.btn_add.click()
        it.b.setValue(-1.0)
        it.btn_add.click()
        pump(0.2)
        n_lines = len(it.fig_item.figure.axes[0].lines)
        it.btn_clear.click()
        pump(0.2)
        return n_lines == 3 and len(it.fig_item.figure.axes[0].lines) == 1, f"{n_lines} curvas → 1"
    rep.check("Modelos IRT", "Añadir/Limpiar comparación", "Fijar 2 curvas y limpiar",
              "3 curvas y luego 1", irt_curves)
    pump(0.4)

    # ---------------------------------------------------------------- CAT
    ct = W.cat_tab
    W.tabs.setCurrentIndex(W.TAB_CAT)
    for est in ("MLE", "MAP", "EAP"):
        def cat_run(est=est):
            set_combo(ct.mode, "sim")
            set_combo(ct.algo.model, "2PL")
            set_combo(ct.algo.estimator, est)
            ct.stopping.max_items.set_value(20)
            ct.stopping.se_threshold.set_value(None)
            ct.btn_reset.click() if ct.session else None
            ct.btn_start.click()
            ct.btn_next.click()
            ct.btn_run.click()
            pump(0.3)
            s = ct.session
            ok = s is not None and s.finished and len(s.administered) == 20 and s.stop_reason == "max_items" \
                and len(ct.figure.figure.axes) == 4 and ct.table.rowCount() == 20
            return ok, f"θ̂={s.theta:.3f}, EE={s.se:.3f}, ítems={len(s.administered)}"
        rep.check("Test adaptativo (CAT)", f"Estimador {est}", "Iniciar, siguiente, ejecutar hasta terminar",
                  "20 ítems, motivo: máximo de ítems, 4 gráficas", cat_run)
    pump(0.4)

    def cat_se_rule():
        ct.btn_reset.click()
        set_combo(ct.algo.estimator, "EAP")
        ct.stopping.max_items.set_value(None)
        ct.stopping.se_threshold.set_value(0.3)
        ct.btn_start.click()
        ct.btn_run.click()
        pump(0.2)
        s = ct.session
        ok = s.finished and s.stop_reason in ("se_threshold", "bank_exhausted") and s.se <= 0.3 + 1e-9
        ct.stopping.max_items.set_value(20)
        ct.stopping.se_threshold.set_value(None)
        return ok, f"{len(s.administered)} ítems, EE={s.se:.3f}, motivo={s.stop_reason}"
    rep.check("Test adaptativo (CAT)", "Umbral de error estándar", "EE* = 0.30 sin máximo de ítems",
              "Termina con EE ≤ 0.30", cat_se_rule)

    def cat_manual():
        ct.btn_reset.click()
        set_combo(ct.mode, "manual")
        ct.btn_start.click()
        for r in (1, 1, 0):
            (ct.btn_correct if r else ct.btn_incorrect).click()
        pump(0.2)
        s = ct.session
        ok = len(s.administered) == 3 and s.responses == [1, 1, 0] and s.pending is not None
        ct.btn_reset.click()
        set_combo(ct.mode, "sim")
        return ok, f"respuestas={s.responses}, θ̂={s.theta:.3f}"
    rep.check("Test adaptativo (CAT)", "Correcta / Incorrecta", "Modo manual: C, C, I",
              "3 ítems con respuestas registradas", cat_manual)

    def cat_no_stop_rule():
        n_before = len(rec.messages)
        ct.stopping.max_items.set_value(None)
        ct.btn_start.click()
        msg = rec.last() if len(rec.messages) > n_before else ""
        ct.stopping.max_items.set_value(20)
        return ct.session is None and "terminación" in msg, msg[:80]
    rep.check("Test adaptativo (CAT)", "Iniciar sesión", "Sin criterios de terminación",
              "Advertencia amigable, no inicia", cat_no_stop_rule)

    # ---------------------------------------------------------------- Monte Carlo
    mc = W.mc_tab
    W.tabs.setCurrentIndex(W.TAB_MC)
    configure_mc(mc, "2PL", "EAP", "Maximum Information", n=5000, seed=12345, compare=True)

    def mc_main():
        ok = run_mc(mc)
        r, f = mc.result, mc.fixed_result
        drawn = sum(1 for p in mc.figs.values() if p.figure.axes)
        ok = ok and f is not None and r.metrics["rmse"] < f.metrics["rmse"] and drawn == 7 \
            and r.theta_true.size == 5000 and np.isfinite(r.metrics["bias"])
        return ok, (f"RMSE CAT={r.metrics['rmse']:.4f} vs fijo={f.metrics['rmse']:.4f}; "
                    f"sesgo={r.metrics['bias']:.4f}; exp. máx.={r.exposure.max_rate:.3f}; figuras={drawn}")
    rep.check("Simulación Monte Carlo", "Ejecutar", "2PL + EAP + Máx. info., N=5000, semilla 12345, comparar fijo",
              "Resultados completos; RMSE CAT < RMSE fijo; 7 figuras", mc_main)
    for key in ("recovery", "compare", "exposure"):
        mc.fig_tabs.setCurrentWidget(mc.figs[key])
        pump(0.4)

    def language_after_results():
        found = []
        for lang in ("en", "es"):
            W.set_language(lang)
            pump(0.4)
            found += [f"{lang}: {p}" for p in language_problems(W, lang)]
            if lang == "en":
                pump(0.4)
        return not found, "; ".join(found[:4]) or "0 problemas en ES y EN con resultados en pantalla"
    rep.check("Simulación Monte Carlo", "Cambio de idioma con resultados", "ES → EN → ES tras simular",
              "Todos los textos (incluido el estado y la tabla de métricas) cambian de idioma",
              language_after_results)
    mc.fig_tabs.setCurrentWidget(mc.figs["recovery"])
    main_metrics = dict(mc.result.metrics)

    def mc_export():
        p = files / "mc_results.csv"
        ok = mc.export_results_to(str(p), silent=True)
        with open(p, encoding="utf-8") as fh:
            rows = list(csv.reader(fh))
        nfig = mc.export_figures_to(str(files), silent=True)
        return ok and len(rows) == 5001 and nfig == 7, f"{len(rows) - 1} filas, {nfig} PNG"
    rep.check("Simulación Monte Carlo", "Exportar resultados / figuras", "Exportar CSV y PNG",
              "CSV con 5000 examinados y 7 figuras", mc_export)

    cfg_path = files / "experiment_config.json"

    def mc_save():
        ok = mc.save_config_to(str(cfg_path), silent=True)
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        keys_ok = all(k in data for k in ("meritum_cat_version", "created_utc", "config", "bank", "results"))
        return ok and keys_ok and data["config"]["seed"] == 12345, \
            f"versión {data['meritum_cat_version']}, semilla {data['config']['seed']}, banco {data['bank']['n_items_active']}"
    rep.check("Simulación Monte Carlo", "Guardar configuración", "Guardar experiment_config.json",
              "JSON con versión, fecha, configuración, banco y resultados", mc_save)

    def mc_reproduce():
        mc.btn_reset.click()
        mc.seed.setValue(999)
        set_combo(mc.algo.estimator, "MLE")
        W.bank_tab.examples.setCurrentIndex(W.bank_tab.examples.findData("synthetic_bank_100_2PL.csv"))
        W.bank_tab.btn_example.click()
        ok_load = mc.load_config_from(str(cfg_path), silent=True)
        restored = mc.seed.value() == 12345 and mc.algo.estimator.currentData() == "EAP" \
            and W.state.bank.n_items == 500
        ok_run = run_mc(mc)
        same = all(abs(mc.result.metrics[k] - main_metrics[k]) < 1e-12
                   for k in main_metrics if k != "elapsed_seconds")
        return ok_load and restored and ok_run and same and mc.repro_message == "ok", \
            f"configuración restaurada={restored}; métricas idénticas={same}; aviso={mc.repro_label.text()[:50]}"
    rep.check("Simulación Monte Carlo", "Cargar configuración + Ejecutar",
              "Restablecer, cambiar valores, cargar configuración y reproducir",
              "Mismos resultados exactos y aviso de reproducción verificada", mc_reproduce)
    pump(0.4)

    for model, est, sel in (("1PL", "EAP", "Maximum Information"), ("2PL", "MAP", "Maximum Information"),
                            ("3PL", "EAP", "Maximum Information"), ("2PL", "MLE", "Random"),
                            ("2PL", "EAP", "Randomesque"), ("2PL", "EAP", "Kullback-Leibler"),
                            ("2PL", "EAP", "Sympson-Hetter")):
        def combo_run(model=model, est=est, sel=sel):
            configure_mc(mc, model, est, sel, n=400, seed=7)
            mc.algo.sh_calibration_examinees.setValue(300)
            mc.algo.sh_iterations.setValue(4)
            ok = run_mc(mc)
            m = mc.result.metrics
            fine = ok and np.isfinite(m["rmse"]) and m["pearson"] > 0.6
            if sel == "Sympson-Hetter":
                fine = fine and mc.result.exposure.max_rate < 0.6 and len(mc.result.sh_history) == 4
            return fine, f"RMSE={m['rmse']:.3f}, r={m['pearson']:.3f}, exp. máx.={m['max_exposure_rate']:.2f}"
        rep.check("Simulación Monte Carlo", f"{model} + {est} + {sel}", "Ejecutar N=400",
                  "Métricas finitas y correlación > 0.6", combo_run)

    def mc_fixed_mode():
        configure_mc(mc, "2PL", "EAP", "Maximum Information", n=300, seed=3, mode="fixed")
        ok = run_mc(mc)
        return ok and set(mc.result.stop_reasons) == {"fixed_length"} and \
            int(mc.result.test_lengths[0]) == 20, f"motivos={set(mc.result.stop_reasons)}"
    rep.check("Simulación Monte Carlo", "Tipo de prueba: longitud fija", "Ejecutar test fijo",
              "Todos con longitud fija de 20", mc_fixed_mode)

    def mc_stop():
        configure_mc(mc, "2PL", "EAP", "Maximum Information", n=300000, seed=1)
        previous = mc.result
        started = mc.run(skip_confirm=True)
        pump(1.5)
        running_mid = mc.runner.running
        mc.btn_stop.click()
        stopped = wait_runner(mc.runner, 60)
        pump(0.3)
        return started and running_mid and stopped and mc.result is previous and \
            mc.status.text() == t("mc.status_cancelled"), mc.status.text()[:60]
    rep.check("Simulación Monte Carlo", "Detener", "Detener simulación de 300000 examinados",
              "Se detiene en segundos, sin resultados parciales, GUI sensible", mc_stop)

    def mc_gui_responsive():
        configure_mc(mc, "2PL", "EAP", "Maximum Information", n=3000, seed=5)
        mc.run(skip_confirm=True)
        t0 = time.monotonic()
        max_gap = 0.0
        last = time.monotonic()
        while mc.runner.running and time.monotonic() - t0 < 120:
            QCoreApplication.processEvents(QEventLoop.AllEvents, 20)
            now = time.monotonic()
            max_gap = max(max_gap, now - last)
            last = now
            time.sleep(0.01)
        wait_runner(mc.runner, 60)
        return max_gap < 0.5 and mc.progress.value() == mc.progress.maximum(), \
            f"máxima pausa del bucle de eventos: {max_gap * 1000:.0f} ms"
    rep.check("Simulación Monte Carlo", "Barra de progreso", "Simulación de 3000 examinados",
              "La GUI no se congela (pausas < 500 ms) y el progreso llega a 100 %", mc_gui_responsive)

    def mc_invalid_inputs():
        configure_mc(mc, n=100)
        n_before = len(rec.messages)
        mc.stopping.max_items.set_value(None)
        started = mc.run(skip_confirm=True)
        msg = rec.last() if len(rec.messages) > n_before else ""
        mc.stopping.max_items.set_value(20)
        return (not started) and "terminación" in msg, msg[:80]
    rep.check("Simulación Monte Carlo", "Validación de entradas", "Ejecutar sin criterio de terminación",
              "Mensaje amigable y no ejecuta", mc_invalid_inputs)

    def mc_spin_limits():
        mc.n_examinees.setValue(-5)
        neg = mc.n_examinees.value()
        mc.algo.prior_sd.setValue(-1.0)
        sd = mc.algo.prior_sd.value()
        mc.n_examinees.setValue(1000)
        mc.algo.prior_sd.setValue(1.0)
        return neg >= 1 and sd > 0, f"N mínimo={neg}, σ₀ mínimo={sd}"
    rep.check("Simulación Monte Carlo", "Campos numéricos", "Escribir N = −5 y σ₀ = −1",
              "Los campos no aceptan valores fuera de rango", mc_spin_limits)

    def mc_large_confirm():
        configure_mc(mc, n=30000)
        rec.answer_yes = False
        started = mc.run()
        rec.answer_yes = True
        return (not started) and not mc.runner.running, "cancelado por el usuario en la confirmación"
    rep.check("Simulación Monte Carlo", "Confirmación N grande", "N=30000, responder No",
              "No ejecuta", mc_large_confirm)
    configure_mc(mc)

    # ---------------------------------------------------------------- experimentos
    ex = W.exp_tab
    W.tabs.setCurrentIndex(W.TAB_EXP)
    from meritum_cat.experiments import EXPERIMENTS
    for key in EXPERIMENTS:
        def exp_run(key=key):
            ex.select(key)
            ex.n_examinees.setValue(150)
            ex.seed.setValue(2026)
            ex.use_bank.setChecked(False)
            ex.btn_run.click()
            wait_runner(ex.runner, 600)
            pump(0.3)
            r = ex.result
            ok = r is not None and r.key == key and ex.table.rowCount() == len(r.rows) > 0 \
                and len(ex.figure.figure.axes) >= 1
            if key == "seeds":
                ok = ok and r.summary_params.get("reproducible") is True
            return ok, f"{len(r.rows)} filas, {r.elapsed_seconds:.1f} s"
        rep.check("Experimentos científicos", t(f"exp.{key}.title"), "Ejecutar con N=150",
                  "Tabla, figura e interpretación", exp_run)
        if key in ("exposure", "robustness", "cat_vs_fixed"):
            pump(0.4)

    def exp_language():
        found = []
        for lang in ("en", "es"):
            W.set_language(lang)
            pump(0.4)
            found += [f"{lang}: {p}" for p in language_problems(W, lang)]
        return not found, "; ".join(found[:4]) or "0 problemas"
    rep.check("Experimentos científicos", "Cambio de idioma con resultados", "ES → EN → ES tras experimentos",
              "Tabla, interpretación y estado cambian de idioma", exp_language)

    def exp_export():
        p = files / "experiment.csv"
        ok = ex.export_csv_to(str(p), silent=True)
        return ok and p.stat().st_size > 50, f"{p.stat().st_size} bytes"
    rep.check("Experimentos científicos", "Exportar tabla CSV", "Exportar", "Archivo CSV escrito", exp_export)

    def exp_use_bank():
        ex.select("estimators")
        ex.use_bank.setChecked(True)
        ex.n_examinees.setValue(100)
        ex.btn_run.click()
        wait_runner(ex.runner, 300)
        ex.use_bank.setChecked(False)
        return ex.result.config.get("bank_name") == W.state.bank.name, str(ex.result.config.get("bank_name"))
    rep.check("Experimentos científicos", "Usar el banco actual", "Marcar y ejecutar Experimento 2",
              "El experimento usa el banco cargado", exp_use_bank)

    def exp_stop():
        ex.select("bank_size")
        ex.n_examinees.setValue(50000)
        previous = ex.result
        ex.btn_run.click()
        pump(1.2)
        ex.btn_stop.click()
        stopped = wait_runner(ex.runner, 120)
        return stopped and ex.result is previous and ex.status.text() == t("exp.status_cancelled"), \
            ex.status.text()[:60]
    rep.check("Experimentos científicos", "Detener", "Detener experimento en curso",
              "Se detiene sin resultados parciales", exp_stop)
    ex.n_examinees.setValue(1000)

    # ---------------------------------------------------------------- ayuda
    def help_button():
        W.tabs.setCurrentIndex(W.TAB_MC)
        from meritum_cat.gui.common import ParamLabel
        labels = [w for w in W.mc_tab.findChildren(ParamLabel) if w.key == "seed"]
        n_before = len(rec.messages)
        labels[0].help_button.click()
        msg = rec.last() if len(rec.messages) > n_before else ""
        return "Semilla aleatoria" in msg and "Rango válido" in msg, msg[:80]
    rep.check("Ayuda contextual", "Botón «?»", "Clic en «?» de Semilla aleatoria",
              "Descripción y rango válido", help_button)

    def tooltips_everywhere():
        from meritum_cat.gui.common import ParamLabel
        labels = W.findChildren(ParamLabel)
        missing = [w.key for w in labels if not w.label.toolTip()]
        return not missing and len(labels) > 40, f"{len(labels)} parámetros con ayuda; sin ayuda: {missing}"
    rep.check("Ayuda contextual", "Tooltips", "Revisar todos los parámetros",
              "Todos los parámetros tienen ayuda", tooltips_everywhere)

    for name, cls in (("Guía rápida", dialogs.QuickStartDialog), ("Glosario", dialogs.GlossaryDialog),
                      ("Acerca de", dialogs.AboutDialog)):
        def open_dialog(name=name, cls=cls):
            d = cls(W)
            d.show()
            pump(0.4)
            texts = " ".join(collect_texts(d))
            ok = d.isVisible()
            if name == "Acerca de":
                ok = ok and "1.0.0" in texts and "Computerized Adaptive Testing" in texts
            if name == "Glosario":
                table = d.findChildren(QTableWidget)[0]
                ok = ok and table.rowCount() == len(PARAM_HELP)
            title = d.windowTitle()
            d.close()
            d.deleteLater()
            return ok, title
        rep.check("Ayuda", name, f"Ayuda → {name}", "Diálogo abre, muestra contenido y cierra", open_dialog)

    # ---------------------------------------------------------------- registro
    def log_file():
        path = cache_dir() / "logs" / "meritum_cat.log"
        text = path.read_text(encoding="utf-8", errors="ignore")
        ok = "Simulación Monte Carlo iniciada" in text and "Banco importado" in text \
            and "Experimento iniciado" in text
        return ok, str(path)
    rep.check("Registro (logs)", "meritum_cat.log", "Revisar archivo de registro",
              "Registra inicio, importaciones, simulaciones y experimentos", log_file)

    def resources_packaged():
        p = resource_path("resources/datasets/datasets.json")
        icon = resource_path("resources/icons/meritum_cat.ico")
        return p.exists() and icon.exists(), str(p.parent)
    rep.check("Recursos", "Datasets e icono", "Resolver rutas de recursos",
              "Recursos disponibles (también dentro del ejecutable)", resources_packaged)

    W.set_language("es")
    W.tabs.setCurrentIndex(0)
    pump(0.3)
