"""
Genera los bancos de ítems SINTÉTICOS incluidos en ``resources/datasets``.

Los bancos son reproducibles (semilla fija) y se documentan en
``resources/datasets/datasets.json`` con su huella SHA-256. Son datos simulados:
no representan ítems reales ni provienen de ninguna prueba o institución.

Uso:
    python scripts/generate_datasets.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meritum_cat import __version__  # noqa: E402
from meritum_cat.datasets import generate_synthetic_bank  # noqa: E402
from meritum_cat.persistence import save_bank_csv  # noqa: E402

SEED = 2026
SPECS = [(100, "2PL"), (500, "1PL"), (500, "2PL"), (500, "3PL"), (1000, "3PL")]


def main() -> None:
    out = ROOT / "resources" / "datasets"
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for n, model in SPECS:
        name = f"synthetic_bank_{n}_{model}"
        bank = generate_synthetic_bank(n, model=model, seed=SEED, name=name)
        path = out / f"{name}.csv"
        save_bank_csv(bank, path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest.append({"file": path.name, "n_items": n, "model": model, "seed": SEED,
                         "synthetic": True, "sha256": digest})
        print(f"{path.name}: {n} ítems, {model}, sha256={digest[:16]}…")
    (out / "datasets.json").write_text(json.dumps({
        "generator": "meritum_cat.datasets.generate_synthetic_bank",
        "meritum_cat_version": __version__,
        "note": "Synthetic, simulated item banks for experimentation. Not real items; not from any real test or institution.",
        "datasets": manifest,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
