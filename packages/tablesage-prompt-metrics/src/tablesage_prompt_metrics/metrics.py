from __future__ import annotations

import json
from collections.abc import Sequence
from typing import ClassVar, cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError
from prompt_model import IssueSignal, MetricResult
from prompt_model.config import LiteLLMConfig
from prompt_model.helpers import acomplete

from .models import (
    ClaimVerdict,
    ClaimVerdictList,
    CompletenessQuestion,
    DuplicateGroupList,
    ExclusionSeverity,
    ExclusionViolationList,
    QuestionAnswerList,
    QuestionCategory,
)

_SNIPPET_LIMIT = 500


def _truncate(value: str, limit: int = _SNIPPET_LIMIT) -> str:
    stripped: str = value.strip()
    if not stripped:
        return "(empty)"
    if len(stripped) <= limit:
        return stripped
    return stripped[:limit] + "..."


def _semantic_ledger(output: str) -> str:
    try:
        value: object = json.loads(output)
    except json.JSONDecodeError:
        return output
    if not isinstance(value, dict):
        return output
    parsed: dict[str, object] = cast(dict[str, object], value)
    semantic: dict[str, object] = {key: item for key, item in parsed.items() if key != "scratchpad"}
    return json.dumps(semantic, ensure_ascii=False, indent=2)


def _semantic_word_count(output: str) -> int:
    try:
        value: object = json.loads(output)
    except json.JSONDecodeError:
        return len(output.split())

    def _strings(item: object, *, key: str | None = None) -> list[str]:
        if key in {"scratchpad", "type"}:
            return []
        if isinstance(item, str):
            return [item]
        if isinstance(item, list):
            return [text for child in item for text in _strings(child)]
        if isinstance(item, dict):
            parsed: dict[str, object] = cast(dict[str, object], item)
            return [text for child_key, child in parsed.items() for text in _strings(child, key=child_key)]
        return []

    return sum(len(text.split()) for text in _strings(value))


def _signal(*, rationale: str, target: str, criterion: str, input_snippet: str, output_snippet: str) -> IssueSignal:
    return IssueSignal(
        culprit_node_id="document",
        rationale=rationale,
        target_behavior=target,
        success_criterion=criterion,
        input_snippet=_truncate(input_snippet),
        output_snippet=_truncate(output_snippet),
    )


class SchemaCorrectnessMetric:
    name: ClassVar[str] = "schema_correctness"
    description: ClassVar[str] = "Checks that target output conforms to the exported production JSON Schema."

    def __init__(self, response_schema: dict[str, object]) -> None:
        try:
            Draft202012Validator.check_schema(response_schema)
        except SchemaError as exc:
            raise ValueError(f"Invalid response JSON Schema: {exc.message}") from exc
        self._validator = Draft202012Validator(response_schema)

    async def evaluate(self, prompt: str, input: str, output: str, ground_truth: str | None) -> MetricResult:
        try:
            parsed: object = json.loads(output)
            self._validator.validate(parsed)
        except (json.JSONDecodeError, ValidationError) as exc:
            message: str = exc.msg if isinstance(exc, json.JSONDecodeError) else exc.message
            return MetricResult(
                metric_name=self.name,
                score=0.0,
                assessment=f"Output failed production schema validation: {message}",
                signals=[
                    _signal(
                        rationale=f"The generated output is not structurally usable: {message}",
                        target="Always return an output conforming to the supplied production schema.",
                        criterion="The output parses as JSON and passes JSON Schema validation.",
                        input_snippet=input,
                        output_snippet=output,
                    )
                ],
            )
        return MetricResult(metric_name=self.name, score=1.0, assessment="Output conforms to the production JSON Schema.")


