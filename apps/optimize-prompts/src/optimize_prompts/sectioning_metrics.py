"""Deterministic metrics for transcript-sectioning prompt optimization."""

from __future__ import annotations

from typing import ClassVar

from prompt_model import IssueSignal, MetricResult
from prompt_model._prompt import PromptNode, Section, parse_from_string
from prompt_model.config import EvalCase
from pydantic import ValidationError
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import (
    InclusiveUtteranceRange,
    TranscriptSections,
    TranscriptSectionsGenerationResponse,
    TranscriptSectionsValidationError,
    validate_generation_response,
)

_ROLE_TRANSCRIPT_OPEN = "<role_transcript>"
_ROLE_TRANSCRIPT_CLOSE = "</role_transcript>"
_DESTRUCTIVE_COEFFICIENT = 0.10
_OVER_INCLUSION_COEFFICIENT = 0.025
_FALSE_RANGE_PENALTY = 0.40
_COMPONENT_WEIGHTS = {
    "session_start": 0.40,
    "starting_context": 0.30,
    "recap": 0.15,
    "introductions": 0.15,
}
_COMPONENT_HEADINGS = {
    "recap": "Recap Range",
    "introductions": "Introduction Range",
    "starting_context": "Starting Context Range",
    "session_start": "Session Start Index",
}
_COMPONENT_TARGET_BEHAVIORS = {
    "recap": "Identify the smallest opening recap range without omitting prior-session evidence.",
    "introductions": "Identify only qualifying attendee-mapped player-character introductions.",
    "starting_context": "Identify the minimum range that directly establishes the immediate starting situation.",
    "session_start": "Choose the earliest defensible index at which active play begins.",
}


class SectioningMetricInputError(ValueError):
    """Raised when an evaluation case has unusable input or golden sections."""


def _penalty(distance: int, coefficient: float) -> float:
    """Return the agreed cumulative exponential penalty for a non-negative distance."""
    if distance < 0:
        raise ValueError("Penalty distance must not be negative.")
    return coefficient * (2**distance - 1)


def _clamp(score: float) -> float:
    return max(0.0, min(1.0, score))


def _range_width(value: InclusiveUtteranceRange) -> int:
    return value.end_index - value.start_index + 1


def _range_f1(expected: InclusiveUtteranceRange | None, predicted: InclusiveUtteranceRange | None) -> float:
    if expected is None or predicted is None:
        return 1.0 if expected is predicted else 0.0
    expected_indices = set(range(expected.start_index, expected.end_index + 1))
    predicted_indices = set(range(predicted.start_index, predicted.end_index + 1))
    return 2 * len(expected_indices & predicted_indices) / (len(expected_indices) + len(predicted_indices))


def _range_score(expected: InclusiveUtteranceRange | None, predicted: InclusiveUtteranceRange | None) -> float:
    if expected is None:
        if predicted is None:
            return 1.0
        return _clamp(1.0 - _FALSE_RANGE_PENALTY - _penalty(_range_width(predicted), _DESTRUCTIVE_COEFFICIENT))
    if predicted is None:
        return 0.0

    penalties: list[float] = []
    if predicted.start_index > expected.start_index:
        penalties.append(_penalty(predicted.start_index - expected.start_index, _DESTRUCTIVE_COEFFICIENT))
    else:
        penalties.append(_penalty(expected.start_index - predicted.start_index, _OVER_INCLUSION_COEFFICIENT))
    if predicted.end_index < expected.end_index:
        penalties.append(_penalty(expected.end_index - predicted.end_index, _DESTRUCTIVE_COEFFICIENT))
    else:
        penalties.append(_penalty(predicted.end_index - expected.end_index, _OVER_INCLUSION_COEFFICIENT))
    return _clamp(1.0 - sum(penalties))


def _session_start_score(expected: int, predicted: int) -> float:
    if predicted > expected:
        return _clamp(1.0 - _penalty(predicted - expected, _DESTRUCTIVE_COEFFICIENT))
    return _clamp(1.0 - _penalty(expected - predicted, _OVER_INCLUSION_COEFFICIENT))


