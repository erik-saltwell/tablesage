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
from tablesage_tui.widgets import CampaignStateWidget, EmptyWidget, GlossaryEntryWidget, GlossaryList, PlayerDetailWidget, PlayerList

from .base_screen import BaseScreen

EMPTY_DATE = "—"


def _sort_glossary_entries(entries: tuple[GlossaryEntry, ...]) -> tuple[GlossaryEntry, ...]:
    return tuple(sorted(entries, key=lambda entry: entry.term.casefold()))


def _sort_players(players: list[Player]) -> tuple[Player, ...]:
    return tuple(sorted(players, key=lambda player: player.name.casefold()))


class CampaignDetailScreen(BaseScreen):
    BINDINGS = [
        Binding("escape", "back", "Back", key_display="Esc"),
        Binding("g", "add_glossary_entry", "Add Glossary"),
        Binding("p", "add_player", "Add Player"),
        Binding("e", "edit_glossary_entry", "Edit Glossary"),
        Binding("e", "update_player_name", "Edit Player"),
        Binding("d", "delete_glossary_entry", "Delete Glossary"),
        Binding("d", "delete_player", "Delete Player"),
        Binding("f", "add_clips_from_folder", "Add Clips Folder", key_display="F"),
        Binding("s", "add_clips_from_session", "Add Clips Session", key_display="S"),
        Binding("r", "recompute_speechprint", "Recompute Speechprint", key_display="V"),
    ]

    def __init__(self, campaign: Campaign) -> None:
        super().__init__()
        self.campaign = campaign
        self._selected_glossary_term: str | None = None
        self.players = self._players()
        self._selected_player_slug: str | None = None

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

    def _players(self, player_count: int = -1) -> tuple[Player, ...]:
        player_names = list(load_player_set(self.campaign.slug).players)
        if player_count >= 0:
            player_names = player_names[:player_count]
        return _sort_players([load_player(self.campaign.slug, player_name.slug) for player_name in player_names])

    def _entry_by_term(self, term: str | None) -> GlossaryEntry | None:
        if term is None:
            return None
        return next((entry for entry in self.campaign.glossary if entry.term == term), None)

    def _glossary_entries(self) -> tuple[GlossaryEntry, ...]:
        return _sort_glossary_entries(self.campaign.glossary)

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
                        with Vertical(id="player-summary") as v:
                            v.border_title = "players"
                            yield PlayerList(self.players, id="player-list")
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
        self._select_glossary_entry(event.term)

    @on(GlossaryEntryWidget.EditRequested)
    def _on_glossary_entry_edit_requested(self, event: GlossaryEntryWidget.EditRequested) -> None:
        self._select_glossary_entry(event.term)
        self.action_edit_glossary_entry()

    @on(GlossaryEntryWidget.DeleteRequested)
    def _on_glossary_entry_delete_requested(self, event: GlossaryEntryWidget.DeleteRequested) -> None:
        self._select_glossary_entry(event.term)
        self.action_delete_glossary_entry()

    @on(PlayerDetailWidget.Selected)
    def _on_player_selected(self, event: PlayerDetailWidget.Selected) -> None:
        self._select_player(event.player_slug)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action in {"edit_glossary_entry", "delete_glossary_entry"}:
            return bool(self._selected_glossary_term)

        if action in {
            "delete_player",
            "update_player_name",
            "add_clips_from_folder",
            "add_clips_from_session",
            "recompute_speechprint",
        }:
            return bool(self._selected_player_slug)

        return super().check_action(action, parameters)

    def _select_glossary_entry(self, term: str) -> None:
        self._selected_glossary_term = term
        self._selected_player_slug = None
        self.refresh_bindings()

    def _select_player(self, player_slug: str) -> None:
        self._selected_player_slug = player_slug
        self._selected_glossary_term = None
        self.refresh_bindings()

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

    def action_add_player(self) -> None:
        self.notify("Add player")

    def action_delete_player(self) -> None:
        selected_player = self._selected_player()
        if selected_player is None:
            self.notify("Select a player to delete.")
            return
        self.notify(f"Delete player: {selected_player.name}")

    def action_update_player_name(self) -> None:
        selected_player = self._selected_player()
        if selected_player is None:
            self.notify("Select a player to rename.")
            return
        self.notify(f"Rename player: {selected_player.name}")

    def action_add_clips_from_folder(self) -> None:
        selected_player = self._selected_player()
        if selected_player is None:
            self.notify("Select a player to add clips.")
            return
        self.notify(f"Add clips from folder: {selected_player.name}")

    def action_add_clips_from_session(self) -> None:
        selected_player = self._selected_player()
        if selected_player is None:
            self.notify("Select a player to add clips.")
            return
        self.notify(f"Add clips from session: {selected_player.name}")

    def action_recompute_speechprint(self) -> None:
        selected_player = self._selected_player()
        if selected_player is None:
            self.notify("Select a player to recompute speechprint.")
            return
        self.notify(f"Recompute speechprint: {selected_player.name}")

    def _selected_player(self) -> Player | None:
        if self._selected_player_slug is None:
            return None
        return next((player for player in self.players if player.slug == self._selected_player_slug), None)

    def _existing_glossary_terms(self) -> frozenset[str]:
        return frozenset(entry.term for entry in self.campaign.glossary)

    def _on_glossary_entry_dialog_result(self, result: GlossaryEntryDialogResult | None) -> None:
        if result is None:
            return

        self._add_or_update_glossary_entry(result)

    def _on_delete_glossary_entry_result(self, term: str | None) -> None:
        if term is None:
            return

        self._replace_glossary(tuple(entry for entry in self.campaign.glossary if entry.term != term))
        self._selected_glossary_term = None
        self.refresh_bindings()
        self._refresh_glossary_list()

    def _add_or_update_glossary_entry(self, result: GlossaryEntryDialogResult) -> None:
        updated_entry = GlossaryEntry(term=result.term, description=result.description)
        if result.original_term is None:
            updated_glossary = (*self.campaign.glossary, updated_entry)
        else:
            updated_glossary = tuple(entry for entry in self.campaign.glossary if entry.term != result.original_term)
            updated_glossary = (*updated_glossary, updated_entry)

        self._replace_glossary(updated_glossary)
        self._select_glossary_entry(updated_entry.term)
        self._refresh_glossary_list()

    def _replace_glossary(self, glossary: tuple[GlossaryEntry, ...]) -> None:
        self.campaign = self.campaign.model_copy(update={"glossary": _sort_glossary_entries(glossary)})

    def _refresh_glossary_list(self) -> None:
        glossary_list = self.query_one("#glossary-list", GlossaryList)
        glossary_list.entries = self._glossary_entries()
        glossary_list.refresh(recompose=True)
