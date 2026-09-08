import asyncio

import pytest
from optimize_prompts.sectioning_metrics import (
    SectioningMetricInputError,
    TranscriptSectioningMetric,
    _range_score,
    _section_node_ids,
    _session_start_score,
)
from prompt_model.config import EvalCase
from tablesage_application.session_pipeline.transcript_sections import InclusiveUtteranceRange, TranscriptSections


def _range(start: int, end: int) -> InclusiveUtteranceRange:
    return InclusiveUtteranceRange(start_index=start, end_index=end)


_INPUT = """<session_attendees>
- Alice: Zaria
</session_attendees>

<role_transcript>
{"utterances":[
  {"index":0,"speaker":"GM","text":"Previously, the tower fell."},
  {"index":1,"speaker":"GM","text":"Rain falls over the river."},
  {"index":2,"speaker":"Zaria","text":"I light a fire."},
  {"index":3,"speaker":"Zaria","text":"I inspect the ruined tower."}
]}
</role_transcript>
"""

_ROUTING_PROMPT = """# Routing Rules

## Session Start Index

Choose the first active-play utterance.

## Recap Range

Choose the smallest opening recap.

## Starting Context Range

Choose the minimum current situation.

## Introduction Range

Choose qualifying introductions only.
"""


def _case() -> EvalCase:
    ground_truth = TranscriptSections(
        role_transcript_sha256="0" * 64,
        recap_range=_range(0, 0),
        introduction_range=None,
        starting_context_range=_range(1, 1),
        session_start_index=1,
    )
    return EvalCase(input=_INPUT, ground_truth=ground_truth.model_dump_json(), source_path="case.txt")


def _output(**updates: object) -> str:
    values: dict[str, object] = {
        "scratchpad": "Reviewed opening structure.",
        "recap_range": {"start_index": 0, "end_index": 0},
        "introduction_range": None,
        "starting_context_range": {"start_index": 1, "end_index": 1},
        "session_start_index": 1,
    }
    values.update(updates)
    import json

    return json.dumps(values)


def test_exact_range_scores_one() -> None:
    assert _range_score(_range(2, 4), _range(2, 4)) == 1.0


def test_omitted_range_boundary_is_penalized_more_than_extra_boundary() -> None:
    assert _range_score(_range(2, 4), _range(3, 4)) == pytest.approx(0.90)
    assert _range_score(_range(2, 4), _range(1, 4)) == pytest.approx(0.975)


def test_false_range_uses_destructive_width_curve() -> None:
    assert _range_score(None, _range(1, 1)) == pytest.approx(0.50)
    assert _range_score(None, _range(1, 3)) == 0.0


def test_session_start_penalty_is_asymmetric_and_exponential() -> None:
    assert _session_start_score(5, 7) == pytest.approx(0.70)
    assert _session_start_score(5, 3) == pytest.approx(0.925)


def test_metric_scores_exact_routing_perfectly() -> None:
    result = asyncio.run(TranscriptSectioningMetric().evaluate("# Prompt", _case(), _output()))

    assert result.score == 1.0
    assert "span_f1" in result.assessment


def test_missing_required_starting_context_zeros_the_case() -> None:
    result = asyncio.run(TranscriptSectioningMetric().evaluate("# Prompt", _case(), _output(starting_context_range=None)))

    assert result.score == 0.0
    assert "cannot continue" in result.assessment


def test_component_failures_emit_distinct_signals_targeted_at_current_headings() -> None:
    result = asyncio.run(
        TranscriptSectioningMetric().evaluate(
            _ROUTING_PROMPT,
            _case(),
            _output(
                recap_range=None,
                introduction_range={"start_index": 0, "end_index": 0},
                starting_context_range={"start_index": 1, "end_index": 2},
                session_start_index=2,
            ),
        )
    )

    node_ids = _section_node_ids(_ROUTING_PROMPT)

    assert len(result.signals) == 4
    assert {signal.culprit_node_id for signal in result.signals} == set(node_ids.values())
    assert {signal.target_behavior for signal in result.signals} == {
        "Identify the smallest opening recap range without omitting prior-session evidence.",
        "Identify only qualifying attendee-mapped player-character introductions.",
        "Identify the minimum range that directly establishes the immediate starting situation.",
        "Choose the earliest defensible index at which active play begins.",
    }


def test_missing_routing_heading_falls_back_to_document_signal() -> None:
    result = asyncio.run(
        TranscriptSectioningMetric().evaluate(
            "# Minimal prompt\n",
            _case(),
            _output(recap_range=None),
        )
    )

    assert [signal.culprit_node_id for signal in result.signals] == ["document"]


def test_structurally_invalid_output_zeros_the_case() -> None:
    result = asyncio.run(TranscriptSectioningMetric().evaluate("# Prompt", _case(), "not json"))

    assert result.score == 0.0
    assert "Invalid" in result.assessment
    assert [signal.culprit_node_id for signal in result.signals] == ["document"]


def test_missing_golden_sections_is_a_configuration_error() -> None:
    with pytest.raises(SectioningMetricInputError, match="golden"):
        asyncio.run(TranscriptSectioningMetric().evaluate("# Prompt", EvalCase(input=_INPUT), _output()))
