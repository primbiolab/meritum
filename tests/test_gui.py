"""Pruebas de la interfaz gráfica (plataforma Qt «offscreen», sin ventana visible)."""
from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QLabel  # noqa: E402


@pytest.fixture(scope="module")
def window():
    app = QApplication.instance() or QApplication([])
    from meritum_cat.gui.style import apply_theme
    from meritum_cat.i18n import get_translator
    from meritum_cat.gui.main_window import MainWindow
    apply_theme(app)
    get_translator().set_language("es")
    w = MainWindow()
    w.show()
    app.processEvents()
    yield w
    w._force_close = True
    w.close()


def test_window_and_default_bank(window):
    from meritum_cat import __version__
    assert __version__ in window.windowTitle()
    assert window.state.bank is not None and window.state.bank.n_items == 500
    assert window.tabs.count() == 6


@pytest.mark.parametrize("lang,tab", [("en", "Item bank"), ("es", "Banco de ítems")])
def test_language_toggle_without_mixing(window, lang, tab):
    from meritum_cat.gui.automation import language_problems, pump
    (window.btn_en if lang == "en" else window.btn_es).click()
    pump(0.2)
    assert window.tabs.tabText(1) == tab
    assert language_problems(window, lang) == []


def test_mixing_detector_positive_control(window):
    """Control positivo: un texto en español en modo inglés debe detectarse."""
    from meritum_cat.gui.automation import language_problems
    window.set_language("en")
    planted = QLabel("Banco de ítems", window)
    try:
        assert any("otro idioma" in p for p in language_problems(window, "en"))
    finally:
        planted.setParent(None)
        planted.deleteLater()
        window.set_language("es")


def test_cat_tab_session(window):
    ct = window.cat_tab
    ct.btn_start.click()
    ct.btn_run.click()
    assert ct.session.finished and len(ct.session.administered) == 20
    ct.btn_reset.click()
    assert ct.session is None


def test_irt_tab_analytic_maximum(window):
    it = window.irt_tab
    it.model.setCurrentIndex(it.model.findData("2PL"))
    it.a.setValue(2.0)
    it.b.setValue(0.5)
    assert "1.000" in it.lbl_max.text() and "0.50" in it.lbl_max.text()


def test_mc_config_roundtrip_through_widgets(window):
    from meritum_cat.core.simulation import MonteCarloConfig
    mc = window.mc_tab
    cfg = MonteCarloConfig(n_examinees=1234, model="3PL", estimation_method="MAP",
                           selection_method="Kullback-Leibler", max_items=17, se_threshold=0.25,
                           theta_mean=0.5, seed=4321)
    mc.set_config(cfg)
    assert mc.current_config() == cfg
    mc.reset_values()
    assert mc.current_config() == MonteCarloConfig()


def test_status_retranslated_after_run(window):
    """Los mensajes de estado con parámetros se retraducen al cambiar de idioma."""
    from meritum_cat.gui.automation import configure_mc, language_problems, run_mc
    configure_mc(window.mc_tab, n=50, max_items=5)
    assert run_mc(window.mc_tab)
    window.set_language("en")
    assert window.mc_tab.status.text().startswith("Simulation completed")
    assert language_problems(window, "en") == []
    planted = QLabel("Simulación completada en 3.2 s.", window)
    try:
        assert any("otro idioma" in p for p in language_problems(window, "en"))
    finally:
        planted.setParent(None)
        planted.deleteLater()
        window.set_language("es")
