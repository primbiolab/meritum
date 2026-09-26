"""Importación/exportación, validación del banco y bancos sintéticos incluidos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo
from meritum_cat.core.validation import has_errors, validate_bank
from meritum_cat.datasets import generate_synthetic_bank
from meritum_cat.models import Item, ItemBank
from meritum_cat.persistence import (
    BankIOError, ConfigIOError, bank_fingerprint, bank_from_payload, load_bank, load_bank_csv,
    load_bank_json, load_experiment_config, monte_carlo_config_from_dict, save_bank_csv, save_bank_json,
    save_experiment_config, save_results_csv,
)

ROOT = Path(__file__).resolve().parents[1]


def test_csv_roundtrip(tmp_path, bank_3pl):
    p = tmp_path / "bank.csv"
    save_bank_csv(bank_3pl, p)
    loaded = load_bank_csv(p)
    assert bank_fingerprint(loaded) == bank_fingerprint(bank_3pl)


def test_json_roundtrip_with_optional_fields(tmp_path):
    bank = ItemBank([Item("Q1", 1.2, -0.3, 0.2, category="Álgebra", tags=("t1", "t2"),
                          question="¿2+2?", alternatives=("3", "4"), correct="4", active=False, notes="nota")])
    p = tmp_path / "bank.json"
    save_bank_json(bank, p)
    it = load_bank_json(p).items[0]
    assert it == bank.items[0]


def test_column_aliases_and_semicolon(tmp_path):
    p = tmp_path / "real.csv"
    p.write_text("ID;Discrimination;Difficulty;Guessing\nA1;1,5;0,25;0,1\n", encoding="utf-8")
    it = load_bank(p).items[0]
    assert (it.item_id, it.a, it.b, it.c) == ("A1", 1.5, 0.25, 0.1)


def test_defaults_for_1pl_import(tmp_path):
    p = tmp_path / "rasch.csv"
    p.write_text("item_id,b\nR1,0.4\n", encoding="utf-8")
    it = load_bank(p).items[0]
    assert it.a == 1.0 and it.c == 0.0 and it.active


@pytest.mark.parametrize("content,code", [
    ("item_id,a,c\nX,1,0\n", "missing_difficulty"),
    ("a,b\n1,0\n", "missing_column"),
    ("item_id,b\nX,abc\n", "non_numeric"),
    ("item_id,b\nX,\n", "missing_value"),
    ("item_id,b\n", "no_items"),
])
def test_friendly_csv_errors(tmp_path, content, code):
    p = tmp_path / "bad.csv"
    p.write_text(content, encoding="utf-8")
    with pytest.raises(BankIOError) as exc:
        load_bank_csv(p)
    assert exc.value.code == code
    assert "Traceback" not in str(exc.value)


def test_json_errors(tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(BankIOError) as exc:
        load_bank_json(p)
    assert exc.value.code == "json_invalid"
    p.write_text('{"items": 3}', encoding="utf-8")
    with pytest.raises(BankIOError) as exc:
        load_bank_json(p)
    assert exc.value.code == "json_structure"
    with pytest.raises(BankIOError) as exc:
        load_bank(tmp_path / "missing.csv")
    assert exc.value.code == "file_not_found"


def test_validation_detects_all_problems():
    bank = ItemBank([
        Item("I1", 1.0, 0.0, 0.1, category="A"),
        Item("I1", 1.0, 0.0, 0.1, category="A"),          # ID duplicado
        Item("", 1.0, 0.0, 0.0, category="A"),            # sin ID
        Item("I3", -0.2, 0.0, 0.0, category="A"),         # a <= 0
        Item("I4", 3.5, 0.0, 0.0, category="A"),          # a alta
        Item("I5", 1.0, float("nan"), 0.0, category="A"),  # NaN
        Item("I6", 1.0, 4.5, 0.0, category="A"),          # b extrema
        Item("I7", 1.0, 0.0, -0.1, category="A"),         # c < 0
        Item("I8", 1.0, 0.0, 1.0, category="A"),          # c >= 1
        Item("I9", 1.0, 0.0, 0.6, category="A"),          # c alta
        Item("I10", 1.0, 0.0, 0.0),                        # sin categoría
    ])
    codes = {i.code for i in validate_bank(bank)}
    assert codes == {"duplicate_id", "missing_id", "a_nonpositive", "a_high", "b_nan", "b_extreme",
                     "c_negative", "c_ge_one", "c_high", "missing_category"}
    assert has_errors(validate_bank(bank))
    for issue in validate_bank(bank):
        assert issue.message  # mensaje comprensible en español


def test_validation_empty_banks():
    assert {i.code for i in validate_bank(ItemBank([]))} == {"bank_empty"}
    assert "bank_no_active" in {i.code for i in validate_bank(ItemBank([Item("A", active=False, category="x")]))}


def test_clean_synthetic_bank_has_no_errors(bank_2pl):
    assert not has_errors(validate_bank(bank_2pl))


@pytest.mark.parametrize("model", ["1PL", "2PL", "3PL"])
def test_synthetic_generation_reproducible_and_valid(model):
    b1 = generate_synthetic_bank(200, model=model, seed=5)
    b2 = generate_synthetic_bank(200, model=model, seed=5)
    b3 = generate_synthetic_bank(200, model=model, seed=6)
    assert bank_fingerprint(b1) == bank_fingerprint(b2) != bank_fingerprint(b3)
    assert np.all(b1.a > 0) and np.all((b1.c >= 0) & (b1.c < 1))
    if model == "1PL":
        assert np.allclose(b1.a, 1)
    if model != "3PL":
        assert np.allclose(b1.c, 0)
    assert all(it.source == "SYN" for it in b1.items)


def test_shipped_datasets_match_manifest_and_generator(tmp_path):
    folder = ROOT / "resources" / "datasets"
    manifest = json.loads((folder / "datasets.json").read_text(encoding="utf-8"))
    sizes = set()
    for ds in manifest["datasets"]:
        path = folder / ds["file"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == ds["sha256"]
        regenerated = generate_synthetic_bank(ds["n_items"], model=ds["model"], seed=ds["seed"])
        out = tmp_path / ds["file"]
        save_bank_csv(regenerated, out)
        assert out.read_bytes() == path.read_bytes()
        assert ds["synthetic"] is True
        sizes.add(ds["n_items"])
    assert {100, 500, 1000} <= sizes


def test_experiment_config_roundtrip(tmp_path, bank_2pl):
    cfg = MonteCarloConfig(n_examinees=120, estimation_method="MAP", selection_method="Randomesque",
                           max_items=12, se_threshold=0.4, seed=77)
    res = run_monte_carlo(bank_2pl, cfg)
    path = tmp_path / "experiment_config.json"
    save_experiment_config(path, cfg, bank_2pl, metrics=res.metrics, elapsed_seconds=res.elapsed_seconds)
    data = load_experiment_config(path)
    for key in ("meritum_cat_version", "created_utc", "environment", "config", "bank", "results"):
        assert key in data
    cfg2 = monte_carlo_config_from_dict(data["config"])
    bank2 = bank_from_payload(data)
    assert cfg2 == cfg
    assert bank_fingerprint(bank2) == data["bank"]["sha256"] == bank_fingerprint(bank_2pl)
    res2 = run_monte_carlo(bank2, cfg2)
    assert np.array_equal(res.theta_est, res2.theta_est)
    for k, v in data["results"]["metrics"].items():
        if k != "elapsed_seconds" and v is not None:
            assert res2.metrics[k] == pytest.approx(v, abs=1e-12)


def test_config_errors(tmp_path):
    p = tmp_path / "x.json"
    p.write_text("[]", encoding="utf-8")
    with pytest.raises(ConfigIOError) as exc:
        load_experiment_config(p)
    assert exc.value.code == "not_config"
    p.write_text("{oops", encoding="utf-8")
    with pytest.raises(ConfigIOError) as exc:
        load_experiment_config(p)
    assert exc.value.code == "invalid_json"


def test_results_csv(tmp_path, bank_2pl):
    res = run_monte_carlo(bank_2pl, MonteCarloConfig(n_examinees=30, max_items=5))
    p = tmp_path / "r.csv"
    save_results_csv(res, p)
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0].startswith("examinee,theta_true,theta_est") and len(lines) == 31


def test_cache_dir_is_inside_application_folder():
    """El programa guarda su caché (registro, preferencias) en su propia carpeta, no en el perfil del usuario."""
    from meritum_cat.utils.paths import app_dir, cache_dir
    assert cache_dir() == app_dir() / "cache"
    assert cache_dir().is_dir()
