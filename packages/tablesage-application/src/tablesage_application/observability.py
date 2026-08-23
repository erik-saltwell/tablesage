from __future__ import annotations

import functools
import logging
import subprocess
import time
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import structlog

from .paths import logs_root

_OWN_PACKAGES = ("tablesage_application", "tablesage_tools")


def configure_logging(cwd: Path) -> None:
    """Configure structlog (and the stdlib logging it sits on) to write one JSON line per
    event to `<cwd>/.tablesage/logs/tablesage.log`. Call once, from the TUI's composition
    root, before anything else logs -- structlog's configuration is process-global, so
    `tablesage-tools`/`tablesage-application` code elsewhere just calls
    `structlog.get_logger(__name__)` directly, with no need to import this module.

    Never logs to stdout/stderr: Textual owns the terminal, and writing there would corrupt
    the running TUI's display. Third-party library logs are capped at WARNING (their INFO
    chatter isn't worth the noise); this app's own two packages log at INFO.
    """
    log_dir = logs_root(cwd)
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(log_dir / "tablesage.log", maxBytes=10_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter("%(message)s"))

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)
    root_logger.addHandler(handler)
    for name in _OWN_PACKAGES:
        logging.getLogger(name).setLevel(logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def _summarize(value: object) -> object:
    """A safe, compact representation of one argument for a wide event -- scalars pass
    through as strings, collections collapse to a length so a huge clip list or resolution
    map doesn't blow up a single log line."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (Path, UUID)):
        return str(value)
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return f"<{type(value).__name__} len={len(value)}>"
    return type(value).__name__


def wide_event[F: Callable[..., Any]](func: F) -> F:
    """Wrap a synchronous `Application` method to emit exactly one structured log line per
    call -- the event name, a safe summary of its arguments, duration, outcome, and (on
    failure) the exception's type/message, plus `subprocess.CalledProcessError`'s cmd/
    returncode/stderr when that's the underlying error, since that's the one place this app
    currently has no other way to see why an external tool (ffmpeg, etc.) failed.

    Always re-raises -- this only observes the call, it never changes its outcome.
    """

    @functools.wraps(func)
    def wrapper(self: object, *args: object, **kwargs: object) -> object:
        logger = structlog.get_logger(func.__module__)
        event = f"{type(self).__name__}.{func.__name__}"
        bound_args = {f"arg{i}": _summarize(a) for i, a in enumerate(args)}
        bound_args.update({k: _summarize(v) for k, v in kwargs.items()})
        start = time.monotonic()
        try:
            result = func(self, *args, **kwargs)
        except Exception as exc:
            duration_ms = round((time.monotonic() - start) * 1000, 1)
            error: dict[str, object] = {"type": type(exc).__name__, "message": str(exc)}
            if isinstance(exc, subprocess.CalledProcessError):
                error["cmd"] = exc.cmd
                error["returncode"] = exc.returncode
                error["stderr"] = exc.stderr
            logger.error(event, **bound_args, duration_ms=duration_ms, outcome="error", error=error)
            raise
        duration_ms = round((time.monotonic() - start) * 1000, 1)
        logger.info(event, **bound_args, duration_ms=duration_ms, outcome="success")
        return result

    return cast("F", wrapper)
