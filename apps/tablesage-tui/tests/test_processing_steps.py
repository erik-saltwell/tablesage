"""The individual processing steps: what each one shows, saves, and returns.

Each step runs against a fake step context (scripted screen results, work run inline) and a mock application, so these
tests pin down every step's behavior -- auto-completing empty reviews, reopening as left, drafts, cancel -- without a
running app or the coordinator.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from tablesage_application.paths import ArtifactName
from tablesage_application.players_from_session import EnhanceResult
from tablesage_application.processing_steps import StepID
from tablesage_application.session_pipeline.artifact_graph import GenerationTask
from tablesage_application.session_pipeline.extract_glossary import GlossaryCommitResult, GlossaryProposal
from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
from tablesage_tools.model import Transcript
from tablesage_tui.corrections_review import DraftCorrection
from tablesage_tui.dialogs.file_picker import FileOpen
from tablesage_tui.processing import steps
from tablesage_tui.processing.coordinator import Outcome, StepResult
from tablesage_tui.screens.corrections_step import CorrectionsStepScreen
from tablesage_tui.screens.glossary_review import GlossaryReviewScreen
from tablesage_tui.screens.new_speaker_assignments import NewSpeakerAssignmentsScreen
from tablesage_tui.screens.speaker_review import ManualReviewScreen


class _Context:
    """Stands in for `StepContext`: screens return scripted results; background and quick work run inline."""

    def __init__(self, application: MagicMock, *results: object) -> None:
        self.application = application
        self.session_id = uuid.uuid4()
        self.facts: dict[str, Any] = {}
        self.shown: list[object] = []
        self.background_messages: list[str] = []
        self.notified: list[tuple[str, str]] = []
        self._results = list(results)

    async def background(self, message: str, work: Callable[[], Any]) -> Any:
        self.background_messages.append(message)
        return work()

    async def call(self, work: Callable[[], Any]) -> Any:
        return work()

    def progress(self, message: str, completed: int = 0, total: int = 0) -> None:
        pass

    async def show(self, screen: object) -> object:
        self.shown.append(screen)
        return self._results.pop(0)

    async def confirm(self, **dialog: Any) -> object:
        self.shown.append(("confirm", dialog))
        return self._results.pop(0)

    def notify(self, message: str, *, severity: str = "information") -> None:  # same shape as StepContext.notify
        self.notified.append((message, severity))


def _run(step: Callable[[Any], Coroutine[Any, Any, StepResult]], context: _Context) -> StepResult:
    return asyncio.run(step(context))


def _application(**configured: Any) -> MagicMock:
    application = MagicMock()
    application.is_imported_placeholder.return_value = False
    application.load_step_draft.return_value = None
    for name, value in configured.items():
        getattr(application, name).return_value = value
    return application


_TRANSCRIPT = Transcript(utterances=[])
_SUGGESTION = SpellingSuggestion("Brandonsfrd", "Brandonsford", False, 2)
_DECISION = SpellingSuggestion("Rach", "Rich", True, 0)


def test_every_step_has_a_function() -> None:
    assert set(steps.STEP_FUNCTIONS) == set(StepID)


# Review Name Corrections and Spellcheck Against Glossary (shared review)


def test_corrections_review_with_nothing_to_review_saves_an_empty_decision_without_a_screen() -> None:
    application = _application(name_correction_review=(_TRANSCRIPT, [], None))
    context = _Context(application)

    result = _run(steps.review_name_corrections, context)

    assert result.outcome is Outcome.SUCCESS
    assert context.shown == []
    application.save_name_correction_decisions.assert_called_once_with(context.session_id, ())


def test_corrections_review_shows_suggestions_and_saves_the_reviewed_rows() -> None:
    application = _application(name_correction_review=(_TRANSCRIPT, [_SUGGESTION], None))
    reviewed = [DraftCorrection(id=uuid.uuid4(), from_text="Brandonsfrd", to_text="Brandonsford", case_sensitive=False)]
    context = _Context(application, reviewed)

    result = _run(steps.review_name_corrections, context)

    assert result.outcome is Outcome.SUCCESS
    (screen,) = context.shown
    assert isinstance(screen, CorrectionsStepScreen)
    assert screen._suggestions == [_SUGGESTION]
    application.save_name_correction_decisions.assert_called_once_with(context.session_id, reviewed)
    application.discard_step_draft.assert_called_once_with(context.session_id, StepID.REVIEW_NAME_CORRECTIONS.value)


def test_corrections_review_reopens_with_the_last_decision() -> None:
    application = _application(spelling_review=(_TRANSCRIPT, [_SUGGESTION], [_DECISION]))
    context = _Context(application, [])

    _run(steps.review_spelling_corrections, context)

    (screen,) = context.shown
    assert isinstance(screen, CorrectionsStepScreen)
    assert screen._suggestions == [_DECISION]


def test_corrections_review_reopens_from_a_saved_draft_first() -> None:
    application = _application(spelling_review=(_TRANSCRIPT, [_SUGGESTION], [_DECISION]))
    application.load_step_draft.return_value = [{"from_text": "Draft", "to_text": "Draught", "case_sensitive": False}]
    context = _Context(application, [])

    _run(steps.review_spelling_corrections, context)

    (screen,) = context.shown
    assert isinstance(screen, CorrectionsStepScreen)
    assert [(row.from_text, row.to_text) for row in screen._suggestions] == [("Draft", "Draught")]


def test_corrections_review_cancel_saves_nothing() -> None:
    application = _application(name_correction_review=(_TRANSCRIPT, [_SUGGESTION], None))
    context = _Context(application, None)

    result = _run(steps.review_name_corrections, context)

    assert result.outcome is Outcome.CANCEL
    application.save_name_correction_decisions.assert_not_called()


def test_corrections_review_on_an_imported_session_suggests_again_first() -> None:
    application = _application(spelling_review=(_TRANSCRIPT, [_SUGGESTION], None))
    application.is_imported_placeholder.return_value = True
    context = _Context(application, [])

    _run(steps.review_spelling_corrections, context)

    application.is_imported_placeholder.assert_called_once_with(context.session_id, ArtifactName.SPELLING_SUGGESTIONS)
    application.propose_spelling_corrections.assert_called_once_with(context.session_id)


# Extract Glossary Terms


_PROPOSAL = GlossaryProposal(term="Veyra", description="An envoy.")


def test_glossary_review_with_no_proposals_completes_empty() -> None:
    application = _application(glossary_term_review=([], None))
    context = _Context(application)

    result = _run(steps.review_glossary_terms, context)

    assert result.outcome is Outcome.SUCCESS and context.shown == []
    application.save_glossary_decisions.assert_called_once_with(context.session_id, ())


def test_glossary_review_saves_the_reviewed_entries() -> None:
    application = _application(glossary_term_review=([_PROPOSAL], None))
    context = _Context(application, [_PROPOSAL])

    result = _run(steps.review_glossary_terms, context)

    assert result.outcome is Outcome.SUCCESS
    assert isinstance(context.shown[0], GlossaryReviewScreen)
    application.save_glossary_decisions.assert_called_once_with(context.session_id, [_PROPOSAL])


def test_glossary_review_reopens_with_a_decision_even_when_proposals_are_now_empty() -> None:
    kept = GlossaryProposal(term="Kept", description=None)
    application = _application(glossary_term_review=([], [kept]))
    context = _Context(application, None)

    result = _run(steps.review_glossary_terms, context)

    assert result.outcome is Outcome.CANCEL
    (screen,) = context.shown
    assert isinstance(screen, GlossaryReviewScreen)
    assert [entry.term for entry in screen._entries] == ["Kept"]
    application.save_glossary_decisions.assert_not_called()


def test_add_glossary_entries_reports_what_was_added() -> None:
    application = _application(add_glossary_entries=GlossaryCommitResult(added_count=2, skipped_duplicate_count=1))

    result = _run(steps.add_glossary_entries, _Context(application))

    assert result == StepResult.success("Added 2 glossary entries. Skipped 1 duplicate.")


def test_add_glossary_entries_is_quiet_when_nothing_was_new() -> None:
    application = _application(add_glossary_entries=GlossaryCommitResult(added_count=0, skipped_duplicate_count=3))

    assert _run(steps.add_glossary_entries, _Context(application)) == StepResult.success()


# Review New Speaker Assignments


def test_new_speaker_review_without_new_players_saves_an_empty_review() -> None:
    application = _application(new_speaker_proposals=MagicMock(players=()))
    context = _Context(application)

    result = _run(steps.review_new_speaker_assignments, context)

    assert result.outcome is Outcome.SUCCESS and context.shown == []
    application.confirm_new_speaker_assignment_review.assert_called_once_with(context.session_id, {})


def test_new_speaker_review_saves_kept_and_rejected_utterances() -> None:
    player_id = uuid.uuid4()
    application = _application(new_speaker_proposals=MagicMock(players=(object(),)))
    context = _Context(application, ({player_id: [1, 2]}, {player_id: [7]}))

    result = _run(steps.review_new_speaker_assignments, context)

    assert result.outcome is Outcome.SUCCESS
    assert isinstance(context.shown[0], NewSpeakerAssignmentsScreen)
    application.confirm_new_speaker_assignment_review.assert_called_once_with(context.session_id, {player_id: [1, 2]}, {player_id: [7]})


def test_new_speaker_review_cancel_saves_nothing() -> None:
    application = _application(new_speaker_proposals=MagicMock(players=(object(),)))

    result = _run(steps.review_new_speaker_assignments, _Context(application, None))

    assert result.outcome is Outcome.CANCEL
    application.confirm_new_speaker_assignment_review.assert_not_called()


# Review Transcript


def test_review_transcript_saves_the_edited_transcript_as_its_decision() -> None:
    application = _application()
    edited = Transcript(utterances=[])
    context = _Context(application, edited)

    result = _run(steps.review_transcript, context)

    assert result.outcome is Outcome.SUCCESS
    assert isinstance(context.shown[0], ManualReviewScreen)
    application.save_transcript_review.assert_called_once_with(context.session_id, edited)


def test_review_transcript_cancel_saves_nothing() -> None:
    application = _application()

    assert _run(steps.review_transcript, _Context(application, None)).outcome is Outcome.CANCEL
    application.save_transcript_review.assert_not_called()


# Import Audio


def _import_application() -> MagicMock:
    application = _application()
    application.audio_import_extensions.return_value = frozenset({".wav", ".m4a"})
    return application


def test_import_audio_cancelled_picker_cancels_the_step() -> None:
    application = _import_application()

    result = _run(steps.import_audio, _Context(application, None))

    assert result.outcome is Outcome.CANCEL
    application.save_import_request.assert_not_called()


def test_import_audio_checks_credentials_before_the_picker() -> None:
    application = _import_application()

    _run(steps.import_audio, _Context(application, None))

    application.require_credentials.assert_called_once_with("llm_model_lite", transcription=True)


def test_import_audio_wav_asks_whether_to_clean() -> None:
    application = _import_application()
    context = _Context(application, Path("/audio/game.wav"), False)

    result = _run(steps.import_audio, context)

    assert result.outcome is Outcome.SUCCESS
    assert isinstance(context.shown[0], FileOpen)
    prompt = context.shown[1]
    assert isinstance(prompt, tuple) and prompt[0] == "confirm"
    application.save_import_request.assert_called_once_with(context.session_id, Path("/audio/game.wav"), clean_audio=False)


def test_import_audio_other_formats_are_always_cleaned() -> None:
    application = _import_application()
    context = _Context(application, Path("/audio/game.m4a"))

    _run(steps.import_audio, context)

    assert len(context.shown) == 1
    application.save_import_request.assert_called_once_with(context.session_id, Path("/audio/game.m4a"), clean_audio=True)


def test_import_audio_cancel_at_the_clean_prompt_cancels_the_step() -> None:
    application = _import_application()

    result = _run(steps.import_audio, _Context(application, Path("/audio/game.wav"), None))

    assert result.outcome is Outcome.CANCEL
    application.save_import_request.assert_not_called()


def test_import_audio_rejected_file_reopens_the_picker_where_it_was() -> None:
    application = _import_application()
    application.validate_import_audio_source.side_effect = [ValueError("Not an audio file."), None]
    context = _Context(application, Path("/audio/notes.txt"), Path("/audio/game.m4a"))

    result = _run(steps.import_audio, context)

    assert result.outcome is Outcome.SUCCESS
    assert context.notified == [("Not an audio file.", "error")]
    second_picker = context.shown[1]
    assert isinstance(second_picker, FileOpen)


# Generate Artifacts and its prior-Session approval


def test_approval_with_nothing_to_rebuild_completes_without_asking() -> None:
    application = _application(prior_rebuild_tasks=())
    context = _Context(application)

    result = _run(steps.approve_prior_rebuild, context)

    assert result.outcome is Outcome.SUCCESS and context.shown == []
    application.approve_prior_rebuild.assert_called_once_with(context.session_id, ())


def test_approval_asks_before_rebuilding_prior_sessions() -> None:
    tasks = (GenerationTask(uuid.uuid4(), ArtifactName.RECAP_SUMMARY),)
    application = _application(prior_rebuild_tasks=tasks)
    context = _Context(application, True)

    result = _run(steps.approve_prior_rebuild, context)

    assert result.outcome is Outcome.SUCCESS
    application.approve_prior_rebuild.assert_called_once_with(context.session_id, tasks)


def test_declining_the_prior_rebuild_cancels() -> None:
    tasks = (GenerationTask(uuid.uuid4(), ArtifactName.RECAP_SUMMARY),)
    application = _application(prior_rebuild_tasks=tasks)

    result = _run(steps.approve_prior_rebuild, _Context(application, False))

    assert result.outcome is Outcome.CANCEL
    application.approve_prior_rebuild.assert_not_called()


def test_generation_uses_a_forced_artifact_once_and_reports_the_count() -> None:
    session_id = uuid.uuid4()
    plan = (GenerationTask(session_id, ArtifactName.LEDGER), GenerationTask(session_id, ArtifactName.SUMMARY))
    application = _application(generate_outputs=plan)
    context = _Context(application)
    context.facts["force"] = ArtifactName.LEDGER

    result = _run(steps.generate_artifacts, context)

    assert result == StepResult.success("Generated 2 outputs.")
    assert application.generate_outputs.call_args.kwargs["force"] is ArtifactName.LEDGER
    assert "force" not in context.facts


# Improve Player Voice Profiles


def test_voice_profile_offer_accepted_is_saved_quietly() -> None:
    application = _application()
    context = _Context(application, True)

    assert _run(steps.improve_voice_profiles, context) == StepResult.success()
    application.save_voice_profile_decision.assert_called_once_with(context.session_id, accepted=True)


def test_voice_profile_offer_declined_says_how_to_do_it_later() -> None:
    application = _application()
    context = _Context(application, False)

    result = _run(steps.improve_voice_profiles, context)

    assert result.outcome is Outcome.SUCCESS and "From Session" in (result.message or "")
    application.save_voice_profile_decision.assert_called_once_with(context.session_id, accepted=False)


def test_voice_profile_offer_dismissed_cancels() -> None:
    application = _application()

    assert _run(steps.improve_voice_profiles, _Context(application, None)).outcome is Outcome.CANCEL
    application.save_voice_profile_decision.assert_not_called()


def test_enhancement_reports_what_it_added_and_is_quiet_when_declined() -> None:
    added = _application(enhance_voice_profiles=EnhanceResult(enhanced_player_count=2, clip_count=9))
    declined = _application(enhance_voice_profiles=None)

    assert _run(steps.enhance_voice_profiles, _Context(added)) == StepResult.success("Enhanced 2 player(s) with 9 clip(s) total.")
    assert _run(steps.enhance_voice_profiles, _Context(declined)) == StepResult.success()


# Automatic steps: each runs its application method behind the progress dialog


@pytest.mark.parametrize(
    ("step", "method"),
    [
        (steps.import_audio_file, "import_requested_audio"),
        (steps.create_transcript, "create_transcript"),
        (steps.remove_backchannels, "remove_bad_utterances"),
        (steps.suggest_name_corrections, "propose_name_corrections"),
        (steps.isolate_new_speakers, "isolate_new_speakers"),
        (steps.seed_voice_samples, "seed_player_voice_samples"),
        (steps.identify_speakers, "identify_session_speakers"),
        (steps.suggest_glossary_terms, "propose_glossary_terms"),
        (steps.suggest_spelling_corrections, "propose_spelling_corrections"),
        (steps.apply_transcript_review, "apply_transcript_review"),
        (steps.assign_roles, "clean_transcript"),
    ],
)
def test_automatic_step_runs_its_application_method_behind_the_progress_dialog(step: Any, method: str) -> None:
    application = _application()
    context = _Context(application)

    result = _run(step, context)

    assert result == StepResult.success()
    assert getattr(application, method).call_args.args == (context.session_id,)
    assert len(context.background_messages) == 1


@pytest.mark.parametrize(
    ("step", "method"),
    [(steps.apply_name_corrections, "apply_name_corrections"), (steps.apply_spelling_corrections, "apply_spelling_corrections")],
)
def test_applying_corrections_reports_replacements(step: Any, method: str) -> None:
    replaced = _application(**{method: 3})
    unchanged = _application(**{method: 0})

    assert _run(step, _Context(replaced)) == StepResult.success("Replaced 3 occurrences.")
    assert _run(step, _Context(unchanged)) == StepResult.success()
