"""Metrics and input helpers for Recap Summary prompt optimization."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import ClassVar

from prompt_model import IssueSignal, Metric, MetricResult
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics.summarization import ExclusionMetric, InclusionMetric
from prompt_model_metrics.summarization.prompt_schemas import QuestionAnswers
from prompt_model_metrics.summarization.question_factories import QuestionFactory
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from tablesage_application.session_pipeline.scene_breakdown import SceneBreakdown

from .ledger_metrics import JsonQuestionFactory
from .recap_alignment import DirectRecapAlignmentMetric, RecapJudgeError

_SCENE_BREAKDOWN_OPEN = "<scene_breakdown>"
_SCENE_BREAKDOWN_CLOSE = "</scene_breakdown>"
_BULLET = re.compile(r"^- [^\s].*$")


class RecapSummaryInputError(ValueError):
    """Raised when a recap evaluation input lacks one unambiguous Scene Breakdown block."""


def extract_scene_breakdown(rendered_input: str) -> str:
    """Extract the sole Scene Breakdown block from a rendered Recap Summary input."""
    if rendered_input.count(_SCENE_BREAKDOWN_OPEN) != 1 or rendered_input.count(_SCENE_BREAKDOWN_CLOSE) != 1:
        raise RecapSummaryInputError("Expected exactly one <scene_breakdown> block in the Recap Summary evaluation input.")
    if rendered_input.index(_SCENE_BREAKDOWN_CLOSE) < rendered_input.index(_SCENE_BREAKDOWN_OPEN):
        raise RecapSummaryInputError("The closing Scene Breakdown tag precedes its opening tag.")
    _, after_open = rendered_input.split(_SCENE_BREAKDOWN_OPEN, maxsplit=1)
    breakdown, after_close = after_open.split(_SCENE_BREAKDOWN_CLOSE, maxsplit=1)
    if after_close.strip():
        raise RecapSummaryInputError("Unexpected content after </scene_breakdown> in the Recap Summary evaluation input.")
    if not breakdown.strip():
        raise RecapSummaryInputError("The Recap Summary evaluation input has an empty <scene_breakdown> block.")
    try:
        SceneBreakdown.model_validate_json(breakdown)
    except ValidationError as exc:
        raise RecapSummaryInputError("The Recap Summary evaluation input is not a valid Scene Breakdown v1.") from exc
    return breakdown.strip()


def scene_breakdown_case(case: EvalCase) -> EvalCase:
    """Keep case identity while replacing recap prompt scaffolding with its Scene Breakdown."""
    return case.model_copy(update={"input": extract_scene_breakdown(case.input)})


async def _validated_answers(ask: Callable[[], Awaitable[QuestionAnswers]], questions: list[str], attempts: int) -> QuestionAnswers:
    expected = Counter(question.strip() for question in questions)
    for _ in range(attempts):
        try:
            response = await ask()
        except ValidationError:
            continue
        if Counter(answer.question.strip() for answer in response.answers) == expected:
            return response
    raise RecapJudgeError("Question judge did not return exactly one answer for every requested question.")


class ValidatedInclusionMetric(InclusionMetric):
    def __init__(self, judge: LiteLLMConfig, question_factory: QuestionFactory, attempts: int = 3) -> None:
        super().__init__(judge, question_factory=question_factory)
        self.attempts = attempts

    async def _ask(self, output: str, questions: list[str]) -> QuestionAnswers:
        return await _validated_answers(lambda: InclusionMetric._ask(self, output, questions), questions, self.attempts)


class RecapSummaryCoverageMetric(ValidatedInclusionMetric):
    name: ClassVar[str] = "recap_summary_coverage"
    description: ClassVar[str] = "Checks that the curated facts needed to resume play are present."


class RecapSummaryRecognitionMetric(ValidatedInclusionMetric):
    name: ClassVar[str] = "recap_summary_recognition"
    description: ClassVar[str] = "Checks that selected memorable moments retain their recognizable details."


class RecapSummaryExclusionMetric(ExclusionMetric):
    name: ClassVar[str] = "recap_summary_exclusion"
    description: ClassVar[str] = "Checks that curated low-value details are left unmentioned, including in denials."

    def __init__(self, judge: LiteLLMConfig, question_factory: QuestionFactory, attempts: int = 3) -> None:
        super().__init__(judge, question_factory=question_factory)
        self.attempts = attempts

    async def _ask(self, output: str, questions: list[str]) -> QuestionAnswers:
        return await _validated_answers(lambda: ExclusionMetric._ask(self, output, questions), questions, self.attempts)


class RecapSummaryAlignmentMetric(DirectRecapAlignmentMetric):
    name: ClassVar[str] = "recap_summary_alignment"
    description: ClassVar[str] = "Checks that every recap claim is supported by the session Scene Breakdown."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, scene_breakdown_case(case), output)


class RecapLengthSettings(BaseModel):
    """Output limits independent of source size or JSON formatting."""

    model_config = ConfigDict(extra="forbid")

    target_words: int = Field(gt=0)
    max_words: int = Field(gt=0)
    max_bullets: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_word_limits(self) -> RecapLengthSettings:
        if self.target_words > self.max_words:
            raise ValueError("target_words must not exceed max_words.")
        return self


class RecapSummaryConcisenessMetric:
    name: ClassVar[str] = "recap_summary_conciseness"
    description: ClassVar[str] = "Rewards recaps within an output word budget, without rewarding deletion below the target."

    def __init__(self, limits: RecapLengthSettings) -> None:
        self.limits = limits

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        del prompt
        valid, assessment = validate_recap_format(output)
        if not valid:
            return MetricResult(metric_name=self.name, score=0.0, assessment=assessment)
        lines = [line for line in output.splitlines() if line.strip()]
        words = sum(len(line[2:].split()) for line in lines)
        over_limit = words > self.limits.max_words or len(lines) > self.limits.max_bullets
        score = 0.0 if over_limit else min(1.0, self.limits.target_words / words)
        assessment = (
            f"Recap has {words} words and {len(lines)} bullets; target {self.limits.target_words} words, "
            f"maximum {self.limits.max_words} words and {self.limits.max_bullets} bullets."
        )
        signals = []
        if score < 1.0:
            signals.append(
                IssueSignal(
                    culprit_node_id="document",
                    rationale=assessment,
                    target_behavior="Select a short, recognizable recap rather than an exhaustive session account.",
                    success_criterion="Fit the output budget while retaining required facts and recognition cues.",
                    input_snippet=case.input[:500],
                    output_snippet=output[:500],
                )
            )
        return MetricResult(metric_name=self.name, score=score, assessment=assessment, signals=signals)


class RecapSummaryFormatMetric:
    """Deterministically validate the persisted flat-bullet recap contract."""

    name: ClassVar[str] = "recap_summary_format"
    description: ClassVar[str] = "Requires a non-empty flat sequence of Markdown bullets only."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        del prompt
        valid, assessment = validate_recap_format(output)
        signals = []
        if not valid and output.strip() and case.input.strip():
            signals.append(
                IssueSignal(
                    culprit_node_id="document",
                    rationale=assessment,
                    target_behavior="Return only flat Markdown bullets.",
                    success_criterion="No headings, nesting, fences, or continuation prose.",
                    input_snippet=case.input[:500],
                    output_snippet=output[:500],
                )
            )
        return MetricResult(metric_name=self.name, score=1.0 if valid else 0.0, assessment=assessment, signals=signals)


def validate_recap_format(output: str) -> tuple[bool, str]:
    """Return whether *output* contains only non-nested, non-empty Markdown bullets."""
    stripped = output.strip()
    if not stripped:
        return False, "Recap output is empty."
    if "```" in stripped:
        return False, "Recap output contains a Markdown code fence."
    lines = output.splitlines()
    content_lines = [line for line in lines if line.strip()]
    if not content_lines:
        return False, "Recap output has no bullet content."
    invalid = next((line for line in content_lines if _BULLET.fullmatch(line) is None), None)
    if invalid is not None:
        return False, f"Recap output contains non-flat-bullet content: {invalid!r}."
    return True, f"Recap output contains {len(content_lines)} flat Markdown bullets."


def build_recap_summary_metrics(
    *,
    judge_llm: LiteLLMConfig,
    coverage_question_directory: Path,
    recognition_question_directory: Path,
    exclusion_question_directory: Path,
    length: RecapLengthSettings,
    judge_attempts: int = 3,
) -> list[Metric]:
    """Build the recap metric suite in gated-scorer order."""
    coverage_factory: QuestionFactory = JsonQuestionFactory(coverage_question_directory)
    return [
        RecapSummaryFormatMetric(),
        RecapSummaryCoverageMetric(judge_llm, question_factory=coverage_factory, attempts=judge_attempts),
        RecapSummaryRecognitionMetric(
            judge_llm, question_factory=JsonQuestionFactory(recognition_question_directory), attempts=judge_attempts
        ),
        RecapSummaryExclusionMetric(judge_llm, question_factory=JsonQuestionFactory(exclusion_question_directory), attempts=judge_attempts),
        RecapSummaryAlignmentMetric(judge_llm, attempts=judge_attempts),
        RecapSummaryConcisenessMetric(length),
    ]
