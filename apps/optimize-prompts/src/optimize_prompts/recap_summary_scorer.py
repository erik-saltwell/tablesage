"""Gated scoring policy for Recap Summary optimization."""

from __future__ import annotations

from collections.abc import Iterable

from prompt_model import MetricResult


class RecapSummaryGatedScorer:
    """Rank only valid, complete, Ledger-aligned recaps by compression."""

    _REQUIRED = frozenset(
        {
            "recap_summary_format",
            "recap_summary_coverage",
            "recap_summary_alignment",
            "recap_summary_conciseness",
        }
    )

    def __init__(self, *, alignment_threshold: float = 0.95) -> None:
        if not 0.0 <= alignment_threshold <= 1.0:
            raise ValueError("alignment_threshold must be between 0 and 1.")
        self.alignment_threshold = alignment_threshold

    def compute(self, results: list[MetricResult]) -> float:
        by_name = self._index(results)
        if by_name["recap_summary_format"].score < 1.0:
            return 0.0
        if by_name["recap_summary_coverage"].score < 1.0:
            return 0.0
        if by_name["recap_summary_alignment"].score < self.alignment_threshold:
            return 0.0
        return by_name["recap_summary_conciseness"].score

    @classmethod
    def _index(cls, results: Iterable[MetricResult]) -> dict[str, MetricResult]:
        by_name: dict[str, MetricResult] = {}
        for result in results:
            if result.metric_name not in cls._REQUIRED:
                raise ValueError(f"Unexpected Recap Summary metric {result.metric_name!r}.")
            if result.metric_name in by_name:
                raise ValueError(f"Duplicate Recap Summary metric {result.metric_name!r}.")
            by_name[result.metric_name] = result
        missing = cls._REQUIRED - by_name.keys()
        if missing:
            raise ValueError(f"Missing Recap Summary metrics: {', '.join(sorted(missing))}.")
        return by_name
