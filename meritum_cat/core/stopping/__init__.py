"""Criterios de terminación (stopping rules) del CAT."""
from __future__ import annotations

from meritum_cat.core.stopping.rules import (
    StoppingRule,
    MaxItemsRule,
    StandardErrorRule,
    MinInformationRule,
    CompositeRule,
    make_stopping_rule,
)

__all__ = [
    "StoppingRule",
    "MaxItemsRule",
    "StandardErrorRule",
    "MinInformationRule",
    "CompositeRule",
    "make_stopping_rule",
]
