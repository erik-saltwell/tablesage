from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import clean_transcript as clean_transcript_module
from tablesage_application.session_pipeline.clean_transcript import (
    CleanTranscriptResult,
    Stage,
    can_clean_transcript,
    clean_transcript,
    render_role_transcript_text,
)
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord
from tablesage_tools.speakers import UNASSIGNED_SPEAKER


def _word(text: str, speaker: str, start: float, end: float) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=start, end=end, speaker=speaker)


def _transcript() -> Transcript:
    return Transcript.from_words(
        [
            _word("hello", "Alice", 0.0, 1.0),
            _word("world", "Bob", 1.0, 2.0),
        ]
    )


def test_can_clean_transcript_requires_machine_transcript(tmp_path: Path) -> None:
    enabled, reason = can_clean_transcript(tmp_path)
    assert enabled is False
    assert reason == "Transcribe the session first."

    _transcript().save(tmp_path / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)

    enabled, reason = can_clean_transcript(tmp_path)
    assert enabled is True
    assert reason is None


async def _no_op_remove_backchannels(transcript: Transcript, max_words: int, llm_model: str, question_timeout: float) -> Transcript:
    return transcript


def test_clean_transcript_writes_role_transcript_and_invalidates_derivatives(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clean_transcript_module, "remove_backchannels", _no_op_remove_backchannels)

    _transcript().save(tmp_path / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    ledger_path = tmp_path / ARTIFACTS[ArtifactName.LEDGER].filename
    summary_path = tmp_path / ARTIFACTS[ArtifactName.SUMMARY].filename
    ledger_path.write_text("{}")
    summary_path.write_text("stale summary")

    result = clean_transcript(
        tmp_path, max_words=3, question_timeout=1200, llm_model_lite="anthropic/claude-haiku-4-5", role_names={"Alice": "Wizard"}
    )

    assert result == CleanTranscriptResult(utterance_count=2, removed_count=0)
    assert not ledger_path.exists()
    assert not summary_path.exists()

    role_transcript = Transcript.load(tmp_path / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
    assert [utterance.speaker for utterance in role_transcript.utterances] == ["Wizard", "Bob"]


def test_clean_transcript_never_renames_unassigned_speaker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clean_transcript_module, "remove_backchannels", _no_op_remove_backchannels)

    transcript = Transcript.from_words(
        [
            _word("hello", UNASSIGNED_SPEAKER, 0.0, 1.0),
        ]
    )
    transcript.save(tmp_path / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)

    clean_transcript(tmp_path, max_words=3, question_timeout=1200, llm_model_lite="anthropic/claude-haiku-4-5", role_names={})

    role_transcript = Transcript.load(tmp_path / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
    assert role_transcript.utterances[0].speaker == UNASSIGNED_SPEAKER


def test_clean_transcript_reports_staged_progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(clean_transcript_module, "remove_backchannels", _no_op_remove_backchannels)
    _transcript().save(tmp_path / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)

    calls: list[tuple[Stage, int, int]] = []
    clean_transcript(
        tmp_path,
        max_words=3,
        question_timeout=1200,
        llm_model_lite="anthropic/claude-haiku-4-5",
        role_names={},
        on_progress=lambda stage, completed, total: calls.append((stage, completed, total)),
    )

    assert calls == [
        (Stage.REMOVING_BACKCHANNELS, 0, 0),
        (Stage.REMOVING_BACKCHANNELS, 1, 1),
        (Stage.ASSIGNING_ROLES, 0, 0),
        (Stage.ASSIGNING_ROLES, 1, 1),
    ]


def test_render_role_transcript_text(tmp_path: Path) -> None:
    role_transcript = Transcript.from_words(
        [
            _word("hello", "Wizard", 0.0, 1.0),
            _word("world", UNASSIGNED_SPEAKER, 1.0, 2.0),
        ]
    )
    role_transcript.save(tmp_path / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)

    assert render_role_transcript_text(tmp_path) == f"**Wizard** - hello\n\n**{UNASSIGNED_SPEAKER}** - world\n"
