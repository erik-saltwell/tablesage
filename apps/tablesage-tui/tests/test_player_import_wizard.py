from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tablesage_application.player_import_from_audio import (
    AttendeeSummary as ImportAttendeeSummary,
)
from tablesage_application.player_import_from_audio import (
    ImportFromAudioResult,
    ProposeResult,
    SpeakerCandidate,
    SpeakerProposal,
    SpeakerUtteranceClip,
)
from tablesage_model.model import Player
from tablesage_tui.audio_playback import ClipPlayer
from tablesage_tui.dialogs.speaker_resolution import NEW_PLAYER, SpeakerResolutionDialog, SpeakerResolutionResult
from tablesage_tui.dialogs.transcript_view import TranscriptViewDialog
from tablesage_tui.player_import_run import PlayerImportRun, SpeakerResolution
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_import_prestep import PlayerImportPreStepScreen
from tablesage_tui.screens.player_import_review import PlayerImportReviewScreen
from tablesage_tui.screens.player_import_summary import PlayerImportSummaryScreen
from textual.pilot import Pilot
from textual.widgets import Button, Checkbox, DataTable, Input, Select

_ALICE = Player(name="Alice")


async def _wait_for_progress_worker(pilot: Pilot) -> None:
    await pilot.app.workers.wait_for_complete()
    await pilot.pause()


# --- SpeakerResolutionDialog ---


@pytest.mark.anyio
async def test_speaker_resolution_dialog_new_player_requires_name() -> None:
    current = SpeakerResolution(player_id=None, player_name="", role="GM")

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(SpeakerResolutionDialog(players=[_ALICE], current=current))
        await pilot.pause()

        pilot.app.screen.query_one("#speaker-resolution-name", Input).value = ""
        pilot.app.screen.query_one("#speaker-resolution-save", Button).press()
        await pilot.pause()

        assert isinstance(pilot.app.screen, SpeakerResolutionDialog)


@pytest.mark.anyio
async def test_speaker_resolution_dialog_new_player_submits_result() -> None:
    current = SpeakerResolution(player_id=None, player_name="Guessed Name", role="GM")
    results: list[SpeakerResolutionResult | None] = []

    async with TableSageApp().run_test() as pilot:

        def on_dismiss(result: SpeakerResolutionResult | None) -> None:
            results.append(result)

        pilot.app.push_screen(SpeakerResolutionDialog(players=[_ALICE], current=current), on_dismiss)
        await pilot.pause()

        assert pilot.app.screen.query_one("#speaker-resolution-player-select", Select).value == NEW_PLAYER
        pilot.app.screen.query_one("#speaker-resolution-save", Button).press()
        await pilot.pause()

        assert results == [SpeakerResolutionResult(player_id=None, player_name="Guessed Name", role="GM", excluded=False)]


@pytest.mark.anyio
async def test_speaker_resolution_dialog_selecting_existing_player_submits_its_id() -> None:
    current = SpeakerResolution(player_id=None, player_name="Guessed Name", role="")
    results: list[SpeakerResolutionResult | None] = []

    async with TableSageApp().run_test() as pilot:

        def on_dismiss(result: SpeakerResolutionResult | None) -> None:
            results.append(result)

        pilot.app.push_screen(SpeakerResolutionDialog(players=[_ALICE], current=current), on_dismiss)
        await pilot.pause()

        pilot.app.screen.query_one("#speaker-resolution-player-select", Select).value = _ALICE.id
        await pilot.pause()
        pilot.app.screen.query_one("#speaker-resolution-save", Button).press()
        await pilot.pause()

        assert results == [SpeakerResolutionResult(player_id=_ALICE.id, player_name="Alice", role="", excluded=False)]


@pytest.mark.anyio
async def test_speaker_resolution_dialog_cancel_dismisses_none() -> None:
    current = SpeakerResolution(player_id=None, player_name="X", role="")

    async with TableSageApp().run_test() as pilot:
        pilot.app.push_screen(SpeakerResolutionDialog(players=[_ALICE], current=current))
        await pilot.pause()
        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, SpeakerResolutionDialog)


# --- PlayerImportPreStepScreen ---


def _application() -> MagicMock:
    return MagicMock(list_players=MagicMock(return_value=[]))


async def _add_candidate(pilot: Pilot, name: str, *roles: str) -> None:
    await pilot.press("n")
    await pilot.pause()
    pilot.app.screen.query_one("#attendee-name", Input).value = name
    await pilot.pause()
    for role in roles:
        pilot.app.screen.query_one("#attendee-add-role", Button).press()
        await pilot.pause()
        pilot.app.screen.query_one("#text-input-value", Input).value = role
        await pilot.press("enter")
        await pilot.pause()
    pilot.app.screen.query_one("#attendee-save", Button).press()
    await pilot.pause()


