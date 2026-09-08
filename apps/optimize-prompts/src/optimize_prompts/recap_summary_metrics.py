"""Metrics and input helpers for Recap Summary prompt optimization."""

from __future__ import annotations

import re
from pathlib import Path
from typing import ClassVar

from prompt_model import Metric, MetricResult
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics import CompressionMetric
from prompt_model_metrics.summarization import AlignmentMetric, InclusionMetric
from prompt_model_metrics.summarization.question_factories import QuestionFactory

from .ledger_metrics import JsonQuestionFactory

_LEDGER_OPEN = "<session_ledger>"
_LEDGER_CLOSE = "</session_ledger>"
_BULLET = re.compile(r"^-\s+\S.*$")


class RecapSummaryInputError(ValueError):
    """Raised when a recap evaluation input lacks one unambiguous Ledger block."""


def extract_session_ledger(rendered_input: str) -> str:
    """Extract the sole Ledger block from a rendered Recap Summary input."""
    if rendered_input.count(_LEDGER_OPEN) != 1 or rendered_input.count(_LEDGER_CLOSE) != 1:
        raise RecapSummaryInputError("Expected exactly one <session_ledger> block in the Recap Summary evaluation input.")
    _, after_open = rendered_input.split(_LEDGER_OPEN, maxsplit=1)
    ledger, after_close = after_open.split(_LEDGER_CLOSE, maxsplit=1)
    if after_close.strip():
        raise RecapSummaryInputError("Unexpected content after </session_ledger> in the Recap Summary evaluation input.")
    if not ledger.strip():
        raise RecapSummaryInputError("The Recap Summary evaluation input has an empty <session_ledger> block.")
    return ledger.strip()


def ledger_case(case: EvalCase) -> EvalCase:
    """Keep case identity while replacing recap prompt scaffolding with its Ledger."""
    return case.model_copy(update={"input": extract_session_ledger(case.input)})


class RecapSummaryCoverageMetric(InclusionMetric):
    name: ClassVar[str] = "recap_summary_coverage"
    description: ClassVar[str] = "Checks that every manually reviewed recap fact is present."


class RecapSummaryAlignmentMetric(AlignmentMetric):
    name: ClassVar[str] = "recap_summary_alignment"
    description: ClassVar[str] = "Checks that every recap claim is supported by the session Ledger."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, ledger_case(case), output)


class RecapSummaryConcisenessMetric(CompressionMetric):
    name: ClassVar[str] = "recap_summary_conciseness"
    description: ClassVar[str] = "Measures recap word-count compression relative to the session Ledger."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        return await super().evaluate(prompt, ledger_case(case), output)


class RecapSummaryFormatMetric:
    """Deterministically validate the persisted flat-bullet recap contract."""

    name: ClassVar[str] = "recap_summary_format"
    description: ClassVar[str] = "Requires a non-empty flat sequence of Markdown bullets only."

    async def evaluate(self, prompt: str, case: EvalCase, output: str) -> MetricResult:
        del prompt, case
        valid, assessment = validate_recap_format(output)
        return MetricResult(metric_name=self.name, score=1.0 if valid else 0.0, assessment=assessment)


def validate_recap_format(output: str) -> tuple[bool, str]:
    """Return whether *output* contains only non-nested, non-empty Markdown bullets."""
    stripped = output.strip()
    if not stripped:
        return False, "Recap output is empty."
    if "```" in stripped:
        return False, "Recap output contains a Markdown code fence."
    lines = stripped.splitlines()
    content_lines = [line for line in lines if line.strip()]
    if not content_lines:
        return False, "Recap output has no bullet content."
    invalid = next((line for line in content_lines if _BULLET.fullmatch(line) is None), None)
    if invalid is not None:
        return False, f"Recap output contains non-flat-bullet content: {invalid!r}."
    return True, f"Recap output contains {len(content_lines)} flat Markdown bullets."


def build_recap_summary_metrics(*, judge_llm: LiteLLMConfig, coverage_question_directory: Path) -> list[Metric]:
    """Build the recap metric suite in gated-scorer order."""
    coverage_factory: QuestionFactory = JsonQuestionFactory(coverage_question_directory)
    return [
        RecapSummaryFormatMetric(),
        RecapSummaryCoverageMetric(judge_llm, question_factory=coverage_factory),
        RecapSummaryAlignmentMetric(judge_llm),
        RecapSummaryConcisenessMetric(judge_llm),
    ]
