"""Session processing's application layer: completion records, sections, restarts, drafts, failures, and the overview.

A Session is driven through the real producers step by step. Only transcription, LLM calls, audio import, and
speaker identification are stubbed; everything that records completion and decides staleness is real.
"""

from __future__ import annotations

import json
import os
import shutil
import time
import uuid
import wave
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlmodel import Session
from tablesage_application import Application
from tablesage_application import application as application_module
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.processing_steps import StepID
from tablesage_application.session_pipeline import import_audio, legacy_import, processing_state, transcribe_audio
from tablesage_application.session_pipeline.artifact_graph import ArtifactStatus
from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
from tablesage_model.model import Campaign, Player
from tablesage_model.settings import ReviewAudioNormalizationSettings
from tablesage_tools.model import Transcript, Utterance

_UTTERANCES = [("Anna", 0.0, 2.0, "We ride to Brandonsfrd."), ("Bo", 2.0, 4.0, "The dragon waits."), ("Anna", 4.0, 6.0, "Fine.")]


@dataclass
class _Stubs:
    glossary: list[GlossaryProposal]
    spelling: list[SpellingSuggestion]
    llm_calls: int = 0


def _transcript() -> Transcript:
    return Transcript(
        utterances=[
            Utterance(speaker=speaker, start=start, end=end, words=[], punctuated_text=text) for speaker, start, end, text in _UTTERANCES
        ]
    )


def _write_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 1600)


@pytest.fixture
def stubs(monkeypatch: pytest.MonkeyPatch) -> _Stubs:
    stubs = _Stubs(
        glossary=[GlossaryProposal(term="Brandonsford", description="A village.")],
        spelling=[SpellingSuggestion("Brandonsfrd", "Brandonsford", False, 1)],
    )

    def fake_import(
        source_path: Path,
        session_folder: Path,
        normalize_volume: bool,
        *,
        should_clean_audio: bool = True,
        review_normalization: ReviewAudioNormalizationSettings | None = None,
    ) -> None:
        shutil.copyfile(source_path, session_folder / "input_audio.wav")
        shutil.copyfile(source_path, session_folder / "normalized_review_audio.wav")

    def fake_create_transcript(session_folder: Path, *_args: object, **_kwargs: object) -> int:
        _transcript().save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
        (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_TEXT].filename).write_text("transcript", encoding="utf-8")
        return len(_UTTERANCES)

    async def fake_remove_backchannels(transcript: Transcript, *_args: object, **_kwargs: object) -> Transcript:
        return transcript

    def fake_identify(_folder: Path, transcript: Transcript, *_args: object, **_kwargs: object) -> Transcript:
        return transcript

    def fake_glossary(_self: Application, _session_id: object) -> list[GlossaryProposal]:
        stubs.llm_calls += 1
        return list(stubs.glossary)

    def fake_spelling(_self: Application, _session_id: object) -> tuple[Transcript, list[SpellingSuggestion]]:
        stubs.llm_calls += 1
        return _transcript(), list(stubs.spelling)

    monkeypatch.setattr(import_audio, "import_audio", fake_import)
    monkeypatch.setattr(transcribe_audio, "create_transcript", fake_create_transcript)
    monkeypatch.setattr(transcribe_audio, "identify_raw_transcript", fake_identify)
    monkeypatch.setattr(application_module, "remove_backchannels", fake_remove_backchannels)
    monkeypatch.setattr(Application, "embedding_factory", lambda self: None)
    monkeypatch.setattr(Application, "suggest_glossary_terms", fake_glossary)
    monkeypatch.setattr(Application, "suggest_glossary_spelling_corrections", fake_spelling)
    return stubs


def _returning_player(application: Application, name: str) -> Player:
    player = application.create_player(Player(name=name))
    with Session(application._engine) as session:
        stored = session.get(Player, player.id)
        assert stored is not None
        stored.voice_print_embedding = json.dumps([1.0, 0.0])
        stored.embedding_dimension = 2
        stored.sample_count = 3
        session.commit()
    return player


