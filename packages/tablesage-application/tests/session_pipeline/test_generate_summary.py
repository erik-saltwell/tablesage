from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_summary as generate_summary_module
from tablesage_application.session_pipeline.generate_summary import GlossaryPromptEntry
from tablesage_model.model import Campaign, GlossaryEntry
from tablesage_model.settings import AppSettings


@pytest.mark.anyio
async def test_generate_summary_uses_application_prompt_helper_without_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _stub_call_llm_with_prompt(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.update(prompt=prompt, template_data=template_data, model=model, response_model=response_model)
        return "  # The Adventure\n\nA summary.  \n"

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)
    glossary = [GlossaryPromptEntry(term="Zaria", description="a wizard")]

    result = await generate_summary_module.generate_summary("**Wizard** - Hello.\n", glossary, "test-model")

    assert result == "# The Adventure\n\nA summary.\n"
    assert captured["prompt"] is PromptName.SUMMARIZE_SESSION
    assert captured["model"] == "test-model"
    assert captured["response_model"] is None
    assert captured["template_data"].transcript == "**Wizard** - Hello.\n"
    assert captured["template_data"].glossary == glossary


@pytest.mark.anyio
async def test_generate_summary_rejects_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _empty_response(*args: object, **kwargs: object) -> str:
        return " \n\t "

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _empty_response)

    with pytest.raises(ValueError, match="empty response"):
        await generate_summary_module.generate_summary("transcript", [], "test-model")


def test_application_generate_summary_reads_role_transcript_sorts_glossary_and_replaces_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = Application(tmp_path, AppSettings(llm_model="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Zaria", description="a wizard"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Aldor", description=None))

    session_folder = application.session_folder(game_session.id)
    transcript = "**Game Master** - The gate opens.\n"
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename).write_text(transcript, encoding="utf-8")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_summary(source: str, glossary: list[GlossaryPromptEntry], model: str) -> str:
        captured.update(source=source, glossary=glossary, model=model)
        return "new summary\n"

    monkeypatch.setattr(generate_summary_module, "generate_summary", _stub_generate_summary)

    application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "new summary\n"
    assert captured["source"] == transcript
    captured_glossary = cast(list[GlossaryPromptEntry], captured["glossary"])
    assert [entry.term for entry in captured_glossary] == ["Aldor", "Zaria"]
    assert captured["model"] == "test-model"
    assert not (session_folder / ".summary.tmp.md").exists()


def test_application_generate_summary_preserves_existing_summary_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    (session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_ROLES_TEXT].filename).write_text("**Wizard** - Hello.\n", encoding="utf-8")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _failing_generate_summary(*args: object, **kwargs: object) -> str:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_summary_module, "generate_summary", _failing_generate_summary)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".summary.tmp.md").exists()
