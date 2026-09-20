"""The supported editor for workspace behavior and personal credentials."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, cast

from pydantic import ValidationError
from tablesage_application.configuration import MODEL_FIELDS, MODEL_PRESETS, PROVIDERS, Configuration
from tablesage_model.settings import AppSettings
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Button, Collapsible, Input, Select, Static

from ..dialogs import ConfirmationDialog, TextInputDialog
from .base import TableSageScreen


def field_id(path: str) -> str:
    return path.replace(".", "--")


class SettingsScreen(TableSageScreen):
    section = "settings"
    COMMON_BINDINGS = [
        Binding("ctrl+s", "save", "Save", key_display="Ctrl+S"),
        Binding("ctrl+d", "remove_key", "Remove key", key_display="^D", priority=True),
    ]
    HIDDEN_BINDINGS = [Binding("escape", "leave", "Back", show=False)]

    def __init__(self, configuration: Configuration, *, required: bool = False) -> None:
        super().__init__()
        self.configuration = configuration
        self.required = required
        self._initial: dict[str, Any] = {}
        self._model_values: dict[str, str] = {}
        self._removed_keys: set[str] = set()

    def compose_content(self) -> ComposeResult:
        with Vertical(id="settings-panel", classes="panel surface-2") as panel:
            panel.border_title = " settings "
            yield from self._compose_settings()

    def _compose_settings(self) -> ComposeResult:
        self._initial = self.application.settings.model_dump(include=set(MODEL_FIELDS))
        self._model_values = {path: str(self._initial[path]) for path in MODEL_FIELDS}
        with VerticalScroll(id="settings-scroll"):
            yield Static(
                "Review settings and Save to begin. New fields have recommended defaults."
                if self.required
                else "Workspace settings apply to subsequent actions. Save validates the entire form.",
                id="settings-intro",
            )
            with Collapsible(title="Keys", collapsed=False, id="settings-keys"):
                for provider in PROVIDERS:
                    with Horizontal(classes="credential-row"):
                        yield Static(
                            {"elevenlabs": "ElevenLabs (transcription)", "openai": "OpenAI"}.get(provider, provider.title()),
                            classes="credential-label",
                        )
                        key_input = Input(
                            password=True, placeholder=self._key_placeholder(provider), id=f"key-{provider}", classes="credential-input"
                        )
                        if self.configuration.shell_provided(provider):
                            key_input.tooltip = "Provided by shell environment; overrides the stored key."
                            key_input.disabled = True
                        yield key_input
            with Collapsible(title="LLM", collapsed=False):
                for path in MODEL_FIELDS:
                    label = {
                        "llm_model_high": "High model",
                        "llm_model": "Medium model",
                        "llm_model_lite": "Low model",
                    }[path]
                    yield Static(label, markup=False)
                    yield Select(
                        self._model_options(self._initial[path]),
                        value=self._initial[path],
                        allow_blank=False,
                        id=f"field-{field_id(path)}",
                    )
            yield Static("", id="settings-error", classes="settings-error", markup=False)
            with Horizontal(classes="settings-buttons"):
                yield Button("Save", id="settings-save", variant="primary")
                yield Button("Back", id="settings-back")

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if action == "remove_key":
            provider = self._focused_provider()
            if provider is None or self.configuration.shell_provided(provider):
                return None
            if not (self.configuration.stored.get(PROVIDERS[provider]) or self.query_one(f"#key-{provider}", Input).value):
                return None
        return False if action == "refresh_screen" else True

    def _focused_provider(self) -> str | None:
        provider = (self.focused.id or "").removeprefix("key-") if self.focused else ""
        return provider if provider in PROVIDERS else None

    def _key_placeholder(self, provider: str) -> str:
        if provider in self._removed_keys:
            return "Removed on Save"
        if self.configuration.stored.get(PROVIDERS[provider]) or self.configuration.shell_provided(provider):
            return "••••••••••••••••"
        return "Enter API key…"

    def _key_changes(self) -> dict[str, str | None]:
        changes: dict[str, str | None] = {provider: None for provider in self._removed_keys}
        for provider in PROVIDERS:
            value = self.query_one(f"#key-{provider}", Input).value
            if value:
                changes[provider] = value
        return changes

    def _restore_keys(self) -> None:
        self._removed_keys.clear()
        for provider in PROVIDERS:
            widget = self.query_one(f"#key-{provider}", Input)
            widget.value = ""
            widget.placeholder = self._key_placeholder(provider)
        self.refresh_bindings()

    def _values(self) -> dict[str, Any]:
        return {path: self._model_values[path] for path in MODEL_FIELDS}

    @staticmethod
    def _model_options(value: str) -> list[tuple[str, str]]:
        options = [(SettingsScreen._model_label(model), model) for _, model in MODEL_PRESETS]
        if value not in dict(MODEL_PRESETS).values():
            options.append((SettingsScreen._model_label(value), value))
        options.append(("Custom…", "custom"))
        return options

    @staticmethod
    def _model_label(model: str) -> str:
        provider, _, _ = model.partition("/")
        company = {"openai": "OpenAI", "anthropic": "Anthropic", "gemini": "Gemini"}.get(provider, provider.title())
        return f"{company}: {model}"

    def _set_model_value(self, path: str, value: str) -> None:
        select = self.query_one(f"#field-{field_id(path)}", Select)
        select.set_options(self._model_options(value))
        select.value = value
        self._model_values[path] = value

    def _dirty(self) -> bool:
        return bool(self._key_changes()) or self._values() != {k: v if isinstance(v, bool) else str(v) for k, v in self._initial.items()}

    def _save(self) -> bool:
        # Merge visible edits into the complete settings snapshot so hidden
        # processing options survive saves and LLM resets unchanged.
        data: dict[str, Any] = self.application.settings.model_dump()
        for path, value in self._values().items():
            node = data
            parts = path.split(".")
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = value
        try:
            settings = AppSettings.model_validate(data)
            saved = self.configuration.save_settings(settings, self._key_changes())
        except ValidationError as exc:
            first_error: str | None = None
            for error in exc.errors(include_input=False):
                path = ".".join(map(str, error["loc"]))
                if path in MODEL_FIELDS:
                    first_error = first_error or path
                    self._reveal_field(path)
            self.query_one("#settings-error", Static).update("Correct the indicated fields before saving. Expand sections to see errors.")
            if first_error:
                self.call_after_refresh(self.query_one(f"#field-{field_id(first_error)}").focus)
            return False
        except (ValueError, OSError) as exc:
            self.query_one("#settings-error", Static).update(str(exc))
            return False
        self.application.apply_settings(saved)
        self._initial = saved.model_dump(include=set(MODEL_FIELDS))
        self._restore(self._initial)
        self._restore_keys()
        from .main_app import TableSageApp

        cast(TableSageApp, self.app).settings_review_required = False
        self.required = False
        self.query_one("#settings-intro", Static).update("Settings saved. Changes apply to subsequent actions.")
        return True

    def _save_and_verify(self, finish: Callable[[], object]) -> None:
        """Save, then test every configured model and fetch missing local models before `finish`.

        A failed check keeps the (already saved) settings on screen with the reason, so the
        user can correct a key or model and save again.
        """
        if not self._save():
            return

        def verified(failure: str | None) -> None:
            if failure is None:
                self.notify("Settings saved. Models responded and local models are ready.")
                finish()
            else:
                show_failure(failure)

        def show_failure(message: str) -> None:
            self.query_one("#settings-error", Static).update(f"Settings saved, but the check failed. {message}")
            self.notify(message, title="Settings check failed", severity="error")

        self.run_with_progress(
            title="Checking settings",
            message="Testing models…",
            work=lambda: self.application.verify_setup(on_progress=lambda message: self.report_stage_progress(message, 0, 0)),
            on_success=verified,
            on_error=lambda error: show_failure(str(error)),
        )

    def _reveal_field(self, path: str) -> None:
        widget = self.query_one(f"#field-{field_id(path)}")
        for parent in widget.ancestors:
            if isinstance(parent, Collapsible):
                parent.collapsed = False
        self.call_after_refresh(widget.scroll_visible)

    def action_save(self) -> None:
        self._save_and_verify(self.app.pop_screen)

    def action_leave(self) -> None:
        def finish() -> None:
            if self.required:
                self.notify("Save settings to finish setup, or use Ctrl-Q to quit.")
            else:
                self.app.pop_screen()

        self.confirm_leave(finish)

    def confirm_leave(self, finish: Callable[[], None]) -> None:
        if not self._dirty():
            finish()
            return

        def chosen(result: bool | None) -> None:
            if result is True:
                self._save_and_verify(finish)
            elif result is False:
                if self.required:
                    self._restore(self._initial)
                    self._restore_keys()
                finish()

        self.app.push_screen(
            ConfirmationDialog(title="Unsaved settings", prompt="Save changes before leaving?", yes_label="Save", no_label="Discard"),
            chosen,
        )

    def on_input_changed(self, event: Input.Changed) -> None:
        if not self.is_mounted:
            return
        if (event.input.id or "").startswith("key-"):
            self.refresh_bindings()
            return
        path = (event.input.id or "").removeprefix("field-")
        if path in MODEL_FIELDS:
            preset = self.query_one(f"#preset-{path}", Select)
            value = event.value if event.value in dict(MODEL_PRESETS).values() else "custom"
            if preset.value != value:
                preset.value = value

    def _restore(self, values: dict[str, Any]) -> None:
        for path, value in values.items():
            if path in MODEL_FIELDS:
                self._set_model_value(path, str(value))

    def on_select_changed(self, event: Select.Changed) -> None:
        if not event.select.id or not event.select.id.startswith("field-"):
            return
        path = event.select.id.removeprefix("field-").replace("--", ".")
        if path not in MODEL_FIELDS:
            return
        if isinstance(event.value, str) and event.value != "custom":
            self._model_values[path] = event.value
            return
        previous = self._model_values[path]
        self.app.push_screen(
            TextInputDialog(
                title="Custom model ID",
                prompt="Enter an anthropic/, openai/, or gemini/ model ID.",
                placeholder="provider/model-name",
                submit_label="Use model",
            ),
            lambda value: self._set_model_value(path, value or previous),
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        key = event.button.id or ""
        if key == "settings-save":
            self.action_save()
        elif key == "settings-back":
            self.action_leave()

    def action_remove_key(self) -> None:
        provider = self._focused_provider()
        if provider is None or not self.check_action("remove_key", ()):
            return
        widget = self.query_one(f"#key-{provider}", Input)
        widget.value = ""
        if self.configuration.stored.get(PROVIDERS[provider]):
            self._removed_keys.add(provider)
        widget.placeholder = self._key_placeholder(provider)
        self.notify("Removal takes effect on Save. Shell keys remain active.")
        self.refresh_bindings()
