"""Generate, revise, and export ephemeral Campaign opportunities."""

from pathlib import Path

from tablesage_application.campaign_recap import CampaignSceneRecap
from tablesage_application.opportunities import OpportunityResult
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Static, TextArea
from textual_fspicker import Filters

from ..dialogs.file_picker import FileSave
from ..dialogs.generic import ConfirmationDialog
from .base import TableSageScreen


class OpportunitiesScreen(TableSageScreen):
    section = "generate opportunities"
    DEFAULT_CSS = """
    OpportunitiesScreen #opportunity-ending { height: auto; max-height: 5; overflow-y: auto; }
    OpportunitiesScreen #opportunity-prompt { height: 5; }
    OpportunitiesScreen #opportunity-results { height: 1fr; }
    OpportunitiesScreen #opportunity-error { height: auto; max-height: 5; color: $error; }
    OpportunitiesScreen .opportunity-actions { height: 3; }
    OpportunitiesScreen Button { margin-right: 1; }
    """
    COMMON_BINDINGS = [
        Binding("escape", "pop_screen", "Back", key_display="Esc"),
        Binding("ctrl+g", "generate", "Generate", key_display="Ctrl+G", priority=True),
        Binding("ctrl+s", "save", "Save Markdown", key_display="Ctrl+S", priority=True),
    ]

    def __init__(self, recap: CampaignSceneRecap) -> None:
        super().__init__()
        self.recap = recap
        self.campaign = recap.campaign_name
        self.result: OpportunityResult | None = None

    def compose_content(self) -> ComposeResult:
        yield Static(self.recap.ending_situation, id="opportunity-ending", markup=False)
        yield Static("What might happen next Session? (required)")
        yield TextArea(id="opportunity-prompt", tab_behavior="focus")
        yield Static("", id="opportunity-error", markup=False)
        yield TextArea(read_only=True, id="opportunity-results", tab_behavior="focus")
        with Horizontal(classes="opportunity-actions"):
            yield Button("Generate", id="opportunity-generate", disabled=True, variant="primary")
            yield Button("Save Markdown…", id="opportunity-save", disabled=True)

    def on_mount(self) -> None:
        self.query_one("#opportunity-prompt", TextArea).focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if event.text_area.id == "opportunity-prompt":
            self.query_one("#opportunity-generate", Button).disabled = not event.text_area.text.strip()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "opportunity-generate":
            self.action_generate()
        elif event.button.id == "opportunity-save":
            self.action_save()

    def _error(self, error: BaseException) -> None:
        self.query_one("#opportunity-error", Static).update(str(error))

    def action_generate(self) -> None:
        prompt = self.query_one("#opportunity-prompt", TextArea).text.strip()
        if not prompt or not self.check_credentials("llm_model_high"):
            return
        self.query_one("#opportunity-error", Static).update("")
        self.run_with_progress(
            title="Generate Opportunities",
            message="Reading Campaign history for useful reincorporation seeds…",
            work=lambda: self.application.generate_opportunities(self.recap.campaign_id, prompt),
            on_success=self._generated,
            on_error=self._error,
        )

    def _generated(self, result: OpportunityResult) -> None:
        self.result = result
        self.query_one("#opportunity-results", TextArea).load_text(result.markdown())
        self.query_one("#opportunity-save", Button).disabled = False

    def action_save(self) -> None:
        if self.result is None:
            return
        self.app.push_screen(
            FileSave(
                title="Save Opportunities",
                location=Path.home(),
                default_file="opportunities.md",
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
            self._error(exc)
            return
        if destination.exists():
            self.app.push_screen(
                ConfirmationDialog(title="Replace Markdown file?", prompt=f"Replace {destination}?", yes_label="Replace"),
                lambda confirmed: self._save(destination, overwrite=True) if confirmed else None,
            )
        else:
            self._save(destination, overwrite=False)

    def _save(self, destination: Path, *, overwrite: bool) -> None:
        result = self.result
        if result is None:
            return
        self.query_one("#opportunity-error", Static).update("")
        self.run_with_progress(
            title="Save Opportunities",
            message="Saving Markdown…",
            work=lambda: self.application.save_opportunities(result, destination, overwrite=overwrite),
            on_success=lambda _: self.notify(f"Saved opportunities to {destination}"),
            on_error=self._error,
        )
