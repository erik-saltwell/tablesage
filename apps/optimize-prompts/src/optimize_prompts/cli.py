"""Typer commands for prompt-optimization workflows."""

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(
    name="optimize-prompts",
    help="Optimize TableSage prompts with Prompt Forge.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def ledger() -> None:
    """Start the Ledger prompt-optimization workflow."""
    console.print(
        Panel(
            "Ledger optimization workflow is ready for its Prompt Forge configuration.",
            title="Ledger",
            border_style="cyan",
        )
    )


@app.command()
def summary() -> None:
    """Start the summary prompt-optimization workflow."""
    console.print(
        Panel(
            "Summary optimization workflow is ready for its Prompt Forge configuration.",
            title="Summary",
            border_style="cyan",
        )
    )
