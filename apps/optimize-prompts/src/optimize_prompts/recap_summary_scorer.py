"""Gated scoring policy for Recap Summary optimization."""

from __future__ import annotations

from collections.abc import Iterable

from prompt_model import MetricResult


class RecapSummaryGatedScorer:
    """Apply content gates before measuring length against an output budget."""

    _REQUIRED = frozenset(
        {
            "recap_summary_format",
            "recap_summary_coverage",
            "recap_summary_recognition",
            "recap_summary_exclusion",
            "recap_summary_alignment",
            "recap_summary_conciseness",
        }
    )

    def __init__(self, *, alignment_threshold: float = 1.0) -> None:
        if not 0.0 <= alignment_threshold <= 1.0:
            raise ValueError("alignment_threshold must be between 0 and 1.")
        self.alignment_threshold = alignment_threshold

    def compute(self, results: list[MetricResult]) -> float:
        by_name = self._index(results)
        if by_name["recap_summary_format"].score < 1.0:
            return 0.0
        if by_name["recap_summary_coverage"].score < 1.0:
            return 0.0
        if by_name["recap_summary_recognition"].score < 1.0:
            return 0.0
        if by_name["recap_summary_exclusion"].score < 1.0:
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


class RecapSummarySearchScorer(RecapSummaryGatedScorer):
    """Give search a gradient while keeping every accepted result above rejected ones."""

    def compute(self, results: list[MetricResult]) -> float:
        by_name = self._index(results)
        content = [by_name[f"recap_summary_{name}"].score for name in ("format", "coverage", "recognition", "exclusion")]
        alignment = by_name["recap_summary_alignment"].score
        content.append(min(1.0, alignment / self.alignment_threshold) if self.alignment_threshold else 1.0)
        if all(value == 1.0 for value in content) and by_name["recap_summary_conciseness"].score > 0:
            return 0.8 + 0.2 * by_name["recap_summary_conciseness"].score
        # Length earns nothing until content passes; over-limit outputs remain rejected.
        return 0.79 * sum(content) / len(content)
