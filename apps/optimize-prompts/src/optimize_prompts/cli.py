"""Typer commands for prompt-optimization workflows."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from .optimize_ledger import optimize_ledger
from .optimize_recap_summary import optimize_recap_summary
from .optimize_section_transcript import optimize_section_transcript
from .optimize_summary import optimize_summary

app = typer.Typer(
    name="optimize-prompts",
    help="Optimize TableSage prompts with Prompt Forge.",
    no_args_is_help=True,
)
console = Console()

_RESUME_HELP = "Continue from outputs/checkpoint.md (the best prompt found before the last run stopped) instead of seed_prompt.txt."


@app.command()
def ledger(
    run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration."),
    resume: bool = typer.Option(False, help=_RESUME_HELP),
) -> None:
    """Start the Ledger prompt-optimization workflow."""
    console.print(
        Panel(
            "Ledger optimization workflow is ready for its Prompt Forge configuration.",
            title="Ledger",
            border_style="cyan",
        )
    )
    optimize_ledger(Path("prompt_optimization/ledger"), console, run=run, resume=resume)


@app.command()
def summary(
    run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration."),
    resume: bool = typer.Option(False, help=_RESUME_HELP),
) -> None:
    """Start the summary prompt-optimization workflow."""
    console.print(
        Panel(
            "Summary optimization workflow is ready for its Prompt Forge configuration.",
            title="Summary",
            border_style="cyan",
        )
    )
    optimize_summary(Path("prompt_optimization/summary"), console, run=run, resume=resume)


@app.command("recap-summary")
def recap_summary(
    run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration."),
    resume: bool = typer.Option(False, help=_RESUME_HELP),
    evaluate: bool = typer.Option(False, help="Generate and score a baseline without searching."),
    case: str | None = typer.Option(None, help="Exact input filename for --evaluate only."),
    prompt: Annotated[Path | None, typer.Option(help="System prompt file to score with --evaluate; defaults to the seed.")] = None,
    iterations: int | None = typer.Option(None, min=1, help="Override iteration count for --run."),
) -> None:
    """Start the Recap Summary prompt-optimization workflow."""
    console.print(
        Panel(
            "Recap Summary optimization preserves essential facts and recognition cues within a short read-aloud budget.",
            title="Recap Summary",
            border_style="cyan",
        )
    )
    optimize_recap_summary(
        Path("prompt_optimization/recap_summary"),
        console,
        run=run,
        resume=resume,
        evaluate=evaluate,
        case_name=case,
        prompt_path=prompt,
        iterations=iterations,
    )


@app.command("section-transcript")
def section_transcript(
    run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration."),
    resume: bool = typer.Option(False, help=_RESUME_HELP + " Applies only to the default full-corpus run."),
    cross_validate: bool = typer.Option(False, help="Run leave-one-case-out training and holdout rotations."),
    holdout_prefix: str | None = typer.Option(
        None,
        help="Optimize on cases outside this source-name prefix, then score matching cases as a group holdout.",
    ),
) -> None:
    """Start the transcript-sectioning prompt-optimization workflow."""
    console.print(
        Panel(
            "Transcript-sectioning optimization uses reviewed routing ranges as deterministic ground truth.",
            title="Transcript Sectioning",
            border_style="cyan",
        )
    )
    optimize_section_transcript(
        Path("prompt_optimization/section_transcript"),
        console,
        run=run,
        resume=resume,
        cross_validate=cross_validate,
        holdout_prefix=holdout_prefix,
    )
