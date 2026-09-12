from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_player_introductions as module
from tablesage_application.session_pipeline.generate_player_introductions import (
    Attendee,
    GlossaryPromptEntry,
    PlayerIntroduction,
    PlayerIntroductions,
    PlayerIntroductionsGenerationResponse,
    PlayerIntroductionsValidationError,
)
from tablesage_application.session_pipeline.role_transcript import RoleTranscript, RoleTranscriptUtterance
from tablesage_application.session_pipeline.transcript_sections import (
    InclusiveUtteranceRange,
    RoutedUtterance,
    TranscriptSectionsGenerationResponse,
    persist_transcript_sections,
)
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_model.settings import AppSettings


def _attendees() -> tuple[Attendee, ...]:
    return (
        Attendee(player_name="Alice", roles=("Zaria",)),
        Attendee(player_name="Bob", roles=("Game Master",)),
    )


def _transcript() -> tuple[RoutedUtterance, ...]:
    return (
        RoutedUtterance(speaker="Zaria", text="Zaria is an elven wizard searching for her sister."),
        RoutedUtterance(speaker="Game Master", text="Last time, the party escaped the flooded mine."),
        RoutedUtterance(speaker="Corin", text="Corin is a former royal guard."),
    )


def _response(character: str = "Zaria") -> PlayerIntroductionsGenerationResponse:
    return PlayerIntroductionsGenerationResponse(
        scratchpad="Zaria is an explicitly introduced attendee role.",
        introductions=[PlayerIntroduction(character=character, description="An elven wizard searching for her sister.")],
    )


@pytest.mark.anyio
async def test_null_introduction_range_returns_empty_without_calling_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    called = False

    async def _unexpected_call(*args: object, **kwargs: object) -> str:
        nonlocal called
        called = True
        return "{}"

    monkeypatch.setattr(module, "call_llm_with_prompt", _unexpected_call)

    result = await module.generate_player_introductions(
        None, _attendees(), [], "Iron Pact", "2026-09-06", "Blades in the Dark", "high-model"
    )

    assert result == PlayerIntroductionsGenerationResponse(scratchpad="", introductions=[])
    assert called is False


@pytest.mark.anyio
async def test_generation_supplies_only_selected_transcript_and_full_session_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    async def _stub_call(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.update(prompt=prompt, template_data=template_data, model=model, response_model=response_model)
        return _response().model_dump_json()

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call)
    glossary = [GlossaryPromptEntry(term="Ashmoor", description="A blighted moorland.")]

    result = await module.generate_player_introductions(
        _transcript()[:2], _attendees(), glossary, "Iron Pact", "2026-09-06", "Blades in the Dark", "high-model"
    )

    assert result == _response()
    assert captured["prompt"] is PromptName.GENERATE_PLAYER_INTRODUCTIONS
    assert captured["model"] == "high-model"
    assert captured["response_model"] is PlayerIntroductionsGenerationResponse
    prompt_data = cast(module.PlayerIntroductionsPromptData, captured["template_data"])
    assert prompt_data.campaign_name == "Iron Pact"
    assert prompt_data.session_date == "2026-09-06"
    assert prompt_data.game_system == "Blades in the Dark"
    assert prompt_data.attendees == _attendees()
    assert prompt_data.glossary == tuple(glossary)
    assert "Zaria is an elven wizard" in prompt_data.introduction_transcript
    assert "Last time" in prompt_data.introduction_transcript
    assert "Corin is a former" not in prompt_data.introduction_transcript
    assert '"index"' not in prompt_data.introduction_transcript


def test_response_rejects_duplicate_characters_case_insensitively() -> None:
    with pytest.raises(ValidationError, match="at most once"):
        PlayerIntroductionsGenerationResponse(
            scratchpad="",
            introductions=[
                PlayerIntroduction(character="Zaria", description="A wizard."),
                PlayerIntroduction(character="zaria", description="Carries a staff."),
            ],
        )


@pytest.mark.anyio
async def test_generation_retries_unknown_gm_npc_and_player_names(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter(
        [
            _response("Game Master").model_dump_json(),
            _response("Alice").model_dump_json(),
            _response("Zaria").model_dump_json(),
        ]
    )
    calls = 0

    async def _stub_call(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        return next(responses)

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call)

    result = await module.generate_player_introductions(_transcript(), _attendees(), [], "Iron Pact", None, None, "high-model")

    assert calls == 3
    assert result.introductions[0].character == "Zaria"


@pytest.mark.anyio
async def test_generation_rejects_npc_and_requires_exact_role_name(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([_response("Veyra").model_dump_json(), _response("zaria").model_dump_json(), _response("Veyra").model_dump_json()])

    async def _stub_call(*args: object, **kwargs: object) -> str:
        return next(responses)

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call)

    with pytest.raises(PlayerIntroductionsValidationError, match="failed validation in all 3 attempts"):
        await module.generate_player_introductions(_transcript(), _attendees(), [], "Iron Pact", None, None, "high-model")


@pytest.mark.anyio
async def test_generation_does_not_retry_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    provider_error = RuntimeError("provider failed")
    calls = 0

    async def _stub_call(*args: object, **kwargs: object) -> str:
        nonlocal calls
        calls += 1
        raise provider_error

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call)

    with pytest.raises(RuntimeError) as raised:
        await module.generate_player_introductions(_transcript(), _attendees(), [], "Iron Pact", None, None, "high-model")
    assert raised.value is provider_error
    assert calls == 1


