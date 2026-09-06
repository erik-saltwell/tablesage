from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import transcript_sections as module
from tablesage_application.session_pipeline.role_transcript import RoleTranscript, RoleTranscriptUtterance
from tablesage_application.session_pipeline.transcript_sections import (
    Attendee,
    InclusiveUtteranceRange,
    TranscriptSections,
    TranscriptSectionsGenerationResponse,
    TranscriptSectionsValidationError,
)
from tablesage_model.model import Campaign, Player
from tablesage_model.settings import AppSettings


def _transcript() -> RoleTranscript:
    return RoleTranscript(
        utterances=[
            RoleTranscriptUtterance(index=0, speaker="GM", text="Previously, the tower fell."),
            RoleTranscriptUtterance(index=1, speaker="Zaria", text="I am Zaria, an elven wizard."),
            RoleTranscriptUtterance(index=2, speaker="GM", text="Rain falls as you wake beside the river."),
            RoleTranscriptUtterance(index=3, speaker="Zaria", text="I light a fire."),
        ]
    )


def _response(**updates: Any) -> TranscriptSectionsGenerationResponse:
    values: dict[str, Any] = {
        "scratchpad": "The active scene begins at the fire.",
        "recap_range": {"start_index": 0, "end_index": 0},
        "introduction_range": {"start_index": 1, "end_index": 1},
        "starting_context_range": {"start_index": 2, "end_index": 2},
        "session_start_index": 3,
    }
    values.update(updates)
    return TranscriptSectionsGenerationResponse.model_validate(values)


def test_ranges_are_inclusive_ordered_and_may_overlap() -> None:
    response = _response(
        recap_range={"start_index": 0, "end_index": 2},
        introduction_range={"start_index": 1, "end_index": 2},
        starting_context_range={"start_index": 2, "end_index": 2},
    )

    assert module.validate_generation_response(response, 4) is response
    with pytest.raises(ValidationError, match="end_index"):
        InclusiveUtteranceRange(start_index=2, end_index=1)


@pytest.mark.parametrize(
    ("updates", "message"),
    [
        ({"recap_range": {"start_index": 0, "end_index": 4}}, "recap_range"),
        ({"session_start_index": 5}, "session_start_index"),
    ],
)
def test_validation_rejects_out_of_bounds_references(updates: dict[str, Any], message: str) -> None:
    with pytest.raises(TranscriptSectionsValidationError, match=message):
        module.validate_generation_response(_response(**updates), 4)


def test_terminal_session_start_is_valid() -> None:
    assert module.validate_generation_response(_response(session_start_index=4), 4).session_start_index == 4


