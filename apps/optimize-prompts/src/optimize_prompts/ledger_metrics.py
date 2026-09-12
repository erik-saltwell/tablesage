"""Ledger-specific Prompt Forge metrics and evaluation-input helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import ClassVar, cast

from prompt_model import Metric, MetricResult
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics import CompressionMetric
from prompt_model_metrics.summarization import AlignmentMetric, ExclusionMetric, InclusionMetric
from prompt_model_metrics.summarization.question_factories import MissingCuratedQuestionsError, QuestionFactory
from tablesage_application.session_pipeline.generate_ledger import LedgerGenerationResponse

_TRANSCRIPT_OPEN = "<session_transcript>"
_TRANSCRIPT_CLOSE = "</session_transcript>"


class LedgerInputError(ValueError):
    """Raised when a Ledger evaluation input lacks one unambiguous transcript block."""


def extract_session_transcript(rendered_input: str) -> str:
    """Extract the sole transcript block from a rendered Ledger user prompt."""
    if "<session_utterances>" in rendered_input:
        blocks: dict[str, str] = {}
        for tag in ("starting_context", "session_utterances"):
            opening, closing = f"<{tag}>", f"</{tag}>"
            if rendered_input.count(opening) != 1 or rendered_input.count(closing) != 1:
                raise LedgerInputError(f"Expected exactly one {opening} block.")
            if rendered_input.index(closing) < rendered_input.index(opening):
                raise LedgerInputError(f"Reversed {opening} block.")
            blocks[tag] = rendered_input.split(opening, 1)[1].split(closing, 1)[0].strip()
            try:
                records = json.loads(blocks[tag])
            except json.JSONDecodeError as exc:
                raise LedgerInputError(f"Invalid JSON in {opening}.") from exc
            if not isinstance(records, list):
                raise LedgerInputError(f"Expected an utterance array in {opening}.")
        if rendered_input.split("</session_utterances>", 1)[1].strip():
            raise LedgerInputError("Unexpected content after </session_utterances>.")
        return json.dumps(blocks, ensure_ascii=False)
    if rendered_input.count(_TRANSCRIPT_OPEN) != 1 or rendered_input.count(_TRANSCRIPT_CLOSE) != 1:
        raise LedgerInputError("Expected exactly one <session_transcript> block in the Ledger evaluation input.")

    _, after_open = rendered_input.split(_TRANSCRIPT_OPEN, maxsplit=1)
    transcript, after_close = after_open.split(_TRANSCRIPT_CLOSE, maxsplit=1)
    if after_close.strip():
        # The current template has no content after the transcript. Rejecting a changed layout
        # avoids silently grounding metrics in a different source boundary.
        raise LedgerInputError("Unexpected content after </session_transcript> in the Ledger evaluation input.")
    if not transcript.strip():
        raise LedgerInputError("The Ledger evaluation input has an empty <session_transcript> block.")
    return transcript.strip()


def transcript_case(case: EvalCase) -> EvalCase:
    """Keep case identity while replacing prompt scaffolding with the factual source."""
    return case.model_copy(update={"input": extract_session_transcript(case.input)})


def ledger_content(output: str) -> str:
    """Assess only the Ledger portion of the joint response."""
    response = LedgerGenerationResponse.model_validate_json(output)
    return json.dumps({"starting_situation": response.starting_situation, **response.ledger.model_dump()}, ensure_ascii=False)


class JsonQuestionFactory:
    """Load manually reviewed per-session questions from exact-name JSON files."""

    name = "ledger_curated_json"

    def __init__(self, directory: Path, *, allow_empty: bool = False) -> None:
        self.directory = directory
        self.allow_empty = allow_empty

    async def questions(self, input: str, source_path: str | None) -> list[str]:
        del input
        if source_path is None:
            raise MissingCuratedQuestionsError("Ledger curated questions require EvalCase.source_path.")
        source = Path(source_path)
        if source.name != source_path:
            raise MissingCuratedQuestionsError(f"Ledger curated questions require a filename source_path, got {source_path!r}.")
        question_path = self.directory / f"{source.stem}.json"
        if not question_path.is_file():
            raise MissingCuratedQuestionsError(f"No curated Ledger questions for {source.name!r}: expected {question_path}.")

        try:
            payload_object: object = json.loads(question_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Curated Ledger question file {question_path} is not valid JSON.") from exc
        if not isinstance(payload_object, dict):
            raise ValueError(f'Curated Ledger question file {question_path} must be {{"questions": [<non-empty strings>]}}.')
        payload = cast(dict[str, object], payload_object)
        questions_object = payload.get("questions")
        if set(payload) != {"questions"} or not isinstance(questions_object, list):
            raise ValueError(f'Curated Ledger question file {question_path} must be {{"questions": [<non-empty strings>]}}.')
        questions = cast(list[object], questions_object)
        if not all(isinstance(question, str) and question.strip() for question in questions):
            raise ValueError(f"Curated Ledger question file {question_path} contains an empty or non-string question.")
        if not questions and not self.allow_empty:
            raise MissingCuratedQuestionsError(f"Curated Ledger question file {question_path} is empty.")
        return [question.strip() for question in questions if isinstance(question, str)]


class LedgerCoverageMetric(InclusionMetric):
    name: ClassVar[str] = "ledger_coverage"
    description: ClassVar[str] = "Checks that every manually curated in-fiction detail is present in the Ledger."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, case, ledger_content(output))


class LedgerAccuracyMetric(AlignmentMetric):
    name: ClassVar[str] = "ledger_accuracy"
    description: ClassVar[str] = "Checks that every Ledger claim is supported by the session transcript alone."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, transcript_case(case), ledger_content(output))


class LedgerConcisenessMetric(CompressionMetric):
    name: ClassVar[str] = "ledger_conciseness"
    description: ClassVar[str] = "Measures Ledger word-count compression relative to the session transcript."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, transcript_case(case), ledger_content(output))


class LedgerExclusionMetric(ExclusionMetric):
    name: ClassVar[str] = "ledger_exclusion"
    description: ClassVar[str] = "Checks that reviewed table talk and mechanical procedure are absent from the Ledger."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, case, ledger_content(output))

    def _no_questions_result(self, case: EvalCase, output: str) -> MetricResult:
        del case, output
        # The weighted scorer has no weight for this sentinel metric name, so an exclusion
        # corpus with no approved items is omitted rather than earning a vacuous reward.
        return MetricResult(
            metric_name="ledger_exclusion_not_applicable",
            score=1.0,
            assessment="No reviewed exclusion questions apply to this session.",
        )


def build_ledger_metrics(
    *,
    judge_llm: LiteLLMConfig,
    coverage_question_directory: Path,
    exclusion_question_directory: Path,
) -> list[Metric]:
    """Build the agreed Ledger metric suite in optimizer-score order."""
    coverage_factory: QuestionFactory = JsonQuestionFactory(coverage_question_directory)
    exclusion_factory: QuestionFactory = JsonQuestionFactory(exclusion_question_directory, allow_empty=True)
    return [
        LedgerCoverageMetric(judge_llm, question_factory=coverage_factory),
        LedgerAccuracyMetric(judge_llm),
        LedgerConcisenessMetric(judge_llm),
        LedgerExclusionMetric(judge_llm, question_factory=exclusion_factory),
    ]
