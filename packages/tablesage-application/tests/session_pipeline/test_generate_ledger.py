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
    Attendee,
    CharacterIntroduction,
    Correction,
    Expression,
    GlossaryPromptEntry,
    Ledger,
    LedgerGenerationResponse,
    Narration,
    Preamble,
    Question,
    Recap,
    Speech,
)
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_model.settings import AppSettings
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _response(*, source: str = "Zaria", character: str = "Zaria", asker: str = "Alice", resolver: str = "Bob") -> LedgerGenerationResponse:
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
            Question(
                type="question",
                asker=asker,
                question="Is the eastern road flooded?",
                resolver=resolver,
                resolution="Yes, the bridge is underwater.",
            ),
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
        attendees=(Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=("Game Master",))),
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
        "question",
    ]
    assert reparsed.attendees[0].player_name == "Alice"
    question = reparsed.utterances[-1]
    assert isinstance(question, Question)
    assert question.resolution == "Yes, the bridge is underwater."


def test_ledger_markdown_is_a_numbered_chronological_human_readable_view() -> None:
    session_id = uuid.uuid4()
    generated = _response()
    generated.utterances[-1] = Question(
        type="question",
        asker="Alice",
        question="Who built the bridge?",
        resolver=None,
        resolution=None,
    )
    ledger = Ledger(
        session_id=session_id,
        session_name="Session One",
        attendees=(Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=())),
        preamble=generated.preamble,
        utterances=generated.utterances,
    )

    markdown = ledger.to_markdown()

    assert markdown.startswith("# Session One\n\n**Attendees:** Alice (Zaria) · Bob (No roles)")
    assert "## Recap\n\n1. The party escaped the flooded mine." in markdown
    assert "## Characters\n\n- **Zaria** — A storm-touched elven wizard seeking her sister." in markdown
    assert "1. Rain falls over the camp. *— Zaria*" in markdown
    assert "2. **Zaria** — Lights a signal fire." in markdown
    assert "3. **Zaria:** We should leave before dawn." in markdown
    assert "5. **⚠ Correction (Zaria):** The riders came from the east, not the north." in markdown
    assert "6. **? Alice:** Who built the bridge? → *unresolved*" in markdown
    assert f"*Session `{session_id}` · ledger format 3*" in markdown
    assert '"We should leave before dawn."' not in markdown


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

    with pytest.raises(ValidationError, match="both be set or both be absent"):
        Question(type="question", asker="Alice", question="Is it locked?", resolver="Bob", resolution=None)

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        Question.model_validate(
            {"type": "question", "asker": "Alice", "question": "Is it locked?", "resolver": None, "resolution": None, "source": "Zaria"}
        )


def test_question_allows_unresolved_exchange_and_attendee_warnings_are_separate_from_roles() -> None:
    response = LedgerGenerationResponse(
        scratchpad="",
        preamble=None,
        utterances=[Question(type="question", asker="Unknown", question="Is it locked?", resolver=None, resolution=None)],
    )

    assert generate_ledger_module._introduction_warning_count(response, frozenset({"Zaria"})) == 0
    assert generate_ledger_module._attendee_warning_count(response, frozenset({"Alice"})) == 1


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
        [Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=("Game Master",))],
        [GlossaryPromptEntry(term="Ashmoor", description="The blighted moorland.")],
        "test-model",
    )

    assert isinstance(result.utterances[0], Narration)
    assert result.utterances[0].source == "Zaria"
    assert captured["prompt"] is PromptName.GENERATE_LEDGER
    assert captured["model"] == "test-model"
    assert captured["response_model"] is LedgerGenerationResponse
    assert captured["template_data"].transcript == "**Zaria** - We should leave.\n"
    assert captured["template_data"].known_roles == ("Game Master", "Zaria")
    assert captured["template_data"].attendees == (
        Attendee(player_name="Alice", roles=("Zaria",)),
        Attendee(player_name="Bob", roles=("Game Master",)),
    )
    assert captured["template_data"].glossary == (GlossaryPromptEntry(term="Ashmoor", description="The blighted moorland."),)


@pytest.mark.anyio
async def test_generate_ledger_retries_malformed_response_but_accepts_unknown_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            "not json",
            _response(source="Unknown Wanderer").model_dump_json(),
        ]
    )
    call_count = 0

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger(
        "transcript",
        ["Zaria"],
        [Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=())],
        [],
        "test-model",
    )

    assert call_count == 2
    assert result.utterances[0].source == "Unknown Wanderer"


@pytest.mark.anyio
async def test_generate_ledger_retries_unknown_question_attendee(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = iter([_response(asker="Unknown Player").model_dump_json(), _response().model_dump_json()])
    call_count = 0

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger(
        "transcript",
        ["Zaria"],
        [Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=())],
        [],
        "test-model",
    )

    assert call_count == 2
    question = result.utterances[-1]
    assert isinstance(question, Question)
    assert question.asker == "Alice"


