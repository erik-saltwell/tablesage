from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_recap_summary as module
from tablesage_application.session_pipeline.generate_ledger import Ledger, Narration
from tablesage_application.session_pipeline.generate_recap_summary import Attendee, GlossaryPromptEntry
from tablesage_application.session_pipeline.scene_breakdown import (
    LedgerRange,
    Scene,
    SceneBreakdown,
    SceneBreakdownContent,
    persist_ledger_pair,
)
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_model.settings import AppSettings


def _content() -> SceneBreakdownContent:
    return SceneBreakdownContent(
        ending_situation="The party enters the city.",
        scenes=[
            Scene(
                title="The gate",
                location="City gate",
                participants=["Zaria"],
                situation="Enter the city.",
                outcome="The gate opens.",
                carry_forward=[],
                signature_detail=None,
                ledger_ranges=[LedgerRange(start_index=0, end_index=0)],
            )
        ],
    )


def _source() -> str:
    return SceneBreakdown(
        session_id=uuid.UUID(int=1),
        session_name="Session One",
        starting_situation="At the gate.",
        ledger_sha256="0" * 64,
        **_content().model_dump(),
    ).model_dump_json()


def _write_ledger(application: Application, session_id: uuid.UUID) -> str:
    game_session = application.get_session(session_id)
    ledger = Ledger(
        session_id=game_session.id,
        session_name=game_session.name,
        starting_situation="The party stands before the gate.",
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.")],
    )
    return persist_ledger_pair(ledger, _content(), application.session_folder(game_session.id)).model_dump_json(indent=2)


