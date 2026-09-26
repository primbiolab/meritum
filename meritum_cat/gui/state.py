"""Estado compartido de la aplicación y preferencias del usuario."""
from __future__ import annotations

import json

from PySide6.QtCore import QObject, Signal

from meritum_cat.models import ItemBank
from meritum_cat.core.validation import validate_bank, has_errors
from meritum_cat.utils.paths import cache_dir
from meritum_cat.utils.logging_setup import get_logger

log = get_logger("gui.state")


class AppState(QObject):
    """Banco de ítems activo, compartido por todas las pestañas."""

    bank_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._bank: ItemBank | None = None

    @property
    def bank(self) -> ItemBank | None:
        return self._bank

    def set_bank(self, bank: ItemBank | None) -> None:
        self._bank = bank
        if bank is not None:
            bank.refresh()
            log.info("Banco activo: %s (%d ítems, %d activos)", bank.name, bank.n_total, bank.n_items)
        self.bank_changed.emit()

    def notify_bank_edited(self) -> None:
        if self._bank is not None:
            self._bank.refresh()
        self.bank_changed.emit()

    def bank_error_count(self) -> int:
        if self._bank is None:
            return 0
        return sum(1 for i in validate_bank(self._bank) if i.severity == "error")

    def bank_is_usable(self) -> bool:
        return self._bank is not None and self._bank.n_items > 0 and not has_errors(validate_bank(self._bank))


_SETTINGS_FILE = "settings.json"


def load_settings() -> dict:
    path = cache_dir() / _SETTINGS_FILE
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_settings(settings: dict) -> None:
    path = cache_dir() / _SETTINGS_FILE
    try:
        path.write_text(json.dumps(settings, indent=2), encoding="utf-8")
    except OSError as exc:
        log.warning("No se pudieron guardar las preferencias: %s", exc)
