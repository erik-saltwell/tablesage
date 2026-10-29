from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.session_pipeline import generate_summary as generate_summary_module
from tablesage_application.session_pipeline import session_summary
from tablesage_application.session_pipeline.generate_summary import (
    PLAYER_INTRODUCTIONS_MARKER,
    RECAP_MARKER,
    Attendee,
    GlossaryPromptEntry,
    SummaryValidationError,
)
from tablesage_model.model import Campaign
from tablesage_model.settings import AppSettings


@pytest.mark.anyio
async def test_generate_summary_uses_application_prompt_helper_without_structured_output(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _stub_call_llm_with_prompt(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
        timeout: float | None = None,
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


def test_application_generate_summary_reads_current_matters_and_scene_cue_without_model(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    summary_sources: Callable[[Application, uuid.UUID], Path],
    complete_campaign: Callable[[Application, uuid.UUID], None],
) -> None:
    application = Application(tmp_path, AppSettings(llm_model_high="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One", date(2026, 8, 18))
    folder = summary_sources(application, game_session.id)
    (folder / "summary.md").write_text("old summary\n")
    (folder / "table_recap.md").write_text("existing recap\n")
    complete_campaign(application, campaign.id)

    def unexpected_model(*args: object, **kwargs: object) -> str:
        raise AssertionError("Summary must remain model-free")

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", unexpected_model)
    result = application.generate_summary(game_session.id)
    assert result.startswith("# Iron Pact\n")
    assert "2026-08-18" in result and "The burning gate" in result
    assert "- The party stands before the gate." in result
    assert "- The gate is burning." in result
    assert (folder / "summary.md").read_text() == result
    assert (folder / "table_recap.md").read_text() == "existing recap\n"
    assert any(path.read_text() == "old summary\n" for path in (folder / "legacy/narrative").rglob("summary.md"))


def test_application_generate_summary_preserves_existing_summary_on_render_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    summary_sources: Callable[[Application, uuid.UUID], Path],
    complete_campaign: Callable[[Application, uuid.UUID], None],
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = summary_sources(application, game_session.id)
    (folder / "summary.md").write_text("old summary\n")
    complete_campaign(application, campaign.id)

    def failing_render(*args: object, **kwargs: object) -> str:
        raise RuntimeError("render failed")

    monkeypatch.setattr(session_summary, "render", failing_render)
    with pytest.raises(RuntimeError, match="render failed"):
        application.generate_summary(game_session.id)
    assert (folder / "summary.md").read_text() == "old summary\n"


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


@pytest.mark.parametrize("source", ["matters-session", "scene-session", "malformed-matters"])
def test_application_preserves_existing_summary_when_source_validation_fails(
    source: str,
    tmp_path: Path,
    summary_sources: Callable[[Application, uuid.UUID], Path],
    complete_campaign: Callable[[Application, uuid.UUID], None],
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = summary_sources(application, game_session.id)
    (folder / "summary.md").write_text("old summary\n")
    path = folder / ("scene_log.json" if source == "scene-session" else "post_session_matters.json")
    document = json.loads(path.read_text())
    if source == "malformed-matters":
        del document["present_matters"]
    else:
        document["session_id"] = str(uuid.uuid4())
    path.write_text(json.dumps(document))
    complete_campaign(application, campaign.id)
    expected_error = jsonschema.ValidationError if source == "malformed-matters" else ValueError
    expected_message = {
        "malformed-matters": "'present_matters' is a required property",
        "matters-session": "Post-Session Matters belongs to a different Session",
        "scene-session": "Scene Log identity or predecessor differs",
    }[source]
    with pytest.raises(expected_error, match=expected_message):
        application.generate_summary(game_session.id)
    assert (folder / "summary.md").read_text() == "old summary\n"


def test_application_rejects_missing_matters_before_reading_scene_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from tablesage_application.session_pipeline import narrative

    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    def unexpected_load(folder: Path) -> narrative.SceneLog:
        raise AssertionError("Read Scene Log before checking Matters")

    monkeypatch.setattr(narrative.SceneLog, "load", unexpected_load)
    with pytest.raises(ValueError, match="Post-Session Matters is missing"):
        application.generate_summary(game_session.id)


def test_application_preserves_existing_summary_when_atomic_replace_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    summary_sources: Callable[[Application, uuid.UUID], Path],
    complete_campaign: Callable[[Application, uuid.UUID], None],
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = summary_sources(application, game_session.id)
    (folder / "summary.md").write_text("old summary\n")
    complete_campaign(application, campaign.id)
    original_replace = Path.replace

    def failing_replace(self: Path, target: Path) -> Path:
        if Path(target) == folder / "summary.md":
            raise OSError("replace failed")
        return original_replace(self, target)

    monkeypatch.setattr(Path, "replace", failing_replace)
    with pytest.raises(OSError, match="replace failed"):
        application.generate_summary(game_session.id)
    assert (folder / "summary.md").read_text() == "old summary\n"
