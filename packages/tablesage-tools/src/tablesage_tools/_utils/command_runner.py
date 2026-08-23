from __future__ import annotations

import asyncio
import subprocess
import time

import structlog

logger = structlog.get_logger(__name__)


def run_command(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command and raise if it fails."""
    start = time.monotonic()
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        logger.error(
            "tool.run_command",
            cmd=cmd,
            returncode=exc.returncode,
            duration_ms=round((time.monotonic() - start) * 1000, 1),
            outcome="error",
            stderr=exc.stderr,
        )
        raise
    duration_ms = round((time.monotonic() - start) * 1000, 1)
    logger.info("tool.run_command", cmd=cmd, returncode=result.returncode, duration_ms=duration_ms, outcome="success")
    return result if capture_output else subprocess.CompletedProcess(cmd, result.returncode, None, None)


async def run_command_async(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command asynchronously and raise if it fails.

    Always pipes stdout/stderr internally, regardless of *capture_output* -- inheriting the
    parent's stdio would leak straight into the running TUI's terminal (Textual owns it),
    and captured stderr is what makes a failure debuggable at all (see the raised
    `CalledProcessError` below, and the wide event this logs either way). *capture_output*
    only controls whether a *successful* call's stdout/stderr come back non-`None`, matching
    prior behavior for callers (e.g. `measure_loudness`) that parse them.
    """
    start = time.monotonic()
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    assert process.returncode is not None
    duration_ms = round((time.monotonic() - start) * 1000, 1)

    stdout_text = stdout_bytes.decode(errors="replace")
    stderr_text = stderr_bytes.decode(errors="replace")

    if process.returncode != 0:
        logger.error(
            "tool.run_command",
            cmd=cmd,
            returncode=process.returncode,
            duration_ms=duration_ms,
            outcome="error",
            stderr=stderr_text,
        )
        raise subprocess.CalledProcessError(process.returncode, cmd, output=stdout_text, stderr=stderr_text)

    logger.info("tool.run_command", cmd=cmd, returncode=0, duration_ms=duration_ms, outcome="success")

    return subprocess.CompletedProcess(
        cmd,
        process.returncode,
        stdout_text if capture_output else None,
        stderr_text if capture_output else None,
    )
