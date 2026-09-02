from __future__ import annotations

from prompt_model import MetricResult


class LedgerScorer:
    """Apply hard gates, then the agreed 50/20/20/10 weighted reward."""

    _WEIGHTS: dict[str, float] = {
        "completeness": 0.50,
        "table_talk_exclusion": 0.20,
        "mechanics_exclusion": 0.20,
        "concision": 0.10,
    }
    _GATES: tuple[str, ...] = ("schema_correctness", "no_hallucinations")

    def compute(self, results: list[MetricResult]) -> float:
        by_name: dict[str, MetricResult] = {result.metric_name: result for result in results}
        missing: list[str] = [name for name in (*self._GATES, *self._WEIGHTS) if name not in by_name]
        if missing:
            raise ValueError(f"Ledger scorer is missing metric results: {', '.join(missing)}")
        if any(by_name[name].score < 1.0 for name in self._GATES):
            return 0.0
        return sum(weight * by_name[name].score for name, weight in self._WEIGHTS.items())
