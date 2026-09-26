"""
Ejemplo: una sesión CAT paso a paso con un examinado simulado.

    python examples/run_cat_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meritum_cat.core.estimation import EAPEstimator  # noqa: E402
from meritum_cat.core.selection import MaximumInformationSelector  # noqa: E402
from meritum_cat.core.simulation import CATConfig, CATSession  # noqa: E402
from meritum_cat.core.stopping import make_stopping_rule  # noqa: E402
from meritum_cat.datasets import generate_synthetic_bank  # noqa: E402

bank = generate_synthetic_bank(300, model="2PL", seed=2026)
config = CATConfig(estimator=EAPEstimator(), selector=MaximumInformationSelector(),
                   stopping_rule=make_stopping_rule(max_items=30, se_threshold=0.30))
session = CATSession(bank, config, np.random.default_rng(12345), theta_true=1.0)

while not session.finished:
    idx = session.next_item()
    response = session.simulate_answer()
    item = bank.active_items[idx]
    print(f"{len(session.administered):2d}  {item.item_id}  b={item.b:+.2f}  x={response}  "
          f"θ̂={session.theta:+.3f}  SE={session.se:.3f}")
print("Motivo de terminación:", session.stop_reason)
