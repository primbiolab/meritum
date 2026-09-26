"""
Controles de configuración compartidos por las pestañas CAT y Monte Carlo.

* :class:`AlgorithmControls`: modelo IRT, estimador (con parámetros de la previa)
  y algoritmo de selección (con sus parámetros específicos). Los parámetros que
  no aplican a la opción elegida se deshabilitan.
* :class:`StoppingControls`: criterios de terminación combinables (número máximo
  de ítems, umbral de error estándar, información objetivo, mínimo de ítems).
"""
from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QWidget

from meritum_cat.core.estimation.base import EstimationMethod
from meritum_cat.core.selection.base import SelectionMethod
from meritum_cat.gui.common import Binder, dspin, param_row, spin

MODEL_ITEMS = [("1PL", "model.1PL"), ("2PL", "model.2PL"), ("3PL", "model.3PL")]
ESTIMATOR_ITEMS = [(m.value, f"est.{m.value}") for m in EstimationMethod]


def selector_items(include_sh: bool = True) -> list[tuple[str, str]]:
    return [(s.value, f"sel.{s.value}") for s in SelectionMethod
            if include_sh or s != SelectionMethod.SYMPSON_HETTER]


class CheckedValue(QWidget):
    """Casilla de activación + campo numérico (criterios de terminación opcionales)."""

    def __init__(self, field: QWidget, checked: bool) -> None:
        super().__init__()
        self.check = QCheckBox()
        self.field = field
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.check)
        lay.addWidget(field, 1)
        self.check.toggled.connect(field.setEnabled)
        self.check.setChecked(checked)
        field.setEnabled(checked)

    def value(self):
        return self.field.value() if self.check.isChecked() else None

    def set_value(self, value) -> None:
        self.check.setChecked(value is not None)
        if value is not None:
            self.field.setValue(value)


class AlgorithmControls:
    """Controles de modelo, estimador y selección añadidos a un formulario."""

    def __init__(self, binder: Binder, include_sh: bool = True) -> None:
        self.model = QComboBox()
        binder.combo(self.model, MODEL_ITEMS)
        self.model.setCurrentIndex(1)
        self.estimator = QComboBox()
        binder.combo(self.estimator, ESTIMATOR_ITEMS)
        self.estimator.setCurrentIndex(2)
        self.prior_mean = dspin(-4.0, 4.0, 0.0, 0.1)
        self.prior_sd = dspin(0.1, 5.0, 1.0, 0.1)
        self.selector = QComboBox()
        binder.combo(self.selector, selector_items(include_sh))
        self.randomesque_bin = spin(1, 100, 5)
        self.sh_r_max = dspin(0.01, 1.0, 0.25, 0.01)
        self.sh_iterations = spin(1, 50, 8)
        self.sh_calibration_examinees = spin(1, 100_000, 1000, 100)
        self.include_sh = include_sh
        self.estimator.currentIndexChanged.connect(self._update_enabled)
        self.selector.currentIndexChanged.connect(self._update_enabled)

    def add_model(self, form: QFormLayout, binder: Binder) -> None:
        param_row(form, binder, "model", self.model)

    def add_estimation(self, form: QFormLayout, binder: Binder) -> None:
        param_row(form, binder, "estimator", self.estimator)
        param_row(form, binder, "prior_mean", self.prior_mean)
        param_row(form, binder, "prior_sd", self.prior_sd)

    def add_selection(self, form: QFormLayout, binder: Binder) -> None:
        param_row(form, binder, "selector", self.selector)
        param_row(form, binder, "randomesque_bin", self.randomesque_bin)
        if self.include_sh:
            param_row(form, binder, "sh_r_max", self.sh_r_max)
            param_row(form, binder, "sh_iterations", self.sh_iterations)
            param_row(form, binder, "sh_calibration_examinees", self.sh_calibration_examinees)
        self._update_enabled()

    def _update_enabled(self, *_args) -> None:
        bayes = self.estimator.currentData() in (EstimationMethod.MAP.value, EstimationMethod.EAP.value)
        self.prior_mean.setEnabled(bayes)
        self.prior_sd.setEnabled(bayes)
        sel = self.selector.currentData()
        self.randomesque_bin.setEnabled(sel == SelectionMethod.RANDOMESQUE.value)
        sh = sel == SelectionMethod.SYMPSON_HETTER.value
        for w in (self.sh_r_max, self.sh_iterations, self.sh_calibration_examinees):
            w.setEnabled(sh)

    def set_combo(self, combo: QComboBox, value) -> None:
        idx = combo.findData(value)
        if idx >= 0:
            combo.setCurrentIndex(idx)


class StoppingControls:
    """Criterios de terminación combinables."""

    def __init__(self) -> None:
        self.max_items = CheckedValue(spin(1, 5000, 20), True)
        self.se_threshold = CheckedValue(dspin(0.01, 5.0, 0.30, 0.01), False)
        self.target_information = CheckedValue(dspin(0.1, 10000.0, 11.1, 0.5, 1), False)
        self.min_items = spin(1, 5000, 1)

    def add(self, form: QFormLayout, binder: Binder) -> None:
        param_row(form, binder, "max_items", self.max_items)
        param_row(form, binder, "se_threshold", self.se_threshold)
        param_row(form, binder, "target_information", self.target_information)
        param_row(form, binder, "min_items", self.min_items)

    def values(self) -> dict:
        return {
            "max_items": self.max_items.value(),
            "se_threshold": self.se_threshold.value(),
            "target_information": self.target_information.value(),
            "min_items": self.min_items.value(),
        }
