from __future__ import annotations

import uuid
from datetime import date
from pathlib import Path
from typing import Any, cast

import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import generate_summary as generate_summary_module
from tablesage_application.session_pipeline.generate_ledger import Ledger, Narration
from tablesage_application.session_pipeline.generate_player_introductions import PlayerIntroduction, PlayerIntroductions
from tablesage_application.session_pipeline.generate_summary import (
    PLAYER_INTRODUCTIONS_MARKER,
    RECAP_MARKER,
    Attendee,
    GlossaryPromptEntry,
    SummaryValidationError,
)
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
        return f"  # The Adventure\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\nA summary.  \n"

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _stub_call_llm_with_prompt)
    glossary = [GlossaryPromptEntry(term="Zaria", description="a wizard")]
    attendees = [Attendee(player_name="Alice", roles=("Zaria",))]
    ledger_json = '{"session_name": "Session One"}'

    result = await generate_summary_module.generate_summary(
        ledger_json, attendees, glossary, "Iron Pact", "2026-08-18", "Blades in the Dark", "test-model"
    )

    assert result == f"# The Adventure\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\nA summary.\n"
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
    call_count = 0

    async def _empty_response(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return " \n\t "

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _empty_response)

    with pytest.raises(SummaryValidationError, match="all 3 attempts"):
        await generate_summary_module.generate_summary("{}", [], [], "Iron Pact", None, None, "test-model")

    assert call_count == 3


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
    previous_session = application.create_session(campaign.id, "Previous Session", date(2026, 8, 11))
    game_session = application.create_session(campaign.id, "Session One", date(2026, 8, 18))

    session_folder = application.session_folder(game_session.id)
    previous_folder = application.session_folder(previous_session.id)
    ledger = Ledger(
        session_id=game_session.id,
        session_name="Session One",
        starting_situation="The party stands before the gate.",
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.")],
    )
    expected_ledger_text = ledger.model_dump_json(indent=2) + "\n"
    ledger.save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    (previous_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text(
        "## Recap\n\n- The party escaped the flooded mine.\n",
        encoding="utf-8",
    )
    (session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text(
        "## Recap\n\n- This current-Session Recap must not be inserted here.\n",
        encoding="utf-8",
    )
    PlayerIntroductions(
        session_id=game_session.id,
        introductions=[PlayerIntroduction(character="Zaria", description="An elven wizard.")],
    ).save(session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename)
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
        return f"# The Adventure\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n\n- At the gate.\n"

    monkeypatch.setattr(generate_summary_module, "generate_summary", _stub_generate_summary)

    application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == (
        "# The Adventure\n\n"
        "## Recap\n\n"
        "- The party escaped the flooded mine.\n\n"
        "## Player Characters\n\n"
        "- **Zaria** — An elven wizard.\n\n"
        "## Starting Situation\n\n"
        "- At the gate.\n"
    )
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
        starting_situation="The party stands before the gate.",
        utterances=[Narration(type="narration", source="Game Master", fact="The gate opens.")],
    ).save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    (session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text("## Recap\n\n- Old recap.\n", encoding="utf-8")
    PlayerIntroductions(session_id=game_session.id, introductions=[]).save(
        session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename
    )
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _failing_generate_summary(*args: object, **kwargs: object) -> str:
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_summary_module, "generate_summary", _failing_generate_summary)

    with pytest.raises(RuntimeError, match="provider failed"):
        application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".summary.tmp.md").exists()


@pytest.mark.parametrize(
    ("response", "message"),
    [
        (f"# Title\n\n{RECAP_MARKER}", "exactly once"),
        (
            f"# Title\n\n{RECAP_MARKER}\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}",
            "exactly once",
        ),
        (
            f"# Title\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n{RECAP_MARKER}",
            "Recap marker must precede",
        ),
    ],
)
def test_validate_summary_markers_rejects_missing_duplicate_and_reversed_markers(response: str, message: str) -> None:
    with pytest.raises(SummaryValidationError, match=message):
        generate_summary_module.validate_summary_markers(response)


@pytest.mark.anyio
async def test_generate_summary_selects_first_marker_valid_response_within_three_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = iter(
        [
            "# Missing both markers",
            f"# Reversed\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n{RECAP_MARKER}",
            f"# Valid\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n- Ready.",
        ]
    )
    call_count = 0

    async def _next_response(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        return next(responses)

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _next_response)

    result = await generate_summary_module.generate_summary("{}", (), (), "Iron Pact", None, None, "test-model")

    assert result.startswith("# Valid\n")
    assert call_count == 3


@pytest.mark.anyio
async def test_generate_summary_does_not_retry_provider_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    call_count = 0

    async def _provider_failure(*args: object, **kwargs: object) -> str:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("provider failed")

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _provider_failure)

    with pytest.raises(RuntimeError, match="provider failed"):
        await generate_summary_module.generate_summary("{}", (), (), "Iron Pact", None, None, "test-model")

    assert call_count == 1


