"""Criterios de terminación, exposición de ítems y balanceo de contenido."""
from __future__ import annotations

import numpy as np
import pytest

from meritum_cat.core.balancing import ContentBalancer
from meritum_cat.core.estimation import EAPEstimator
from meritum_cat.core.exposure import compute_exposure
from meritum_cat.core.selection import MaximumInformationSelector
from meritum_cat.core.simulation.cat import CATConfig, simulate_cat
from meritum_cat.core.stopping import (
    CompositeRule, MaxItemsRule, MinInformationRule, StandardErrorRule, make_stopping_rule,
)
from meritum_cat.core.stopping.rules import CATState


def st(n=5, se=0.5, info=4.0, rem=10):
    return CATState(n_administered=n, standard_error=se, information=info, n_remaining=rem)


def test_max_items_rule():
    rule = MaxItemsRule(5)
    assert rule.should_stop(st(n=4)) == (False, "")
    assert rule.should_stop(st(n=5)) == (True, "max_items")


def test_se_rule_with_minimum():
    rule = StandardErrorRule(0.3, min_items=5)
    assert not rule.should_stop(st(n=3, se=0.2))[0]
    assert rule.should_stop(st(n=5, se=0.3))[0]
    assert not rule.should_stop(st(n=6, se=0.31))[0]


def test_information_rule():
    rule = MinInformationRule(11.0)
    assert not rule.should_stop(st(info=10.9))[0]
    assert rule.should_stop(st(info=11.0)) == (True, "target_information")


def test_composite_and_factory():
    rule = make_stopping_rule(max_items=20, se_threshold=0.3)
    assert isinstance(rule, CompositeRule)
    assert rule.should_stop(st(n=20, se=0.9)) == (True, "max_items")
    assert rule.should_stop(st(n=4, se=0.25)) == (True, "se_threshold")
    assert isinstance(make_stopping_rule(max_items=10), MaxItemsRule)
    with pytest.raises(ValueError):
        make_stopping_rule(max_items=None)
    with pytest.raises(ValueError):
        MaxItemsRule(0)
    with pytest.raises(ValueError):
        StandardErrorRule(0)


def test_se_rule_in_cat_reaches_threshold(bank_2pl, rng):
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), StandardErrorRule(0.35))
    for theta in (-1.0, 0.0, 1.2):
        r = simulate_cat(theta, bank_2pl, cfg, rng)
        assert r.stop_reason == "se_threshold" and r.standard_error <= 0.35


def test_exposure_counts_and_rates():
    stats = compute_exposure([[0, 1], [0, 2], [0, 1]], n_items=4)
    assert stats.counts.tolist() == [3, 2, 1, 0]
    assert stats.exposure_rates.tolist() == pytest.approx([1.0, 2 / 3, 1 / 3, 0.0])
    assert stats.max_rate == 1.0
    assert stats.unused_items == 1
    assert stats.overexposed_items == 3
    assert stats.mean_rate == pytest.approx(0.5)


def test_exposure_uniform_chi_square_zero():
    stats = compute_exposure([[0, 1], [2, 3]], n_items=4)
    assert stats.chi_square_uniformity() == pytest.approx(0.0)


def test_mean_exposure_equals_length_over_bank(bank_2pl, rng):
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(15))
    adm = [simulate_cat(t, bank_2pl, cfg, rng).administered_items for t in rng.normal(size=50)]
    stats = compute_exposure(adm, bank_2pl.n_items)
    # Identidad: suma de tasas = longitud media del test.
    assert stats.exposure_rates.sum() == pytest.approx(15.0)


def test_balancer_restricts_to_largest_deficit():
    cats = ["X", "X", "Y", "Y", "Z"]
    bal = ContentBalancer(cats, {"X": 1, "Y": 1, "Z": 2})
    avail = np.ones(5, bool)
    mask = bal.restrict(avail, [])
    assert mask.tolist() == [False, False, False, False, True]  # Z tiene el mayor objetivo
    mask = bal.restrict(avail, ["Z", "Z"])
    assert set(np.flatnonzero(mask)) in ({0, 1}, {2, 3})


def test_balancer_disabled_returns_input():
    avail = np.array([True, False, True])
    assert ContentBalancer(["a", "b", "c"], None).restrict(avail, []) is avail


def test_balancing_in_cat_matches_targets(bank_2pl, rng):
    cats = [it.category for it in bank_2pl.active_items]
    targets = {c: 1.0 for c in sorted(set(cats))}
    cfg = CATConfig(EAPEstimator(), MaximumInformationSelector(), MaxItemsRule(20),
                    balancer=ContentBalancer(cats, targets))
    r = simulate_cat(0.3, bank_2pl, cfg, rng)
    counts = {c: 0 for c in targets}
    for idx in r.administered_items:
        counts[bank_2pl.category_of(idx)] += 1
    assert set(counts.values()) == {5}  # 4 categorías x 5 ítems


def test_balancer_invalid_targets():
    with pytest.raises(ValueError):
        ContentBalancer(["a"], {"a": 0.0})
