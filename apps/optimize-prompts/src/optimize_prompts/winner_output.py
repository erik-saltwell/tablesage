"""Shared helpers for persisting and resuming prompt-optimization runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

WINNING_PROMPT_FILENAME = "best_prompt.md"
WINNING_RESULT_FILENAME = "best_prompt_result.json"
CHECKPOINT_FILENAME = "checkpoint.md"


def save_winner(output_directory: Path, prompt: str, metadata: dict[str, Any]) -> Path:
    """Persist the prompt selected by an optimizer run and its selection evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    prompt_path = output_directory / WINNING_PROMPT_FILENAME
    prompt_path.write_text(prompt.rstrip() + "\n", encoding="utf-8")
    (output_directory / WINNING_RESULT_FILENAME).write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return prompt_path


def save_checkpoint(output_directory: Path, prompt: str) -> Path:
    """Write the best prompt found so far. Called after every completed iteration.

    `optimize_prompt` also fires this once more on a hard failure (an out-of-funds
    error, a transient API error, ...) before re-raising, so a mid-run crash still
    leaves the best prompt found through the last completed iteration on disk.
    """
    output_directory.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_directory / CHECKPOINT_FILENAME
    checkpoint_path.write_text(prompt.rstrip() + "\n", encoding="utf-8")
    return checkpoint_path


def checkpoint_callback(output_directory: Path, prompt: str) -> None:
    """Persist a checkpoint with the optimizer callback's void return contract."""
    save_checkpoint(output_directory, prompt)


def resolve_seed_prompt(seed_prompt_path: Path, output_directory: Path, *, resume: bool, console: Console) -> str:
    """Return the seed prompt to optimize from: a checkpoint when resuming, else the file on disk."""
    checkpoint_path = output_directory / CHECKPOINT_FILENAME
    if resume:
        if checkpoint_path.is_file():
            console.print(f"Resuming from checkpoint at {checkpoint_path}.")
            return checkpoint_path.read_text(encoding="utf-8")
        console.print(f"--resume passed but no checkpoint found at {checkpoint_path}; starting from {seed_prompt_path} instead.")
    return seed_prompt_path.read_text(encoding="utf-8")


def report_interruption(exc: BaseException, output_directory: Path, console: Console, *, title: str) -> None:
    """Print where a mid-run failure left its checkpoint, so the run can be resumed with --resume."""
    checkpoint_path = output_directory / CHECKPOINT_FILENAME
    if checkpoint_path.is_file():
        body = (
            f"{type(exc).__name__}: {exc}\n\n"
            f"Progress through the last completed iteration was saved to {checkpoint_path}.\n"
            "Rerun with --resume to continue from there instead of starting over."
        )
    else:
        body = f"{type(exc).__name__}: {exc}\n\nNo iteration completed before the failure; nothing to resume from."
    console.print(Panel(body, title=f"{title} Interrupted", border_style="red"))
