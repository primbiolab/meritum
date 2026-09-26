"""Pestaña de inicio: presentación, flujo de trabajo guiado y banco actual."""
from __future__ import annotations

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QScrollArea

from meritum_cat import __app_name__, __version__
from meritum_cat.gui.common import Binder, button, muted_label, tr
from meritum_cat.gui.state import AppState


class HomeTab(QWidget):
    """Pantalla de bienvenida con los pasos del flujo científico."""

    # (clave del paso, índice de la pestaña destino)
    STEPS = [("home.step1", 1), ("home.step2", 2), ("home.step3", 3),
             ("home.step4", 4), ("home.step5", 4), ("home.step6", 5)]

    def __init__(self, state: AppState, go_to_tab: Callable[[int], None]) -> None:
        super().__init__()
        self.state = state
        self.binder = Binder()
        b = self.binder

        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        title = QLabel()
        title.setProperty("role", "title")
        b.call(lambda: title.setText(f"{__app_name__} {__version__}"))
        subtitle = muted_label("subtitle")
        b.text(subtitle, "app.subtitle")
        intro = QLabel()
        intro.setWordWrap(True)
        b.text(intro, "home.intro")
        lay.addWidget(title)
        lay.addWidget(subtitle)
        lay.addWidget(intro)

        steps_box = QGroupBox()
        b.title(steps_box, "home.workflow")
        grid = QGridLayout(steps_box)
        grid.setColumnStretch(0, 1)
        self.step_buttons = []
        for row, (key, tab_index) in enumerate(self.STEPS):
            lab = QLabel()
            lab.setWordWrap(True)
            b.text(lab, key)
            btn = button()
            b.text(btn, "btn.go")
            btn.clicked.connect(lambda _=False, i=tab_index: go_to_tab(i))
            self.step_buttons.append(btn)
            grid.addWidget(lab, row, 0)
            grid.addWidget(btn, row, 1, Qt.AlignRight)
        lay.addWidget(steps_box)

        bank_box = QGroupBox()
        b.title(bank_box, "home.bank_group")
        bl = QVBoxLayout(bank_box)
        self.bank_label = QLabel()
        self.bank_label.setWordWrap(True)
        bl.addWidget(self.bank_label)
        lay.addWidget(bank_box)

        note = muted_label("note")
        b.text(note, "home.synthetic_note")
        offline = muted_label()
        b.text(offline, "home.offline")
        lay.addWidget(note)
        lay.addWidget(offline)
        lay.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        state.bank_changed.connect(self.refresh)
        b.call(self.refresh)

    def refresh(self) -> None:
        bank = self.state.bank
        if bank is None:
            self.bank_label.setText(tr("bank.empty"))
            return
        import numpy as np
        a = float(np.mean(bank.a)) if bank.n_items else 0.0
        bb = float(np.mean(bank.b)) if bank.n_items else 0.0
        c = float(np.mean(bank.c)) if bank.n_items else 0.0
        self.bank_label.setText(tr("bank.summary", name=bank.name, n=bank.n_total, active=bank.n_items,
                                   ncat=len(bank.categories), a=a, b=bb, c=c))

    def retranslate(self) -> None:
        self.binder.retranslate()
