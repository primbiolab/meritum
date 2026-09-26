"""Experimentos científicos reproducibles predefinidos."""
from __future__ import annotations

from meritum_cat.experiments.base import ExperimentResult, ExperimentCancelled
from meritum_cat.experiments.predefined import EXPERIMENTS, run_experiment

__all__ = ["ExperimentResult", "ExperimentCancelled", "EXPERIMENTS", "run_experiment"]