@pytest.fixture
def processed(tmp_path: Path, stubs: _Stubs) -> tuple[Application, uuid.UUID]:
    """A returning-players Session processed through Review Transcript (Assign Roles is next)."""
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    for name in ("Anna", "Bo"):
        application.add_attendance(game_session.id, _returning_player(application, name).id)
    sid = game_session.id
    source = tmp_path / "recording.wav"
    _write_wav(source)

    application.save_import_request(sid, source, clean_audio=False)
    application.import_requested_audio(sid)
    application.create_transcript(sid)
    application.remove_bad_utterances(sid)
    assert application.propose_name_corrections(sid) == []
    application.save_name_correction_decisions(sid, ())
    application.apply_name_corrections(sid)
    application.isolate_new_speakers(sid)
    application.confirm_new_speaker_assignment_review(sid, {})
    application.seed_player_voice_samples(sid)
    application.identify_session_speakers(sid)
    application.propose_glossary_terms(sid)
    application.save_glossary_decisions(sid, stubs.glossary)
    application.add_glossary_entries(sid)
    application.propose_spelling_corrections(sid)
    application.save_spelling_decisions(sid, stubs.spelling)
    application.apply_spelling_corrections(sid)
    application.save_transcript_review(sid, application.transcript_review_source(sid))
    application.apply_transcript_review(sid)
    return application, sid


def _incomplete(application: Application, sid: uuid.UUID) -> list[StepID]:
    return [state.step.id for state in application.processing_overview(sid).steps if not state.complete]


