from __future__ import annotations

from tablesage_model.io import load_player, load_player_set, load_session, load_session_set
from tablesage_model.model import Campaign, GlossaryEntry, Player, Session
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.widgets import Input, Static, TabbedContent, TabPane

from tablesage_tui.dialogs import ConfirmDeleteGlossaryEntryDialog, GlossaryEntryDialog, GlossaryEntryDialogResult
from tablesage_tui.widgets import CampaignStateWidget, EmptyWidget, GlossaryEntryWidget, GlossaryList

from .base_screen import BaseScreen

EMPTY_DATE = "—"


def _sort_glossary_entries(entries: tuple[GlossaryEntry, ...]) -> tuple[GlossaryEntry, ...]:
    return tuple(sorted(entries, key=lambda entry: entry.term.casefold()))


class CampaignDetailScreen(BaseScreen):
    BINDINGS = [
        Binding("escape", "back", "Back", key_display="Esc"),
        Binding("a", "add_glossary_entry", "Add Glossary"),
        Binding("e", "edit_glossary_entry", "Edit Glossary"),
        Binding("d", "delete_glossary_entry", "Delete Glossary"),
    ]

    def __init__(self, campaign: Campaign) -> None:
        super().__init__()
        self.campaign = campaign
        self.glossary: tuple[GlossaryEntry, ...] = _sort_glossary_entries(campaign.glossary)
        self._selected_glossary_term: str | None = None

    def get_header_section(self) -> str:
        return f"campaigns / {self.campaign.name}"

    def _sessions(self, session_count: int = -1) -> list[Session]:
        session_names = sorted(
            load_session_set(self.campaign.slug).sessions,
            key=lambda session_name: session_name.session_date,
            reverse=True,
        )
        if session_count >= 0:
            session_names = session_names[:session_count]
        return [load_session(self.campaign.slug, session_name.slug) for session_name in session_names]

    def _players(self, player_count: int = -1) -> list[Player]:
        player_names = list(load_player_set(self.campaign.slug).players)
        if player_count >= 0:
            player_names = player_names[:player_count]
        return [load_player(self.campaign.slug, player_name.slug) for player_name in player_names]

    def _glossary_entries(self, entry_count: int = -1) -> tuple[GlossaryEntry, ...]:
        entries = _sort_glossary_entries(self.glossary)
        if entry_count >= 0:
            return entries[:entry_count]
        return entries

    def _entry_by_term(self, term: str | None) -> GlossaryEntry | None:
        if term is None:
            return None
        return next((entry for entry in self.glossary if entry.term == term), None)

    def _last_session(self) -> Session | None:
        sessions = self._sessions(session_count=1)
        if not sessions:
            return None
        return sessions[0]

    def _last_session_date_text(self) -> str:
        last_session = self._last_session()
        if last_session is None:
            return EMPTY_DATE
        return last_session.session_date.strftime("%a %b %-d %Y")

    def compose_content(self) -> ComposeResult:
        with Vertical(id="content-panel"):
            with Horizontal(id="campaign-header"):
                yield Static(id="back-keycap", classes="keycap", content="←")
                yield Static(classes="campaigns-text", content=" return to campaigns")
                yield EmptyWidget(classes="fill-space-horizontal")
            yield Static(id="campaign-name", content=self.campaign.name.upper())
            with TabbedContent(initial="overview", id="campaign-tabs"):
                with TabPane(" overview ", id="overview"):
                    with Horizontal(id="overview-tabbed-panel") as h:
                        h.border_title = "campaign details"
                        with Vertical(id="metadata-editor"):
                            yield Static(content="Description")
                            yield Input(id="description-input", placeholder="campaign description", value=self.campaign.description)
                            with Horizontal(id="details-row"):
                                yield Static(classes="label", content="System:")
                                yield Input(id="input-system", placeholder="system", value=self.campaign.system)
                                yield Static(classes="label", content="GM:")
                                yield Input(id="input-gm", placeholder="game master", value=self.campaign.default_gm)
                                yield Static(classes="label", content="State: ")
                                yield CampaignStateWidget(self.campaign.state, id="campaign-state")
                        with Vertical(id="last_session_data"):
                            yield Static(content="Last Session")
                            yield Static(id="last-session-display", content=self._last_session_date_text())
                    with Horizontal(id="players-and-glossary"):
                        with Vertical(id="players-summary") as v:
                            v.border_title = "players"
                        with Vertical(id="glossary-summary") as v:
                            v.border_title = "glossary"
                            yield GlossaryList(self._glossary_entries(), id="glossary-list")
                with TabPane(" sessions ", id="sessions"):
                    yield Static()

    @on(Click, "#back-keycap")
    def _on_back_click(self) -> None:
        self.action_back()

    @on(GlossaryEntryWidget.Selected)
    def _on_glossary_entry_selected(self, event: GlossaryEntryWidget.Selected) -> None:
        self._selected_glossary_term = event.term

    @on(GlossaryEntryWidget.EditRequested)
    def _on_glossary_entry_edit_requested(self, event: GlossaryEntryWidget.EditRequested) -> None:
        self._selected_glossary_term = event.term
        self.action_edit_glossary_entry()

    @on(GlossaryEntryWidget.DeleteRequested)
    def _on_glossary_entry_delete_requested(self, event: GlossaryEntryWidget.DeleteRequested) -> None:
        self._selected_glossary_term = event.term
        self.action_delete_glossary_entry()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_add_glossary_entry(self) -> None:
        self.app.push_screen(
            GlossaryEntryDialog(existing_terms=self._existing_glossary_terms()),
            self._on_glossary_entry_dialog_result,
        )

    def action_edit_glossary_entry(self) -> None:
        entry = self._entry_by_term(self._selected_glossary_term)
        if entry is None:
            self.notify("Select a glossary entry to edit.")
            return

        self.app.push_screen(
            GlossaryEntryDialog(
                existing_terms=self._existing_glossary_terms(),
                original_entry=entry,
            ),
            self._on_glossary_entry_dialog_result,
        )

    def action_delete_glossary_entry(self) -> None:
        entry = self._entry_by_term(self._selected_glossary_term)
        if entry is None:
            self.notify("Select a glossary entry to delete.")
            return

        self.app.push_screen(ConfirmDeleteGlossaryEntryDialog(entry.term), self._on_delete_glossary_entry_result)

    def _existing_glossary_terms(self) -> frozenset[str]:
        return frozenset(entry.term for entry in self.glossary)

    def _on_glossary_entry_dialog_result(self, result: GlossaryEntryDialogResult | None) -> None:
        if result is None:
            return

        self._add_or_update_glossary_entry(result)

    def _on_delete_glossary_entry_result(self, term: str | None) -> None:
        if term is None:
            return

        self.glossary = tuple(entry for entry in self.glossary if entry.term != term)
        self._selected_glossary_term = None
        self._refresh_glossary_list()

    def _add_or_update_glossary_entry(self, result: GlossaryEntryDialogResult) -> None:
        updated_entry = GlossaryEntry(term=result.term, description=result.description)
        if result.original_term is None:
            self.glossary = (*self.glossary, updated_entry)
        else:
            self.glossary = tuple(entry for entry in self.glossary if entry.term != result.original_term)
            self.glossary = (*self.glossary, updated_entry)

        self._selected_glossary_term = updated_entry.term
        self._refresh_glossary_list()

    def _refresh_glossary_list(self) -> None:
        glossary_list = self.query_one("#glossary-list", GlossaryList)
        glossary_list.entries = self._glossary_entries()
        glossary_list.refresh(recompose=True)
