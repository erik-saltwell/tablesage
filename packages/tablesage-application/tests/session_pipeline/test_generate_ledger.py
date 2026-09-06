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
    Correction,
    Expression,
    GlossaryPromptEntry,
    Ledger,
    LedgerGenerationResponse,
    Narration,
    Question,
    Speech,
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


def _response(
    *, source: str = "Zaria", asker: str = "Alice", resolver: str = "Bob", starting_situation: str = "The party wakes beside the river."
) -> LedgerGenerationResponse:
    return LedgerGenerationResponse(
        scratchpad="Classified the campaign-relevant moves.",
        starting_situation=starting_situation,
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


def _starting_context() -> tuple[RoutedUtterance, ...]:
    return (RoutedUtterance(speaker="Game Master", text="The party wakes beside the river."),)


def _session_utterances() -> tuple[RoutedUtterance, ...]:
    return (RoutedUtterance(speaker="Zaria", text="I light a signal fire."),)


def _write_role_and_sections(
    session_folder: Path,
    role_transcript: RoleTranscript,
    *,
    starting_context: tuple[int, int] = (0, 0),
    session_start_index: int = 1,
    recap: tuple[int, int] | None = None,
) -> None:
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    role_transcript.save(role_path)
    response = TranscriptSectionsGenerationResponse(
        scratchpad="",
        recap_range=InclusiveUtteranceRange(start_index=recap[0], end_index=recap[1]) if recap else None,
        introduction_range=None,
        starting_context_range=InclusiveUtteranceRange(start_index=starting_context[0], end_index=starting_context[1]),
        session_start_index=session_start_index,
    )
    persist_transcript_sections(
        response,
        role_path,
        session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename,
    )


def test_ledger_v4_schema_supports_starting_situation_and_all_discriminated_utterance_types() -> None:
    session_id = uuid.uuid4()
    generated = _response()

    ledger = Ledger(
        version=4,
        session_id=session_id,
        session_name="  Session One  ",
        attendees=(Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=("Game Master",))),
        starting_situation=generated.starting_situation,
        utterances=generated.utterances,
    )
    reparsed = Ledger.model_validate_json(ledger.model_dump_json())

    assert reparsed.version == 4
    assert reparsed.session_id == session_id
    assert reparsed.session_name == "Session One"
    assert reparsed.starting_situation == "The party wakes beside the river."
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
        starting_situation=generated.starting_situation,
        utterances=generated.utterances,
    )

    markdown = ledger.to_markdown()

    assert markdown.startswith("# Session One\n\n**Attendees:** Alice (Zaria) · Bob (No roles)")
    assert "## Starting Situation\n\nThe party wakes beside the river.\n\n## Session" in markdown
    assert "## Recap" not in markdown
    assert "## Characters" not in markdown
    assert "1. Rain falls over the camp. *— Zaria*" in markdown
    assert "2. **Zaria** — Lights a signal fire." in markdown
    assert "3. **Zaria:** We should leave before dawn." in markdown
    assert "5. **⚠ Correction (Zaria):** The riders came from the east, not the north." in markdown
    assert "6. **? Alice:** Who built the bridge? → *unresolved*" in markdown
    assert f"*Session `{session_id}` · ledger format 4*" in markdown
    assert '"We should leave before dawn."' not in markdown


def test_ledger_schema_requires_non_empty_starting_situation_and_forbids_preamble_and_extra_fields() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        LedgerGenerationResponse(scratchpad="", starting_situation="  ", utterances=[])

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        LedgerGenerationResponse.model_validate(
            {"scratchpad": "", "starting_situation": "At the river.", "preamble": None, "utterances": []}
        )

    with pytest.raises(ValidationError, match="Input should be 4"):
        Ledger.model_validate(
            {
                "version": 3,
                "session_id": str(uuid.uuid4()),
                "session_name": "Session One",
                "starting_situation": "At the river.",
                "utterances": [],
            }
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
        starting_situation="The party stands before a locked door.",
        utterances=[Question(type="question", asker="Unknown", question="Is it locked?", resolver=None, resolution=None)],
    )

    assert generate_ledger_module._attendee_warning_count(response, frozenset({"Alice"})) == 1


