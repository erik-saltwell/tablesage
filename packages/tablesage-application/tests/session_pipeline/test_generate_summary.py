from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_summary as generate_summary_module
from tablesage_application.session_pipeline.generate_ledger import Ledger, Narration
from tablesage_application.session_pipeline.generate_summary import Attendee, GlossaryPromptEntry
from tablesage_model.model import Campaign, GlossaryEntry, Player
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
    attendees = [Attendee(player_name="Alice", roles=("Zaria",))]
    ledger_json = '{"session_name": "Session One"}'

    result = await generate_summary_module.generate_summary(
        ledger_json, attendees, glossary, "Iron Pact", "2026-08-18", "Blades in the Dark", "test-model"
    )

    assert result == "# The Adventure\n\nA summary.\n"
    assert captured["prompt"] is PromptName.SUMMARIZE_SESSION
    assert captured["model"] == "test-model"
    assert captured["response_model"] is None
    assert captured["template_data"].ledger == ledger_json
    assert captured["template_data"].attendees == attendees
    assert captured["template_data"].glossary == glossary
    assert captured["template_data"].campaign_name == "Iron Pact"
    assert captured["template_data"].session_date == "2026-08-18"
    assert captured["template_data"].game_system == "Blades in the Dark"


@pytest.mark.anyio
async def test_generate_summary_rejects_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _empty_response(*args: object, **kwargs: object) -> str:
        return " \n\t "

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _empty_response)

    with pytest.raises(ValueError, match="empty response"):
        await generate_summary_module.generate_summary("{}", [], [], "Iron Pact", None, None, "test-model")


def test_application_generate_summary_reads_ledger_sorts_glossary_and_replaces_atomically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.update_campaign(campaign.id, None, "Blades in the Dark")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Zaria", description="a wizard"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Aldor", description=None))
    game_session = application.create_session(campaign.id, "Session One", date(2026, 8, 18))

    session_folder = application.session_folder(game_session.id)
    ledger = Ledger(
        session_id=game_session.id,
        session_name="Session One",
        preamble=None,
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.")],
    )
    expected_ledger_text = ledger.model_dump_json(indent=2) + "\n"
    ledger.save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_summary(
        ledger_text: str,
        attendees: list[Attendee],
        glossary: list[GlossaryPromptEntry],
        campaign_name: str,
        session_date: str | None,
        game_system: str | None,
        model: str,
    ) -> str:
        captured.update(
            ledger=ledger_text,
            attendees=attendees,
            glossary=glossary,
            campaign_name=campaign_name,
            session_date=session_date,
            game_system=game_system,
            model=model,
        )
        return "new summary\n"

    monkeypatch.setattr(generate_summary_module, "generate_summary", _stub_generate_summary)

    application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "new summary\n"
    assert captured["ledger"] == expected_ledger_text
    assert captured["attendees"] == (Attendee(player_name="Alice", roles=("Zaria",)),)
    captured_glossary = cast(list[GlossaryPromptEntry], captured["glossary"])
    assert [entry.term for entry in captured_glossary] == ["Aldor", "Zaria"]
    assert captured["campaign_name"] == "Iron Pact"
    assert captured["session_date"] == "2026-08-18"
    assert captured["game_system"] == "Blades in the Dark"
    assert captured["model"] == "test-model"
    assert not (session_folder / ".summary.tmp.md").exists()


def test_application_generate_summary_preserves_existing_summary_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    Ledger(
        session_id=game_session.id,
        session_name="Session One",
        preamble=None,
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.")],
    ).save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _failing_generate_summary(*args: object, **kwargs: object) -> str:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_summary_module, "generate_summary", _failing_generate_summary)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".summary.tmp.md").exists()
