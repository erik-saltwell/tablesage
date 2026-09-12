import asyncio
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from optimize_prompts.optimize_recap_summary import _load_eval_cases, _load_settings, validate_corpus, validate_source_manifests
from optimize_prompts.recap_alignment import DirectRecapAlignmentMetric, RecapJudgeError
from optimize_prompts.recap_summary_metrics import (
    RecapLengthSettings,
    RecapSummaryAlignmentMetric,
    RecapSummaryConcisenessMetric,
    RecapSummaryExclusionMetric,
    RecapSummaryFormatMetric,
    RecapSummaryInputError,
    _validated_answers,
    extract_scene_breakdown,
)
from optimize_prompts.recap_summary_scorer import RecapSummaryGatedScorer
from prompt_model import MetricResult
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics.summarization.prompt_schemas import AnswerValue, QuestionAnswer, QuestionAnswers
from pydantic import ValidationError

_INPUT = """<session_metadata>
Campaign: Brandonsford
</session_metadata>

<scene_breakdown>
{"version": 1, "session_id": "00000000-0000-0000-0000-000000000001", "session_name": "The bridge",
 "starting_situation": "The party reaches the bridge.",
 "ledger_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
 "ending_situation": "The bridge collapses.", "scenes": []}
</scene_breakdown>
"""


@pytest.mark.parametrize("returned", [["first"], ["first", "first"], ["first", "rephrased"]])
def test_question_judge_retries_incomplete_duplicate_or_changed_questions(returned: list[str]) -> None:
    def answers(questions: list[str]) -> QuestionAnswers:
        return QuestionAnswers(answers=[QuestionAnswer(question=q, answer="yes", evidence="test") for q in questions])

    valid = answers(["second", "first"])
    ask = AsyncMock(side_effect=[answers(returned), valid])
    assert asyncio.run(_validated_answers(ask, ["first", "second"], 2)) == valid
    assert ask.await_count == 2


def test_question_judge_exhaustion_is_an_error() -> None:
    ask = AsyncMock(return_value=QuestionAnswers(answers=[]))
    with pytest.raises(RecapJudgeError, match="exactly one answer"):
        asyncio.run(_validated_answers(ask, ["first"], 2))
    assert ask.await_count == 2


def _result(name: str, score: float) -> MetricResult:
    return MetricResult(metric_name=name, score=score, assessment="test")


def _passing_results() -> list[MetricResult]:
    return [
        _result("recap_summary_format", 1.0),
        _result("recap_summary_coverage", 1.0),
        _result("recap_summary_recognition", 1.0),
        _result("recap_summary_exclusion", 1.0),
        _result("recap_summary_alignment", 1.0),
        _result("recap_summary_conciseness", 0.8),
    ]


def test_extract_scene_breakdown_uses_only_ledger() -> None:
    assert extract_scene_breakdown(_INPUT).startswith('{"version": 1')


@pytest.mark.parametrize("source", ["{}", "not JSON", '{"version": 3}', ""])
def test_extract_rejects_invalid_ledger(source: str) -> None:
    with pytest.raises(RecapSummaryInputError):
        extract_scene_breakdown(f"<scene_breakdown>{source}</scene_breakdown>")


def test_extract_rejects_reversed_or_duplicate_tags() -> None:
    for source in ("</scene_breakdown><scene_breakdown>{}", _INPUT + _INPUT):
        with pytest.raises(RecapSummaryInputError):
            extract_scene_breakdown(source)


def test_extract_scene_breakdown_rejects_trailing_content() -> None:
    with pytest.raises(RecapSummaryInputError, match="Unexpected content"):
        extract_scene_breakdown(_INPUT + "\n<extra>not ledger</extra>")


def test_conciseness_is_independent_of_input_size_and_stops_rewarding_deletion() -> None:
    metric = RecapSummaryConcisenessMetric(RecapLengthSettings(target_words=5, max_words=10, max_bullets=2))
    for source in (_INPUT, _INPUT * 10):
        for output in ("- The bridge collapses.", "- The bridge over town collapses."):
            assert asyncio.run(metric.evaluate("# Prompt", EvalCase(input=source), output)).score == 1.0


@pytest.mark.parametrize(
    ("output", "score"),
    [
        ("- one two three four five six", 5 / 6),
        ("- one two three four five six seven eight nine ten", 0.5),
        ("- one two three four five six seven eight nine ten eleven", 0.0),
        ("- one\n- two\n- three", 0.0),
        ("", 0.0),
        ("## Recap\n- one", 0.0),
    ],
)
def test_length_limits_and_failure_feedback(output: str, score: float) -> None:
    metric = RecapSummaryConcisenessMetric(RecapLengthSettings(target_words=5, max_words=10, max_bullets=2))
    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT), output))
    assert result.score == pytest.approx(score)
    if output.startswith("- "):
        assert result.signals


