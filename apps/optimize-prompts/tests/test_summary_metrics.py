import asyncio
from pathlib import Path

import pytest
from optimize_prompts.summary_metrics import (
    SummaryConcisenessMetric,
    SummaryInputError,
    build_summary_metrics,
    extract_session_ledger,
)
from prompt_model.config import EvalCase, LiteLLMConfig

_INPUT = """<session_metadata>
Campaign: Brandonsford
</session_metadata>

<session_ledger>
{"preamble": null, "utterances": [{"type": "narration", "fact": "The bridge collapses."}]}
</session_ledger>
"""

_ALL_SECTIONS = """## The Party
- None.

## Starting Situation
- None.

## Scene Breakdown
- None.

## Key Decisions & Events
- None.

## Ending Situation
- None.

## Open Loops
- None.

## Clocks
- None.
"""


def test_extract_session_ledger_uses_only_the_ledger_block() -> None:
    assert extract_session_ledger(_INPUT).startswith('{"preamble"')


def test_extract_session_ledger_rejects_content_after_the_ledger() -> None:
    with pytest.raises(SummaryInputError, match="Unexpected content"):
        extract_session_ledger(_INPUT + "\n<extra>not Ledger content</extra>")


def test_conciseness_uses_ledger_not_prompt_scaffolding() -> None:
    metric = SummaryConcisenessMetric()

    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT), "The bridge collapses."))

    ledger_words = len(extract_session_ledger(_INPUT).split())
    assert result.score == pytest.approx((ledger_words - 3) / ledger_words)


def test_section_metric_requires_all_sections_in_order(tmp_path: Path) -> None:
    metrics = build_summary_metrics(
        judge_llm=LiteLLMConfig(model="fake/model"),
        coverage_question_directory=tmp_path,
    )

    result = asyncio.run(metrics[-1].evaluate("# Prompt", EvalCase(input=_INPUT), _ALL_SECTIONS))

    assert result.metric_name == "summary_section_structure"
    assert result.score == 1.0
