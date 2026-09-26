"""
Persistencia de configuraciones y resultados de experimentos.

``experiment_config.json`` registra todo lo necesario para reproducir exactamente
una simulación: versión de Meritum_CAT, fecha (UTC), versiones de Python/NumPy,
modelo, estimador, selector, criterio de terminación, semilla, parámetros
poblacionales, el banco completo (con huella SHA-256 de sus parámetros) y los
resultados obtenidos. Al recargarlo, la misma configuración con la misma semilla
produce los mismos resultados, y la huella permite verificar que el banco es
idéntico.
"""
from __future__ import annotations

import csv
import hashlib
import json
import platform
from dataclasses import asdict, fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from meritum_cat import __app_name__, __version__
from meritum_cat.models import Item, ItemBank
from meritum_cat.core.simulation.monte_carlo import MonteCarloConfig

FORMAT_VERSION = 1

_MESSAGES_ES: dict[str, str] = {
    "file_not_found": "No se encuentra el archivo: {path}",
    "invalid_json": "El archivo de configuración no es un JSON válido: {msg} (línea {line}).",
    "not_config": "El archivo no es una configuración de experimento de Meritum_CAT.",
    "invalid_value": "La configuración contiene un valor inválido en '{field}'.",
}


class ConfigIOError(Exception):
    """Error al leer o escribir una configuración (con código traducible)."""

    def __init__(self, code: str, **params: Any) -> None:
        self.code = code
        self.params = params
        super().__init__(_MESSAGES_ES[code].format(**params))


def _bank_rows(bank: ItemBank) -> list[dict[str, Any]]:
    return [
        {"item_id": it.item_id, "a": it.a, "b": it.b, "c": it.c,
         "category": it.category, "subcategory": it.subcategory, "active": it.active}
        for it in bank.items
    ]


def bank_fingerprint(bank: ItemBank) -> str:
    """Huella SHA-256 de los parámetros del banco (identifica bancos idénticos)."""
    canonical = json.dumps(_bank_rows(bank), sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _clean(value: Any) -> Any:
    """Convierte tipos NumPy y NaN a tipos JSON estándar."""
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_clean(v) for v in value]
    if isinstance(value, (np.floating, float)):
        f = float(value)
        return None if np.isnan(f) else f
    if isinstance(value, np.integer):
        return int(value)
    return value


def save_experiment_config(
    path: str | Path,
    config: MonteCarloConfig,
    bank: ItemBank,
    metrics: dict[str, float] | None = None,
    elapsed_seconds: float | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Guarda la configuración (y opcionalmente los resultados) en JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "software": __app_name__,
        "meritum_cat_version": __version__,
        "format_version": FORMAT_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
        },
        "config": _clean(asdict(config)),
        "bank": {
            "name": bank.name,
            "n_items_total": bank.n_total,
            "n_items_active": bank.n_items,
            "sha256": bank_fingerprint(bank),
            "items": _bank_rows(bank),
        },
    }
    if metrics is not None:
        payload["results"] = {"metrics": _clean(metrics), "elapsed_seconds": elapsed_seconds}
    if extra:
        payload["extra"] = _clean(extra)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_experiment_config(path: str | Path) -> dict[str, Any]:
    """Carga y valida un ``experiment_config.json``. Devuelve el diccionario completo."""
    path = Path(path)
    if not path.exists():
        raise ConfigIOError("file_not_found", path=str(path))
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ConfigIOError("invalid_json", msg=exc.msg, line=exc.lineno) from None
    if not isinstance(data, dict) or "config" not in data or not isinstance(data["config"], dict):
        raise ConfigIOError("not_config")
    return data


def monte_carlo_config_from_dict(cfg: dict[str, Any]) -> MonteCarloConfig:
    """Reconstruye un :class:`MonteCarloConfig` desde su diccionario serializado."""
    valid = {f.name for f in fields(MonteCarloConfig)}
    kwargs = {k: v for k, v in cfg.items() if k in valid}
    if "theta_bounds" in kwargs and kwargs["theta_bounds"] is not None:
        try:
            lo, hi = kwargs["theta_bounds"]
            kwargs["theta_bounds"] = (float(lo), float(hi))
        except (TypeError, ValueError):
            raise ConfigIOError("invalid_value", field="theta_bounds") from None
    try:
        return MonteCarloConfig(**kwargs)
    except TypeError:
        raise ConfigIOError("not_config") from None


def bank_from_payload(data: dict[str, Any]) -> ItemBank | None:
    """Reconstruye el banco embebido en una configuración (o None si no hay)."""
    bank = data.get("bank")
    if not isinstance(bank, dict) or not isinstance(bank.get("items"), list):
        return None
    items = []
    for row in bank["items"]:
        items.append(Item(
            item_id=str(row["item_id"]), a=float(row["a"]), b=float(row["b"]), c=float(row["c"]),
            category=str(row.get("category", "")), subcategory=str(row.get("subcategory", "")),
            active=bool(row.get("active", True)),
        ))
    return ItemBank(items=items, name=str(bank.get("name", "bank")))


def save_results_csv(result: Any, path: str | Path) -> None:
    """Exporta a CSV los resultados por examinado de una simulación Monte Carlo."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["examinee", "theta_true", "theta_est", "standard_error",
                         "test_length", "stop_reason"])
        for i in range(len(result.theta_true)):
            writer.writerow([
                i + 1,
                f"{result.theta_true[i]:.6f}",
                f"{result.theta_est[i]:.6f}",
                f"{result.se[i]:.6f}",
                int(result.test_lengths[i]),
                result.stop_reasons[i],
            ])


def save_experiment_result_csv(exp_result: Any, path: str | Path) -> None:
    """Exporta a CSV la tabla de resultados de un experimento predefinido."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=exp_result.columns)
        writer.writeheader()
        for row in exp_result.rows:
            writer.writerow({c: row.get(c, "") for c in exp_result.columns})
