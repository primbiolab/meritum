"""Catálogo bilingüe completo y figuras científicas."""
from __future__ import annotations

import re
import string
from pathlib import Path

import numpy as np
import pytest
from matplotlib.figure import Figure

from meritum_cat.core.estimation.base import EstimationMethod
from meritum_cat.core.selection.base import SelectionMethod
from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo
from meritum_cat.core.validation.bank_validation import _MESSAGES_ES as VALIDATION_CODES
from meritum_cat.experiments import EXPERIMENTS, run_experiment
from meritum_cat.i18n import Translator
from meritum_cat.i18n.strings import PARAM_HELP, STRINGS
from meritum_cat.persistence.item_bank_io import _MESSAGES_ES as IO_CODES
from meritum_cat.persistence.experiment_io import _MESSAGES_ES as CONFIG_CODES
from meritum_cat import plotting

PKG = Path(__file__).resolve().parents[1] / "meritum_cat"
KEY_CALL = re.compile(r"""\btr\(\s*["']([a-zA-Z0-9_.\- ]+)["']""")
KEY_BINDER = re.compile(r"""\.(?:text|title|tooltip|tab)\([^,]+,\s*(?:[^,]+,\s*)?["']([a-z_]+\.[a-zA-Z0-9_.]+)["']""")


def used_keys() -> set[str]:
    keys = set()
    for path in PKG.rglob("*.py"):
        src = path.read_text(encoding="utf-8")
        keys |= set(KEY_CALL.findall(src))
        keys |= set(KEY_BINDER.findall(src))
        keys |= set(re.findall(r'"((?:home|bank|val|col|mc|cat|exp|irt|model|est|dist|mode|stop|cat)\.[a-z_0-9]+)"', src))
    return {k for k in keys if not k.endswith((".png", ".csv", ".json", ".log"))}


def fields(text: str) -> set[str]:
    return {f for _, f, _, _ in string.Formatter().parse(text) if f}


def test_all_used_keys_exist():
    missing = sorted(k for k in used_keys() if k not in STRINGS)
    assert not missing, missing


def test_every_entry_has_both_languages_and_same_placeholders():
    for key, (es, en) in STRINGS.items():
        assert es.strip() and en.strip(), key
        assert fields(es) == fields(en), key


def test_dynamic_keys_exist():
    for m in SelectionMethod:
        assert f"sel.{m.value}" in STRINGS
    for m in EstimationMethod:
        assert f"est.{m.value}" in STRINGS
    for m in ("1PL", "2PL", "3PL"):
        assert f"model.{m}" in STRINGS
    for k in EXPERIMENTS:
        for part in ("title", "desc", "summary"):
            assert f"exp.{k}.{part}" in STRINGS
    for code in ("max_items", "se_threshold", "target_information", "bank_exhausted", "fixed_length"):
        assert f"stop.{code}" in STRINGS
    for code in VALIDATION_CODES:
        assert f"val.{code}" in STRINGS
    for code in list(IO_CODES) + list(CONFIG_CODES):
        assert f"ioerr.{code}" in STRINGS
    for field, code in [("x", c) for c in ("must_be_positive_int", "must_be_positive", "min_lt_max",
                                           "invalid_choice", "need_stopping_rule", "fixed_needs_length",
                                           "invalid_seed", "must_be_probability")]:
        assert f"valerr.{code}" in STRINGS


def test_experiment_columns_translated():
    for key in EXPERIMENTS:
        res = run_experiment(key, n_examinees=20, seed=1)
        for col in res.columns:
            assert f"col.{col}" in STRINGS, col


def test_param_help_complete():
    for key, p in PARAM_HELP.items():
        for field in ("name", "help", "range"):
            assert len(p[field]) == 2 and all(x.strip() for x in p[field]), (key, field)
    t = Translator("es")
    assert t.param_label("a") == "Discriminación del ítem (a)"
    t.set_language("en")
    assert t.param_label("a") == "Item discrimination (a)"
    assert "Valid range" in t.param_tooltip("seed")


def test_translator_switch_notifies():
    t = Translator("es")
    seen = []
    t.add_listener(seen.append)
    t.set_language("en")
    t.set_language("en")
    t.set_language("xx")
    assert seen == ["en"] and t("tab.bank") == "Item bank"
    assert t("clave.inexistente") == "clave.inexistente"


@pytest.fixture(scope="module")
def mc_result():
    from meritum_cat.datasets import generate_synthetic_bank
    bank = generate_synthetic_bank(150, "2PL", seed=2)
    return run_monte_carlo(bank, MonteCarloConfig(n_examinees=200, max_items=10, seed=2))


@pytest.mark.parametrize("lang", ["es", "en"])
def test_all_figures_render(mc_result, lang):
    tr = Translator(lang).t
    r = mc_result
    k, rmse_k, se_k = r.precision_by_item_number()
    calls = [
        (plotting.plot_icc_iic, ([{"a": 1.2, "b": 0.0, "c": 0.2, "label": "x"},
                                  {"a": 0.8, "b": 1.0, "c": 0.0, "label": "y"}], tr), 2),
        (plotting.plot_test_information, (np.ones(5), np.linspace(-1, 1, 5), np.zeros(5), tr), 2),
        (plotting.plot_cat_trace, ([0.1, 0.3], [0.9, 0.7], [1.2, 2.0], [0.0, 0.4], tr, 0.5), 4),
        (plotting.plot_recovery, (r.theta_true, r.theta_est, tr), 1),
        (plotting.plot_error_distribution, (r.theta_true, r.theta_est, tr), 1),
        (plotting.plot_bias_rmse_by_theta, (r.theta_true, r.theta_est, tr), 2),
        (plotting.plot_precision_by_items, (k, rmse_k, se_k, tr), 2),
        (plotting.plot_exposure, (r.exposure.exposure_rates, tr, 0.25), 2),
        (plotting.plot_test_length, (r.test_lengths, tr), 1),
        (plotting.plot_cat_vs_fixed, (r.theta_true, r.theta_est, r.theta_true, r.theta_est * 0.9, tr), 2),
    ]
    for fn, args, n_axes in calls:
        fig = Figure()
        fn(fig, *args)
        assert len(fig.axes) == n_axes, fn.__name__  # sin ejes gemelos (nunca doble eje Y)
        for ax in fig.axes:
            assert ax.get_title(loc="left") and ax.get_ylabel(), fn.__name__
            for text in (ax.get_title(loc="left"), ax.get_ylabel()):
                assert not re.fullmatch(r"[a-z_]+(\.[a-z_]+)+", text), text


@pytest.mark.parametrize("key", list(EXPERIMENTS))
def test_experiment_figures(key):
    res = run_experiment(key, n_examinees=20, seed=1)
    fig = Figure()
    plotting.plot_experiment(fig, res, Translator("en").t)
    assert fig.axes and fig._suptitle is not None
