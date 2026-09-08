import asyncio

import pytest
from optimize_prompts.recap_summary_metrics import (
    RecapSummaryConcisenessMetric,
    RecapSummaryFormatMetric,
    RecapSummaryInputError,
    extract_session_ledger,
)
from optimize_prompts.recap_summary_scorer import RecapSummaryGatedScorer
from prompt_model import MetricResult
from prompt_model.config import EvalCase

_INPUT = """<session_metadata>
Campaign: Brandonsford
</session_metadata>

<session_ledger>
{"preamble": null, "utterances": [{"type": "narration", "fact": "The bridge collapses."}]}
</session_ledger>
"""


def _result(name: str, score: float) -> MetricResult:
    return MetricResult(metric_name=name, score=score, assessment="test")


def _passing_results() -> list[MetricResult]:
    return [
        _result("recap_summary_format", 1.0),
        _result("recap_summary_coverage", 1.0),
        _result("recap_summary_alignment", 0.96),
        _result("recap_summary_conciseness", 0.8),
    ]


def test_extract_session_ledger_uses_only_ledger() -> None:
    assert extract_session_ledger(_INPUT).startswith('{"preamble"')


def test_extract_session_ledger_rejects_trailing_content() -> None:
    with pytest.raises(RecapSummaryInputError, match="Unexpected content"):
        extract_session_ledger(_INPUT + "\n<extra>not ledger</extra>")


def test_conciseness_uses_ledger_not_prompt_scaffolding() -> None:
    metric = RecapSummaryConcisenessMetric()
    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT), "- The bridge collapses."))
    ledger_words = len(extract_session_ledger(_INPUT).split())
    assert result.score == pytest.approx((ledger_words - 4) / ledger_words)


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("- The bridge collapses.\n- The party escapes.", 1.0),
        ("## Recap\n\n- The bridge collapses.", 0.0),
        ("- The bridge collapses.\n  - The party escapes.", 0.0),
        ("```markdown\n- The bridge collapses.\n```", 0.0),
        ("", 0.0),
    ],
)
def test_format_metric_accepts_only_flat_bullets(output: str, expected: float) -> None:
    result = asyncio.run(RecapSummaryFormatMetric().evaluate("# Prompt", EvalCase(input=_INPUT), output))
    assert result.score == expected


@pytest.mark.parametrize("failed_metric", ["recap_summary_format", "recap_summary_coverage", "recap_summary_alignment"])
def test_gated_scorer_returns_zero_when_any_gate_fails(failed_metric: str) -> None:
    results = _passing_results()
    for result in results:
        if result.metric_name == failed_metric:
            result.score = 0.94 if failed_metric == "recap_summary_alignment" else 0.0
    assert RecapSummaryGatedScorer().compute(results) == 0.0


def test_gated_scorer_returns_conciseness_after_all_gates_pass() -> None:
    assert RecapSummaryGatedScorer().compute(_passing_results()) == 0.8


def test_gated_scorer_rejects_missing_or_duplicate_results() -> None:
    with pytest.raises(ValueError, match="Missing"):
        RecapSummaryGatedScorer().compute(_passing_results()[:-1])
    with pytest.raises(ValueError, match="Duplicate"):
        RecapSummaryGatedScorer().compute(_passing_results() + [_result("recap_summary_format", 1.0)])
