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


def test_recap_command_validates_corpus_without_running_optimizer() -> None:
    result = runner.invoke(app, ["recap-summary"])

    assert result.exit_code == 0, result.output
    assert "3 evaluation cases and 6 metrics" in result.output
    assert "alignment gate: 1.0" in result.output


def test_section_transcript_command_is_registered() -> None:
    result = runner.invoke(app, ["section-transcript", "--help"])

    assert result.exit_code == 0
    assert "cross-validate" in result.output
