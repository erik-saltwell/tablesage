from optimize_prompts.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_ledger_command() -> None:
    result = runner.invoke(app, ["ledger"])

    assert result.exit_code == 0
    assert "Ledger" in result.output


def test_summary_command() -> None:
    result = runner.invoke(app, ["summary"])

    assert result.exit_code == 0
    assert "Summary" in result.output
