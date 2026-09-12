import json
from pathlib import Path

from optimize_prompts.winner_output import report_interruption, resolve_seed_prompt, save_checkpoint, save_winner
from rich.console import Console


def test_save_winner_writes_prompt_and_selection_metadata(tmp_path: Path) -> None:
    prompt_path = save_winner(
        tmp_path / "outputs",
        "# Optimized sectioning prompt\n",
        {"mode": "cross_validation", "held_out_case": "001.txt", "held_out_result": {"score": 0.8}},
    )

    assert prompt_path.read_text(encoding="utf-8") == "# Optimized sectioning prompt\n"
    metadata = json.loads((tmp_path / "outputs" / "best_prompt_result.json").read_text(encoding="utf-8"))
    assert metadata["held_out_case"] == "001.txt"
    assert metadata["held_out_result"]["score"] == 0.8


def test_save_checkpoint_writes_prompt(tmp_path: Path) -> None:
    checkpoint_path = save_checkpoint(tmp_path / "outputs", "# Checkpointed prompt")

    assert checkpoint_path == tmp_path / "outputs" / "checkpoint.md"
    assert checkpoint_path.read_text(encoding="utf-8") == "# Checkpointed prompt\n"


def test_resolve_seed_prompt_without_resume_reads_seed_file(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed_prompt.txt"
    seed_path.write_text("seed text", encoding="utf-8")
    save_checkpoint(tmp_path / "outputs", "checkpoint text")

    seed_prompt = resolve_seed_prompt(seed_path, tmp_path / "outputs", resume=False, console=Console())

    assert seed_prompt == "seed text"


def test_resolve_seed_prompt_with_resume_reads_checkpoint_when_present(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed_prompt.txt"
    seed_path.write_text("seed text", encoding="utf-8")
    save_checkpoint(tmp_path / "outputs", "checkpoint text")

    seed_prompt = resolve_seed_prompt(seed_path, tmp_path / "outputs", resume=True, console=Console())

    assert seed_prompt == "checkpoint text\n"


def test_resolve_seed_prompt_with_resume_falls_back_to_seed_file_when_no_checkpoint(tmp_path: Path) -> None:
    seed_path = tmp_path / "seed_prompt.txt"
    seed_path.write_text("seed text", encoding="utf-8")

    seed_prompt = resolve_seed_prompt(seed_path, tmp_path / "outputs", resume=True, console=Console())

    assert seed_prompt == "seed text"


def test_report_interruption_does_not_raise_with_or_without_checkpoint(tmp_path: Path) -> None:
    console = Console()
    report_interruption(RuntimeError("boom"), tmp_path / "outputs", console, title="Example")

    save_checkpoint(tmp_path / "outputs", "checkpoint text")
    report_interruption(RuntimeError("boom"), tmp_path / "outputs", console, title="Example")