@pytest.mark.anyio
async def test_generate_ledger_selects_fewest_warnings_and_earliest_candidate_on_tie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _response(character="Unknown First")
    second = _response(character="Unknown Second")
    third = _response(character="Unknown Third", asker="Unknown Player")
    responses = iter([first.model_dump_json(), second.model_dump_json(), third.model_dump_json()])

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger(
        "transcript",
        ["Zaria"],
        [Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=())],
        [],
        "test-model",
    )

    assert result.preamble is not None
    assert result.preamble.character_introductions is not None
    assert result.preamble.character_introductions[0].character == "Unknown First"


@pytest.mark.anyio
async def test_generate_ledger_fails_when_all_three_responses_are_structurally_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return "{}"

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    with pytest.raises(ValueError, match="failed structural validation in all 3 attempts") as raised:
        await generate_ledger_module.generate_ledger(
            "transcript", ["Zaria"], [Attendee(player_name="Alice", roles=("Zaria",))], [], "test-model"
        )

    assert call_count == 3
    assert "scratchpad" in str(raised.value)


@pytest.mark.anyio
async def test_generate_ledger_does_not_retry_or_mask_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0
    provider_error = RuntimeError('tool_choice: type "tool" and "any" are not supported for this model.')

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        raise provider_error

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    with pytest.raises(RuntimeError, match="tool_choice") as raised:
        await generate_ledger_module.generate_ledger(
            "transcript", ["Zaria"], [Attendee(player_name="Alice", roles=("Zaria",))], [], "test-model"
        )

    assert raised.value is provider_error
    assert call_count == 1


def test_application_can_generate_ledger_requires_role_transcript(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    assert application.can_generate_ledger(game_session.id) == (False, "Clean the transcript first.")

    Transcript.from_words([_word("Hello")]).save(
        application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    )

    assert application.can_generate_ledger(game_session.id) == (True, None)


def test_application_generate_ledger_reads_role_transcript_injects_metadata_and_replaces_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ashmoor", description="The blighted moorland."))
    game_session = application.create_session(campaign.id, "Session One")
    attendee = application.list_attendance(game_session.id)[0]
    application.set_attendance_roles(game_session.id, attendee.attendance_id, ["Zaria", "Narrator"])
    session_folder = application.session_folder(game_session.id)

    role_transcript = Transcript(
        utterances=[
            Transcript.from_words([_word("opening", speaker="Narrator")])
            .utterances[0]
            .model_copy(update={"punctuated_text": "Reviewed opening."})
        ]
    )
    role_transcript.save(session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("stale summary\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_ledger(
        transcript: str,
        known_roles: list[str] | tuple[str, ...],
        attendees: tuple[Attendee, ...],
        glossary: tuple[GlossaryPromptEntry, ...],
        model: str,
    ) -> LedgerGenerationResponse:
        captured.update(transcript=transcript, known_roles=known_roles, attendees=attendees, glossary=glossary, model=model)
        return _response(source="Narrator", asker="Alice", resolver="Alice")

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _stub_generate_ledger)

    application.generate_ledger(game_session.id)

    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    ledger_markdown_path = session_folder / "ledger.md"
    ledger = Ledger.model_validate_json(ledger_path.read_text(encoding="utf-8"))
    assert ledger.version == 3
    assert ledger.session_id == game_session.id
    assert ledger.session_name == "Session One"
    assert ledger.attendees == (Attendee(player_name="Alice", roles=("Narrator", "Zaria")),)
    assert captured == {
        "transcript": "**Narrator** - Reviewed opening.\n",
        "known_roles": ("Narrator", "Zaria"),
        "attendees": (Attendee(player_name="Alice", roles=("Narrator", "Zaria")),),
        "glossary": (GlossaryPromptEntry(term="Ashmoor", description="The blighted moorland."),),
        "model": "test-model",
    }
    assert not summary_path.exists()
    assert ledger_markdown_path.read_text(encoding="utf-8") == ledger.to_markdown()
    assert not (session_folder / ".ledger.tmp.json").exists()
    assert not (session_folder / ".ledger.tmp.md").exists()


def test_application_generate_ledger_preserves_existing_artifacts_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    Transcript.from_words([_word("Hello")]).save(session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)
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


def test_application_lazily_creates_and_exports_ledger_markdown(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    ledger = Ledger(
        session_id=game_session.id,
        session_name=game_session.name,
        preamble=None,
        utterances=[Narration(type="narration", source="Game Master", fact="Rain begins.")],
    )
    ledger.save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    destination = tmp_path / "exported-ledger.md"

    application.export_ledger_markdown(game_session.id, destination)

    assert destination.read_text(encoding="utf-8") == ledger.to_markdown()
    assert (session_folder / "ledger.md").read_text(encoding="utf-8") == ledger.to_markdown()