def test_compose_summary_inserts_sidecars_and_normalizes_blank_lines() -> None:
    template = (
        f"# Session\r\n\r\n{RECAP_MARKER}\r\n\r\n\r\n{PLAYER_INTRODUCTIONS_MARKER}\r\n\r\n\r\n## Starting Situation\r\n- At the gate.\r\n"
    )
    recap = "## Recap\n\n- The party crossed the gorge.\n"
    introductions = "## Player Characters\n\n- **Zaria** — An elven wizard.\n"

    result = generate_summary_module.compose_summary(template, recap, introductions)

    assert result == (
        "# Session\n\n"
        "## Recap\n\n"
        "- The party crossed the gorge.\n\n"
        "## Player Characters\n\n"
        "- **Zaria** — An elven wizard.\n\n"
        "## Starting Situation\n"
        "- At the gate.\n"
    )


def test_compose_summary_removes_empty_player_introductions_marker_cleanly() -> None:
    template = f"# Session\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n- At the gate."

    result = generate_summary_module.compose_summary(template, "## Recap\n\n- The party arrived.\n", "")

    assert result == "# Session\n\n## Recap\n\n- The party arrived.\n\n## Starting Situation\n- At the gate.\n"


def test_compose_summary_removes_recap_marker_when_there_is_no_previous_session() -> None:
    template = f"# Session\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n- At the gate."

    result = generate_summary_module.compose_summary(template, None, "## Player Characters\n\n- **Zaria** — A wizard.\n")

    assert result == ("# Session\n\n## Player Characters\n\n- **Zaria** — A wizard.\n\n## Starting Situation\n- At the gate.\n")


@pytest.mark.parametrize("sidecar", ["recap", "session", "character"])
def test_application_preserves_existing_summary_when_sidecar_validation_fails(
    sidecar: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    previous_session = application.create_session(campaign.id, "Previous Session", date(2026, 8, 11))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    previous_folder = application.session_folder(previous_session.id)
    Ledger(
        session_id=game_session.id,
        session_name="Session One",
        starting_situation="The party stands before the gate.",
        utterances=[],
    ).save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    recap = "" if sidecar == "recap" else "## Recap\n\n- The party arrived.\n"
    (previous_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text(recap, encoding="utf-8")
    introductions = PlayerIntroductions(
        session_id=uuid.uuid4() if sidecar == "session" else game_session.id,
        introductions=[
            PlayerIntroduction(
                character="Unknown" if sidecar == "character" else "Zaria",
                description="An elven wizard.",
            )
        ],
    )
    introductions.save(session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename)
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _valid_template(*args: object, **kwargs: object) -> str:
        return f"# Session\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n- Ready.\n"

    monkeypatch.setattr(generate_summary_module, "generate_summary", _valid_template)

    with pytest.raises(ValueError):
        application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".summary.tmp.md").exists()


def test_application_does_not_load_sidecars_before_marker_validation(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    Ledger(
        session_id=game_session.id,
        session_name="Session One",
        starting_situation="The party stands before the gate.",
        utterances=[],
    ).save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    (session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text("unread recap", encoding="utf-8")
    (session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename).write_text("unread introductions", encoding="utf-8")

    async def _invalid_template(*args: object, **kwargs: object) -> str:
        return "# Session without markers"

    def _unexpected_load(path: Path) -> PlayerIntroductions:
        raise AssertionError(f"Loaded sidecar before marker validation: {path}")

    monkeypatch.setattr(generate_summary_module, "call_llm_with_prompt", _invalid_template)
    monkeypatch.setattr(PlayerIntroductions, "load", _unexpected_load)

    with pytest.raises(SummaryValidationError, match="all 3 attempts"):
        application.generate_summary(game_session.id)


def test_application_preserves_existing_summary_when_atomic_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    session_folder = application.session_folder(game_session.id)
    Ledger(
        session_id=game_session.id,
        session_name="Session One",
        starting_situation="The party stands before the gate.",
        utterances=[],
    ).save(session_folder / ARTIFACTS[ArtifactName.LEDGER].filename)
    (session_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).write_text(
        "## Recap\n\n- The party arrived.\n",
        encoding="utf-8",
    )
    PlayerIntroductions(session_id=game_session.id, introductions=[]).save(
        session_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename
    )
    summary_path = session_folder / ARTIFACTS[ArtifactName.SUMMARY].filename
    summary_path.write_text("old summary\n", encoding="utf-8")

    async def _valid_template(*args: object, **kwargs: object) -> str:
        return f"# Session\n\n{RECAP_MARKER}\n\n{PLAYER_INTRODUCTIONS_MARKER}\n\n## Starting Situation\n- Ready.\n"

    def _failing_replace(self: Path, target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(generate_summary_module, "generate_summary", _valid_template)
    monkeypatch.setattr(Path, "replace", _failing_replace)

    with pytest.raises(OSError, match="replace failed"):
        application.generate_summary(game_session.id)

    assert summary_path.read_text(encoding="utf-8") == "old summary\n"
    assert not (session_folder / ".summary.tmp.md").exists()
