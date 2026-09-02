from __future__ import annotations

import json
from typing import Any

import pytest
from prompt_model import MetricResult
from prompt_model.config import LiteLLMConfig
from tablesage_prompt_metrics import metrics as metrics_module
from tablesage_prompt_metrics.metrics import (
    CompletenessMetric,
    ConcisionMetric,
    ExclusionMetric,
    HallucinationMetric,
    SchemaCorrectnessMetric,
)
from tablesage_prompt_metrics.models import (
    ClaimVerdict,
    ClaimVerdictList,
    CompletenessQuestion,
    DuplicateGroup,
    DuplicateGroupList,
    ExclusionSeverity,
    ExclusionViolation,
    ExclusionViolationList,
    QuestionAnswer,
    QuestionAnswerList,
    QuestionCategory,
)
from tablesage_prompt_metrics.scoring import LedgerScorer


@pytest.mark.anyio
async def test_schema_correctness_validates_raw_target_json() -> None:
    metric = SchemaCorrectnessMetric(
        {
            "type": "object",
            "properties": {"scratchpad": {"type": "string"}, "utterances": {"type": "array"}},
            "required": ["scratchpad", "utterances"],
            "additionalProperties": False,
        }
    )

    passing = await metric.evaluate("prompt", "input", json.dumps({"scratchpad": "", "utterances": []}), None)
    failing = await metric.evaluate("prompt", "input", json.dumps({"utterances": []}), None)

    assert passing.score == 1.0
    assert failing.score == 0.0
    assert failing.signals


def _result(name: str, score: float) -> MetricResult:
    return MetricResult(metric_name=name, score=score, assessment="assessment")


def test_ledger_scorer_applies_hard_gates_then_agreed_weights() -> None:
    scorer = LedgerScorer()
    results = [
        _result("schema_correctness", 1.0),
        _result("no_hallucinations", 1.0),
        _result("completeness", 0.8),
        _result("table_talk_exclusion", 0.9),
        _result("mechanics_exclusion", 0.7),
        _result("concision", 0.5),
    ]

    assert scorer.compute(results) == pytest.approx(0.77)
    results[1] = _result("no_hallucinations", 0.99)
    assert scorer.compute(results) == 0.0


def test_prompt_model_dependency_is_available_to_external_package() -> None:
    config = LiteLLMConfig(model="test-model")
    assert config.model == "test-model"


@pytest.mark.anyio
async def test_hallucination_gate_requires_two_unsupported_verdicts_and_ignores_scratchpad(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def _stub(*, user_prompt: str, **kwargs: Any) -> ClaimVerdictList:
        calls.append(user_prompt)
        return ClaimVerdictList(verdicts=[ClaimVerdict(claim="A dragon lands.", supported=False, rationale="No dragon appears.")])

    monkeypatch.setattr(metrics_module, "acomplete", _stub)
    metric = HallucinationMetric("The gate opens.", LiteLLMConfig(model="judge"))

    result = await metric.evaluate(
        "prompt",
        "input",
        json.dumps({"scratchpad": "Invent a dragon.", "preamble": None, "utterances": [{"fact": "A dragon lands."}]}),
        None,
    )

    assert result.score == 0.0
    assert len(calls) == 2
    assert all("Invent a dragon" not in call for call in calls)


@pytest.mark.anyio
async def test_completeness_combines_question_coverage_and_correction_classification(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub(**kwargs: Any) -> QuestionAnswerList:
        return QuestionAnswerList(
            answers=[
                QuestionAnswer(id="q0001", covered=True),
                QuestionAnswer(id="q0002", covered=True, covered_by_correction=False),
            ]
        )

    monkeypatch.setattr(metrics_module, "acomplete", _stub)
    metric = CompletenessMetric(
        [
            CompletenessQuestion(
                id="q0001", category=QuestionCategory.FICTION_CHANGE, question="Did the gate open?", evidence="The gate opens."
            ),
            CompletenessQuestion(
                id="q0002",
                category=QuestionCategory.CORRECTION,
                question="Was the eastern door locked?",
                evidence="The eastern door is locked.",
            ),
        ],
        LiteLLMConfig(model="judge"),
    )

    result = await metric.evaluate("prompt", "input", '{"scratchpad":"","utterances":[]}', None)

    assert result.score == pytest.approx(0.9)
    assert len(result.signals) == 1


@pytest.mark.anyio
async def test_exclusion_and_concision_apply_fixed_deductions(monkeypatch: pytest.MonkeyPatch) -> None:
    responses: list[object] = [
        ExclusionViolationList(
            violations=[ExclusionViolation(entry="I rolled 18.", severity=ExclusionSeverity.MODERATE, rationale="A die roll remains.")]
        ),
        DuplicateGroupList(groups=[DuplicateGroup(entries=["entry 1", "entry 4"], rationale="Same gate-opening event.")]),
    ]

    async def _stub(**kwargs: Any) -> object:
        return responses.pop(0)

    monkeypatch.setattr(metrics_module, "acomplete", _stub)
    judge = LiteLLMConfig(model="judge")
    exclusion = ExclusionMetric(kind="mechanics", judge_llm=judge)
    concision = ConcisionMetric("one two three four five six seven eight nine ten", judge)

    exclusion_result = await exclusion.evaluate("prompt", "input", '{"scratchpad":"","utterances":[]}', None)
    concision_result = await concision.evaluate("prompt", "input", '{"scratchpad":"","utterances":[]}', None)

    assert exclusion_result.score == pytest.approx(0.85)
    assert concision_result.score == pytest.approx(0.8)
    assert exclusion_result.signals
    assert concision_result.signals
