"""
Sesión CAT paso a paso.

Permite administrar un test adaptativo ítem por ítem, con respuestas simuladas a
partir de una habilidad verdadera o introducidas manualmente. Se usa en la
pestaña interactiva de la interfaz. Con respuestas simuladas, el generador
aleatorio se consume en el mismo orden que :func:`simulate_cat` (selección y
luego respuesta), por lo que ambos producen resultados idénticos con la misma
semilla.
"""
from __future__ import annotations

import numpy as np

from meritum_cat.models import ItemBank, CATResult
from meritum_cat.core.irt.information import test_information
from meritum_cat.core.simulation.cat import CATConfig, _simulate_response
from meritum_cat.core.stopping.rules import CATState


class CATSession:
    """Sesión CAT interactiva (paso a paso)."""

    def __init__(self, bank: ItemBank, config: CATConfig, rng: np.random.Generator,
                 theta_true: float | None = None) -> None:
        if bank.n_items == 0:
            raise ValueError("El banco no tiene ítems activos.")
        self.bank = bank
        self.config = config
        self.rng = rng
        self.theta_true = theta_true
        self.available = np.ones(bank.n_items, dtype=bool)
        self.administered: list[int] = []
        self.responses: list[int] = []
        self.categories: list[str] = []
        self.theta_history: list[float] = []
        self.se_history: list[float] = []
        self.info_history: list[float] = []
        self.theta = config.initial_theta
        self.se = float("inf")
        self.info = 0.0
        self.pending: int | None = None
        self.finished = False
        self.stop_reason = ""
        start_session = getattr(config.selector, "start_session", None)
        if start_session is not None:
            start_session()

    def next_item(self) -> int:
        """Selecciona y presenta el siguiente ítem (queda pendiente de respuesta)."""
        if self.finished:
            raise RuntimeError("La sesión ya terminó.")
        if self.pending is not None:
            return self.pending
        selectable = self.available
        if self.config.balancer is not None:
            selectable = self.config.balancer.restrict(self.available, self.categories)
        a, b, c = self.bank.a, self.bank.b, self.bank.c
        self.pending = self.config.selector.select(self.theta, a, b, c, selectable, self.rng)
        return self.pending

    def answer(self, response: int) -> None:
        """Registra la respuesta (1 correcta, 0 incorrecta) al ítem pendiente."""
        if self.pending is None:
            raise RuntimeError("No hay un ítem pendiente de respuesta.")
        idx = self.pending
        self.pending = None
        self.administered.append(idx)
        self.responses.append(int(response))
        self.categories.append(self.bank.category_of(idx))
        self.available[idx] = False

        a, b, c = self.bank.a, self.bank.b, self.bank.c
        adm = np.array(self.administered)
        self.theta, self.se = self.config.estimator.estimate(
            np.array(self.responses, dtype=float), a[adm], b[adm], c[adm])
        self.info = test_information(self.theta, a[adm], b[adm], c[adm])
        self.theta_history.append(self.theta)
        self.se_history.append(self.se)
        self.info_history.append(self.info)

        n_remaining = int(self.available.sum())
        stop, reason = self.config.stopping_rule.should_stop(
            CATState(len(self.administered), self.se, self.info, n_remaining))
        if stop:
            self.finished, self.stop_reason = True, reason
        elif n_remaining == 0:
            self.finished, self.stop_reason = True, "bank_exhausted"

    def simulate_answer(self) -> int:
        """Genera la respuesta del examinado simulado al ítem pendiente."""
        if self.theta_true is None:
            raise RuntimeError("La sesión no tiene habilidad verdadera para simular.")
        idx = self.pending if self.pending is not None else self.next_item()
        resp = _simulate_response(self.theta_true, self.bank.a[idx], self.bank.b[idx],
                                  self.bank.c[idx], self.rng)
        self.answer(resp)
        return resp

    def step(self) -> int:
        """Un paso completo con respuesta simulada: seleccionar y responder."""
        self.next_item()
        return self.simulate_answer()

    def run_to_end(self) -> None:
        """Completa la sesión con respuestas simuladas."""
        while not self.finished:
            self.step()

    def result(self) -> CATResult:
        return CATResult(
            theta_true=self.theta_true, theta_estimate=self.theta, standard_error=self.se,
            administered_items=list(self.administered), responses=list(self.responses),
            theta_history=list(self.theta_history), se_history=list(self.se_history),
            information_history=list(self.info_history), stop_reason=self.stop_reason,
        )
