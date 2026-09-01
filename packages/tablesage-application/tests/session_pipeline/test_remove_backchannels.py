from __future__ import annotations

import pytest
from tablesage_application.session_pipeline import remove_backchannels as remove_backchannels_module
from tablesage_application.session_pipeline.remove_backchannels import BackchannelJudgment, BackchannelJudgments, remove_backchannels
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import UNASSIGNED_SPEAKER


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
    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert result == transcript


@pytest.mark.anyio
async def test_removes_candidate_whose_previous_utterance_is_not_a_question(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=False)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert [utterance.text for utterance in result.utterances] == ["Are you coming", "Let's go"]


@pytest.mark.anyio
async def test_keeps_candidate_whose_previous_utterance_is_a_question(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=True)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert result == transcript


@pytest.mark.anyio
async def test_llm_failure_fails_open_and_keeps_everything(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()

    async def _failing_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        raise RuntimeError("litellm exploded")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _failing_call_llm_with_prompt)

    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

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
    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert result == transcript


@pytest.mark.anyio
async def test_unassigned_speaker_candidate_removed_without_calling_llm(monkeypatch: pytest.MonkeyPatch) -> None:
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

    async def _fail_if_called(*args: object, **kwargs: object) -> str:
        raise AssertionError("should not call the LLM for an unassigned-speaker candidate")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _fail_if_called)
    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert [utterance.text for utterance in result.utterances] == ["Are you coming", "Let's go"]


@pytest.mark.anyio
async def test_first_utterance_unassigned_speaker_candidate_is_still_removed_without_calling_llm(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transcript = Transcript.from_words(
        [
            _word("Yeah", UNASSIGNED_SPEAKER, 0.0, 0.3),
            _word("Anyway", "speaker_1", 0.3, 0.6),
        ]
    )

    async def _fail_if_called(*args: object, **kwargs: object) -> str:
        raise AssertionError("should not call the LLM for an unassigned-speaker candidate")

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _fail_if_called)
    result = await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert [utterance.text for utterance in result.utterances] == ["Anyway"]


@pytest.mark.anyio
async def test_question_timeout_forwarded_to_llm_call(monkeypatch: pytest.MonkeyPatch) -> None:
    transcript = _transcript_with_candidate()
    captured: dict[str, object] = {}

    async def _capturing_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        captured.update(kwargs)
        return BackchannelJudgments(scratchpad="", judgments=[BackchannelJudgment(candidate_id=1, is_question=True)]).model_dump_json()

    monkeypatch.setattr(remove_backchannels_module, "call_llm_with_prompt", _capturing_call_llm_with_prompt)

    await remove_backchannels(transcript, max_words=3, llm_model="anthropic/claude-haiku-4-5", question_timeout=1200)

    assert captured["timeout"] == 1200