class HallucinationMetric:
    name: ClassVar[str] = "no_hallucinations"
    description: ClassVar[str] = "Checks that every user-visible Ledger claim is supported by the transcript alone."

    def __init__(self, transcript: str, judge_llm: LiteLLMConfig) -> None:
        self._transcript: str = transcript
        self._judge_llm: LiteLLMConfig = judge_llm

    async def _judge(self, ledger: str, *, claims: Sequence[str] | None = None, pass_name: str) -> ClaimVerdictList:
        focus: str = ""
        if claims is not None:
            focus = "\nIndependently reassess only these claims. Do not rely on a previous verdict:\n" + json.dumps(
                list(claims), ensure_ascii=False
            )
        return await acomplete(
            system_prompt=(
                "Extract the atomic factual claims from the user-visible Ledger and decide whether each claim is explicitly supported "
                "or directly entailed by the transcript alone. Metadata outside the transcript is not evidence. Preserve uncertainty. "
                "A claim is supported only when no outside assumption is required. Return one verdict per assessed claim."
            ),
            user_prompt=f"<transcript>\n{self._transcript}\n</transcript>\n\n<ledger>\n{ledger}\n</ledger>{focus}",
            config=self._judge_llm,
            response_format=ClaimVerdictList,
            log_name=f"tablesage_hallucination:{pass_name}",
        )

    async def evaluate(self, prompt: str, input: str, output: str, ground_truth: str | None) -> MetricResult:
        ledger: str = _semantic_ledger(output)
        first: ClaimVerdictList = await self._judge(ledger, pass_name="initial")
        alleged: list[ClaimVerdict] = [verdict for verdict in first.verdicts if not verdict.supported]
        if not alleged:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                assessment=f"All {len(first.verdicts)} extracted Ledger claims are supported by the transcript.",
            )

        second: ClaimVerdictList = await self._judge(
            ledger,
            claims=[verdict.claim for verdict in alleged],
            pass_name="confirmation",
        )
        confirmed: list[ClaimVerdict] = [verdict for verdict in second.verdicts if not verdict.supported]
        if not confirmed:
            return MetricResult(
                metric_name=self.name,
                score=1.0,
                assessment=f"A second independent pass cleared all {len(alleged)} initially unsupported claims.",
            )

        signals: list[IssueSignal] = [
            _signal(
                rationale=verdict.rationale or f"Two independent passes found this claim unsupported: {verdict.claim}",
                target="Include no fictional claim that is absent from the transcript.",
                criterion="Every user-visible Ledger claim is explicitly supported or directly entailed by the transcript.",
                input_snippet=verdict.evidence or self._transcript,
                output_snippet=verdict.claim,
            )
            for verdict in confirmed
        ]
        return MetricResult(
            metric_name=self.name,
            score=0.0,
            assessment=f"Two passes agreed that {len(confirmed)} Ledger claim(s) are unsupported.",
            signals=signals,
        )


class CompletenessMetric:
    name: ClassVar[str] = "completeness"
    description: ClassVar[str] = "Checks reviewed fiction, recap, introduction, and correction questions against the Ledger."

    def __init__(self, questions: Sequence[CompletenessQuestion], judge_llm: LiteLLMConfig) -> None:
        self._questions: tuple[CompletenessQuestion, ...] = tuple(question for question in questions if question.enabled)
        if not self._questions:
            raise ValueError("Completeness requires at least one enabled reviewed question.")
        self._judge_llm: LiteLLMConfig = judge_llm

    async def evaluate(self, prompt: str, input: str, output: str, ground_truth: str | None) -> MetricResult:
        ledger: str = _semantic_ledger(output)
        question_data: list[dict[str, str]] = [
            {"id": question.id, "category": question.category.value, "question": question.question} for question in self._questions
        ]
        result: QuestionAnswerList = await acomplete(
            system_prompt=(
                "For each reviewed question, determine whether the Ledger alone supplies an affirmative answer. Require explicit coverage, "
                "not a merely related statement. For correction questions, also report whether the final canonical state is represented by "
                "a correction entry; other categories must set covered_by_correction false. Return exactly one answer for every "
                "supplied id."
            ),
            user_prompt=f"<questions>\n{json.dumps(question_data, ensure_ascii=False)}\n</questions>\n\n<ledger>\n{ledger}\n</ledger>",
            config=self._judge_llm,
            response_format=QuestionAnswerList,
            log_name="tablesage_completeness",
        )
        by_id = {answer.id: answer for answer in result.answers}
        expected_ids: set[str] = {question.id for question in self._questions}
        if set(by_id) != expected_ids:
            raise ValueError("Completeness judge did not return exactly one answer for every question id.")

        covered_count: int = sum(by_id[question.id].covered for question in self._questions)
        coverage_score: float = covered_count / len(self._questions)
        corrections: list[CompletenessQuestion] = [
            question for question in self._questions if question.category is QuestionCategory.CORRECTION
        ]
        correction_score: float = (
            sum(by_id[question.id].covered_by_correction for question in corrections) / len(corrections) if corrections else 1.0
        )
        score: float = 0.9 * coverage_score + 0.1 * correction_score
        signals: list[IssueSignal] = []
        for question in self._questions:
            answer = by_id[question.id]
            if not answer.covered:
                signals.append(
                    _signal(
                        rationale=answer.rationale or f"The Ledger does not answer reviewed question {question.id}: {question.question}",
                        target="Represent every reviewed change to fiction, recap fact, introduction, and final corrected state.",
                        criterion="Every enabled reviewed completeness question is answerable from the Ledger.",
                        input_snippet=question.evidence,
                        output_snippet=ledger,
                    )
                )
            elif question.category is QuestionCategory.CORRECTION and not answer.covered_by_correction:
                signals.append(
                    _signal(
                        rationale=answer.rationale or f"Question {question.id} is covered without using a correction entry.",
                        target="Represent known corrections using the correction Ledger type.",
                        criterion="Every enabled correction question is covered by a correction entry.",
                        input_snippet=question.evidence,
                        output_snippet=ledger,
                    )
                )
        return MetricResult(
            metric_name=self.name,
            score=score,
            assessment=(
                f"Covered {covered_count}/{len(self._questions)} reviewed questions; correction classification score "
                f"{correction_score:.2f}."
            ),
            signals=signals,
        )


