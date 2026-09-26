"""Ventana principal de Meritum_CAT."""
from __future__ import annotations

from PySide6.QtCore import QUrl
from PySide6.QtGui import QAction, QActionGroup, QDesktopServices, QKeySequence
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QTabWidget, QToolButton, QWidget

from meritum_cat import __app_name__, __version__
from meritum_cat.i18n import get_translator
from meritum_cat.utils.logging_setup import get_logger
from meritum_cat.utils.paths import cache_dir
from meritum_cat.gui.common import confirm, tr
from meritum_cat.gui.dialogs import AboutDialog, GlossaryDialog, QuickStartDialog
from meritum_cat.gui.state import AppState, load_settings, save_settings
from meritum_cat.gui.tabs.bank_tab import BankTab
from meritum_cat.gui.tabs.cat_tab import CATTab
from meritum_cat.gui.tabs.experiments_tab import ExperimentsTab
from meritum_cat.gui.tabs.home_tab import HomeTab
from meritum_cat.gui.tabs.irt_tab import IRTTab
from meritum_cat.gui.tabs.mc_tab import MonteCarloTab

log = get_logger("gui.main")


class MainWindow(QMainWindow):
    """Ventana principal con pestañas, menús, selector de idioma y barra de estado."""

    TAB_BANK, TAB_IRT, TAB_CAT, TAB_MC, TAB_EXP = 1, 2, 3, 4, 5

    def __init__(self) -> None:
        super().__init__()
        self.translator = get_translator()
        self.state = AppState()
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(False)
        self.home = HomeTab(self.state, self.tabs.setCurrentIndex)
        self.bank_tab = BankTab(self.state)
        self.irt_tab = IRTTab(self.state)
        self.cat_tab = CATTab(self.state)
        self.mc_tab = MonteCarloTab(self.state, lambda: self.tabs.setCurrentIndex(self.TAB_BANK))
        self.exp_tab = ExperimentsTab(self.state)
        self._tab_keys = [(self.home, "tab.home"), (self.bank_tab, "tab.bank"), (self.irt_tab, "tab.irt"),
                          (self.cat_tab, "tab.cat"), (self.mc_tab, "tab.mc"), (self.exp_tab, "tab.exp")]
        for page, _ in self._tab_keys:
            self.tabs.addTab(page, "")
        self.setCentralWidget(self.tabs)

        self._build_menus()
        self._build_language_toggle()
        self.status_bank = QLabel()
        self.status_lang = QLabel()
        self.status_version = QLabel(f"{__app_name__} {__version__}")
        self.status_version.setContentsMargins(14, 0, 6, 0)
        self.status_lang.setContentsMargins(6, 0, 6, 0)
        self.statusBar().addWidget(self.status_bank, 1)
        self.statusBar().addPermanentWidget(self.status_lang)
        self.statusBar().addPermanentWidget(self.status_version)

        self.state.bank_changed.connect(self._update_status)
        self.translator.add_listener(lambda _lang: self.retranslate())
        self.retranslate()

        # Banco de ejemplo inicial (sintético) para que todas las pestañas tengan datos.
        idx = self.bank_tab.examples.findData("synthetic_bank_500_2PL.csv")
        if idx >= 0:
            self.bank_tab.examples.setCurrentIndex(idx)
            self.bank_tab.load_example(silent=True)

    # ------------------------------------------------------------------ construcción
    def _build_menus(self) -> None:
        mb = self.menuBar()
        self.menu_file = mb.addMenu("")
        self.act_import = QAction(self)
        self.act_import.setShortcut(QKeySequence.Open)
        self.act_import.triggered.connect(self.bank_tab.import_bank)
        self.act_export_csv = QAction(self)
        self.act_export_csv.triggered.connect(lambda: self.bank_tab.export_bank("csv"))
        self.act_export_json = QAction(self)
        self.act_export_json.triggered.connect(lambda: self.bank_tab.export_bank("json"))
        self.act_load_cfg = QAction(self)
        self.act_load_cfg.triggered.connect(self._load_config)
        self.act_save_cfg = QAction(self)
        self.act_save_cfg.setShortcut(QKeySequence.Save)
        self.act_save_cfg.triggered.connect(self._save_config)
        self.act_exit = QAction(self)
        self.act_exit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_exit.triggered.connect(self.close)
        for act in (self.act_import, self.act_export_csv, self.act_export_json):
            self.menu_file.addAction(act)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_load_cfg)
        self.menu_file.addAction(self.act_save_cfg)
        self.menu_file.addSeparator()
        self.menu_file.addAction(self.act_exit)

        self.menu_lang = mb.addMenu("")
        group = QActionGroup(self)
        group.setExclusive(True)
        self.act_es = QAction(self, checkable=True)
        self.act_en = QAction(self, checkable=True)
        self.act_es.triggered.connect(lambda: self.set_language("es"))
        self.act_en.triggered.connect(lambda: self.set_language("en"))
        for act in (self.act_es, self.act_en):
            group.addAction(act)
            self.menu_lang.addAction(act)

        self.menu_help = mb.addMenu("")
        self.act_quick = QAction(self)
        self.act_quick.setShortcut(QKeySequence.HelpContents)
        self.act_quick.triggered.connect(lambda: self._show_dialog(QuickStartDialog))
        self.act_glossary = QAction(self)
        self.act_glossary.triggered.connect(lambda: self._show_dialog(GlossaryDialog))
        self.act_logs = QAction(self)
        self.act_logs.triggered.connect(self._open_logs)
        self.act_about = QAction(self)
        self.act_about.triggered.connect(lambda: self._show_dialog(AboutDialog))
        for act in (self.act_quick, self.act_glossary, self.act_logs):
            self.menu_help.addAction(act)
        self.menu_help.addSeparator()
        self.menu_help.addAction(self.act_about)

    def _build_language_toggle(self) -> None:
        corner = QWidget()
        lay = QHBoxLayout(corner)
        lay.setContentsMargins(0, 2, 8, 2)
        lay.setSpacing(0)
        self.btn_es = QToolButton()
        self.btn_es.setText("ES")
        self.btn_en = QToolButton()
        self.btn_en.setText("EN")
        self.lang_group = QButtonGroup(self)
        for btn, lang in ((self.btn_es, "es"), (self.btn_en, "en")):
            btn.setCheckable(True)
            btn.setProperty("kind", "lang")
            btn.clicked.connect(lambda _=False, lg=lang: self.set_language(lg))
            self.lang_group.addButton(btn)
            lay.addWidget(btn)
        # Se conserva la referencia: setCornerWidget no transfiere la propiedad en PySide6.
        self.lang_corner = corner
        self.menuBar().setCornerWidget(corner)

    # ------------------------------------------------------------------ idioma
    def apply_qt_translation(self) -> None:
        """
        Carga la traducción de los textos propios de Qt (menús contextuales de los
        campos de texto, botones de diálogos estándar) según el idioma activo.
        """
        from PySide6.QtCore import QCoreApplication, QLibraryInfo, QTranslator
        app = QCoreApplication.instance()
        old = getattr(self, "_qt_translator", None)
        if old is not None:
            app.removeTranslator(old)
            self._qt_translator = None
        if self.translator.language == "es":
            translator = QTranslator(self)
            path = QLibraryInfo.path(QLibraryInfo.TranslationsPath)
            if translator.load("qtbase_es", path):
                app.installTranslator(translator)
                self._qt_translator = translator
            else:
                log.warning("No se encontró la traducción qtbase_es en %s", path)

    def set_language(self, lang: str) -> None:
        if lang == self.translator.language:
            self._sync_language_controls()
            return
        log.info("Idioma cambiado a: %s", lang)
        self.translator.set_language(lang)
        settings = load_settings()
        settings["language"] = lang
        save_settings(settings)

    def _sync_language_controls(self) -> None:
        es = self.translator.language == "es"
        self.btn_es.setChecked(es)
        self.btn_en.setChecked(not es)
        self.act_es.setChecked(es)
        self.act_en.setChecked(not es)

    def retranslate(self) -> None:
        self.apply_qt_translation()
        self.setWindowTitle(f"{__app_name__} {__version__} — {tr('app.subtitle')}")
        for page, key in self._tab_keys:
            self.tabs.setTabText(self.tabs.indexOf(page), tr(key))
        self.menu_file.setTitle(tr("menu.file"))
        self.menu_lang.setTitle(tr("menu.language"))
        self.menu_help.setTitle(tr("menu.help"))
        for act, key in ((self.act_import, "action.import_bank"), (self.act_export_csv, "action.export_bank_csv"),
                         (self.act_export_json, "action.export_bank_json"), (self.act_load_cfg, "action.load_config"),
                         (self.act_save_cfg, "action.save_config"), (self.act_exit, "action.exit"),
                         (self.act_es, "action.lang_es"), (self.act_en, "action.lang_en"),
                         (self.act_quick, "action.quick_start"), (self.act_glossary, "action.glossary"),
                         (self.act_logs, "action.open_logs"), (self.act_about, "action.about")):
            act.setText(tr(key))
        self.btn_es.setToolTip(tr("lang.toggle_tooltip"))
        self.btn_en.setToolTip(tr("lang.toggle_tooltip"))
        for page, _ in self._tab_keys:
            page.retranslate()
        self._sync_language_controls()
        self._update_status()

    def _update_status(self) -> None:
        bank = self.state.bank
        self.status_bank.setText(tr("status.no_bank") if bank is None else
                                 tr("status.bank", name=bank.name, n=bank.n_items))
        self.status_lang.setText(tr("status.language"))

    # ------------------------------------------------------------------ acciones
    def _show_dialog(self, cls) -> None:
        """Abre un diálogo modal y lo libera al cerrarse."""
        dlg = cls(self)
        dlg.exec()
        dlg.deleteLater()

    def _load_config(self) -> None:
        self.tabs.setCurrentIndex(self.TAB_MC)
        self.mc_tab.load_config()

    def _save_config(self) -> None:
        self.tabs.setCurrentIndex(self.TAB_MC)
        self.mc_tab.save_config()

    def _open_logs(self) -> None:
        folder = cache_dir() / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def any_task_running(self) -> bool:
        return self.mc_tab.runner.running or self.exp_tab.runner.running

    def closeEvent(self, event) -> None:  # noqa: N802 (API de Qt)
        if self.any_task_running() and not getattr(self, "_force_close", False):
            if not confirm(self, tr("close.running")):
                event.ignore()
                return
        for runner in (self.mc_tab.runner, self.exp_tab.runner):
            if runner.running:
                runner.cancel()
                runner.wait(30000)
        log.info("Meritum_CAT cerrado.")
        event.accept()