@pytest.mark.anyio
async def test_generate_recap_summary_uses_dedicated_prompt_and_adds_heading(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _stub_call_llm_with_prompt(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.update(prompt=prompt, template_data=template_data, model=model, response_model=response_model)
        return "- The gate — The party entered the city.  \n\n"

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call_llm_with_prompt)
    attendees = (Attendee(player_name="Alice", roles=("Zaria",)),)
    glossary = (GlossaryPromptEntry(term="Aldor", description="a kingdom"),)

    result = await module.generate_recap_summary(
        _source(), attendees, glossary, "Iron Pact", "2026-08-18", "Blades in the Dark", "high-model"
    )

    assert result == "## Recap\n\n- The gate — The party entered the city.\n"
    assert captured["prompt"] is PromptName.GENERATE_RECAP_SUMMARY
    assert captured["model"] == "high-model"
    assert captured["response_model"] is None
    prompt_data = cast(module.RecapSummaryPromptData, captured["template_data"])
    assert prompt_data.scene_breakdown == _source()
    assert prompt_data.attendees == attendees
    assert prompt_data.glossary == glossary
    assert prompt_data.campaign_name == "Iron Pact"
    assert prompt_data.session_date == "2026-08-18"
    assert prompt_data.game_system == "Blades in the Dark"


@pytest.mark.anyio
async def test_generate_recap_summary_rejects_empty_response(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _empty_response(*args: object, **kwargs: object) -> str:
        return " \n\t "

    monkeypatch.setattr(module, "call_llm_with_prompt", _empty_response)

    with pytest.raises(ValueError, match="empty response"):
        await module.generate_recap_summary(_source(), (), (), "Iron Pact", None, None, "high-model")


def test_can_generate_recap_summary_requires_ledger(tmp_path: Path) -> None:
    assert module.can_generate_recap_summary(tmp_path) == (False, "Generate the Ledger and Scene Breakdown first.")
    (tmp_path / ARTIFACTS[ArtifactName.LEDGER].filename).write_text("{}", encoding="utf-8")
    assert module.can_generate_recap_summary(tmp_path)[0] is False


@pytest.mark.anyio
async def test_recap_retries_malformed_bullets_then_accepts_valid_content(monkeypatch: pytest.MonkeyPatch) -> None:
    outputs = iter(["## Recap\n- Heading is forbidden", "- First bullet\n  - Nested bullet", "- The gate opens."])

    async def respond(*args: object, **kwargs: object) -> str:
        return next(outputs)

    monkeypatch.setattr(module, "call_llm_with_prompt", respond)
    assert await module.generate_recap_summary(_source(), (), (), "Campaign", None, None, "model") == "## Recap\n\n- The gate opens.\n"


@pytest.mark.anyio
async def test_recap_provider_failure_is_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    async def respond(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        raise RuntimeError("provider failed")

    monkeypatch.setattr(module, "call_llm_with_prompt", respond)
    with pytest.raises(RuntimeError, match="provider failed"):
        await module.generate_recap_summary(_source(), (), (), "Campaign", None, None, "model")
    assert calls == 1


def test_application_generates_recap_without_automatically_invalidating_any_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="high-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.update_campaign(campaign.id, None, "Blades in the Dark")
    player = application.create_player(Player(name="Alice"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Zaria", description="a wizard"))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Aldor", description=None))
    game_session = application.create_session(campaign.id, "Session One", date(2026, 8, 18))
    attendee = application.add_attendance(game_session.id, player.id)
    application.set_attendance_roles(game_session.id, attendee.attendance_id, ["Zaria"])
    next_session = application.create_session(campaign.id, "Session Two", date(2026, 8, 25))
    expected_ledger = _write_ledger(application, game_session.id)
    session_folder = application.session_folder(game_session.id)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("stale summary\n", encoding="utf-8")
    next_summary_path = application.session_folder(next_session.id) / ARTIFACTS[ArtifactName.SUMMARY].filename
    next_summary_path.write_text("user-owned stale summary\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_recap_summary(
        scene_breakdown: str,
        attendees: tuple[Attendee, ...],
        glossary: tuple[GlossaryPromptEntry, ...],
        campaign_name: str,
        session_date: str | None,
        game_system: str | None,
        model: str,
    ) -> str:
        captured.update(
            scene_breakdown=scene_breakdown,
            attendees=attendees,
            glossary=glossary,
            campaign_name=campaign_name,
            session_date=session_date,
            game_system=game_system,
            model=model,
        )
        return "## Recap\n\n- The gate — The party entered the city.\n"

    monkeypatch.setattr(module, "generate_recap_summary", _stub_generate_recap_summary)

    result = application.generate_recap_summary(game_session.id)

    recap_path = session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename
    assert result == "## Recap\n\n- The gate — The party entered the city.\n"
    assert recap_path.read_text(encoding="utf-8") == result
    assert summary_path.read_text(encoding="utf-8") == "stale summary\n"
    assert next_summary_path.read_text(encoding="utf-8") == "user-owned stale summary\n"
    assert captured == {
        "scene_breakdown": expected_ledger,
        "attendees": (Attendee(player_name="Alice", roles=("Zaria",)),),
        "glossary": (
            GlossaryPromptEntry(term="Aldor", description=None),
            GlossaryPromptEntry(term="Zaria", description="a wizard"),
        ),
        "campaign_name": "Iron Pact",
        "session_date": "2026-08-18",
        "game_system": "Blades in the Dark",
        "model": "high-model",
    }
    assert not (session_folder / ".recap_summary.tmp.md").exists()


def test_application_preserves_existing_recap_and_summary_when_generation_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    _write_ledger(application, game_session.id)
    session_folder = application.session_folder(game_session.id)
    recap_path = session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    recap_path.write_text("old recap\n", encoding="utf-8")
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _failing_generate(*args: object, **kwargs: object) -> str:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(module, "generate_recap_summary", _failing_generate)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_recap_summary(game_session.id)

    assert recap_path.read_text(encoding="utf-8") == "old recap\n"
    assert summary_path.read_text(encoding="utf-8") == "old summary\n"


def test_persist_recap_summary_preserves_existing_file_when_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "recap_summary.md"
    target.write_text("old recap\n", encoding="utf-8")

    def _failing_replace(self: Path, target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="replace failed"):
        module.persist_recap_summary("new recap\n", target)

    assert target.read_text(encoding="utf-8") == "old recap\n"
    assert not (tmp_path / ".recap_summary.tmp.md").exists()
