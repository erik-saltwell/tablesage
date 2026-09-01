from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.session_pipeline.extract_glossary import GlossaryCommitResult, GlossaryProposal
from tablesage_tui.dialogs import FindReplaceDialog, GlossaryEntryDialog
from tablesage_tui.screens.glossary_review import GlossaryReviewScreen
from tablesage_tui.screens.main_app import TableSageApp
from textual.pilot import Pilot
from textual.widgets import DataTable, Input


def _application() -> MagicMock:
    return MagicMock(complete_glossary_extraction=MagicMock(return_value=GlossaryCommitResult(added_count=2, skipped_duplicate_count=1)))


async def _open_review(pilot: Pilot, session_id: uuid.UUID) -> None:
    pilot.app.push_screen(
        GlossaryReviewScreen(
            session_id,
            [
                GlossaryProposal(term="Veyra", description="An envoy from Ashfall."),
                GlossaryProposal(term="Ashfall", description="A ruined city."),
            ],
        )
    )
    await pilot.pause()


def test_review_binding_keys() -> None:
    bindings = {binding.action: binding.key for binding in GlossaryReviewScreen.BINDINGS}
    assert bindings == {
        "cancel": "escape",
        "new_entry": "n,N",
        "edit_entry": "enter,e,E",
        "delete_entry": "d,D,delete,backspace",
        "find_replace": "f,F",
        "complete": "c,C",
    }


@pytest.mark.anyio
async def test_review_starts_sorted_and_supports_new_edit_delete() -> None:
    application = _application()
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review(pilot, session_id)
        table = pilot.app.screen.query_one("#glossary-review-table", DataTable)
        assert list(table.get_column("term")) == ["Ashfall", "Veyra"]

        await pilot.press("n")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, GlossaryEntryDialog)
        dialog.query_one("#glossary-entry-term", Input).value = "Black Spire"
        await pilot.click("#glossary-entry-submit")
        await pilot.pause()
        table = pilot.app.screen.query_one("#glossary-review-table", DataTable)
        assert list(table.get_column("term")) == ["Ashfall", "Black Spire", "Veyra"]

        await pilot.press("e")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, GlossaryEntryDialog)
        dialog.query_one("#glossary-entry-term", Input).value = "Cinder Spire"
        await pilot.click("#glossary-entry-submit")
        await pilot.pause()
        table = pilot.app.screen.query_one("#glossary-review-table", DataTable)
        assert list(table.get_column("term")) == ["Ashfall", "Cinder Spire", "Veyra"]

        await pilot.press("d")
        await pilot.pause()
        assert list(table.get_column("term")) == ["Ashfall", "Veyra"]


@pytest.mark.anyio
async def test_global_replace_changes_terms_and_descriptions_and_resorts() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review(pilot, uuid.uuid4())
        await pilot.press("f")
        await pilot.pause()
        dialog = pilot.app.screen
        assert isinstance(dialog, FindReplaceDialog)
        dialog.query_one("#find-replace-find", Input).value = "Ashfall"
        dialog.query_one("#find-replace-replace", Input).value = "Cinderfall"
        await pilot.click("#find-replace-submit")
        await pilot.pause()

        table = pilot.app.screen.query_one("#glossary-review-table", DataTable)
        assert list(table.get_column("term")) == ["Cinderfall", "Veyra"]
        assert list(table.get_column("description")) == ["A ruined city.", "An envoy from Cinderfall."]


@pytest.mark.anyio
async def test_complete_blocks_blank_term_created_by_find_replace() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review(pilot, uuid.uuid4())
        screen = pilot.app.screen
        assert isinstance(screen, GlossaryReviewScreen)
        screen._entries[0] = type(screen._entries[0])(id=screen._entries[0].id, term="", description=screen._entries[0].description)

        with patch.object(GlossaryReviewScreen, "notify") as notify:
            await pilot.press("c")
            await pilot.pause()

        notify.assert_called_once_with("Glossary terms cannot be blank.", severity="error")
        application.complete_glossary_extraction.assert_not_called()


@pytest.mark.anyio
async def test_complete_commits_working_copy_and_returns() -> None:
    application = _application()
    session_id = uuid.uuid4()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review(pilot, session_id)
        await pilot.press("c")
        await pilot.pause()

        application.complete_glossary_extraction.assert_called_once()
        assert application.complete_glossary_extraction.call_args.args[0] == session_id
        proposals = application.complete_glossary_extraction.call_args.args[1]
        assert [proposal.term for proposal in proposals] == ["Ashfall", "Veyra"]
        assert not isinstance(pilot.app.screen, GlossaryReviewScreen)


@pytest.mark.anyio
async def test_cancel_discards_without_committing() -> None:
    application = _application()

    async with TableSageApp(application).run_test() as pilot:
        await _open_review(pilot, uuid.uuid4())
        await pilot.press("escape")
        await pilot.pause()

        application.complete_glossary_extraction.assert_not_called()
