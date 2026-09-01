from __future__ import annotations

import asyncio
from typing import cast

import pytest
from tablesage_application.session_pipeline import remove_backchannels as remove_backchannels_module
from tablesage_application.session_pipeline.remove_backchannels import (
    BackchannelClassificationPromptData,
    BackchannelJudgment,
    BackchannelJudgments,
    remove_backchannels,
)
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript_with_candidate() -> Transcript:
    return Transcript.from_words(
        [
            _word("Are", "speaker_0", 0.0, 0.3),
            _word("you", "speaker_0", 0.3, 0.6),
            _word("coming", "speaker_0", 0.6, 0.9),
            _word("Yeah", "speaker_1", 0.9, 1.2),
            _word("Let's", "speaker_0", 1.2, 1.5),
            _word("go", "speaker_0", 1.5, 1.8),
        ]
    )


@pytest.mark.anyio
async def test_no_candidates_returns_transcript_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = Transcript.from_words([_word("Fireball", "speaker_0", 0.0, 0.5)])

    async def _fail_if_called(*args: object, **kwargs: object) -> str:
        raise AssertionError("should not call the LLM when there are no candidates")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _fail_if_called)
    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert result == transcript


@pytest.mark.anyio
async def test_removes_candidate_whose_previous_utterance_is_not_a_question(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=False)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert [utterance.text for utterance in result.utterances] == ["Are you coming", "Let's go"]


@pytest.mark.anyio
async def test_keeps_candidate_whose_previous_utterance_is_a_question(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=True)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert result == transcript


@pytest.mark.anyio
async def test_llm_failure_fails_open_and_keeps_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _failing_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        raise RuntimeError("litellm exploded")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _failing_call_llm_with_prompt)

    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert result == transcript


@pytest.mark.anyio
async def test_first_utterance_candidate_is_never_removed_without_calling_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = Transcript.from_words(
        [
            _word("Yeah", "speaker_0", 0.0, 0.3),
            _word("Anyway", "speaker_1", 0.3, 0.6),
        ]
    )

    async def _fail_if_called(*args: object, **kwargs: object) -> str:
        raise AssertionError("should not call the LLM for a first-utterance-only candidate")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _fail_if_called)
    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert result == transcript


