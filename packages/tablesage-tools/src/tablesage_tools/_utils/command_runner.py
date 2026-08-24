from __future__ import annotations

import asyncio
import subprocess

import widelog


def _record_failure(cmd: list[str], returncode: int, stderr: str) -> None:
    """Attach the failing command's stderr to whatever wide event is currently open.

    widelog's automatic error capture only stringifies the raised exception, and
    `CalledProcessError.__str__` drops stderr entirely -- attaching it as a field here
    is the only way it ends up in the log. Outside an open `wide_event`, `use_logger()`
    returns a standalone logger that emits this immediately, so a failure is never lost
    even when this runs outside session_pipeline/voice_clips' instrumented calls.
    """
    widelog.use_logger().set(cmd=cmd, returncode=returncode, stderr=stderr)


def run_command(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command and raise if it fails."""
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        _record_failure(cmd, exc.returncode, exc.stderr)
        raise
    return result if capture_output else subprocess.CompletedProcess(cmd, result.returncode, None, None)


async def run_command_async(cmd: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run a shell command asynchronously and raise if it fails.

    Always pipes stdout/stderr internally, regardless of *capture_output* -- inheriting the
    parent's stdio would leak straight into the running TUI's terminal (Textual owns it),
    and captured stderr is what makes a failure debuggable at all (see `_record_failure`
    below). *capture_output* only controls whether a *successful* call's stdout/stderr come
    back non-`None`, matching prior behavior for callers (e.g. `measure_loudness`) that parse
    them.
    """
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout_bytes, stderr_bytes = await process.communicate()
    assert process.returncode is not None

    stdout_text = stdout_bytes.decode(errors="replace")
    stderr_text = stderr_bytes.decode(errors="replace")

    if process.returncode != 0:
        _record_failure(cmd, process.returncode, stderr_text)
        raise subprocess.CalledProcessError(process.returncode, cmd, output=stdout_text, stderr=stderr_text)

    return subprocess.CompletedProcess(
        cmd,
        process.returncode,
        stdout_text if capture_output else None,
        stderr_text if capture_output else None,
    )