def test_invalid_length_configuration() -> None:
    with pytest.raises(ValidationError):
        RecapLengthSettings(target_words=11, max_words=10, max_bullets=2)
    with pytest.raises(ValidationError):
        RecapLengthSettings(target_words=5, max_words=10, max_bullets=0)


@pytest.mark.parametrize(
    ("output", "expected"),
    [
        ("- The bridge collapses.\n- The party escapes.", 1.0),
        ("## Recap\n\n- The bridge collapses.", 0.0),
        ("- The bridge collapses.\n  - The party escapes.", 0.0),
        ("```markdown\n- The bridge collapses.\n```", 0.0),
        ("", 0.0),
        ("  - Indented first bullet.", 0.0),
        ("-\tTab instead of space.", 0.0),
        ("- First line.\nContinued prose.", 0.0),
        ("\n- One bullet.\n\n", 1.0),
    ],
)
def test_format_metric_accepts_only_flat_bullets(output: str, expected: float) -> None:
    result = asyncio.run(RecapSummaryFormatMetric().evaluate("# Prompt", EvalCase(input=_INPUT), output))
    assert result.score == expected


@pytest.mark.parametrize(
    "failed_metric",
    ["recap_summary_format", "recap_summary_coverage", "recap_summary_recognition", "recap_summary_exclusion", "recap_summary_alignment"],
)
def test_gated_scorer_returns_zero_when_any_gate_fails(failed_metric: str) -> None:
    results = _passing_results()
    for result in results:
        if result.metric_name == failed_metric:
            result.score = 0.99
    assert RecapSummaryGatedScorer().compute(results) == 0.0


def test_gated_scorer_returns_conciseness_after_all_gates_pass() -> None:
    assert RecapSummaryGatedScorer().compute(_passing_results()) == 0.8


def test_gated_scorer_rejects_missing_or_duplicate_results() -> None:
    with pytest.raises(ValueError, match="Missing"):
        RecapSummaryGatedScorer().compute(_passing_results()[:-1])
    with pytest.raises(ValueError, match="Duplicate"):
        RecapSummaryGatedScorer().compute(_passing_results() + [_result("recap_summary_format", 1.0)])


@pytest.mark.parametrize(("answer", "score"), [("yes", 0.0), ("no", 0.0), ("no_evidence", 1.0)])
def test_exclusions_require_absence_not_denial(answer: AnswerValue, score: float, monkeypatch: pytest.MonkeyPatch) -> None:
    question = "Does the recap mention the room price?"
    factory = AsyncMock()
    factory.questions.return_value = [question]
    metric = RecapSummaryExclusionMetric(LiteLLMConfig(model="test"), question_factory=factory)
    monkeypatch.setattr(
        metric,
        "_ask",
        AsyncMock(return_value=QuestionAnswers(answers=[QuestionAnswer(question=question, answer=answer, evidence="test")])),
    )
    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT, source_path="test.txt"), "- They arrived."))
    assert result.score == score


def test_checked_in_corpus_preflight() -> None:
    directory = Path(__file__).resolve().parents[3] / "data_prompts" / "recap_summary"
    cases = _load_eval_cases(directory / "inputs")
    assert len(cases) == 3
    settings = _load_settings(directory / "settings.yaml")
    assert settings.alignment_threshold == 1.0
    asyncio.run(validate_corpus(directory, cases))


def test_preflight_rejects_missing_questions_before_running(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="missing.*test"):
        asyncio.run(validate_corpus(tmp_path, [EvalCase(input=_INPUT, source_path="test.txt")]))


def test_alignment_receives_only_ledger_and_keeps_case_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    evaluate = AsyncMock(return_value=_result("recap_summary_alignment", 1.0))
    monkeypatch.setattr(DirectRecapAlignmentMetric, "evaluate", evaluate)
    case = EvalCase(input=_INPUT, source_path="test.txt")
    metric = RecapSummaryAlignmentMetric(LiteLLMConfig(model="test"))
    asyncio.run(metric.evaluate("# Prompt", case, "- The bridge collapses."))
    source_case = evaluate.call_args.args[1]
    assert source_case.source_path == "test.txt"
    assert source_case.input == extract_scene_breakdown(_INPUT)
    assert "session_metadata" not in source_case.input


def test_provenance_detects_modified_snapshot() -> None:
    directory = Path(__file__).resolve().parents[3] / "data_prompts" / "recap_summary" / "inputs"
    cases = _load_eval_cases(directory)
    cases[0] = cases[0].model_copy(update={"input": cases[0].input.replace("Brandonsford", "Altered")})
    with pytest.raises(ValueError, match="differs from its manifest"):
        validate_source_manifests(directory, cases)


def test_provenance_detects_template_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    directory = Path(__file__).resolve().parents[3] / "data_prompts" / "recap_summary" / "inputs"
    monkeypatch.setattr("optimize_prompts.optimize_recap_summary.read_prompt_template", lambda name: "changed template")
    with pytest.raises(ValueError, match="template changed"):
        validate_source_manifests(directory, _load_eval_cases(directory))