class ExclusionMetric:
    _DEDUCTIONS: ClassVar[dict[ExclusionSeverity, float]] = {
        ExclusionSeverity.MAJOR: 0.30,
        ExclusionSeverity.MODERATE: 0.15,
        ExclusionSeverity.MINOR: 0.05,
    }

    def __init__(self, *, kind: str, judge_llm: LiteLLMConfig) -> None:
        if kind not in {"table_talk", "mechanics"}:
            raise ValueError(f"Unknown exclusion kind: {kind}")
        self.kind: str = kind
        self.name: str = f"{kind}_exclusion"
        self.description: str = f"Penalizes {kind.replace('_', ' ')} retained in the user-visible Ledger."
        self._judge_llm: LiteLLMConfig = judge_llm

    async def evaluate(self, prompt: str, input: str, output: str, ground_truth: str | None) -> MetricResult:
        ledger: str = _semantic_ledger(output)
        definition: str
        if self.kind == "table_talk":
            definition = (
                "Find non-mechanical out-of-game conversation: jokes, logistics, side conversation, or speculative player strategy that "
                "does not establish an in-fiction decision, action, speech, or state. Do not flag rules, rolls, stats, or procedures here."
            )
        else:
            definition = (
                "Find rules, rolls, statistics, character-sheet operations, and game procedures retained in the Ledger. Do not flag the "
                "fictional consequence established by a mechanic, only the mechanical content itself."
            )
        result: ExclusionViolationList = await acomplete(
            system_prompt=(
                f"{definition} Return each violating Ledger entry with severity: major for a wholly irrelevant entry, moderate for "
                "substantial contamination of otherwise fictional content, and minor for a small retained fragment. Do not report "
                "other exclusion types."
            ),
            user_prompt=f"<ledger>\n{ledger}\n</ledger>",
            config=self._judge_llm,
            response_format=ExclusionViolationList,
            log_name=f"tablesage_exclusion:{self.kind}",
        )
        deduction: float = sum(self._DEDUCTIONS[violation.severity] for violation in result.violations)
        score: float = max(0.0, 1.0 - deduction)
        signals: list[IssueSignal] = [
            _signal(
                rationale=violation.rationale,
                target=f"Exclude {self.kind.replace('_', ' ')} while retaining changes to the fiction.",
                criterion=f"The Ledger contains no {self.kind.replace('_', ' ')}.",
                input_snippet=input,
                output_snippet=violation.entry,
            )
            for violation in result.violations
        ]
        return MetricResult(
            metric_name=self.name,
            score=score,
            assessment=f"Found {len(result.violations)} violation(s), deducting {deduction:.2f}.",
            signals=signals,
        )


class ConcisionMetric:
    name: ClassVar[str] = "concision"
    description: ClassVar[str] = "Penalizes semantic duplication and rewards transcript compression."

    def __init__(self, transcript: str, judge_llm: LiteLLMConfig) -> None:
        self._transcript: str = transcript
        self._judge_llm: LiteLLMConfig = judge_llm

    async def evaluate(self, prompt: str, input: str, output: str, ground_truth: str | None) -> MetricResult:
        ledger: str = _semantic_ledger(output)
        result: DuplicateGroupList = await acomplete(
            system_prompt=(
                "Identify groups of Ledger entries that encode the same fictional change even when phrased differently. Repeated "
                "occurrences at different times are distinct. A correction is distinct from the assertion it supersedes. Return each "
                "duplicate group once."
            ),
            user_prompt=f"<ledger>\n{ledger}\n</ledger>",
            config=self._judge_llm,
            response_format=DuplicateGroupList,
            log_name="tablesage_concision:duplication",
        )
        duplication_score: float = max(0.0, 1.0 - 0.25 * len(result.groups))
        transcript_words: int = len(self._transcript.split())
        ledger_words: int = _semantic_word_count(output)
        compression_score: float = 1.0 - min(ledger_words / transcript_words, 1.0) if transcript_words else 0.0
        score: float = 0.8 * duplication_score + 0.2 * compression_score
        signals: list[IssueSignal] = [
            _signal(
                rationale=group.rationale,
                target="Represent each fictional change once while retaining repeated events that occur at distinct times.",
                criterion="The Ledger contains no semantically duplicated event groups.",
                input_snippet=input,
                output_snippet="\n".join(group.entries),
            )
            for group in result.groups
        ]
        return MetricResult(
            metric_name=self.name,
            score=score,
            assessment=(
                f"Found {len(result.groups)} duplicate group(s); semantic Ledger length is {ledger_words}/{transcript_words} words."
            ),
            signals=signals,
        )
