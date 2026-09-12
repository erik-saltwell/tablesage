from __future__ import annotations

import asyncio
import json
import shutil
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from optimize_prompts import optimize_recap_summary as workflow
from optimize_prompts import recap_evaluation as evaluation
from optimize_prompts.recap_summary_scorer import RecapSummaryGatedScorer, RecapSummarySearchScorer
from prompt_model import MetricResult, OptimizationResult
from prompt_model.config import EvalCase, LiteLLMConfig
from rich.console import Console


def results(coverage: float = 1, length: float = 1) -> list[MetricResult]:
    return [
        MetricResult(
            metric_name=f"recap_summary_{name}",
            score=coverage if name == "coverage" else length if name == "conciseness" else 1,
            assessment="test",
        )
        for name in ("format", "coverage", "recognition", "exclusion", "alignment", "conciseness")
    ]


def test_search_rewards_repairs_without_relaxing_acceptance() -> None:
    search, strict = RecapSummarySearchScorer(), RecapSummaryGatedScorer()
    assert 0 < search.compute(results(0.5)) < search.compute(results(0.9)) < search.compute(results(1, 0.75))
    assert search.compute(results(0.9, 1)) == search.compute(results(0.9, 0.75))
    assert search.compute(results(1, 0)) < search.compute(results(1, 0.75))
    assert strict.compute(results(0.9)) == 0


def fake_metrics() -> list[AsyncMock]:
    return [AsyncMock(evaluate=AsyncMock(return_value=result)) for result in results()]


def test_evaluation_saves_outputs_and_strict_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evaluation, "acomplete", AsyncMock(return_value="- A recap."))
    report = asyncio.run(
        evaluation.evaluate_recap(
            "# Prompt", [EvalCase(input="source", source_path="one.txt")], LiteLLMConfig(model="test"), fake_metrics(), 1, tmp_path
        )
    )
    assert report["accepted"] is True
    assert (tmp_path / "one.md").read_text() == "- A recap."
    assert len(json.loads((tmp_path / "report.json").read_text())["cases"][0]["metrics"]) == 6


def test_judge_failure_preserves_raw_output_and_partial_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evaluation, "acomplete", AsyncMock(return_value="- A recap."))
    metrics = fake_metrics()
    metrics[1].evaluate.side_effect = RuntimeError("judge unavailable")
    with pytest.raises(RuntimeError, match="judge unavailable"):
        asyncio.run(
            evaluation.evaluate_recap(
                "# Prompt", [EvalCase(input="source", source_path="one.txt")], LiteLLMConfig(model="test"), metrics, 1, tmp_path
            )
        )
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "failed"
    assert len(report["cases"][0]["metrics"]) == 1
    assert (tmp_path / "one.md").is_file()


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    source = Path(__file__).resolve().parents[3] / "data_prompts/recap_summary"
    for name in ("inputs", "coverage_questions", "recognition_questions", "exclusion_questions"):
        shutil.copytree(source / name, tmp_path / name)
    for name in ("seed_prompt.txt", "settings.yaml"):
        shutil.copy2(source / name, tmp_path / name)
    return tmp_path


def test_run_uses_progress_score_and_validates_selected_prompt(corpus: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evaluation, "acomplete", AsyncMock(return_value="- A recap."))
    monkeypatch.setattr(workflow, "build_recap_summary_metrics", lambda **kwargs: fake_metrics())
    selected = "# Improved prompt\nReturn bullets."
    optimizer = AsyncMock(return_value=OptimizationResult(best_prompt=selected, best_score=1, iterations_run=1))
    monkeypatch.setattr(workflow, "optimize_prompt", optimizer)
    workflow.optimize_recap_summary(corpus, Console(quiet=True), run=True, iterations=1)
    assert isinstance(optimizer.call_args.kwargs["scorer"], RecapSummarySearchScorer)
    metadata = json.loads((corpus / "outputs/best_prompt_result.json").read_text())
    assert metadata["validation"]["accepted"] is True
    assert len(metadata["baseline"]["cases"]) == len(metadata["validation"]["cases"]) == 3
    assert (corpus / "outputs/checkpoint.md").read_text().strip() == selected
    # A changed question set must not silently reuse a checkpoint from a different objective.
    path = corpus / "recognition_questions/Brandonsford_001.json"
    path.write_text(path.read_text() + "\n")
    with pytest.raises(ValueError, match="Checkpoint inputs"):
        workflow.optimize_recap_summary(corpus, Console(quiet=True), run=True, resume=True, iterations=1)
    assert optimizer.await_count == 1


def test_evaluate_does_not_search_or_replace_winner(corpus: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evaluation, "acomplete", AsyncMock(return_value="- A recap."))
    monkeypatch.setattr(workflow, "build_recap_summary_metrics", lambda **kwargs: fake_metrics())
    optimizer = AsyncMock()
    monkeypatch.setattr(workflow, "optimize_prompt", optimizer)
    workflow.optimize_recap_summary(corpus, Console(quiet=True), evaluate=True, case_name="Brandonsford_001.txt")
    optimizer.assert_not_called()
    assert not (corpus / "outputs/best_prompt.md").exists()
    report = next((corpus / "outputs/runs").glob("*/evaluation/report.json"))
    assert len(json.loads(report.read_text())["cases"]) == 1


def test_rejected_candidate_does_not_replace_existing_winner(corpus: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(evaluation, "acomplete", AsyncMock(return_value="- A recap."))
    failed = [AsyncMock(evaluate=AsyncMock(return_value=result)) for result in results(0.9)]
    monkeypatch.setattr(workflow, "build_recap_summary_metrics", lambda **kwargs: failed)
    monkeypatch.setattr(
        workflow, "optimize_prompt", AsyncMock(return_value=OptimizationResult(best_prompt="# Candidate", best_score=0.7, iterations_run=1))
    )
    (corpus / "outputs").mkdir()
    winner = corpus / "outputs/best_prompt.md"
    winner.write_text("Existing accepted winner")
    workflow.optimize_recap_summary(corpus, Console(quiet=True), run=True, iterations=1)
    assert winner.read_text() == "Existing accepted winner"
    result = next((corpus / "outputs/runs").glob("*/best_prompt_result.json"))
    assert json.loads(result.read_text())["accepted"] is False


@pytest.mark.parametrize("kwargs", [{"resume": True}, {"run": True, "evaluate": True}, {"case_name": "one.txt"}, {"iterations": 1}])
def test_invalid_execution_modes_fail_before_calls(corpus: Path, kwargs: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        workflow.optimize_recap_summary(corpus, Console(quiet=True), **kwargs)
