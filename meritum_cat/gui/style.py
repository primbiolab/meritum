"""Tema visual claro y profesional de la interfaz (Fusion + hoja de estilos)."""
from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

ACCENT = "#2a78d6"
ACCENT_DARK = "#1c5cab"
SURFACE = "#fcfcfb"
PAGE = "#f4f4f1"
INK = "#0b0b0b"
INK_2 = "#52514e"
BORDER = "#d6d5ce"
DANGER = "#d03b3b"

STYLESHEET = f"""
QMainWindow, QDialog {{ background: {PAGE}; }}
QWidget {{ color: {INK}; font-size: 9.5pt; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 6px; background: {SURFACE}; top: -1px; }}
QTabBar::tab {{ background: transparent; padding: 7px 14px; margin-right: 2px; color: {INK_2};
               border: 1px solid transparent; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {SURFACE}; color: {INK}; border-color: {BORDER}; border-bottom-color: {SURFACE};
                        font-weight: 600; }}
QTabBar::tab:hover:!selected {{ color: {INK}; background: #ebeae5; }}
QTabWidget QTabWidget QTabBar::tab {{ padding: 5px 9px; }}
QGroupBox {{ border: 1px solid {BORDER}; border-radius: 6px; margin-top: 14px; padding: 10px 8px 8px 8px;
            background: {SURFACE}; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {INK}; }}
QLabel {{ background: transparent; }}
QLabel[role="muted"] {{ color: {INK_2}; font-weight: normal; }}
QLabel[role="title"] {{ font-size: 15pt; font-weight: 600; }}
QLabel[role="subtitle"] {{ font-size: 10.5pt; color: {INK_2}; }}
QLabel[role="note"] {{ color: {INK_2}; background: #eef4fc; border: 1px solid #cde2fb; border-radius: 5px; padding: 6px; }}
QLabel[role="metric"] {{ font-weight: 600; }}
QPushButton {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 5px; padding: 5px 12px; }}
QPushButton:hover {{ border-color: {ACCENT}; }}
QPushButton:pressed {{ background: #e8f0fb; }}
QPushButton:disabled {{ color: #a3a29c; border-color: #e3e2dc; }}
QPushButton[kind="primary"] {{ background: {ACCENT}; color: white; border-color: {ACCENT}; font-weight: 600; }}
QPushButton[kind="primary"]:hover {{ background: {ACCENT_DARK}; }}
QPushButton[kind="primary"]:disabled {{ background: #a9c7ee; border-color: #a9c7ee; color: white; }}
QPushButton[kind="danger"] {{ color: {DANGER}; }}
QPushButton[kind="danger"]:disabled {{ color: #e2a9a9; }}
QToolButton[kind="help"] {{ border: 1px solid {BORDER}; border-radius: 9px; min-width: 18px; max-width: 18px;
                           min-height: 18px; max-height: 18px; color: {ACCENT}; font-weight: 700; background: {SURFACE}; }}
QToolButton[kind="help"]:hover {{ border-color: {ACCENT}; background: #e8f0fb; }}
QToolButton[kind="lang"] {{ border: 1px solid {BORDER}; padding: 3px 9px; background: {SURFACE}; font-weight: 600; }}
QToolButton[kind="lang"]:checked {{ background: {ACCENT}; color: white; border-color: {ACCENT}; }}
QLineEdit, QPlainTextEdit, QTextEdit {{
    background: white; border: 1px solid {BORDER}; border-radius: 4px; padding: 3px 5px; }}
QLineEdit:focus {{ border-color: {ACCENT}; }}
QTableWidget, QTableView, QListWidget {{ background: white; border: 1px solid {BORDER}; border-radius: 4px;
    gridline-color: #ecebe6; alternate-background-color: #f8f8f6; selection-background-color: #d5e5f9;
    selection-color: {INK}; }}
QHeaderView::section {{ background: #f0efeb; border: none; border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER}; padding: 4px 6px; font-weight: 600; }}
QProgressBar {{ border: 1px solid {BORDER}; border-radius: 4px; background: white; text-align: center; height: 16px; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 3px; }}
QStatusBar {{ background: {PAGE}; color: {INK_2}; }}
QScrollArea {{ border: none; background: transparent; }}
QToolTip {{ background: white; color: {INK}; border: 1px solid {BORDER}; padding: 5px; }}
"""


def apply_theme(app: QApplication) -> None:
    """Aplica el estilo Fusion con paleta clara y la hoja de estilos de la aplicación."""
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(PAGE))
    pal.setColor(QPalette.WindowText, QColor(INK))
    pal.setColor(QPalette.Base, QColor("white"))
    pal.setColor(QPalette.AlternateBase, QColor("#f8f8f6"))
    pal.setColor(QPalette.Text, QColor(INK))
    pal.setColor(QPalette.Button, QColor(SURFACE))
    pal.setColor(QPalette.ButtonText, QColor(INK))
    pal.setColor(QPalette.Highlight, QColor("#d5e5f9"))
    pal.setColor(QPalette.HighlightedText, QColor(INK))
    pal.setColor(QPalette.ToolTipBase, QColor("white"))
    pal.setColor(QPalette.ToolTipText, QColor(INK))
    app.setPalette(pal)
    app.setStyleSheet(STYLESHEET)
