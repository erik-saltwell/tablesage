from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import widelog

from .paths import logs_root

_LOGGER_NAME = "tablesage.widelog"
_SPEAKER_IDENTIFICATION_LOGGER_NAME = "tablesage.speaker_identification"


def configure_logging(cwd: Path) -> None:
    """Configure widelog to write one JSON line per wide event to
    `<cwd>/.tablesage/logs/tablesage.log`. Call once, from the TUI's composition root,
    before anything else logs -- widelog's configuration is process-global, so
    `tablesage-application`/`tablesage-tools` code elsewhere just calls
    `widelog.wide_event(...)`/`widelog.use_logger()` directly, with no need to import
    this module.

    Never logs to stdout/stderr: Textual owns the terminal, and widelog's default sink
    (stdout) would corrupt the running TUI's display, so a rotating-file sink replaces
    it here.

    Also wires up `tablesage.speaker_identification` (plain stdlib logging, not widelog) to
    its own rotating file, `speaker_identification.log` -- `identify_speakers` can emit one
    line per utterance there, which widelog's one-line-per-*operation* model can't carry
    without either dropping the per-utterance detail or bloating a single event.
    """
    log_dir = logs_root(cwd)
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(log_dir / "tablesage.log", maxBytes=10_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(message)s"))

    file_logger = logging.getLogger(_LOGGER_NAME)
    file_logger.setLevel(logging.INFO)
    file_logger.addHandler(handler)
    file_logger.propagate = False

    def _sink(event: dict[str, Any]) -> None:
        file_logger.info(json.dumps(event, default=str))

    widelog.init(service="tablesage", environment="development", sink=_sink)

    speaker_id_handler = RotatingFileHandler(log_dir / "speaker_identification.log", maxBytes=10_000_000, backupCount=3)
    speaker_id_handler.setFormatter(logging.Formatter("%(message)s"))

    speaker_id_logger = logging.getLogger(_SPEAKER_IDENTIFICATION_LOGGER_NAME)
    speaker_id_logger.setLevel(logging.INFO)
    speaker_id_logger.addHandler(speaker_id_handler)
    speaker_id_logger.propagate = False
