from pathlib import Path

import pytest
import yaml
from tablesage_application.configuration import PROVIDERS, Configuration
from tablesage_model.settings import AppSettings


@pytest.fixture
def configuration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Configuration:
    for key in PROVIDERS.values():
        monkeypatch.delenv(key, raising=False)
    return Configuration(tmp_path, tmp_path / "personal" / ".env")


def test_key_edits_preserve_unmanaged_content_and_refresh_environment(configuration: Configuration) -> None:
    import os

    configuration.credentials_path.parent.mkdir()
    original = "# A note\nUNRELATED='keep this'\n"
    configuration.credentials_path.write_text(original)
    configuration.save_credential("gemini", "dummy-gemini-value")
    assert configuration.credentials_path.read_text().startswith(original)
    assert os.environ["GEMINI_API_KEY"] == "dummy-gemini-value"
    assert "dummy-gemini-value" not in configuration.credential_status("gemini")
    configuration.save_credential("gemini", None)
    assert "GEMINI_API_KEY" not in os.environ
    assert configuration.credentials_path.read_text() == original


def test_shell_override_survives_saved_key_changes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    monkeypatch.setenv("OPENAI_API_KEY", "dummy-shell-value")
    config = Configuration(tmp_path, tmp_path / "personal.env")
    config.save_credential("openai", "dummy-stored-value")
    assert os.environ["OPENAI_API_KEY"] == "dummy-shell-value"
    assert "shell" in config.credential_status("openai")
    config.save_credential("openai", None)
    assert os.environ["OPENAI_API_KEY"] == "dummy-shell-value"


def test_review_acknowledgement_and_invalid_model_do_not_overwrite(configuration: Configuration) -> None:
    assert configuration.needs_review(AppSettings())
    saved = configuration.save_settings(AppSettings())
    assert not configuration.needs_review(saved)
    before = configuration.settings_path.read_text()
    assert yaml.safe_load(before)["settings_version"] == 1
    with pytest.raises(ValueError, match="llm_model"):
        configuration.save_settings(AppSettings(llm_model="groq/something"))
    assert configuration.settings_path.read_text() == before
    with pytest.raises(ValueError, match="newer settings schema"):
        configuration.needs_review(AppSettings(settings_version=999))


def test_multiline_key_rejected_before_write(configuration: Configuration) -> None:
    with pytest.raises(ValueError):
        configuration.save_credential("anthropic", "value\nUNRELATED=changed")
    assert not configuration.credentials_path.exists()


def test_combined_save_validates_all_keys_before_writing(configuration: Configuration) -> None:
    with pytest.raises(ValueError):
        configuration.save_settings(AppSettings(), {"gemini": "valid", "openai": "bad\nkey"})
    assert not configuration.credentials_path.exists()
    assert not configuration.settings_path.exists()


def test_failed_settings_write_restores_credentials(configuration: Configuration, monkeypatch: pytest.MonkeyPatch) -> None:
    import os

    from tablesage_application import configuration as module

    configuration.save_credential("gemini", "original")
    original = configuration.credentials_path.read_bytes()
    write = module.atomic_write

    def fail_settings(path: Path, text: str) -> None:
        if path == configuration.settings_path:
            raise OSError("Settings write failed")
        write(path, text)

    monkeypatch.setattr(module, "atomic_write", fail_settings)
    with pytest.raises(OSError):
        configuration.save_settings(AppSettings(), {"gemini": "replacement", "openai": "new"})
    assert configuration.credentials_path.read_bytes() == original
    assert os.environ["GEMINI_API_KEY"] == "original"
    assert configuration.stored.get("OPENAI_API_KEY") is None


def test_replacement_preserves_comments_and_quoted_values(configuration: Configuration) -> None:
    import os

    configuration.credentials_path.parent.mkdir()
    configuration.credentials_path.write_text("# Keep\n\nGEMINI_API_KEY='old # not a comment' # my account\nUNRELATED=keep\n")
    configuration.save_credential("gemini", "dummy'quoted\\value")
    text = configuration.credentials_path.read_text()
    assert text.startswith("# Keep\n\n# my account\nUNRELATED=keep\n")
    assert os.environ["GEMINI_API_KEY"] == "dummy'quoted\\value"
