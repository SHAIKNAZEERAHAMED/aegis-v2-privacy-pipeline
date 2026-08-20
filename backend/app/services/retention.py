"""
Retention backstop (SRS Privacy Requirements).

The normal path deletes a video's temp workspace (raw capture + intermediate
frames) the moment its processing job reaches COMPLETED or FAILED — see
job_orchestrator._finish_pipeline / _fail. This module is the backstop for
when that doesn't happen: a crashed worker, a job that silently died, a
capture that was uploaded but never had /process called on it, etc.

It runs as a daemon thread started once at app startup (see app/main.py). No
new dependency needed for a single-instance MVP; if this moves to multiple
worker processes, this should move to a real scheduler (e.g. Celery beat) so
it only runs once.
"""
import logging
import os
import shutil
import threading
import time
from datetime import datetime, timezone

from app.core.config import settings

logger = logging.getLogger("aegis.retention")

_CHECK_INTERVAL_SECONDS = 60


def _sweep_once():
    if not os.path.isdir(settings.TEMP_DIR):
        return

    cutoff = time.time() - settings.TEMP_RETENTION_MINUTES * 60
    for entry in os.listdir(settings.TEMP_DIR):
        path = os.path.join(settings.TEMP_DIR, entry)
        if not os.path.isdir(path):
            continue
        try:
            mtime = os.path.getmtime(path)
        except OSError:
            continue
        if mtime < cutoff:
            shutil.rmtree(path, ignore_errors=True)
            logger.info(
                "Retention sweep purged stale temp workspace %s (older than %s min)",
                entry, settings.TEMP_RETENTION_MINUTES,
            )


def _loop(stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            _sweep_once()
        except Exception:  # noqa: BLE001 — a sweep failure should never crash the app
            logger.exception("Retention sweep failed")
        stop_event.wait(_CHECK_INTERVAL_SECONDS)


_stop_event = threading.Event()
_thread = None


def start_retention_sweeper():
    global _thread
    if _thread is not None:
        return
    _stop_event.clear()
    _thread = threading.Thread(target=_loop, args=(_stop_event,), daemon=True, name="retention-sweeper")
    _thread.start()
    logger.info(
        "Retention sweeper started (checks every %ss, purges temp workspaces older than %s min)",
        _CHECK_INTERVAL_SECONDS, settings.TEMP_RETENTION_MINUTES,
    )


def stop_retention_sweeper():
    _stop_event.set()
