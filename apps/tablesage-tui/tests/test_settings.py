from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest
from tablesage_application.configuration import PROVIDERS, Configuration
from tablesage_model.settings import AppSettings
from tablesage_tools.credentials import MissingCredential
from tablesage_tui.dialogs import ConfirmationDialog, TextInputDialog
from tablesage_tui.screens.base import TableSageScreen
from tablesage_tui.screens.landing import LandingScreen
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.settings import SettingsScreen
from tablesage_tui.widgets import CommandButton
from textual.widget import Widget
from textual.widgets import Button, Collapsible, Input, Select
from textual.worker import WorkerFailed


@pytest.fixture
def configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Configuration:
    for key in PROVIDERS.values():
        monkeypatch.delenv(key, raising=False)
    return Configuration(tmp_path, tmp_path / "personal.env")


def application() -> MagicMock:
    result = MagicMock(settings=AppSettings())
    result.apply_settings.side_effect = lambda settings: setattr(result, "settings", settings)
    result.verify_setup.return_value = None
    return result


@pytest.mark.anyio
@pytest.mark.parametrize("size", [(80, 24), (120, 45)])
async def test_inline_keys_are_single_line_masked_and_saved_together(configuration: Configuration, size: tuple[int, int]) -> None:
    configuration.save_credential("openai", "dummy-original-secret")
    app = TableSageApp(application(), configuration=configuration)
    async with app.run_test(size=size) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        key = screen.query_one("#key-openai", Input)
        assert key.password and key.value == ""
        assert key.placeholder == "••••••••••••••••"
        for row in screen.query(".credential-row"):
            assert row.size.height == 1
        assert key.size.height == 1
        assert key.size.width >= 16
        high_model = screen.query_one("#field-llm_model_high", Select)
        assert high_model.region.right == key.region.right
        settings_actions = screen.query_one(".settings-buttons")
        back = screen.query_one("#settings-back")
        assert back.region.right == settings_actions.region.right
        keys_title = screen.query_one("#settings-keys > CollapsibleTitle")
        first_row = cast(Widget, screen.query_one("#key-elevenlabs", Input).parent)
        assert first_row is not None
        assert first_row.region.y - keys_title.region.bottom == 1
        save_binding = next(binding for binding in screen.COMMON_BINDINGS if binding.action == "save")
        assert save_binding.key_display == "Ctrl+S"
        assert all(binding.action != "help" for binding in screen.COMMON_BINDINGS)
        await pilot.press("f1")
        assert app.screen is screen
        gemini_row = cast(Widget, screen.query_one("#key-gemini", Input).parent)
        llm_section = next(section for section in screen.query(Collapsible) if section.title == "LLM")
        assert gemini_row is not None
        assert llm_section.region.y - gemini_row.region.bottom == 1
        assert not screen._dirty()
        gemini = screen.query_one("#key-gemini", Input)
        gemini.focus()
        await pilot.press("n", "e", "w")
        assert configuration.stored.get("GEMINI_API_KEY") is None
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert configuration.stored["GEMINI_API_KEY"] == "new"
        assert configuration.stored["OPENAI_API_KEY"] == "dummy-original-secret"
        assert isinstance(app.screen, LandingScreen)
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        key = screen.query_one("#key-openai", Input)
        key.focus()
        await pilot.press("ctrl+d")
        assert configuration.stored["OPENAI_API_KEY"] == "dummy-original-secret"
        assert screen._dirty()
        await pilot.press("ctrl+s")
        assert configuration.stored.get("OPENAI_API_KEY") is None
        assert isinstance(app.screen, LandingScreen)


@pytest.mark.anyio
async def test_key_drafts_discard_and_invalid_models_preserve_keys(configuration: Configuration) -> None:
    configuration.save_credential("anthropic", "dummy-original")
    app = TableSageApp(application(), configuration=configuration, settings_review_required=True)
    async with app.run_test(size=(120, 45)) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        key = screen.query_one("#key-anthropic", Input)
        key.value = "dummy-replacement"
        screen._set_model_value("llm_model", "invalid/model")
        assert not screen._save()
        assert configuration.stored["ANTHROPIC_API_KEY"] == "dummy-original"
        await pilot.press("escape")
        assert isinstance(app.screen, ConfirmationDialog)
        app.screen.dismiss(False)
        await pilot.pause()
        assert app.screen is screen
        assert not screen._dirty() and key.value == ""
        assert configuration.stored["ANTHROPIC_API_KEY"] == "dummy-original"


@pytest.mark.anyio
async def test_required_setup_stays_on_landing_with_toast(configuration: Configuration) -> None:
    app = TableSageApp(application(), configuration=configuration, settings_review_required=True)
    with patch.object(app, "notify", wraps=app.notify) as notify:
        async with app.run_test(size=(120, 45)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, LandingScreen)
            assert app.screen.query_one("#show-campaigns-command", CommandButton).disabled
            assert app.screen.query_one("#show-players-command", CommandButton).disabled
            assert not app.screen.query_one("#show-settings-command", CommandButton).disabled
            notify.assert_called_once_with(
                "Configure and save your settings before progressing. Press S to open Settings.",
                title="Settings required",
                severity="warning",
                timeout=float("inf"),
            )
            await pilot.press("c", "p")
            await pilot.pause()
            assert isinstance(app.screen, LandingScreen)