def test_ledger_allows_no_regular_utterances_when_starting_situation_has_content() -> None:
    ledger = Ledger(
        version=4,
        session_id=uuid.uuid4(),
        session_name="Session One",
        starting_situation="The party surveys the fallen tower.",
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
        _starting_context(),
        _session_utterances(),
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
    assert captured["template_data"].starting_context == (
        '[\n  {\n    "speaker": "Game Master",\n    "text": "The party wakes beside the river."\n  }\n]'
    )
    assert captured["template_data"].session_utterances == ('[\n  {\n    "speaker": "Zaria",\n    "text": "I light a signal fire."\n  }\n]')
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
        _starting_context(),
        _session_utterances(),
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
        _starting_context(),
        _session_utterances(),
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
    first = _response(starting_situation="First candidate.", asker="Unknown Player")
    second = _response(starting_situation="Second candidate.", asker="Another Unknown Player")
    third = _response(starting_situation="Third candidate.", asker="Unknown Player", resolver="Unknown Resolver")
    responses = iter([first.model_dump_json(), second.model_dump_json(), third.model_dump_json()])

    async def _stub_call_llm_with_prompt(*args: object, **kwargs: object) -> str:
        return next(responses)

    monkeypatch.setattr(generate_ledger_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)

    result = await generate_ledger_module.generate_ledger(
        _starting_context(),
        _session_utterances(),
        ["Zaria"],
        [Attendee(player_name="Alice", roles=("Zaria",)), Attendee(player_name="Bob", roles=())],
        [],
        "test-model",
    )

    assert result.starting_situation == "First candidate."


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
            _starting_context(),
            _session_utterances(),
            ["Zaria"],
            [Attendee(player_name="Alice", roles=("Zaria",))],
            [],
            "test-model",
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
            _starting_context(),
            _session_utterances(),
            ["Zaria"],
            [Attendee(player_name="Alice", roles=("Zaria",))],
            [],
            "test-model",
        )

    assert raised.value is provider_error
    assert call_count == 1