def test_envelope_preserves_order_metadata_and_renders_markdown(tmp_path: Path) -> None:
    session_id = uuid.uuid4()
    response = PlayerIntroductionsGenerationResponse(
        scratchpad="",
        introductions=[
            PlayerIntroduction(character="Corin", description="A former royal guard."),
            PlayerIntroduction(character="Zaria", description="An elven wizard."),
        ],
    )
    target = tmp_path / "player_introductions.json"

    persisted = module.persist_player_introductions(response, session_id, target)

    assert PlayerIntroductions.load(target) == persisted
    assert persisted.version == 1
    assert persisted.session_id == session_id
    assert [entry.character for entry in persisted.introductions] == ["Corin", "Zaria"]
    assert persisted.to_markdown() == ("## Player Characters\n\n- **Corin** — A former royal guard.\n- **Zaria** — An elven wizard.\n")
    assert PlayerIntroductions(session_id=session_id, introductions=[]).to_markdown() == ""


def test_atomic_persistence_preserves_existing_artifact_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "player_introductions.json"
    target.write_text("old artifact\n", encoding="utf-8")

    def _failing_save(self: PlayerIntroductions, path: Path) -> None:
        path.write_text("partial", encoding="utf-8")
        raise OSError("disk full")

    monkeypatch.setattr(PlayerIntroductions, "save", _failing_save)

    with pytest.raises(OSError, match="disk full"):
        module.persist_player_introductions(_response(), uuid.uuid4(), target)

    assert target.read_text(encoding="utf-8") == "old artifact\n"
    assert not (tmp_path / ".player_introductions.tmp.json").exists()


def test_application_generates_introductions_from_selected_range_and_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="high-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    application.update_campaign(campaign.id, None, "Blades in the Dark")
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    game_session = application.create_session(campaign.id, "Session One", date(2026, 9, 6))
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ashmoor", description="A moorland."))
    session_folder = application.session_folder(game_session.id)
    role_transcript = RoleTranscript(
        utterances=[
            RoleTranscriptUtterance(index=0, speaker="Game Master", text="Previously, the tower fell."),
            RoleTranscriptUtterance(index=1, speaker="Zaria", text="Zaria is an elven wizard."),
            RoleTranscriptUtterance(index=2, speaker="Game Master", text="The party escaped Ashmoor."),
            RoleTranscriptUtterance(index=3, speaker="Zaria", text="She carries a silver staff."),
            RoleTranscriptUtterance(index=4, speaker="Game Master", text="The party wakes beside the river."),
        ]
    )
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    role_transcript.save(role_path)
    persist_transcript_sections(
        TranscriptSectionsGenerationResponse(
            scratchpad="",
            recap_range=InclusiveUtteranceRange(start_index=0, end_index=2),
            introduction_range=InclusiveUtteranceRange(start_index=1, end_index=3),
            starting_context_range=InclusiveUtteranceRange(start_index=4, end_index=4),
            session_start_index=4,
        ),
        role_path,
        session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename,
    )
    captured: dict[str, Any] = {}

    async def _stub_generate(*args: object, **kwargs: object) -> PlayerIntroductionsGenerationResponse:
        captured.update(args=args)
        return _response()

    monkeypatch.setattr(module, "generate_player_introductions", _stub_generate)

    result = application.generate_player_introductions(game_session.id)

    args = cast(tuple[Any, ...], captured["args"])
    assert [utterance.text for utterance in args[0]] == [
        "Zaria is an elven wizard.",
        "The party escaped Ashmoor.",
        "She carries a silver staff.",
    ]
    assert args[1] == (Attendee(player_name="Alice", roles=("Zaria",)),)
    assert args[2] == (GlossaryPromptEntry(term="Ashmoor", description="A moorland."),)
    assert args[3:] == ("Iron Pact", "2026-09-06", "Blades in the Dark", "high-model")
    target = session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename
    assert PlayerIntroductions.load(target) == result
