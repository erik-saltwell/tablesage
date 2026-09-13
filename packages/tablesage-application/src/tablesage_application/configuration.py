"""Workspace settings persistence and personal credential ownership."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import yaml
from dotenv import dotenv_values
from dotenv.parser import parse_stream
from platformdirs import user_config_path
from tablesage_model.settings import AppSettings

SETTINGS_VERSION = 1
PROVIDERS = {
    "elevenlabs": "ELEVENLABS_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
MODEL_FIELDS = ("llm_model_high", "llm_model", "llm_model_lite")
# Bundled catalog v1. Custom IDs remain possible within these providers.
MODEL_PRESETS = (
    ("openai/gpt-6-astra", "openai/gpt-6-astra"),
    ("openai/gpt-5.6-sol", "openai/gpt-5.6-sol"),
    ("openai/gpt-5.6-terra", "openai/gpt-5.6-terra"),
    ("anthropic/claude-sonnet-4-5", "anthropic/claude-sonnet-4-5"),
    ("anthropic/claude-opus-4-5", "anthropic/claude-opus-4-5"),
    ("anthropic/claude-haiku-4-5", "anthropic/claude-haiku-4-5"),
    ("gemini/gemini-2.5-pro", "gemini/gemini-2.5-pro"),
    ("gemini/gemini-2.5-flash", "gemini/gemini-2.5-flash"),
)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def validate_models(settings: AppSettings) -> None:
    for field in MODEL_FIELDS:
        value = getattr(settings, field)
        provider, separator, model = value.partition("/")
        if provider not in {"anthropic", "openai", "gemini"} or not separator or not model.strip() or any(c.isspace() for c in value):
            raise ValueError(f"{field}: use an anthropic/, openai/, or gemini/ model ID.")


def _keep_comment(original: str) -> str:
    """Preserve blank lines and any trailing comment when removing a managed assignment."""
    prefix = original[: len(original) - len(original.lstrip())]
    value = original.partition("=")[2].lstrip(" \t")
    if value.startswith(("'", '"')):
        quote = value[0]
        escaped = False
        for index, char in enumerate(value[1:], 1):
            if char == quote and not escaped:
                value = value[index + 1 :]
                break
            escaped = char == "\\" and not escaped
        comment = value.find("#")
    else:
        match = re.search(r"[ \t]+#", value)
        comment = value.find("#", match.start()) if match else -1
    return prefix + (value[comment:] if comment >= 0 else "")


class Configuration:
    def __init__(self, cwd: Path, credentials_path: Path | None = None) -> None:
        self.settings_path = cwd / ".tablesage" / "settings.yaml"
        self.credentials_path = credentials_path or user_config_path("tablesage", appauthor=False) / ".env"
        self._shell = {key: os.environ[key] for key in PROVIDERS.values() if key in os.environ}
        self.refresh_credentials()

    def refresh_credentials(self) -> None:
        self.stored = dotenv_values(self.credentials_path, interpolate=False)
        for key in PROVIDERS.values():
            value = self._shell.get(key, self.stored.get(key))
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def credential_status(self, provider: str) -> str:
        key = PROVIDERS[provider]
        value = os.environ.get(key)
        suffix = "" if not value else " ••••" + (value[-4:] if len(value) > 4 else "")
        if key in self._shell:
            return "Provided by shell environment (read-only)" + suffix
        return "Configured for this user" + suffix if value else "Not configured"

    def save_credential(self, provider: str, value: str | None) -> None:
        atomic_write(self.credentials_path, self._credential_text({provider: value}))
        self.refresh_credentials()

    def shell_provided(self, provider: str) -> bool:
        return PROVIDERS[provider] in self._shell

    def _credential_text(self, changes: dict[str, str | None]) -> str:
        updates = {PROVIDERS[provider]: value for provider, value in changes.items()}
        for value in updates.values():
            if value is not None and (not value.strip() or any(c in value for c in "\r\n\0")):
                raise ValueError("Enter a non-empty, single-line API key.")
        pieces: list[str] = []
        if self.credentials_path.exists():
            with self.credentials_path.open(encoding="utf-8", newline="") as stream:
                for binding in parse_stream(stream):
                    if binding.key not in updates:
                        pieces.append(binding.original.string)
                    else:
                        pieces.append(_keep_comment(binding.original.string))
        text = "".join(pieces)
        for key, value in updates.items():
            if value is not None:
                escaped = value.strip().replace("\\", "\\\\").replace("'", "\\'")
                text += ("\n" if text and not text.endswith("\n") else "") + f"{key}='{escaped}'\n"
        return text

    def save_settings(self, settings: AppSettings, credential_changes: dict[str, str | None] | None = None) -> AppSettings:
        validate_models(settings)
        saved = AppSettings.model_validate({**settings.model_dump(), "settings_version": SETTINGS_VERSION})
        settings_text = yaml.safe_dump(saved.model_dump(mode="json"), sort_keys=False)
        previous_credentials = None
        if credential_changes:
            credentials_text = self._credential_text(credential_changes)
            if self.credentials_path.exists():
                previous_credentials = self.credentials_path.read_text(encoding="utf-8")
            atomic_write(self.credentials_path, credentials_text)
        try:
            atomic_write(self.settings_path, settings_text)
        except OSError:
            if credential_changes:
                if previous_credentials is None:
                    self.credentials_path.unlink(missing_ok=True)
                else:
                    atomic_write(self.credentials_path, previous_credentials)
            raise
        if credential_changes:
            self.refresh_credentials()
        return saved

    def stored_field_paths(self) -> set[str]:
        """Fields explicitly present on disk, for highlighting additions during review."""
        if not self.settings_path.exists():
            return set()
        data = yaml.safe_load(self.settings_path.read_text(encoding="utf-8")) or {}

        def paths(node: dict, prefix: str = "") -> set[str]:
            result: set[str] = set()
            for key, value in node.items():
                path = f"{prefix}.{key}" if prefix else key
                result.update(paths(value, path) if isinstance(value, dict) else {path})
            return result

        return paths(data)

    @staticmethod
    def needs_review(settings: AppSettings) -> bool:
        if settings.settings_version > SETTINGS_VERSION:
            raise ValueError("This workspace uses a newer settings schema. Upgrade TableSage before opening it.")
        return settings.settings_version < SETTINGS_VERSION
