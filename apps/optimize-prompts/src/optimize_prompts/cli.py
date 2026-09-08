"""Typer commands for prompt-optimization workflows."""

from pathlib import Path

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


@app.command()
def ledger(run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration.")) -> None:
    """Start the Ledger prompt-optimization workflow."""
    console.print(
        Panel(
            "Ledger optimization workflow is ready for its Prompt Forge configuration.",
            title="Ledger",
            border_style="cyan",
        )
    )
    optimize_ledger(Path("data_prompts/ledger"), console, run=run)


@app.command()
def summary(run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration.")) -> None:
    """Start the summary prompt-optimization workflow."""
    console.print(
        Panel(
            "Summary optimization workflow is ready for its Prompt Forge configuration.",
            title="Summary",
            border_style="cyan",
        )
    )
    optimize_summary(Path("data_prompts/summary"), console, run=run)


@app.command("recap-summary")
def recap_summary(run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration.")) -> None:
    """Start the Recap Summary prompt-optimization workflow."""
    console.print(
        Panel(
            "Recap Summary optimization favors the shortest fully supported recap.",
            title="Recap Summary",
            border_style="cyan",
        )
    )
    optimize_recap_summary(Path("data_prompts/recap_summary"), console, run=run)


@app.command("section-transcript")
def section_transcript(
    run: bool = typer.Option(False, help="Run optimization instead of only validating its configuration."),
    cross_validate: bool = typer.Option(False, help="Run three two-session training and one-session holdout rotations."),
) -> None:
    """Start the transcript-sectioning prompt-optimization workflow."""
    console.print(
        Panel(
            "Transcript-sectioning optimization uses reviewed routing ranges as deterministic ground truth.",
            title="Transcript Sectioning",
            border_style="cyan",
        )
    )
    optimize_section_transcript(Path("data_prompts/section_transcript"), console, run=run, cross_validate=cross_validate)
