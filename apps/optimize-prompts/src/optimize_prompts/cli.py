"""Typer commands for prompt-optimization workflows."""

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from .optimize_ledger import optimize_ledger
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