def _extract_role_transcript(rendered_input: str) -> RoleTranscript:
    if rendered_input.count(_ROLE_TRANSCRIPT_OPEN) != 1 or rendered_input.count(_ROLE_TRANSCRIPT_CLOSE) != 1:
        raise SectioningMetricInputError("Expected exactly one <role_transcript> block in a sectioning evaluation input.")
    _, after_open = rendered_input.split(_ROLE_TRANSCRIPT_OPEN, maxsplit=1)
    transcript, after_close = after_open.split(_ROLE_TRANSCRIPT_CLOSE, maxsplit=1)
    if after_close.strip():
        raise SectioningMetricInputError("Unexpected content after </role_transcript> in a sectioning evaluation input.")
    if not transcript.strip():
        raise SectioningMetricInputError("The sectioning evaluation input has an empty role transcript.")
    try:
        return RoleTranscript.model_validate_json(transcript)
    except ValidationError as exc:
        raise SectioningMetricInputError("The sectioning evaluation input has an invalid role transcript.") from exc


def _golden_response(case: EvalCase, utterance_count: int) -> TranscriptSectionsGenerationResponse:
    if case.ground_truth is None:
        raise SectioningMetricInputError("Transcript sectioning evaluation requires a golden transcript_sections.json response.")
    try:
        sections = TranscriptSections.model_validate_json(case.ground_truth)
        response = TranscriptSectionsGenerationResponse(
            scratchpad="Reviewed golden sections.",
            recap_range=sections.recap_range,
            introduction_range=sections.introduction_range,
            starting_context_range=sections.starting_context_range,
            session_start_index=sections.session_start_index,
        )
        return validate_generation_response(response, utterance_count)
    except (ValidationError, TranscriptSectionsValidationError) as exc:
        raise SectioningMetricInputError("Golden transcript sections are invalid for this evaluation transcript.") from exc


def _section_node_ids(prompt: str) -> dict[str, str]:
    """Find current prompt-tree IDs for routing-definition headings.

    IDs are assigned from tree position and can change after an actor edit, so
    metrics resolve them from the candidate prompt instead of hard-coding IDs.
    """
    headings = set(_COMPONENT_HEADINGS.values())
    found: dict[str, str] = {}

    def visit(node: PromptNode) -> None:
        if isinstance(node, Section) and node.text in headings and node.id is not None:
            found[node.text] = node.id
        for child in getattr(node, "children", ()):
            visit(child)

    try:
        document = parse_from_string(prompt)
    except Exception:  # A malformed candidate cannot be safely localized.
        return {}
    visit(document)
    return found


def _component_value(component: str, response: TranscriptSectionsGenerationResponse) -> object:
    if component == "recap":
        return response.recap_range
    if component == "introductions":
        return response.introduction_range
    if component == "starting_context":
        return response.starting_context_range
    if component == "session_start":
        return response.session_start_index
    raise ValueError(f"Unknown sectioning component: {component}")


def _display_value(value: object) -> object:
    return value.model_dump() if isinstance(value, InclusiveUtteranceRange) else value


def _component_signal(
    component: str,
    node_ids: dict[str, str],
    case: EvalCase,
    output: str,
    expected: TranscriptSectionsGenerationResponse,
    predicted: TranscriptSectionsGenerationResponse,
    component_score: float,
) -> IssueSignal:
    heading = _COMPONENT_HEADINGS[component]
    expected_value = _display_value(_component_value(component, expected))
    predicted_value = _display_value(_component_value(component, predicted))
    return IssueSignal(
        culprit_node_id=node_ids.get(heading, "document"),
        rationale=(f"{heading} scored {component_score:.4f}; expected={expected_value}; predicted={predicted_value}."),
        target_behavior=_COMPONENT_TARGET_BEHAVIORS[component],
        success_criterion=f"The generated {heading} matches the reviewed routing value for this session.",
        suggested_prompt_change=f"Clarify the rules governing {heading} boundaries and nullability.",
        input_snippet=case.input[:1000],
        output_snippet=output[:1000] or "<empty output>",
    )


