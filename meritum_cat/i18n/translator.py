"""
Traductor ES/EN de Meritum_CAT.

Las cadenas visibles se identifican por claves neutrales. Cada clave tiene una
versión en español y otra en inglés en :mod:`meritum_cat.i18n.strings`. El
traductor notifica a los oyentes registrados cuando cambia el idioma, para que
la interfaz se retraduzca en vivo.
"""
from __future__ import annotations

from typing import Any, Callable

from meritum_cat.i18n.strings import STRINGS, PARAM_HELP

LANGUAGES = ("es", "en")


class Translator:
    """Traductor con idioma activo y notificación de cambios."""

    def __init__(self, language: str = "es") -> None:
        self._language = language if language in LANGUAGES else "es"
        self._listeners: list[Callable[[str], None]] = []

    @property
    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in LANGUAGES or language == self._language:
            return
        self._language = language
        for listener in list(self._listeners):
            listener(language)

    def add_listener(self, callback: Callable[[str], None]) -> None:
        self._listeners.append(callback)

    def t(self, key: str, **kwargs: Any) -> str:
        """Devuelve la cadena traducida; si falta, devuelve la clave (visible en QA)."""
        entry = STRINGS.get(key)
        if entry is None:
            return key
        text = entry[0] if self._language == "es" else entry[1]
        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, ValueError, IndexError):
                return text
        return text

    __call__ = t

    def param(self, key: str) -> dict[str, str]:
        """Nombre descriptivo, símbolo, ayuda y rango de un parámetro científico."""
        entry = PARAM_HELP[key]
        i = 0 if self._language == "es" else 1
        symbol = entry.get("symbol", "")
        if isinstance(symbol, tuple):
            symbol = symbol[i]
        return {
            "name": entry["name"][i],
            "symbol": symbol,
            "help": entry["help"][i],
            "range": entry["range"][i] if entry.get("range") else "",
        }

    def param_label(self, key: str) -> str:
        """Etiqueta del parámetro: 'Nombre descriptivo (símbolo)'."""
        p = self.param(key)
        return f"{p['name']} ({p['symbol']})" if p["symbol"] else p["name"]

    def param_tooltip(self, key: str) -> str:
        """Texto de ayuda contextual (tooltip) del parámetro, con rango válido."""
        p = self.param(key)
        text = p["help"]
        if p["range"]:
            text += "\n" + self.t("help.valid_range") + ": " + p["range"]
        return text


_TRANSLATOR: Translator | None = None


def get_translator() -> Translator:
    """Devuelve el traductor único de la aplicación."""
    global _TRANSLATOR
    if _TRANSLATOR is None:
        _TRANSLATOR = Translator("es")
    return _TRANSLATOR
