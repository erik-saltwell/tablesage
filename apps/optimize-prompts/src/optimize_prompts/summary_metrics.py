"""Summary-specific Prompt Forge metrics and evaluation-input helpers."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from prompt_model import Metric, MetricResult
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics import CompressionMetric, SectionStructureMetric
from prompt_model_metrics.summarization import AlignmentMetric, InclusionMetric
from prompt_model_metrics.summarization.question_factories import QuestionFactory

from .ledger_metrics import JsonQuestionFactory

_LEDGER_OPEN = "<session_ledger>"
_LEDGER_CLOSE = "</session_ledger>"
_SUMMARY_SECTIONS = [
    "The Party",
    "Starting Situation",
    "Scene Breakdown",
    "Key Decisions & Events",
    "Ending Situation",
    "Open Loops",
    "Clocks",
]


class SummaryInputError(ValueError):
    """Raised when a Summary evaluation input lacks one unambiguous Ledger block."""


def extract_session_ledger(rendered_input: str) -> str:
    """Extract the sole Ledger block from a rendered Summary user prompt."""
    if rendered_input.count(_LEDGER_OPEN) != 1 or rendered_input.count(_LEDGER_CLOSE) != 1:
        raise SummaryInputError("Expected exactly one <session_ledger> block in the Summary evaluation input.")

    _, after_open = rendered_input.split(_LEDGER_OPEN, maxsplit=1)
    ledger, after_close = after_open.split(_LEDGER_CLOSE, maxsplit=1)
    if after_close.strip():
        raise SummaryInputError("Unexpected content after </session_ledger> in the Summary evaluation input.")
    if not ledger.strip():
        raise SummaryInputError("The Summary evaluation input has an empty <session_ledger> block.")
    return ledger.strip()


def ledger_case(case: EvalCase) -> EvalCase:
    """Keep case identity while replacing prompt scaffolding with its canonical Ledger."""
    return case.model_copy(update={"input": extract_session_ledger(case.input)})


class SummaryCoverageMetric(InclusionMetric):
    name: ClassVar[str] = "summary_coverage"
    description: ClassVar[str] = "Checks that every manually curated Ledger detail is present in the Summary."


class SummaryAccuracyMetric(AlignmentMetric):
    name: ClassVar[str] = "summary_accuracy"
    description: ClassVar[str] = "Checks that every Summary claim is supported by the session Ledger alone."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, ledger_case(case), output)


class SummaryConcisenessMetric(CompressionMetric):
    name: ClassVar[str] = "summary_conciseness"
    description: ClassVar[str] = "Measures Summary word-count compression relative to the session Ledger."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, ledger_case(case), output)


def build_summary_metrics(*, judge_llm: LiteLLMConfig, coverage_question_directory: Path) -> list[Metric]:
    """Build the agreed Summary metric suite in optimizer-score order."""
    coverage_factory: QuestionFactory = JsonQuestionFactory(coverage_question_directory)
    return [
        SummaryCoverageMetric(judge_llm, question_factory=coverage_factory),
        SummaryAccuracyMetric(judge_llm),
        SummaryConcisenessMetric(judge_llm),
        SectionStructureMetric(
            expected_sections=_SUMMARY_SECTIONS,
            allow_additional_sections=False,
            enforce_order=True,
            judge_llm=judge_llm,
            name="summary_section_structure",
        ),
    ]
