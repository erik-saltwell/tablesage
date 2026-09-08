import json
from pathlib import Path

from optimize_prompts.optimize_section_transcript import _save_winner


def test_save_winner_writes_prompt_and_selection_metadata(tmp_path: Path) -> None:
    prompt_path = _save_winner(
        tmp_path / "outputs",
        "# Optimized sectioning prompt\n",
        {"mode": "cross_validation", "held_out_case": "001.txt", "held_out_result": {"score": 0.8}},
    )

    assert prompt_path.read_text(encoding="utf-8") == "# Optimized sectioning prompt\n"
    metadata = json.loads((tmp_path / "outputs" / "best_prompt_result.json").read_text(encoding="utf-8"))
    assert metadata["held_out_case"] == "001.txt"
    assert metadata["held_out_result"]["score"] == 0.8
