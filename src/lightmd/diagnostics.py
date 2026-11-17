"""Diagnóstico de cuelgues y métricas de render — solo biblioteca estándar.

El objetivo es distinguir dos situaciones que antes se confundían:

* el hilo principal de la aplicación está bloqueado (el volcado de trazas
  muestra dónde), o
* la aplicación está viva y esperando en ``mainloop`` mientras el sistema
  gráfico o el driver de la GPU se han colgado (el volcado muestra el hilo
  inactivo esperando eventos).

Todo el registro es *best-effort*: si el sistema de ficheros no es
escribible, la aplicación sigue funcionando sin diagnóstico.
"""

from __future__ import annotations

import faulthandler
import os
import platform
import threading
import time
from pathlib import Path
from typing import Optional

APP_DIR_NAME = "lightmd"
LOG_FILE_NAME = "lightmd.log"
MAX_LOG_BYTES = 1_000_000
STALL_THRESHOLD = 5.0
WATCHDOG_INTERVAL = 1.0
HEARTBEAT_INTERVAL_MS = 1000

_WRITE_LOCK = threading.Lock()


def state_dir() -> Path:
    """Directorio de estado XDG donde se guarda el log de diagnóstico."""
    base = os.environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path.home() / ".local" / "state"
    return root / APP_DIR_NAME


def log_file() -> Path:
    """Ruta del fichero de log de diagnóstico."""
    return state_dir() / LOG_FILE_NAME


def _rotate_if_needed(path: Path) -> None:
    try:
        if path.exists() and path.stat().st_size > MAX_LOG_BYTES:
            path.write_text("", encoding="utf-8")
    except OSError:
        pass


def append_entry(message: str) -> bool:
    """Añade una línea al log. Devuelve False si no se pudo escribir."""
    path = log_file()
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with _WRITE_LOCK:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            _rotate_if_needed(path)
            with path.open("a", encoding="utf-8") as handle:
                handle.write("[%s] %s\n" % (timestamp, message))
        except OSError:
            return False
    return True


def system_report(app_version: str = "") -> str:
    """Informe legible del entorno para triar congelaciones del sistema."""
    lines = []
    if app_version:
        lines.append("lightmd %s" % app_version)
    lines.extend(
        [
            "Python %s" % platform.python_version(),
            "Kernel %s" % platform.release(),
            "Plataforma %s" % platform.platform(),
            "Sesión %s (%s)"
            % (
                os.environ.get("XDG_SESSION_TYPE", "?"),
                os.environ.get("XDG_CURRENT_DESKTOP", "?"),
            ),
            "DISPLAY %s" % os.environ.get("DISPLAY", "-"),
            "WAYLAND_DISPLAY %s" % os.environ.get("WAYLAND_DISPLAY", "-"),
            "Log %s" % log_file(),
        ]
    )
    return "\n".join(lines)


class Diagnostics:
    """Registro de fallos, bloqueos del hilo principal y métricas de render."""

    def __init__(self, metrics: bool = False) -> None:
        self.metrics = metrics
        self._fault_file = None  # type: Optional[object]
        self._watchdog: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._last_beat = time.monotonic()

    def start(self) -> None:
        self._enable_faulthandler()
        self._start_watchdog()

    def stop(self) -> None:
        self._stop.set()

    def beat(self) -> None:
        """Marca que el hilo principal sigue vivo."""
        self._last_beat = time.monotonic()

    def record(self, message: str) -> None:
        """Registra una métrica (solo si el modo debug está activo)."""
        if self.metrics:
            append_entry(message)

    def report(self) -> str:
        return system_report()

    def _enable_faulthandler(self) -> None:
        try:
            path = log_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            self._fault_file = path.open("a", encoding="utf-8")
            faulthandler.enable(file=self._fault_file, all_threads=True)
        except (OSError, ValueError, RuntimeError):
            self._fault_file = None

    def _start_watchdog(self) -> None:
        self._watchdog = threading.Thread(
            target=self._watch,
            name="lightmd-watchdog",
            daemon=True,
        )
        self._watchdog.start()

    def _watch(self) -> None:
        while not self._stop.wait(WATCHDOG_INTERVAL):
            stalled = time.monotonic() - self._last_beat
            if stalled < STALL_THRESHOLD:
                continue
            with self._lock:
                append_entry("Hilo principal bloqueado %.1fs, volcando trazas" % stalled)
                self._dump_stacks()
            self._last_beat = time.monotonic()

    def _dump_stacks(self) -> None:
        try:
            path = log_file()
            with path.open("a", encoding="utf-8") as handle:
                faulthandler.dump_traceback(file=handle, all_threads=True)
        except (OSError, ValueError, RuntimeError):
            pass
