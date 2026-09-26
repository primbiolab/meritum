"""Configuración común de las pruebas de Meritum_CAT."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Las pruebas de interfaz se ejecutan sin ventana visible.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("MPLBACKEND", "Agg")

from meritum_cat.datasets import generate_synthetic_bank  # noqa: E402


@pytest.fixture(scope="session")
def bank_2pl():
    return generate_synthetic_bank(300, model="2PL", seed=11)


@pytest.fixture(scope="session")
def bank_3pl():
    return generate_synthetic_bank(300, model="3PL", seed=11)


@pytest.fixture
def rng():
    return np.random.default_rng(123)