def test_processed_session_is_complete_through_review_and_assign_roles_is_next(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    overview = application.processing_overview(sid)

    assert overview.next_step is not None and overview.next_step.id is StepID.ASSIGN_ROLES
    assert _incomplete(application, sid)[0] is StepID.ASSIGN_ROLES
    # The spellcheck decision was applied to the document.
    spellchecked = application.transcript_review_source(sid)
    assert spellchecked.utterances[0].punctuated_text == "We ride to Brandonsford."


def test_returning_players_session_hides_new_player_rows(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    visible = [state.step.id for state in application.processing_overview(sid).steps if state.visible and state.step.is_manual]

    assert visible == [
        StepID.IMPORT_AUDIO,
        StepID.REVIEW_GLOSSARY_TERMS,
        StepID.REVIEW_SPELLING_CORRECTIONS,
        StepID.REVIEW_TRANSCRIPT,
        StepID.IMPROVE_VOICE_PRINTS,
    ]


def test_sections_replace_the_old_receipt_files(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    folder = application.session_folder(sid)
    sections = processing_state.load(folder).sections

    for name in (ArtifactName.NEW_SPEAKER_ASSIGNMENTS, ArtifactName.SEEDED_VOICE_SAMPLES, ArtifactName.EXTRACTED_GLOSSARY_TERMS):
        assert name.value in sections
        assert not (folder / ARTIFACTS[name].filename).exists()
    assert sections[ArtifactName.EXTRACTED_GLOSSARY_TERMS.value] == {"entries": [{"term": "Brandonsford", "description": "A village."}]}


def test_touching_every_file_keeps_everything_current(processed: tuple[Application, uuid.UUID]) -> None:
    """A copy or restore resets modification times; staleness is decided by content, so nothing changes."""
    application, sid = processed
    before = application.session_artifact_states(sid)
    later = time.time_ns() + 60_000_000_000
    for path in application.session_folder(sid).iterdir():
        os.utime(path, ns=(later, later))

    assert Application(application._cwd).session_artifact_states(sid) == before


def test_changing_a_document_makes_only_its_dependents_stale(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    folder = application.session_folder(sid)
    identified = folder / ARTIFACTS[ArtifactName.IDENTIFIED_TRANSCRIPT].filename
    transcript = Transcript.load(identified)
    transcript.utterances[1] = transcript.utterances[1].model_copy(update={"speaker": "Anna"})
    transcript.save(identified)

    states = application.session_artifact_states(sid)

    assert states[ArtifactName.NAME_CORRECTED_TRANSCRIPT] is ArtifactStatus.CURRENT
    assert states[ArtifactName.GLOSSARY_SUGGESTIONS] is ArtifactStatus.STALE
    assert states[ArtifactName.SPELLCHECKED_TRANSCRIPT] is ArtifactStatus.STALE
    # A hand-edited output stays its step's output; the first step that reads it runs next.
    next_step = application.processing_overview(sid).next_step
    assert next_step is not None and next_step.id is StepID.SUGGEST_GLOSSARY_TERMS


def test_reopened_step_completed_with_the_same_decision_leaves_later_steps_current(
    processed: tuple[Application, uuid.UUID], stubs: _Stubs
) -> None:
    application, sid = processed

    application.reopen_step(sid, StepID.REVIEW_GLOSSARY_TERMS)
    assert _incomplete(application, sid)[:3] == [
        StepID.REVIEW_GLOSSARY_TERMS,
        StepID.ADD_GLOSSARY_ENTRIES,
        StepID.SUGGEST_SPELLING_CORRECTIONS,
    ]
    # The reopened step keeps its decision, to reopen as it was left.
    _proposals, decided = application.glossary_term_review(sid)
    assert decided == stubs.glossary

    application.save_glossary_decisions(sid, stubs.glossary)

    assert _incomplete(application, sid)[0] is StepID.ASSIGN_ROLES


def test_a_changed_decision_makes_the_steps_after_it_run_again(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed

    application.save_glossary_decisions(sid, [GlossaryProposal(term="Veyra", description=None)])

    assert _incomplete(application, sid)[:2] == [StepID.ADD_GLOSSARY_ENTRIES, StepID.SUGGEST_SPELLING_CORRECTIONS]


def test_re_adding_the_same_glossary_decision_keeps_spellcheck_current(processed: tuple[Application, uuid.UUID]) -> None:
    """The receipt lists the decided entries, not the newly added ones, so a repeat commit changes nothing downstream."""
    application, sid = processed
    application.reopen_step(sid, StepID.ADD_GLOSSARY_ENTRIES)

    result = application.add_glossary_entries(sid)

    assert result.added_count == 0 and result.skipped_duplicate_count == 1
    assert _incomplete(application, sid)[0] is StepID.ASSIGN_ROLES


def test_empty_decision_is_reported_as_nothing_to_review(tmp_path: Path, processed: tuple[Application, uuid.UUID], stubs: _Stubs) -> None:
    application, sid = processed
    stubs.glossary = []
    application.propose_glossary_terms(sid)
    application.save_glossary_decisions(sid, ())

    state = application.processing_overview(sid).state(StepID.REVIEW_GLOSSARY_TERMS)

    assert state.complete and state.nothing_to_review


def test_draft_is_offered_until_what_it_reviews_changes(processed: tuple[Application, uuid.UUID], stubs: _Stubs) -> None:
    application, sid = processed
    step = StepID.REVIEW_GLOSSARY_TERMS.value
    application.save_step_draft(sid, step, ArtifactName.GLOSSARY_SUGGESTIONS, [{"term": "Draft", "description": None}])

    assert application.load_step_draft(sid, step) == [{"term": "Draft", "description": None}]

    stubs.glossary = [GlossaryProposal(term="Something else", description=None)]
    application.propose_glossary_terms(sid)
    assert application.load_step_draft(sid, step) is None


def test_review_transcript_draft_and_saved_review_round_trip_as_edit_lists(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    source = application.transcript_review_source(sid)
    edited = Transcript(utterances=[source.utterances[0].model_copy(update={"speaker": "Bo", "adjusted": True}), source.utterances[2]])

    application.save_review_draft(sid, edited)
    draft = application.load_review_draft(sid)
    assert draft is not None and draft.transcript == edited

    application.save_transcript_review(sid, edited)
    assert application.load_review_draft(sid) is None
    saved = application.saved_transcript_review(sid)
    assert saved is not None and saved.transcript == edited
    assert _incomplete(application, sid)[0] is StepID.APPLY_TRANSCRIPT_REVIEW


def test_step_failures_are_kept_until_cleared(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed

    application.record_step_failure(sid, StepID.ASSIGN_ROLES, "Assign Roles failed: boom", "run1")
    assert application.processing_overview(sid).state(StepID.ASSIGN_ROLES).failure == "Assign Roles failed: boom"

    application.clear_step_failure(sid, StepID.ASSIGN_ROLES)
    assert application.processing_overview(sid).state(StepID.ASSIGN_ROLES).failure is None


def test_prior_rebuild_approval_is_complete_when_nothing_needs_rebuilding(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed

    assert application.prior_rebuild_tasks(sid) == ()
    state = application.processing_overview(sid).state(StepID.APPROVE_PRIOR_REBUILD)
    assert not state.visible


def test_new_players_show_their_rows_before_isolation(tmp_path: Path, stubs: _Stubs) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    application.add_attendance(game_session.id, application.create_player(Player(name="Newcomer")).id)

    overview = application.processing_overview(game_session.id)

    assert overview.new_players == ("Newcomer",)
    assert overview.state(StepID.REVIEW_NAME_CORRECTIONS).visible
    assert overview.state(StepID.REVIEW_NEW_SPEAKER_ASSIGNMENTS).visible
    assert overview.next_step is not None and overview.next_step.id is StepID.IMPORT_AUDIO


def test_session_without_attendees_is_blocked(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    assert application.processing_overview(game_session.id).blockers == ("This Session has no attendees. Add them on Session Detail.",)


def test_clean_session_removes_the_processing_state(processed: tuple[Application, uuid.UUID]) -> None:
    application, sid = processed
    folder = application.session_folder(sid)

    application.clean_session(sid)

    assert not processing_state.exists(folder)
    next_step = application.processing_overview(sid).next_step
    assert next_step is not None and next_step.id is StepID.IMPORT_AUDIO


# Legacy import


def test_legacy_sections_are_placeholders_only_where_the_work_was_current(tmp_path: Path) -> None:
    (tmp_path / "input_audio.wav").write_bytes(b"audio")
    (tmp_path / "new_speaker_assignments.json").write_text('{"players": [], "evidence": []}', encoding="utf-8")
    (tmp_path / "seeded_voice_samples.json").write_text("not json", encoding="utf-8")
    current = {ArtifactName.INPUT_AUDIO, ArtifactName.NAME_CORRECTED_TRANSCRIPT, ArtifactName.NEW_SPEAKER_ASSIGNMENTS}

    sections, carried = legacy_import.build_sections(tmp_path, current)

    assert sections["import_request"]["legacy"] is True
    assert sections["name_correction_decisions"] == {"corrections": [], "legacy": True}
    assert sections["new_speaker_assignments"] == {"players": [], "evidence": []}
    assert sections["seeded_voice_samples"] == {"legacy": True, "unreadable": True}
    assert "glossary_decisions" not in sections and "spelling_decisions" not in sections
    assert ArtifactName.NEW_SPEAKER_ASSIGNMENTS in carried
    assert ArtifactName.SEEDED_VOICE_SAMPLES not in carried


def test_legacy_import_moves_retired_files_aside(tmp_path: Path) -> None:
    (tmp_path / "new_speaker_assignments.json").write_text("{}", encoding="utf-8")
    (tmp_path / "transcript.json").write_text("{}", encoding="utf-8")

    moved = legacy_import.move_retired_files(tmp_path)

    assert moved == ["new_speaker_assignments.json"]
    assert (tmp_path / "legacy" / "new_speaker_assignments.json").exists()
    assert (tmp_path / "transcript.json").exists()