@pytest.mark.anyio
async def test_required_setup_cannot_escape_until_valid_save(configuration: Configuration) -> None:
    app = TableSageApp(application(), configuration=configuration, settings_review_required=True)
    async with app.run_test(size=(120, 45)) as pilot:
        await pilot.press("s")
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, SettingsScreen)
        screen = app.screen
        # Invalid values never create or replace the workspace file.
        screen._set_model_value("llm_model", "unsupported/model")
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert app.settings_review_required
        assert not configuration.settings_path.exists()
        screen._set_model_value("llm_model", "gemini/custom-model")
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert not app.settings_review_required
        assert app.application.settings.settings_version == 1
        assert not isinstance(app.screen, SettingsScreen)
        assert not app.screen.query_one("#show-campaigns-command", CommandButton).disabled
        assert not app.screen.query_one("#show-players-command", CommandButton).disabled


@pytest.mark.anyio
async def test_dirty_form_prompts_and_discard_does_not_write(configuration: Configuration) -> None:
    app = TableSageApp(application(), configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        await pilot.press("s")
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        screen._set_model_value("llm_model", "gemini/custom-model")
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmationDialog)
        buttons = list(app.screen.query(Button))
        assert {button.size.width for button in buttons} == {len("Discard") + 2}
        app.screen.dismiss(False)
        await pilot.pause()
        assert not isinstance(app.screen, SettingsScreen)
        assert not configuration.settings_path.exists()


@pytest.mark.anyio
async def test_model_selection_only_changes_draft(configuration: Configuration) -> None:
    source = application()
    source.settings = AppSettings(llm_model="gemini/custom-model")
    app = TableSageApp(source, configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        screen.query_one("#field-llm_model", Select).value = "openai/gpt-5.6-sol"
        await pilot.pause()
        assert source.settings.llm_model == "gemini/custom-model"
        assert not configuration.settings_path.exists()


@pytest.mark.anyio
async def test_llm_roles_are_selectors_and_custom_model_remains_selected(configuration: Configuration) -> None:
    source = application()
    source.settings = AppSettings(llm_model="gemini/already-custom")
    app = TableSageApp(source, configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        selectors = [screen.query_one(f"#field-{field}", Select) for field in ("llm_model_high", "llm_model", "llm_model_lite")]
        assert [selector.value for selector in selectors] == [
            source.settings.llm_model_high,
            "gemini/already-custom",
            source.settings.llm_model_lite,
        ]
        assert {label for label, _ in selectors[0]._options} >= {
            "OpenAI: openai/gpt-6-astra",
            "OpenAI: openai/gpt-5.6-sol",
            "OpenAI: openai/gpt-5.6-terra",
            "Anthropic: anthropic/claude-sonnet-4-5",
            "Anthropic: anthropic/claude-opus-4-5",
            "Anthropic: anthropic/claude-haiku-4-5",
            "Gemini: gemini/gemini-2.5-pro",
            "Gemini: gemini/gemini-2.5-flash",
            "Custom…",
        }
        medium = selectors[1]
        medium.value = "custom"
        await pilot.pause()
        assert isinstance(app.screen, TextInputDialog)
        custom_input = app.screen.query_one("#text-input-value", Input)
        custom_input.value = "openai/my-custom-model"
        custom_input.focus()
        await pilot.press("enter")
        await pilot.pause()
        assert app.screen is screen
        assert medium.value == "openai/my-custom-model"
        assert screen._values()["llm_model"] == "openai/my-custom-model"


@pytest.mark.anyio
async def test_only_llm_and_keys_are_exposed_and_hidden_settings_survive_save(configuration: Configuration) -> None:
    import yaml

    source = application()
    source.settings = AppSettings.model_validate({"remove_outliers": {"min_samples": 11}, "connection_test_timeout": 47})
    before = source.settings.model_dump(exclude={"settings_version", "llm_model"})
    app = TableSageApp(source, configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        assert {section.title for section in screen.query(Collapsible)} == {"LLM", "Keys"}
        assert not screen.query("#field-remove_outliers--min_samples")
        assert not screen.query("#settings-reset-all")
        screen._set_model_value("llm_model", "gemini/custom-model")
        await pilot.press("ctrl+s")
        await pilot.pause()
        assert source.settings.model_dump(exclude={"settings_version", "llm_model"}) == before
        stored = yaml.safe_load(configuration.settings_path.read_text())
        assert stored["remove_outliers"]["min_samples"] == 11
        assert stored["connection_test_timeout"] == 47


@pytest.mark.anyio
async def test_missing_credential_recovery_opens_settings(configuration: Configuration) -> None:
    app = TableSageApp(application(), configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        screen = app.screen
        assert isinstance(screen, TableSageScreen)
        screen.run_with_progress(
            title="Test",
            message="Test",
            work=lambda: (_ for _ in ()).throw(MissingCredential("gemini", "gemini/test-model")),
            on_success=lambda _: None,
        )
        with pytest.raises(WorkerFailed):
            await app.workers.wait_for_complete()
        await pilot.pause()
        assert isinstance(app.screen, ConfirmationDialog)
        app.screen.dismiss(True)
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)


@pytest.mark.anyio
async def test_quit_prompts_for_dirty_settings(configuration: Configuration) -> None:
    app = TableSageApp(application(), configuration=configuration)
    async with app.run_test(size=(120, 45)) as pilot:
        app.action_open_settings()
        await pilot.pause()
        screen = app.screen
        assert isinstance(screen, SettingsScreen)
        screen._set_model_value("llm_model", "gemini/custom-model")
        await pilot.press("ctrl+q")
        await pilot.pause()
        assert isinstance(app.screen, ConfirmationDialog)
        app.screen.dismiss(None)
        await pilot.pause()
        assert isinstance(app.screen, SettingsScreen)