class TranscriptSectioningMetric:
    """Score persisted routing decisions against manually reviewed transcript sections."""

    name: ClassVar[str] = "sectioning_routing"
    description: ClassVar[str] = "Scores opening-section ranges and active-play routing against reviewed golden sections."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        transcript = _extract_role_transcript(case.input)
        expected = _golden_response(case, len(transcript.utterances))
        try:
            predicted = TranscriptSectionsGenerationResponse.model_validate_json(output)
            predicted = validate_generation_response(predicted, len(transcript.utterances))
        except (ValidationError, TranscriptSectionsValidationError) as exc:
            return _invalid_result(case, output, str(exc))

        if expected.starting_context_range is not None and predicted.starting_context_range is None:
            return _hard_gate_result(prompt, case, output, expected, predicted)

        component_scores = {
            "recap": _range_score(expected.recap_range, predicted.recap_range),
            "introductions": _range_score(expected.introduction_range, predicted.introduction_range),
            "starting_context": _range_score(expected.starting_context_range, predicted.starting_context_range),
            "session_start": _session_start_score(expected.session_start_index, predicted.session_start_index),
        }
        score = sum(_COMPONENT_WEIGHTS[name] * component_scores[name] for name in _COMPONENT_WEIGHTS)
        f1 = {
            "recap": _range_f1(expected.recap_range, predicted.recap_range),
            "introductions": _range_f1(expected.introduction_range, predicted.introduction_range),
            "starting_context": _range_f1(expected.starting_context_range, predicted.starting_context_range),
        }
        assessment = (
            f"component_scores={component_scores}; span_f1={f1}; "
            f"expected_session_start={expected.session_start_index}; predicted_session_start={predicted.session_start_index}."
        )
        node_ids = _section_node_ids(prompt)
        signals = [
            _component_signal(component, node_ids, case, output, expected, predicted, component_score)
            for component, component_score in component_scores.items()
            if component_score < 1.0
        ]
        return MetricResult(metric_name=self.name, score=score, assessment=assessment, signals=signals)


def _signal(case: EvalCase, output: str, assessment: str) -> IssueSignal:
    return IssueSignal(
        culprit_node_id="document",
        rationale=assessment,
        target_behavior="Return routing indices that preserve all reviewed opening-section evidence and active-play content.",
        success_criterion="The generated routing values match the reviewed transcript sections without destructive omissions.",
        suggested_prompt_change="Clarify the boundary rules that correspond to the reported routing discrepancy.",
        input_snippet=case.input[:1000],
        output_snippet=output[:1000] or "<empty output>",
    )


def _invalid_result(case: EvalCase, output: str, reason: str) -> MetricResult:
    assessment = f"Invalid transcript-sectioning response: {reason}"
    return MetricResult(
        metric_name=TranscriptSectioningMetric.name,
        score=0.0,
        assessment=assessment,
        signals=[_signal(case, output, assessment)],
    )


def _hard_gate_result(
    prompt: str,
    case: EvalCase,
    output: str,
    expected: TranscriptSectionsGenerationResponse,
    predicted: TranscriptSectionsGenerationResponse,
) -> MetricResult:
    expected_context = expected.starting_context_range
    assert expected_context is not None
    assessment = (
        "The reviewed transcript has a starting-context range, but the prediction returned null; "
        "downstream generation cannot continue. "
        f"expected_starting_context={expected_context.model_dump()}; "
        f"predicted_starting_context={predicted.starting_context_range}."
    )
    return MetricResult(
        metric_name=TranscriptSectioningMetric.name,
        score=0.0,
        assessment=assessment,
        signals=[
            _component_signal(
                "starting_context",
                _section_node_ids(prompt),
                case,
                output,
                expected,
                predicted,
                0.0,
            )
        ],
    )