@pytest.mark.anyio
async def test_unassigned_speaker_candidate_still_needs_llm_judgment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pre-review, speaker assignment isn't human-confirmed yet, so there's no unassigned-speaker
    shortcut here (unlike the post-review pass in `clean_transcript.py`) -- every candidate,
    regardless of speaker, is judged the same way."""
    from tablesage_tools.speakers import UNASSIGNED_SPEAKER

    transcript = Transcript.from_words(
        [
            _word("Are", "speaker_0", 0.0, 0.3),
            _word("you", "speaker_0", 0.3, 0.6),
            _word("coming", "speaker_0", 0.6, 0.9),
            _word("Yeah", UNASSIGNED_SPEAKER, 0.9, 1.2),
            _word("Let's", "speaker_0", 1.2, 1.5),
            _word("go", "speaker_0", 1.5, 1.8),
        ]
    )
    captured: dict[str, object] = {}

    async def _capturing_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        captured.update(kwargs)
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=True)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _capturing_call_llm_with_prompt)

    await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=50, max_concurrent_batches=4
    )

    assert captured  # the LLM was called even though the candidate's speaker is unassigned


@pytest.mark.anyio
async def test_candidates_are_split_into_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    words = [_word("Are", "speaker_0", 0.0, 0.3)]
    for i in range(5):
        words.append(_word("Yeah", "speaker_1", 1.0 + i, 1.1 + i))
        words.append(_word("more", "speaker_0", 2.0 + i, 2.1 + i))
    transcript = Transcript.from_words(words)

    batch_sizes: list[int] = []

    async def _capturing_call_llm_with_prompt(
        prompt: object, template_data: BackchannelClassificationPromptData, model: str, **kwargs: object
    ) -> str:
        candidates = template_data.candidates
        batch_sizes.append(len(candidates))
        judgments = [BackchannelJudgment(candidate_id=cast(int, c["candidate_id"]), is_question=False) for c in candidates]
        return BackchannelJudgments(scratchpad="", judgments=judgments).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _capturing_call_llm_with_prompt)

    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=2, max_concurrent_batches=4
    )

    assert sorted(batch_sizes) == [1, 2, 2]  # 5 candidates, batch_size=2 -> 3 batches
    assert "Yeah" not in [utterance.text for utterance in result.utterances]  # every "Yeah" candidate removed
    assert len(result.utterances) == 6  # "Are" + 5 "more" filler utterances survive


@pytest.mark.anyio
async def test_batches_run_with_bounded_concurrency(monkeypatch: pytest.MonkeyPatch) -> None:
    words = [_word("Are", "speaker_0", 0.0, 0.3)]
    for i in range(6):
        words.append(_word("Yeah", "speaker_1", 1.0 + i, 1.1 + i))
        words.append(_word("more", "speaker_0", 2.0 + i, 2.1 + i))
    transcript = Transcript.from_words(words)

    in_flight = 0
    max_in_flight = 0
    lock = asyncio.Lock()

    async def _slow_call_llm_with_prompt(
        prompt: object, template_data: BackchannelClassificationPromptData, model: str, **kwargs: object
    ) -> str:
        nonlocal in_flight, max_in_flight
        async with lock:
            in_flight += 1
            max_in_flight = max(max_in_flight, in_flight)
        await asyncio.sleep(0.01)
        async with lock:
            in_flight -= 1
        candidates = template_data.candidates
        judgments = [BackchannelJudgment(candidate_id=cast(int, c["candidate_id"]), is_question=True) for c in candidates]
        return BackchannelJudgments(scratchpad="", judgments=judgments).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _slow_call_llm_with_prompt)

    await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=1, max_concurrent_batches=2
    )

    assert max_in_flight <= 2


@pytest.mark.anyio
async def test_progress_reports_completed_of_total_batches(monkeypatch: pytest.MonkeyPatch) -> None:
    words = [_word("Are", "speaker_0", 0.0, 0.3)]
    for i in range(4):
        words.append(_word("Yeah", "speaker_1", 1.0 + i, 1.1 + i))
        words.append(_word("more", "speaker_0", 2.0 + i, 2.1 + i))
    transcript = Transcript.from_words(words)

    async def _stub_call_llm_with_prompt(
        prompt: object, template_data: BackchannelClassificationPromptData, model: str, **kwargs: object
    ) -> str:
        candidates = template_data.candidates
        judgments = [BackchannelJudgment(candidate_id=cast(int, c["candidate_id"]), is_question=True) for c in candidates]
        return BackchannelJudgments(scratchpad="", judgments=judgments).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    calls: list[tuple[int, int]] = []
    await remove_backchannels(
        transcript,
        max_words=3,
        llm_model="anthropic/claude-haiku-4-5",
        question_timeout=120,
        batch_size=2,
        max_concurrent_batches=4,
        on_progress=lambda completed, total: calls.append((completed, total)),
    )

    assert len(calls) == 2  # 4 candidates, batch_size=2 -> 2 batches
    assert all(total == 2 for _completed, total in calls)
    assert sorted(completed for completed, _total in calls) == [1, 2]


@pytest.mark.anyio
async def test_partial_fail_open_keeps_successful_batches_removals(monkeypatch: pytest.MonkeyPatch) -> None:
    """One batch's LLM call failing must not discard another batch's successful judgments."""
    words = [_word("Are", "speaker_0", 0.0, 0.3)]
    for i in range(4):
        words.append(_word("Yeah", "speaker_1", 1.0 + i, 1.1 + i))
        words.append(_word("more", "speaker_0", 2.0 + i, 2.1 + i))
    transcript = Transcript.from_words(words)

    call_count = 0

    async def _flaky_call_llm_with_prompt(
        prompt: object, template_data: BackchannelClassificationPromptData, model: str, **kwargs: object
    ) -> str:
        nonlocal call_count
        call_count += 1
        candidates = template_data.candidates
        if call_count == 1:
            raise RuntimeError("this batch's call failed")
        judgments = [BackchannelJudgment(candidate_id=cast(int, c["candidate_id"]), is_question=False) for c in candidates]
        return BackchannelJudgments(scratchpad="", judgments=judgments).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _flaky_call_llm_with_prompt)

    result = await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=120, batch_size=2, max_concurrent_batches=1
    )

    # batch 1 (candidates 1,2) failed -> kept; batch 2 (candidates 3,4) succeeded -> removed.
    assert call_count == 2
    remaining_speakers = [utterance.speaker for utterance in result.utterances]
    assert remaining_speakers.count("speaker_1") == 2  # both candidates from the failed (first) batch survived


@pytest.mark.anyio
async def test_question_timeout_forwarded_per_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()
    captured: dict[str, object] = {}

    async def _capturing_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        captured.update(kwargs)
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=True)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _capturing_call_llm_with_prompt)

    await remove_backchannels(
        transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=42, batch_size=50, max_concurrent_batches=4
    )

    assert captured["timeout"] == 42