@pytest.mark.anyio
async def test_generation_uses_high_level_inputs_and_retries_invalid_output(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict[str, object]] = []
    outputs = [
        '{"scratchpad":"bad","recap_range":null,"introduction_range":null,"starting_context_range":null,"session_start_index":8}',
        _response().model_dump_json(),
    ]

    async def _stub_call(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.append({"prompt": prompt, "template_data": template_data, "model": model, "response_model": response_model})
        return outputs.pop(0)

    monkeypatch.setattr(module, "call_llm_with_prompt", _stub_call)

    result = await module.generate_transcript_sections(
        _transcript(),
        [Attendee(player_name="Bob", roles=("Game Master",)), Attendee(player_name="Alice", roles=("Zaria",))],
        "high-model",
    )

    assert result == _response()
    assert len(captured) == 2
    assert captured[0]["prompt"] is PromptName.SECTION_TRANSCRIPT
    assert captured[0]["model"] == "high-model"
    assert captured[0]["response_model"] is TranscriptSectionsGenerationResponse
    prompt_data = cast(module.TranscriptSectionsPromptData, captured[0]["template_data"])
    assert [attendee.player_name for attendee in prompt_data.attendees] == ["Alice", "Bob"]
    assert '"index": 3' in prompt_data.role_transcript


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
        await module.generate_transcript_sections(_transcript(), [], "high-model")
    assert raised.value is provider_error
    assert calls == 1


def test_persisted_sections_fingerprint_exact_source_and_omit_scratchpad(tmp_path: Path) -> None:
    role_path = tmp_path / "role_transcript.json"
    sections_path = tmp_path / "transcript_sections.json"
    _transcript().save(role_path)

    sections = module.persist_transcript_sections(_response(), role_path, sections_path)

    assert sections.role_transcript_sha256 == hashlib.sha256(role_path.read_bytes()).hexdigest()
    persisted = sections_path.read_text(encoding="utf-8")
    assert "scratchpad" not in persisted
    assert "Previously" not in persisted
    assert module.load_current_transcript_sections(role_path, sections_path) == sections

    role_path.write_text(role_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(TranscriptSectionsValidationError, match="different role transcript"):
        module.load_current_transcript_sections(role_path, sections_path)


def test_route_transcript_selects_inclusive_ranges_suffix_and_removes_indices() -> None:
    transcript = _transcript()
    sections = TranscriptSections(
        role_transcript_sha256="0" * 64,
        recap_range=InclusiveUtteranceRange(start_index=0, end_index=0),
        introduction_range=InclusiveUtteranceRange(start_index=1, end_index=2),
        starting_context_range=InclusiveUtteranceRange(start_index=2, end_index=2),
        session_start_index=3,
    )

    routed = module.route_transcript(transcript, sections)

    assert [utterance.text for utterance in routed.recap] == ["Previously, the tower fell."]
    assert [utterance.text for utterance in routed.introductions] == [
        "I am Zaria, an elven wizard.",
        "Rain falls as you wake beside the river.",
    ]
    assert [utterance.text for utterance in routed.starting_context] == ["Rain falls as you wake beside the river."]
    assert [utterance.text for utterance in routed.session] == ["I light a fire."]
    assert set(routed.session[0].model_dump()) == {"speaker", "text"}


def test_null_ranges_are_valid_but_missing_starting_context_blocks_routing() -> None:
    response = _response(recap_range=None, introduction_range=None, starting_context_range=None, session_start_index=0)
    module.validate_generation_response(response, 4)
    sections = TranscriptSections(
        role_transcript_sha256="0" * 64,
        recap_range=None,
        introduction_range=None,
        starting_context_range=None,
        session_start_index=0,
    )

    with pytest.raises(TranscriptSectionsValidationError, match="starting_context_range is required"):
        module.route_transcript(_transcript(), sections)


def test_application_generates_sections_with_attendees_high_model_and_atomic_persistence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="high-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    _transcript().save(role_path)
    captured: dict[str, object] = {}

    async def _stub_generate(
        role_transcript: RoleTranscript, attendees: tuple[Attendee, ...], model: str
    ) -> TranscriptSectionsGenerationResponse:
        captured.update(role_transcript=role_transcript, attendees=attendees, model=model)
        return _response()

    monkeypatch.setattr(module, "generate_transcript_sections", _stub_generate)

    result = application.generate_transcript_sections(game_session.id)

    target = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename
    assert TranscriptSections.load(target) == result
    assert captured == {
        "role_transcript": _transcript(),
        "attendees": (Attendee(player_name="Alice", roles=("Zaria",)),),
        "model": "high-model",
    }
    assert not (session_folder / ".transcript_sections.tmp.json").exists()


def test_application_persists_null_starting_context_then_stops(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    _transcript().save(role_path)
    stale_paths = [
        session_folder / ARTIFACTS[ArtifactName.LEDGER].filename,
        session_folder / "ledger.md",
        session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename,
        session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename,
        session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename,
    ]
    for stale_path in stale_paths:
        stale_path.write_text("stale", encoding="utf-8")

    async def _stub_generate(*args: object, **kwargs: object) -> TranscriptSectionsGenerationResponse:
        return _response(starting_context_range=None)

    monkeypatch.setattr(module, "generate_transcript_sections", _stub_generate)

    with pytest.raises(TranscriptSectionsValidationError, match="no usable starting situation"):
        application.generate_transcript_sections(game_session.id)

    target = session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename
    assert TranscriptSections.load(target).starting_context_range is None
    assert all(not stale_path.exists() for stale_path in stale_paths)