@pytest.mark.anyio
async def test_prestep_add_candidate_flow() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        await _add_candidate(pilot, "Alice", "Game Master")

        assert run.candidates == [SpeakerCandidate(name="Alice", roles=("Game Master",))]
        table = pilot.app.screen.query_one("#player-import-candidates-table", DataTable)
        assert table.row_count == 1


@pytest.mark.anyio
async def test_prestep_edit_candidate_flow() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    run.candidates.append(SpeakerCandidate(name="Alice", roles=("Game Master",)))

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        await pilot.press("e")
        await pilot.pause()
        assert pilot.app.screen.query_one("#attendee-name", Input).value == "Alice"
        pilot.app.screen.query_one("#attendee-name", Input).value = "Alicia"
        pilot.app.screen.query_one("#attendee-save", Button).press()
        await pilot.pause()

        assert run.candidates == [SpeakerCandidate(name="Alicia", roles=("Game Master",))]


@pytest.mark.anyio
async def test_prestep_delete_candidate_removes_it() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    run.candidates.append(SpeakerCandidate(name="Alice", roles=("Game Master",)))

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        await pilot.press("d")
        await pilot.pause()

        assert run.candidates == []
        table = pilot.app.screen.query_one("#player-import-candidates-table", DataTable)
        assert table.row_count == 0


def _propose_result() -> ProposeResult:
    return ProposeResult(
        proposals=(
            SpeakerProposal(
                speaker_id="speaker_0",
                utterance_count=1,
                transcript_text="hi",
                suggested_name="Alice",
                suggested_role="GM",
                suggested_confidence="high",
                matched_player_id=None,
                matched_player_name=None,
            ),
        ),
        speaker_clips={},
        speaker_centroids={},
    )


@pytest.mark.anyio
async def test_prestep_continue_with_no_candidates_passes_none_speaker_count() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    application = _application()
    application.import_players_from_audio_transcribe = MagicMock(return_value=object())
    application.import_players_from_audio_propose = MagicMock(return_value=_propose_result())

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        pilot.app.screen.query_one("#player-import-continue", Button).press()
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.import_players_from_audio_transcribe.assert_called_once()
        assert application.import_players_from_audio_transcribe.call_args.args[2] is None
        assert application.import_players_from_audio_transcribe.call_args.kwargs["should_clean_audio"] is True
        assert run.speaker_count is None
        assert isinstance(pilot.app.screen, PlayerImportReviewScreen)


@pytest.mark.anyio
async def test_prestep_unchecking_clean_audio_passes_should_clean_audio_false() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    application = _application()
    application.import_players_from_audio_transcribe = MagicMock(return_value=object())
    application.import_players_from_audio_propose = MagicMock(return_value=_propose_result())

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        pilot.app.screen.query_one("#player-import-clean-audio", Checkbox).value = False
        pilot.app.screen.query_one("#player-import-continue", Button).press()
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.import_players_from_audio_transcribe.assert_called_once()
        assert application.import_players_from_audio_transcribe.call_args.kwargs["should_clean_audio"] is False


@pytest.mark.anyio
async def test_prestep_continue_derives_speaker_count_from_candidate_list() -> None:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    application = _application()
    application.import_players_from_audio_transcribe = MagicMock(return_value=object())
    application.import_players_from_audio_propose = MagicMock(return_value=_propose_result())

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()

        await _add_candidate(pilot, "Alice", "Game Master")
        await _add_candidate(pilot, "Bob", "Rogue")

        pilot.app.screen.query_one("#player-import-continue", Button).press()
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.import_players_from_audio_transcribe.assert_called_once()
        assert application.import_players_from_audio_transcribe.call_args.args[2] == 2
        assert run.speaker_count == 2
        application.import_players_from_audio_propose.assert_called_once()
        assert isinstance(pilot.app.screen, PlayerImportReviewScreen)
        assert run.resolutions["speaker_0"].player_name == "Alice"


# --- PlayerImportReviewScreen ---


