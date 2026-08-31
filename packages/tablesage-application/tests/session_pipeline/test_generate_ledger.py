from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_ledger as generate_ledger_module
from tablesage_application.session_pipeline.generate_ledger import (
    Action,
    CharacterIntroduction,
    Correction,
    Expression,
    Ledger,
    LedgerGenerationResponse,
    Narration,
    Preamble,
    Recap,
    Speech,
)
from tablesage_model.model import Campaign, Player
from tablesage_model.settings import AppSettings
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _response(*, source: str = "Zaria", character: str = "Zaria") -> LedgerGenerationResponse:
    return LedgerGenerationResponse(
        scratchpad="Classified the campaign-relevant moves.",
        preamble=Preamble(
            recap=Recap(events=["The party escaped the flooded mine."], opening_situation="They awaken beside the river."),
            character_introductions=[
                CharacterIntroduction(character=character, description="A storm-touched elven wizard seeking her sister.")
            ],
        ),
        utterances=[
            Narration(type="narration", source=source, fact="Rain falls over the camp."),
            Action(type="action", source=source, entity="Zaria", action="Lights a signal fire."),
            Speech(type="speech", source=source, entity="Zaria", statement="We should leave before dawn."),
            Expression(type="expression", source=source, entity="Zaria", sentiment="Fears the riders will return."),
            Correction(type="correction", source=source, revision="The riders came from the east, not the north."),
        ],
    )


def _word(text: str, speaker: str = "Alice") -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=0.0, end=1.0, speaker=speaker)


def test_ledger_schema_supports_preamble_and_all_discriminated_utterance_types() -> None:
    session_id = uuid.uuid4()
    generated = _response()

    ledger = Ledger(
        version=3,
        session_id=session_id,
        session_name="  Session One  ",
        preamble=generated.preamble,
        utterances=generated.utterances,
    )
    reparsed = Ledger.model_validate_json(ledger.model_dump_json())

    assert reparsed.version == 3
    assert reparsed.session_id == session_id
    assert reparsed.session_name == "Session One"
    assert reparsed.preamble is not None
    assert reparsed.preamble.recap is not None
    assert reparsed.preamble.recap.events == ["The party escaped the flooded mine."]
    assert [utterance.type for utterance in reparsed.utterances] == [
        "narration",
        "action",
        "speech",
        "expression",
        "correction",
    ]


def test_ledger_schema_rejects_empty_content_empty_preamble_duplicate_introductions_and_extra_fields() -> None:
    with pytest.raises(ValidationError, match="meaningful content"):
        LedgerGenerationResponse(scratchpad="", preamble=None, utterances=[])

    with pytest.raises(ValidationError, match="Preamble must contain"):
        Preamble(recap=None, character_introductions=None)

    with pytest.raises(ValidationError, match="one introduction per character"):
        Preamble(
            recap=None,
            character_introductions=[
                CharacterIntroduction(character="Zaria", description="A wizard."),
                CharacterIntroduction(character="zaria", description="Carries a silver staff."),
            ],
        )

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Narration.model_validate({"type": "narration", "source": "Zaria", "fact": "It rains.", "entity": "Zaria"})


def test_ledger_allows_no_regular_utterances_when_preamble_has_content() -> None:
    ledger = Ledger(
        version=3,
        session_id=uuid.uuid4(),
        session_name="Session One",
        preamble=Preamble(recap=Recap(events=["The tower fell."], opening_situation=None), character_introductions=None),
        utterances=[],
    )

    assert ledger.utterances == []


