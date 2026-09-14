"""Quick entry and complete Scene selection for an ephemeral Previously On export."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.text import Text
from tablesage_application.previously_on import (
    CampaignHistory,
    Ingredients,
    SceneRef,
    ScoutInput,
    ScoutResult,
    editor_input,
)
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, ContentSwitcher, Static, TextArea, Tree
from textual_fspicker import Filters

from ..dialogs.file_picker import FileSave
from ..dialogs.generic import ConfirmationDialog
from .base import TableSageScreen


class ChoiceTree(Tree[SceneRef | int | None]):
    BINDINGS = [Binding("space", "select_cursor", "Select", show=False)]


class PreviouslyOnScreen(TableSageScreen):
    section = "previously on"
    CSS_PATH = "../styles/previously_on.tcss"
    COMMON_BINDINGS = [
        Binding("escape", "leave", "Exit", key_display="Esc"),
        Binding("ctrl+n", "continue", "Continue", key_display="^N"),
    ]

    def __init__(self, history: CampaignHistory, ingredients: Ingredients) -> None:
        super().__init__()
        self.history = history
        self.ingredients = ingredients
        self.campaign = history.campaign_name
        self._items = tuple(item for _, items in ingredients.sections() for item in items)
        self._selected_ingredients: set[int] = set()
        self._selected_scenes: set[SceneRef] = set()
        self._rationales: dict[SceneRef, str] = {}
        self._catalog = history.scene_catalog()
        self._reviewed = False
        self._destination: Path | None = None
        self._overwrite = False

    def compose_content(self) -> ComposeResult:
        yield Static("", id="previously-on-error", markup=False)
        with ContentSwitcher(initial="previously-on-entry", id="previously-on-stage"):
            with Vertical(id="previously-on-entry"):
                with Horizontal(classes="previously-on-panes"):
                    with Vertical(classes="previously-on-pane"):
                        yield Static("Starting situation", classes="previously-on-label")
                        yield TextArea(self.history.starting_situation, id="previously-on-start", tab_behavior="focus")
                        yield Static("What might happen next Session?", classes="previously-on-label")
                        yield TextArea(id="previously-on-notes", tab_behavior="focus")
                        yield Static("Select ingredients or add notes to continue. Correct suggestions in your notes.", markup=False)
                    with Vertical(classes="previously-on-pane"):
                        yield Static("Campaign ingredients · Space / Enter to select", classes="previously-on-label")
                        yield ChoiceTree("Ingredients", id="previously-on-ingredients")
                        yield TextArea(read_only=True, id="previously-on-evidence", tab_behavior="focus")
                with Horizontal(classes="previously-on-actions"):
                    yield Button("Exit", id="previously-on-exit-entry")
                    yield Button("Find Scenes", id="previously-on-scout", variant="primary", disabled=True)
            with Vertical(id="previously-on-selection"):
                yield Static("Choose any Scenes · Space / Enter to select or expand Sessions", markup=False)
                with Horizontal(classes="previously-on-panes"):
                    with Vertical(classes="previously-on-pane"):
                        yield ChoiceTree("Sessions", id="previously-on-scenes")
                        yield Static("0 Scenes selected", id="previously-on-count")
                    yield TextArea(read_only=True, id="previously-on-scene-detail", classes="previously-on-pane", tab_behavior="focus")
                yield Static("", id="previously-on-destination", markup=False)
                with Horizontal(classes="previously-on-actions"):
                    yield Button("Back", id="previously-on-back")
                    yield Button("Exit", id="previously-on-exit-selection")
                    yield Button("Retry Save", id="previously-on-retry")
                    yield Button("Save Markdown…", id="previously-on-save", variant="primary", disabled=True)

    def on_mount(self) -> None:
        tree = self.query_one("#previously-on-ingredients", ChoiceTree)
        tree.show_root = False
        index = 0
        for title, items in self.ingredients.sections():
            section = tree.root.add(Text(title), expand=True)
            for _item in items:
                section.add_leaf(self._ingredient_label(index), data=index)
                index += 1
            if not items:
                section.add_leaf(Text("No strong candidates", style="dim"))
        tree.root.expand()
        self.query_one("#previously-on-retry", Button).display = False
        self.query_one("#previously-on-error").display = False
        self.query_one("#previously-on-start", TextArea).focus()

    def _ingredient_label(self, index: int) -> Text:
        item = self._items[index]
        mark = "[x]" if index in self._selected_ingredients else "[ ]"
        return Text(f"{mark} {item.label} — {item.current_state}")

    def _scene_label(self, ref: SceneRef) -> Text:
        scene = self._catalog[ref]
        mark = "[x]" if ref in self._selected_scenes else "[ ]"
        summary = " ".join(f"{scene.situation} → {scene.outcome}".split())
        if len(summary) > 110:
            summary = summary[:107] + "…"
        label = Text(f"{mark} {scene.title} — {summary}")
        if ref in self._rationales:
            label.append(" ★ Scout", style="bold cyan")
        return label

    def _source_label(self, ref: SceneRef) -> str:
        session = next(item for item in self.history.sessions if item.breakdown.session_id == ref.session_id)
        return (
            f"Session {session.sequence_number:03d} — {session.breakdown.session_name}, "
            f"Scene {ref.scene_index + 1}: {self._catalog[ref].title}"
        )

    def on_tree_node_selected(self, event: Tree.NodeSelected[SceneRef | int | None]) -> None:
        event.stop()
        data = event.node.data
        if data is None:
            # Tree already expands/collapses category and Session rows before bubbling.
            return
        elif isinstance(data, int):
            if data in self._selected_ingredients:
                self._selected_ingredients.remove(data)
            else:
                self._selected_ingredients.add(data)
            event.node.set_label(self._ingredient_label(data))
            self._update_entry()
        else:
            if data in self._selected_scenes:
                self._selected_scenes.remove(data)
            else:
                self._selected_scenes.add(data)
            event.node.set_label(self._scene_label(data))
            self._update_selection()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted[SceneRef | int | None]) -> None:
        data = event.node.data
        if isinstance(data, int):
            item = self._items[data]
            sources = "\n\n".join(
                f"{self._source_label(ref)}\n{self._catalog[ref].situation}\n{self._catalog[ref].outcome}" for ref in item.sources
            )
            self.query_one("#previously-on-evidence", TextArea).load_text(f"{item.label}\n{item.current_state}\n\nSources\n{sources}")
        elif isinstance(data, SceneRef):
            detail = f"{self._source_label(data)}\n\n{self._catalog[data].model_dump_json(indent=2)}"
            if data in self._rationales:
                detail += f"\n\nScout rationale (GM only)\n{self._rationales[data]}"
            self.query_one("#previously-on-scene-detail", TextArea).load_text(detail)
        elif event.control.id == "previously-on-ingredients":
            self.query_one("#previously-on-evidence", TextArea).load_text("Focus an ingredient to inspect its sources.")
        else:
            self.query_one("#previously-on-scene-detail", TextArea).load_text(
                "Expand a Session and focus a Scene to inspect its full record."
            )

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id in ("previously-on-start", "previously-on-notes"):
            self._update_entry()

    def _can_scout(self) -> bool:
        return bool(self._selected_ingredients or self.query_one("#previously-on-notes", TextArea).text.strip())

    def _update_entry(self) -> None:
        self.query_one("#previously-on-scout", Button).disabled = not self._can_scout()

    def _update_selection(self) -> None:
        tree = self.query_one("#previously-on-scenes", ChoiceTree)
        for node, session in zip(tree.root.children, self.history.sessions, strict=True):
            count = sum(ref.session_id == session.breakdown.session_id for ref in self._selected_scenes)
            node.set_label(Text(f"Session {session.sequence_number:03d} — {session.breakdown.session_name} ({count} selected)"))
        self.query_one("#previously-on-count", Static).update(f"{len(self._selected_scenes)} Scenes selected")
        self.query_one("#previously-on-save", Button).disabled = not self._selected_scenes
        self.query_one("#previously-on-retry", Button).disabled = not self._selected_scenes

    def _show_error(self, error: BaseException) -> None:
        widget = self.query_one("#previously-on-error", Static)
        widget.update(str(error))
        widget.display = True

    def _clear_error(self) -> None:
        self.query_one("#previously-on-error").display = False

    def action_continue(self) -> None:
        if self.query_one("#previously-on-stage", ContentSwitcher).current == "previously-on-entry":
            self._scout()
        else:
            self._choose_destination()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "previously-on-scout":
                self._scout()
            case "previously-on-save":
                self._choose_destination()
            case "previously-on-retry":
                self._confirm_destination()
            case "previously-on-back":
                self._clear_error()
                self.query_one("#previously-on-stage", ContentSwitcher).current = "previously-on-entry"
                self.query_one("#previously-on-notes", TextArea).focus()
            case "previously-on-exit-entry" | "previously-on-exit-selection":
                self.action_leave()

    def _scout(self) -> None:
        if not self._can_scout() or not self.check_credentials("llm_model_high"):
            return
        data = ScoutInput(
            history=self.history,
            starting_situation=self.query_one("#previously-on-start", TextArea).text,
            selected_ingredients=tuple(self._items[index] for index in sorted(self._selected_ingredients)),
            upcoming_notes=self.query_one("#previously-on-notes", TextArea).text,
        )
        self._clear_error()
        self.run_with_progress(
            title="Find Scenes",
            message="Reading Campaign history for relevant callbacks…",
            work=lambda: self.application.previously_on_scout(data),
            on_success=self._show_selection,
            on_error=self._show_error,
        )

    def _show_selection(self, result: ScoutResult) -> None:
        self._rationales = {item.source: item.rationale for item in result.recommendations}
        self._selected_scenes = set(self._rationales)
        self._reviewed = True
        self._destination = None
        self._overwrite = False
        self.query_one("#previously-on-retry", Button).display = False
        self.query_one("#previously-on-destination", Static).update("")
        tree = self.query_one("#previously-on-scenes", ChoiceTree)
        tree.clear()
        tree.show_root = False
        for session in self.history.sessions:
            session_id = session.breakdown.session_id
            node = tree.root.add(Text(session.breakdown.session_name), expand=any(ref.session_id == session_id for ref in self._rationales))
            for index, _scene in enumerate(session.breakdown.scenes):
                ref = SceneRef(session_id=session_id, scene_index=index)
                node.add_leaf(self._scene_label(ref), data=ref)
        tree.root.expand()
        self._update_selection()
        self.query_one("#previously-on-stage", ContentSwitcher).current = "previously-on-selection"
        tree.focus()

    def _choose_destination(self) -> None:
        if not self._selected_scenes:
            return
        self.app.push_screen(
            FileSave(
                title="Save Previously On",
                location=Path.home(),
                default_file=self.history.suggested_filename,
                filters=Filters(("Markdown", lambda path: path.suffix.lower() == ".md")),
            ),
            self._destination_picked,
        )

    def _destination_picked(self, destination: Path | None) -> None:
        if destination is None:
            return
        try:
            destination = self.application.previously_on_destination(destination)
        except (OSError, ValueError) as exc:
            self._show_error(exc)
            return
        self._destination = destination
        self._overwrite = False
        self._confirm_destination()

    def _confirm_destination(self) -> None:
        if self._destination is None or not self._selected_scenes:
            return
        if self._destination.exists() and not self._overwrite:
            self.app.push_screen(
                ConfirmationDialog(
                    title="Replace Markdown file?",
                    prompt=f"Replace {self._destination}? The existing file stays intact until recap generation succeeds.",
                    yes_label="Replace",
                ),
                self._replacement_confirmed,
            )
        else:
            self._save()

    def _replacement_confirmed(self, answer: bool | None) -> None:
        if answer:
            self._overwrite = True
            self._save()

    def _save(self) -> None:
        destination = self._destination
        if destination is None or not self.check_credentials("llm_model_high"):
            return
        data = editor_input(self.history, frozenset(self._selected_scenes), self.query_one("#previously-on-start", TextArea).text)
        overwrite = self._overwrite
        self._clear_error()
        self.query_one("#previously-on-destination", Static).update(f"Destination: {destination}")
        self.run_with_progress(
            title="Create Previously On",
            message="Writing the selected Scenes into a concise recap…",
            work=lambda: self.application.export_previously_on(data, destination, overwrite=overwrite),
            on_success=self._saved,
            on_error=self._save_failed,
        )

    def _save_failed(self, error: BaseException) -> None:
        self._show_error(error)
        self.query_one("#previously-on-retry", Button).display = True

    def _saved(self, _: None) -> None:
        self.app.pop_screen()

    def has_changes(self) -> bool:
        return bool(
            self._reviewed
            or self._selected_ingredients
            or self.query_one("#previously-on-notes", TextArea).text.strip()
            or self.query_one("#previously-on-start", TextArea).text != self.history.starting_situation
        )

    def confirm_leave(self, leave: Callable[[], object]) -> None:
        if not self.has_changes():
            leave()
            return

        def confirmed(answer: bool | None) -> None:
            if answer:
                leave()

        self.app.push_screen(
            ConfirmationDialog(
                title="Discard Previously On?",
                prompt="Discard your inputs and Scene choices? This workflow does not save a draft.",
                yes_label="Discard",
            ),
            confirmed,
        )

    def action_leave(self) -> None:
        self.confirm_leave(self.app.pop_screen)
