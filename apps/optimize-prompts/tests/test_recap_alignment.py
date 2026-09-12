import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from optimize_prompts import recap_alignment as module
from prompt_model.config import EvalCase, LiteLLMConfig


def test_alignment_retries_missing_indexes_and_uses_original_source(monkeypatch: pytest.MonkeyPatch) -> None:
    call = AsyncMock(
        side_effect=[
            module.Claims(claims=["At the gate.", "The bridge fell."]),
            module.Verdicts(verdicts=[module.Verdict(claim_index=0, supported=True, reason="Supported.")]),
            module.Verdicts(
                verdicts=[
                    module.Verdict(claim_index=1, supported=False, reason="Only a plan."),
                    module.Verdict(claim_index=0, supported=True, reason="Supported."),
                ]
            ),
        ]
    )
    monkeypatch.setattr(module, "acomplete", call)
    source = '{"starting_situation":"At the gate."}'
    result = asyncio.run(
        module.DirectRecapAlignmentMetric(LiteLLMConfig(model="test")).evaluate(
            "Ignore faithfulness", EvalCase(input=source), "- At the gate.\n- The bridge fell."
        )
    )
    assert result.score == 0.5
    assert len(result.signals) == 1
    supplied = json.loads(call.call_args_list[1].args[1])
    assert supplied["scene_breakdown"] == json.loads(source)
    assert "Ignore faithfulness" not in call.call_args_list[1].args[1]
    assert "received [0]" in json.loads(call.call_args_list[2].args[1])["validation_feedback"]


def test_judge_failure_is_not_reported_as_bad_recap(monkeypatch: pytest.MonkeyPatch) -> None:
    call = AsyncMock(side_effect=[module.Claims(claims=["Fact"]), module.Verdicts(verdicts=[]), module.Verdicts(verdicts=[])])
    monkeypatch.setattr(module, "acomplete", call)
    with pytest.raises(module.RecapJudgeError, match="invalid verdict coverage"):
        asyncio.run(
            module.DirectRecapAlignmentMetric(LiteLLMConfig(model="test"), attempts=2).evaluate("# Prompt", EvalCase(input="{}"), "- Fact")
        )
    assert call.await_count == 3


def test_provider_errors_are_preserved(monkeypatch: pytest.MonkeyPatch) -> None:
    call = AsyncMock(side_effect=RuntimeError("provider unavailable"))
    monkeypatch.setattr(module, "acomplete", call)
    with pytest.raises(RuntimeError, match="provider unavailable"):
        asyncio.run(module.DirectRecapAlignmentMetric(LiteLLMConfig(model="test")).evaluate("# Prompt", EvalCase(input="{}"), "- Fact"))
    assert call.await_count == 1