@pytest.mark.anyio
async def test_generate_ledger_uses_structured_output_and_stops_on_warning_free_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    async def _stub_call_llm_with_prompt(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.update(prompt=prompt, template_data=template_data, model=model, response_model=response_model)
        return _response().model_dump_json()

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger(
        "**Zaria** - We should leave.\n",
        ["Game Master", "Zaria"],
        "test-model",
    )

    assert result.utterances[0].source == "Zaria"
    assert captured["prompt"] is PromptName.GENERATE_LEDGER
    assert captured["model"] == "test-model"
    assert captured["response_model"] is LedgerGenerationResponse
    assert captured["template_data"].transcript == "**Zaria** - We should leave.\n"
    assert captured["template_data"].known_roles == ("Game Master", "Zaria")


@pytest.mark.anyio
async def test_generate_ledger_retries_malformed_and_unknown_role_responses_then_returns_clean_candidate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            "not json",
            _response(source="Unknown Wanderer").model_dump_json(),
            _response(source="Zaria").model_dump_json(),
        ]
    )
    call_count = 0

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger("transcript", ["Zaria"], "test-model")

    assert call_count == 3
    assert result.utterances[0].source == "Zaria"


@pytest.mark.anyio
async def test_generate_ledger_selects_fewest_warnings_and_earliest_candidate_on_tie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _response(source="Unknown First")
    second = _response(source="Unknown Second")
    third = _response(source="Unknown Third", character="Unknown Character")
    responses = iter([first.model_dump_json(), second.model_dump_json(), third.model_dump_json()])

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger("transcript", ["Zaria"], "test-model")

    assert result.utterances[0].source == "Unknown First"


@pytest.mark.anyio
async def test_generate_ledger_fails_when_all_three_responses_are_structurally_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return "{}"

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    with pytest.raises(ValueError, match="no structurally valid response"):
        await generate_ledger_module.generate_ledger("transcript", ["Zaria"], "test-model")


def test_application_can_generate_ledger_requires_machine_transcript(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    assert application.can_generate_ledger(game_session.id) == (False, "Transcribe the session first.")

    Transcript.from_words([_word("Hello")]).save(application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)

    assert application.can_generate_ledger(game_session.id) == (True, None)


def test_application_generate_ledger_prefers_reviewed_transcript_injects_metadata_and_replaces_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path, AppSettings(llm_model="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    game_session = application.create_session(campaign.id, "Session One")
    attendee = application.list_attendance(game_session.id)[0]
    application.set_attendance_roles(game_session.id, attendee.attendance_id, ["Zaria", "Narrator"])
    session_folder = application.session_folder(game_session.id)

    machine = Transcript.from_words([_word("machine")])
    machine.save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    reviewed = Transcript(utterances=[machine.utterances[0].model_copy(update={"punctuated_text": "Reviewed opening."})])
    reviewed.save(session_folder / ARTIFACTS[ArtifactName.REVIEWED_TRANSCRIPT].filename)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("stale summary\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_ledger(transcript: str, known_roles: list[str] | tuple[str, ...], model: str) -> LedgerGenerationResponse:
        captured.update(transcript=transcript, known_roles=known_roles, model=model)
        return _response(source="Narrator")

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _stub_generate_ledger)

    application.generate_ledger(game_session.id)

    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    ledger = Ledger.model_validate_json(ledger_path.read_text(encoding="utf-8"))
    assert ledger.version == 3
    assert ledger.session_id == game_session.id
    assert ledger.session_name == "Session One"
    assert captured == {
        "transcript": "**Narrator** - Reviewed opening.\n",
        "known_roles": ("Narrator", "Zaria"),
        "model": "test-model",
    }
    assert not summary_path.exists()
    assert not (session_folder / ".ledger.tmp.json").exists()


def test_application_generate_ledger_preserves_existing_artifacts_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    Transcript.from_words([_word("Hello")]).save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)
    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    old_ledger = Ledger(
        version=3,
        session_id=game_session.id,
        session_name=game_session.name,
        preamble=None,
        utterances=[Narration(type="narration", source="Zaria", fact="Old fact.")],
    )
    ledger_path.write_text(old_ledger.model_dump_json(indent=2), encoding="utf-8")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _failing_generate_ledger(*args: object, **kwargs: object) -> LedgerGenerationResponse:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _failing_generate_ledger)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_ledger(game_session.id)

    assert Ledger.model_validate_json(ledger_path.read_text(encoding="utf-8")) == old_ledger
    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".ledger.tmp.json").exists()
