"""
Ejemplo: simulación Monte Carlo reproducible con la API de Meritum_CAT (sin interfaz gráfica).

    python examples/run_monte_carlo_demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from meritum_cat.core.simulation import MonteCarloConfig, run_monte_carlo  # noqa: E402
from meritum_cat.persistence import load_bank, save_experiment_config  # noqa: E402

bank = load_bank(ROOT / "resources" / "datasets" / "synthetic_bank_500_2PL.csv")
config = MonteCarloConfig(n_examinees=1000, model="2PL", estimation_method="EAP",
                          selection_method="Maximum Information", max_items=20, seed=12345)
result = run_monte_carlo(bank, config, progress_callback=lambda d, t: None)

for key in ("bias", "mae", "rmse", "pearson", "spearman", "coverage_95", "mean_test_length",
            "max_exposure_rate", "elapsed_seconds"):
    print(f"{key:20s} {result.metrics[key]:.4f}")

save_experiment_config(Path("experiment_config.json"), config, bank, metrics=result.metrics,
                       elapsed_seconds=result.elapsed_seconds)
print("Configuración guardada en experiment_config.json")