def _run_with_proposal(*, matched_player_id: uuid.UUID | None = None, matched_player_name: str | None = None) -> PlayerImportRun:
    run = PlayerImportRun(source_audio_path=Path("/tmp/source.wav"))
    clip = SpeakerUtteranceClip(
        utterance=MagicMock(start=0.0, end=1.0, punctuated_text="hello there", text="hello there"), clip_path=Path("/tmp/clip.wav")
    )
    run.propose_result = ProposeResult(
        proposals=(
            SpeakerProposal(
                speaker_id="speaker_0",
                utterance_count=1,
                transcript_text="hello there",
                suggested_name="Guessed",
                suggested_role="GM",
                suggested_confidence="high",
                matched_player_id=matched_player_id,
                matched_player_name=matched_player_name,
            ),
        ),
        speaker_clips={"speaker_0": (clip,)},
        speaker_centroids={"speaker_0": MagicMock()},
    )
    run.resolutions["speaker_0"] = SpeakerResolution(
        player_id=matched_player_id, player_name=matched_player_name or "Guessed", role="GM", excluded=False
    )
    return run


@pytest.mark.anyio
async def test_review_table_shows_new_player_row() -> None:
    run = _run_with_proposal()

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        table = pilot.app.screen.query_one("#player-import-review-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row == ("speaker_0", "New Player: Guessed", "GM", "Included")


@pytest.mark.anyio
async def test_review_view_transcript_opens_dialog() -> None:
    run = _run_with_proposal()

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        await pilot.press("t")
        await pilot.pause()

        assert isinstance(pilot.app.screen, TranscriptViewDialog)


@pytest.mark.anyio
async def test_transcript_view_plays_selected_clip(monkeypatch: pytest.MonkeyPatch) -> None:
    played: list[Path] = []
    monkeypatch.setattr(ClipPlayer, "play", lambda self, path: played.append(path))
    run = _run_with_proposal()
    assert run.propose_result is not None
    clip = run.propose_result.speaker_clips["speaker_0"][0]

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        await pilot.press("t")
        await pilot.pause()

        await pilot.press("p")
        await pilot.pause()

        assert played == [clip.clip_path]


@pytest.mark.anyio
async def test_review_edit_row_updates_resolution() -> None:
    run = _run_with_proposal()
    application = _application()
    application.list_players = MagicMock(return_value=[_ALICE])

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        await pilot.press("e")
        await pilot.pause()
        pilot.app.screen.query_one("#speaker-resolution-player-select", Select).value = _ALICE.id
        await pilot.pause()
        pilot.app.screen.query_one("#speaker-resolution-save", Button).press()
        await pilot.pause()

        assert run.resolutions["speaker_0"].player_id == _ALICE.id
        table = pilot.app.screen.query_one("#player-import-review-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row[1] == "Alice"


@pytest.mark.anyio
async def test_review_build_with_all_excluded_notifies_error() -> None:
    run = _run_with_proposal()
    run.resolutions["speaker_0"].excluded = True
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        with pytest.MonkeyPatch.context() as mp:
            notify = MagicMock()
            mp.setattr(pilot.app.screen, "notify", notify)
            await pilot.press("b")
            await pilot.pause()
            notify.assert_called_once()

        application.import_players_from_audio_build.assert_not_called()


@pytest.mark.anyio
async def test_review_build_success_pops_to_players_list_and_pushes_summary() -> None:
    run = _run_with_proposal()
    application = _application()
    build_result = ImportFromAudioResult(
        affected_player_count=1, clip_count=1, summary=(ImportAttendeeSummary(player_name="Guessed", role="GM", clip_count=1),)
    )
    application.import_players_from_audio_build = MagicMock(return_value=build_result)

    async with TableSageApp(application).run_test() as pilot:
        pilot.app.push_screen(PlayerImportPreStepScreen(run))
        await pilot.pause()
        pilot.app.push_screen(PlayerImportReviewScreen(run))
        await pilot.pause()

        await pilot.press("b")
        await pilot.pause()
        await _wait_for_progress_worker(pilot)

        application.import_players_from_audio_build.assert_called_once()
        assert isinstance(pilot.app.screen, PlayerImportSummaryScreen)


# --- PlayerImportSummaryScreen ---


@pytest.mark.anyio
async def test_summary_screen_renders_rows_and_escape_pops() -> None:
    result = ImportFromAudioResult(
        affected_player_count=1, clip_count=2, summary=(ImportAttendeeSummary(player_name="Alice", role="GM", clip_count=2),)
    )

    async with TableSageApp(_application()).run_test() as pilot:
        pilot.app.push_screen(PlayerImportSummaryScreen(result))
        await pilot.pause()

        table = pilot.app.screen.query_one("#player-import-summary-table", DataTable)
        row = tuple(str(cell) for cell in table.get_row_at(0))
        assert row == ("Alice", "GM", "2")

        await pilot.press("escape")
        await pilot.pause()

        assert not isinstance(pilot.app.screen, PlayerImportSummaryScreen)
