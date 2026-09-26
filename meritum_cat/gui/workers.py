"""
Ejecución de tareas largas en un hilo secundario (QThread) sin congelar la GUI.

:class:`TaskWorker` ejecuta una función científica que acepta los argumentos
``progress`` (callback de avance) y ``cancel_check`` (consulta de cancelación).
La cancelación es cooperativa: al presionar «Detener», la función comprueba el
indicador entre examinados y termina limpiamente sin producir resultados.
"""
from __future__ import annotations

import threading
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QThread, Signal, Slot

from meritum_cat.experiments.base import ExperimentCancelled
from meritum_cat.utils.logging_setup import get_logger

log = get_logger("gui.workers")


class TaskWorker(QObject):
    """Trabajador genérico cancelable con señales de progreso y resultado."""

    progress = Signal(int, int)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def is_cancelled(self) -> bool:
        return self._cancel.is_set()

    @Slot()
    def run(self) -> None:
        try:
            result = self._fn(*self._args, progress=self.progress.emit,
                              cancel_check=self._cancel.is_set, **self._kwargs)
        except ExperimentCancelled:
            self.cancelled.emit()
            return
        except Exception:  # noqa: BLE001 - se registra y se informa de forma amigable
            detail = traceback.format_exc()
            log.error("Fallo en tarea en segundo plano:\n%s", detail)
            self.failed.emit(detail)
            return
        if result is None and self._cancel.is_set():
            self.cancelled.emit()
        else:
            self.finished.emit(result)


class TaskRunner(QObject):
    """
    Gestiona el ciclo de vida de un :class:`TaskWorker` en su propio QThread.

    Mantiene referencias para evitar la recolección prematura y libera el hilo
    al terminar, fallar o cancelarse la tarea.
    """

    progress = Signal(int, int)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: TaskWorker | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None

    def start(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        if self.running:
            raise RuntimeError("Ya hay una tarea en ejecución.")
        thread = QThread()
        worker = TaskWorker(fn, *args, **kwargs)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.progress.connect(self.progress)
        worker.finished.connect(self._on_finished)
        worker.failed.connect(self._on_failed)
        worker.cancelled.connect(self._on_cancelled)
        self._thread, self._worker = thread, worker
        thread.start()

    def cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()

    def wait(self, msecs: int = 30000) -> bool:
        """
        Espera a que la tarea termine procesando eventos (usado al cerrar la
        aplicación y en las pruebas automatizadas). Se procesan eventos para que
        las señales encoladas del hilo secundario lleguen y se libere el hilo.
        """
        import time
        from PySide6.QtCore import QCoreApplication, QEventLoop

        deadline = time.monotonic() + msecs / 1000.0
        while self.running and time.monotonic() < deadline:
            QCoreApplication.processEvents(QEventLoop.AllEvents, 50)
            time.sleep(0.01)
        return not self.running

    def _cleanup(self) -> None:
        thread, worker = self._thread, self._worker
        self._thread, self._worker = None, None
        if thread is not None:
            thread.quit()
            thread.wait()
            thread.deleteLater()
        if worker is not None:
            worker.deleteLater()

    def _on_finished(self, result: object) -> None:
        self._cleanup()
        self.finished.emit(result)

    def _on_failed(self, detail: str) -> None:
        self._cleanup()
        self.failed.emit(detail)

    def _on_cancelled(self) -> None:
        self._cleanup()
        self.cancelled.emit()
