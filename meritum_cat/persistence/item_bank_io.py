"""
Importación y exportación de bancos de ítems en CSV y JSON.

Formato CSV: una fila por ítem, con encabezados en la primera fila. Columnas
obligatorias: ``item_id`` y ``b`` (dificultad). ``a`` (discriminación) y ``c``
(pseudo-azar) toman los valores 1 y 0 si faltan, lo que permite importar bancos
1PL/2PL. Se aceptan alias en inglés habituales en software psicométrico
(``id``, ``difficulty``, ``discrimination``, ``guessing``...).

Los errores se señalan con :class:`BankIOError`, que incluye un código y sus
parámetros para que la interfaz muestre un mensaje comprensible (nunca una
traza técnica).
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from meritum_cat.models import Item, ItemBank

# Encabezados canónicos del CSV exportado.
CSV_FIELDS = [
    "item_id", "a", "b", "c", "category", "subcategory", "tags",
    "question", "alternatives", "correct", "source", "active", "notes",
]

# Alias aceptados al importar (en minúsculas) -> nombre canónico.
COLUMN_ALIASES: dict[str, str] = {
    "id": "item_id", "item": "item_id", "itemid": "item_id",
    "discrimination": "a", "discriminacion": "a", "discriminación": "a",
    "difficulty": "b", "dificultad": "b",
    "guessing": "c", "pseudoguessing": "c", "pseudoazar": "c", "pseudo-azar": "c",
    "categoria": "category", "categoría": "category",
    "subcategoria": "subcategory", "subcategoría": "subcategory",
    "pregunta": "question", "alternativas": "alternatives",
    "respuesta": "correct", "answer": "correct", "fuente": "source",
    "activo": "active", "observaciones": "notes",
}

_MESSAGES_ES: dict[str, str] = {
    "file_not_found": "No se encuentra el archivo: {path}",
    "missing_column": "No se puede importar el banco porque falta la columna '{column}'.",
    "missing_difficulty": "No se puede importar el banco porque falta la columna de dificultad 'b' (también se acepta 'difficulty' o 'dificultad').",
    "missing_value": "No se puede importar el ítem '{item_id}': falta el valor de '{column}'.",
    "non_numeric": "No se puede importar el ítem '{item_id}': el valor '{value}' de la columna '{column}' no es numérico.",
    "no_items": "El archivo no contiene ítems válidos.",
    "json_invalid": "El archivo JSON no es válido: {msg} (línea {line}).",
    "json_structure": "El JSON debe contener una lista de ítems o un objeto con la clave 'items'.",
    "encoding": "No se pudo leer el archivo: la codificación no es UTF-8.",
}


class BankIOError(Exception):
    """Error de importación/exportación de un banco (con código traducible)."""

    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(_MESSAGES_ES[code].format(**params))


def _canonical(header: str) -> str:
    h = (header or "").strip().lower()
    return COLUMN_ALIASES.get(h, h)


def _to_float(value: Any, column: str, item_id: str, default: float | None) -> float:
    text = "" if value is None else str(value).strip()
    if text == "":
        if default is None:
            raise BankIOError("missing_value", item_id=item_id, column=column)
        return default
    try:
        number = float(text.replace(",", ".")) if text.count(",") == 1 and "." not in text else float(text)
    except ValueError:
        raise BankIOError("non_numeric", item_id=item_id, column=column, value=text) from None
    if math.isinf(number):
        raise BankIOError("non_numeric", item_id=item_id, column=column, value=text)
    return number


def _to_bool(value: Any) -> bool:
    return str(value).strip().lower() not in ("0", "false", "no", "inactivo", "inactive")


def _split(text: Any, sep: str) -> tuple[str, ...]:
    return tuple(x.strip() for x in str(text or "").split(sep) if x.strip())


def _row_to_item(row: dict[str, Any]) -> Item | None:
    iid = str(row.get("item_id") or "").strip()
    if not iid:
        return None
    return Item(
        item_id=iid,
        a=_to_float(row.get("a"), "a", iid, 1.0),
        b=_to_float(row.get("b"), "b", iid, None),
        c=_to_float(row.get("c"), "c", iid, 0.0),
        category=str(row.get("category") or "").strip(),
        subcategory=str(row.get("subcategory") or "").strip(),
        tags=_split(row.get("tags"), ";"),
        question=str(row.get("question") or "").strip(),
        alternatives=_split(row.get("alternatives"), "|"),
        correct=str(row.get("correct") or "").strip(),
        source=str(row.get("source") or "").strip(),
        active=_to_bool(row.get("active", "1") if row.get("active") not in (None, "") else "1"),
        notes=str(row.get("notes") or "").strip(),
    )


def load_bank_csv(path: str | Path, name: str | None = None) -> ItemBank:
    """Carga un banco de ítems desde un archivo CSV (UTF-8, separador , o ;)."""
    path = Path(path)
    if not path.exists():
        raise BankIOError("file_not_found", path=str(path))
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise BankIOError("encoding") from None

    first_line = text.splitlines()[0] if text else ""
    delimiter = ";" if first_line.count(";") > first_line.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        raise BankIOError("no_items")
    headers = [_canonical(h) for h in reader.fieldnames]
    if "item_id" not in headers:
        raise BankIOError("missing_column", column="item_id")
    if "b" not in headers:
        raise BankIOError("missing_difficulty")

    items: list[Item] = []
    for raw in reader:
        row = {_canonical(k): v for k, v in raw.items() if k is not None}
        item = _row_to_item(row)
        if item is not None:
            items.append(item)
    if not items:
        raise BankIOError("no_items")
    return ItemBank(items=items, name=name or path.stem)


def save_bank_csv(bank: ItemBank, path: str | Path) -> None:
    """Guarda un banco de ítems en un archivo CSV (UTF-8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for it in bank.items:
            writer.writerow({
                "item_id": it.item_id, "a": it.a, "b": it.b, "c": it.c,
                "category": it.category, "subcategory": it.subcategory,
                "tags": ";".join(it.tags), "question": it.question,
                "alternatives": "|".join(it.alternatives), "correct": it.correct,
                "source": it.source, "active": int(it.active), "notes": it.notes,
            })


def load_bank_json(path: str | Path, name: str | None = None) -> ItemBank:
    """Carga un banco de ítems desde un archivo JSON."""
    path = Path(path)
    if not path.exists():
        raise BankIOError("file_not_found", path=str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except UnicodeDecodeError:
        raise BankIOError("encoding") from None
    except json.JSONDecodeError as exc:
        raise BankIOError("json_invalid", msg=exc.msg, line=exc.lineno) from None

    raw_items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(raw_items, list):
        raise BankIOError("json_structure")

    items: list[Item] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            raise BankIOError("json_structure")
        row = {_canonical(k): v for k, v in raw.items()}
        for key in ("tags", "alternatives"):
            if isinstance(row.get(key), list):
                row[key] = (";" if key == "tags" else "|").join(str(x) for x in row[key])
        if isinstance(row.get("active"), bool):
            row["active"] = "1" if row["active"] else "0"
        item = _row_to_item(row)
        if item is not None:
            items.append(item)
    if not items:
        raise BankIOError("no_items")
    bank_name = name or (data.get("name") if isinstance(data, dict) else None) or path.stem
    return ItemBank(items=items, name=str(bank_name))


def save_bank_json(bank: ItemBank, path: str | Path) -> None:
    """Guarda un banco de ítems en un archivo JSON (UTF-8)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"name": bank.name, "items": [it.to_dict() for it in bank.items]}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_bank(path: str | Path) -> ItemBank:
    """Carga un banco según la extensión del archivo (.csv o .json)."""
    path = Path(path)
    if path.suffix.lower() == ".json":
        return load_bank_json(path)
    return load_bank_csv(path)
