"""Algoritmos de selección de ítems."""
from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from meritum_cat.core.irt.information import item_information
from meritum_cat.core.selection import (
    KullbackLeiblerSelector, MaximumInformationSelector, RandomSelector, RandomesqueSelector,
    SelectionMethod, SympsonHetterSelector, calibrate_sympson_hetter, make_selector,
)
from meritum_cat.core.simulation.cat import CATConfig, simulate_cat
from meritum_cat.core.estimation import EAPEstimator
from meritum_cat.core.stopping import MaxItemsRule

A = np.array([0.5, 1.0, 2.0, 1.5, 0.8, 1.2])
B = np.array([-2.0, -1.0, 0.0, 0.5, 1.0, 2.0])
C = np.zeros(6)


def test_max_info_picks_argmax(rng):
    avail = np.ones(6, bool)
    for theta in (-1.5, 0.0, 0.6, 1.8):
        expected = int(np.argmax(item_information(theta, A, B, C)))
        assert MaximumInformationSelector().select(theta, A, B, C, avail, rng) == expected


def test_selection_respects_availability(rng):
    avail = np.ones(6, bool)
    avail[2] = False
    for sel in (MaximumInformationSelector(), RandomSelector(), RandomesqueSelector(3),
                KullbackLeiblerSelector(), SympsonHetterSelector(n_items=6)):
        for _ in range(50):
            assert sel.select(0.0, A, B, C, avail, rng) != 2


def test_no_available_items_raises(rng):
    with pytest.raises(ValueError):
        MaximumInformationSelector().select(0.0, A, B, C, np.zeros(6, bool), rng)


def test_random_is_uniform(rng):
    counts = np.zeros(6)
    for _ in range(6000):
        counts[RandomSelector().select(0.0, A, B, C, np.ones(6, bool), rng)] += 1
    assert stats.chisquare(counts).pvalue > 0.001


def test_randomesque_only_top_k(rng):
    info = item_information(0.0, A, B, C)
    top3 = set(np.argsort(-info)[:3].tolist())
    chosen = {RandomesqueSelector(3).select(0.0, A, B, C, np.ones(6, bool), rng) for _ in range(300)}
    assert chosen == top3


def test_randomesque_bin_one_equals_max_info(rng):
    for theta in (-1, 0, 1):
        assert RandomesqueSelector(1).select(theta, A, B, C, np.ones(6, bool), rng) == \
            MaximumInformationSelector().select(theta, A, B, C, np.ones(6, bool), rng)


def test_kl_prefers_items_near_theta(rng):
    a = np.ones(5)
    b = np.array([-3.0, -1.0, 0.0, 1.0, 3.0])
    c = np.zeros(5)
    assert KullbackLeiblerSelector().select(0.0, a, b, c, np.ones(5, bool), rng) == 2
    assert KullbackLeiblerSelector().select(2.8, a, b, c, np.ones(5, bool), rng) == 4


def test_sympson_hetter_with_k_one_is_max_info(rng):
    sel = SympsonHetterSelector(n_items=6)
    for theta in (-1, 0, 1):
        sel.start_session()
        assert sel.select(theta, A, B, C, np.ones(6, bool), rng) == \
            MaximumInformationSelector().select(theta, A, B, C, np.ones(6, bool), rng)


def test_sympson_hetter_blocks_items_within_session():
    rng = np.random.default_rng(0)
    k = np.ones(6)
    best = int(np.argmax(item_information(0.0, A, B, C)))
    k[best] = 1e-9
    sel = SympsonHetterSelector(k_params=k)
    sel.start_session()
    chosen = sel.select(0.0, A, B, C, np.ones(6, bool), rng)
    assert chosen != best and best in sel._blocked
    sel.start_session()
    assert not sel._blocked


def test_sympson_hetter_invalid_k():
    with pytest.raises(ValueError):
        SympsonHetterSelector(k_params=np.array([0.5, 0.0]))
    with pytest.raises(ValueError):
        SympsonHetterSelector()


def test_sympson_hetter_calibration_reduces_exposure(bank_2pl):
    rng = np.random.default_rng(9)
    thetas = rng.normal(size=300)

    def run_population(selector):
        cfg = CATConfig(estimator=EAPEstimator(), selector=selector, stopping_rule=MaxItemsRule(10))
        counts = np.zeros(bank_2pl.n_items)
        for t in thetas:
            r = simulate_cat(t, bank_2pl, cfg, rng)
            counts[r.administered_items] += 1
        return counts, len(thetas)

    k, history = calibrate_sympson_hetter(run_population, bank_2pl.n_items, r_max=0.3, n_iterations=5)
    assert history[0] > 0.9            # sin control, máxima información sobreexpone
    assert history[-1] < 0.45          # tras calibrar se acerca al objetivo
    assert np.all((k > 0) & (k <= 1))


def test_factory():
    assert isinstance(make_selector("Maximum Information"), MaximumInformationSelector)
    assert isinstance(make_selector(SelectionMethod.RANDOMESQUE, bin_size=4), RandomesqueSelector)
    assert isinstance(make_selector("Sympson-Hetter", n_items=3), SympsonHetterSelector)
    with pytest.raises(ValueError):
        make_selector("nope")
    with pytest.raises(ValueError):
        RandomesqueSelector(0)
