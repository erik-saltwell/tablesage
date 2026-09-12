"""Reproducible per-case evidence for recap baseline and selected-candidate evaluations."""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from prompt_model import Metric
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model.helpers import acomplete
from prompt_model.observation import MetricsEvaluatedEvent, OptimizationCompletedEvent, OptimizationFailedEvent, TargetGeneratedEvent
from pydantic import BaseModel

from .recap_summary_scorer import RecapSummaryGatedScorer, RecapSummarySearchScorer


class RecapRunObserver:
    """Append every search output and assessment, including events preceding a failure."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def _record(self, kind: str, event: BaseModel) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"event": kind, **event.model_dump(mode="json")}, ensure_ascii=False) + "\n")

    async def on_target_generated(self, event: TargetGeneratedEvent) -> None:
        self._record("target_generated", event)

    async def on_metrics_evaluated(self, event: MetricsEvaluatedEvent) -> None:
        self._record("metrics_evaluated", event)

    async def on_optimization_completed(self, event: OptimizationCompletedEvent) -> None:
        self._record("completed", event)

    async def on_optimization_failed(self, event: OptimizationFailedEvent) -> None:
        self._record("failed", event)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


async def evaluate_recap(
    prompt: str,
    cases: list[EvalCase],
    target: LiteLLMConfig,
    metrics: Sequence[Metric],
    alignment_threshold: float,
    directory: Path,
) -> dict[str, Any]:
    """Save each target output before judging, retaining partial evidence on failure."""
    if not cases:
        raise ValueError("Evaluation requires at least one case.")
    strict = RecapSummaryGatedScorer(alignment_threshold=alignment_threshold)
    search = RecapSummarySearchScorer(alignment_threshold=alignment_threshold)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "prompt.md").write_text(prompt, encoding="utf-8")
    rows: list[dict[str, Any]] = []
    report: dict[str, Any] = {"status": "running", "cases": rows}
    write_json(directory / "report.json", report)
    try:
        for case in cases:
            assert case.source_path is not None
            name = Path(case.source_path).stem
            report["current_case"] = case.source_path
            (directory / f"{name}.input.txt").write_text(case.input, encoding="utf-8")
            write_json(directory / "report.json", report)
            output = await acomplete(prompt, case.input, target)
            (directory / f"{name}.md").write_text(output, encoding="utf-8")
            results = []
            row: dict[str, Any] = {"source_path": case.source_path, "metrics": []}
            rows.append(row)
            for metric in metrics:
                result = await metric.evaluate(prompt, case, output)
                results.append(result)
                row["metrics"].append(result.model_dump(mode="json"))
                write_json(directory / "report.json", report)
            row.update(strict_score=strict.compute(results), search_score=search.compute(results))
            row["accepted"] = row["strict_score"] > 0
            write_json(directory / "report.json", report)
        report.update(
            status="complete",
            accepted=all(row["accepted"] for row in rows),
            mean_strict_score=sum(row["strict_score"] for row in rows) / len(rows),
            mean_search_score=sum(row["search_score"] for row in rows) / len(rows),
            worst_search_score=min(row["search_score"] for row in rows),
        )
        report.pop("current_case", None)
    except BaseException as exc:
        report.update(status="failed", error_type=type(exc).__name__, error=str(exc))
        write_json(directory / "report.json", report)
        raise
    write_json(directory / "report.json", report)
    return report