def test_application_can_generate_ledger_requires_role_transcript(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    assert application.can_generate_ledger(game_session.id) == (False, "Clean the transcript first.")

    RoleTranscript(utterances=[RoleTranscriptUtterance(index=0, speaker="Alice", text="Hello")]).save(
        application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    )

    assert application.can_generate_ledger(game_session.id) == (False, "Section the transcript first.")

    _write_role_and_sections(
        application.session_folder(game_session.id),
        RoleTranscript(utterances=[RoleTranscriptUtterance(index=0, speaker="Alice", text="Hello")]),
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

    role_transcript = RoleTranscript(
        utterances=[
            RoleTranscriptUtterance(index=0, speaker="Narrator", text="Previously, the tower fell."),
            RoleTranscriptUtterance(index=1, speaker="Narrator", text="The party wakes beside the river."),
            RoleTranscriptUtterance(index=2, speaker="Zaria", text="I light a signal fire."),
        ]
    )
    _write_role_and_sections(session_folder, role_transcript, starting_context=(1, 1), session_start_index=2, recap=(0, 0))
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    recap_path = session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename
    summary_path.write_text("stale summary\n", encoding="utf-8")
    recap_path.write_text("stale recap\n", encoding="utf-8")
    captured: dict[str, object] = {}

    async def _stub_generate_ledger(
        starting_context: tuple[RoutedUtterance, ...],
        session_utterances: tuple[RoutedUtterance, ...],
        known_roles: list[str] | tuple[str, ...],
        attendees: tuple[Attendee, ...],
        glossary: tuple[GlossaryPromptEntry, ...],
        model: str,
    ) -> LedgerGenerationResponse:
        captured.update(
            starting_context=starting_context,
            session_utterances=session_utterances,
            known_roles=known_roles,
            attendees=attendees,
            glossary=glossary,
            model=model,
        )
        return _response(source="Narrator", asker="Alice", resolver="Alice")

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _stub_generate_ledger)

    application.generate_ledger(game_session.id)

    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    ledger_markdown_path = session_folder / "ledger.md"
    ledger = Ledger.model_validate_json(ledger_path.read_text(encoding="utf-8"))
    assert ledger.version == 4
    assert ledger.session_id == game_session.id
    assert ledger.session_name == "Session One"
    assert ledger.attendees == (Attendee(player_name="Alice", roles=("Narrator", "Zaria")),)
    assert captured == {
        "starting_context": (RoutedUtterance(speaker="Narrator", text="The party wakes beside the river."),),
        "session_utterances": (RoutedUtterance(speaker="Zaria", text="I light a signal fire."),),
        "known_roles": ("Narrator", "Zaria"),
        "attendees": (Attendee(player_name="Alice", roles=("Narrator", "Zaria")),),
        "glossary": (GlossaryPromptEntry(term="Ashmoor", description="The blighted moorland."),),
        "model": "test-model",
    }
    assert not summary_path.exists()
    assert not recap_path.exists()
    assert ledger_markdown_path.read_text(encoding="utf-8") == ledger.to_markdown()
    assert not (session_folder / ".ledger.tmp.json").exists()
    assert not (session_folder / ".ledger.tmp.md").exists()


def test_application_generate_ledger_preserves_existing_artifacts_on_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    _write_role_and_sections(
        session_folder,
        RoleTranscript(utterances=[RoleTranscriptUtterance(index=0, speaker="Alice", text="Hello")]),
    )
    ledger_path = session_folder / ARTIFACTS[ArtifactName.LEDGER].filename
    old_ledger = Ledger(
        version=4,
        session_id=game_session.id,
        session_name=game_session.name,
        starting_situation="The party waits at the gate.",
        utterances=[Narration(type="narration", source="Zaria", fact="Old fact.")],
    )
    ledger_path.write_text(old_ledger.model_dump_json(indent=2), encoding="utf-8")
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    recap_path = session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")
    recap_path.write_text("old recap\n", encoding="utf-8")

    async def _failing_generate_ledger(*args: object, **kwargs: object) -> LedgerGenerationResponse:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _failing_generate_ledger)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_ledger(game_session.id)

    assert Ledger.model_validate_json(ledger_path.read_text(encoding="utf-8")) == old_ledger
    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert recap_path.read_text(encoding="utf-8") == "old recap\n"
    assert not (session_folder / ".ledger.tmp.json").exists()


def test_application_generate_ledger_rejects_stale_transcript_sections(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    role_transcript = RoleTranscript(
        utterances=[
            RoleTranscriptUtterance(index=0, speaker="Game Master", text="The party waits at the gate."),
            RoleTranscriptUtterance(index=1, speaker="Zaria", text="I open it."),
        ]
    )
    _write_role_and_sections(session_folder, role_transcript)
    role_path = session_folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    role_path.write_text(role_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    called = False

    async def _stub_generate_ledger(*args: object, **kwargs: object) -> LedgerGenerationResponse:
        nonlocal called
        called = True
        return _response()

    monkeypatch.setattr(generate_ledger_module, "generate_ledger", _stub_generate_ledger)

    with pytest.raises(ValueError, match="different role transcript"):
        application.generate_ledger(game_session.id)

    assert called is False


def test_application_lazily_creates_and_exports_ledger_markdown(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    ledger = Ledger(
        session_id=game_session.id,
        session_name=game_session.name,
        starting_situation="The party waits beneath storm clouds.",
        utterances=[Narration(type="narration", source="Game Master", fact="Rain begins.")],
    )
    ledger.save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    destination = tmp_path / "exported-ledger.md"

    application.export_ledger_markdown(game_session.id, destination)

    assert destination.read_text(encoding="utf-8") == ledger.to_markdown()
    assert (session_folder / "ledger.md").read_text(encoding="utf-8") == ledger.to_markdown()
