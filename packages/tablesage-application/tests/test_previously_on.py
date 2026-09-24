from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from tablesage_application import Application
from tablesage_application import previously_on as module
from tablesage_application.llm import PromptName, llm_helper
from tablesage_application.paths import ARTIFACTS, LEDGER_PAIR_MARKER, ArtifactName
from tablesage_application.session_pipeline.scene_breakdown import LedgerRange, Scene, SceneBreakdown
from tablesage_model.model import Campaign, GlossaryEntry
from tablesage_model.settings import AppSettings, PreviouslyOnSettings


def _breakdown(session_id: uuid.UUID, name: str = "At the gate") -> SceneBreakdown:
    return SceneBreakdown(
        session_id=session_id,
        session_name=name,
        ledger_sha256="0" * 64,
        starting_situation="Outside the gate.",
        ending_situation=f"Ending of {name}.",
        scenes=[
            Scene(
                title=f"{name} {index}",
                location="Forest",
                participants=["George the Woodsman"],
                situation=f"Question {index}",
                outcome=f"Answer {index}",
                carry_forward=["The dragon is poisonous."],
                signature_detail=None,
                ledger_ranges=[LedgerRange(start_index=index, end_index=index)],
            )
            for index in range(4)
        ],
    )


@pytest.fixture
def history() -> module.CampaignHistory:
    return module.CampaignHistory(
        campaign_name="Brandonsford",
        sessions=tuple(
            module.CampaignSession(sequence_number=index, breakdown=_breakdown(uuid.UUID(int=index), f"Session {index}"))
            for index in (1, 7)
        ),
        glossary=(module.GlossaryEntry(term="George", description="Woodsman"),),
    )


def _ingredients(source: module.SceneRef) -> module.Ingredients:
    return module.Ingredients(
        people_and_factions=(module.Ingredient(label="George", current_state="Warned of poison", sources=(source,)),),
        threads_and_commitments=(),
        active_pressures=(),
        places_and_objects=(),
    )


@pytest.mark.anyio
async def test_ingredients_render_full_history_and_validate_sources(
    history: module.CampaignHistory, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = next(iter(history.scene_catalog()))
    expected = _ingredients(source)
    call = AsyncMock(return_value=expected.model_dump_json())
    monkeypatch.setattr(llm_helper, "call_llm", call)
    assert await module.generate_ingredients(history, "configured-model", 27) == expected
    system, prompt, model = call.call_args.args
    assert model == "configured-model"
    assert all(str(session.breakdown.session_id) in prompt for session in history.sessions)
    assert "George" in prompt
    assert "never evidence" in system
    assert call.call_args.kwargs["timeout"] == 27
    assert call.call_args.kwargs["response_format"] is module.Ingredients
    call.return_value = _ingredients(source.model_copy(update={"scene_index": 999})).model_dump_json()
    with pytest.raises(ValueError, match="Unknown Scene"):
        await module.generate_ingredients(history, "configured-model", 27)


@pytest.mark.anyio
async def test_scout_accepts_unlimited_scenes_and_rejects_bad_references(
    history: module.CampaignHistory, monkeypatch: pytest.MonkeyPatch
) -> None:
    refs = tuple(history.scene_catalog())
    data = module.ScoutInput(history=history, starting_situation="A new opening", selected_ingredients=(), upcoming_notes="Visit a witch")
    result = module.ScoutResult(recommendations=tuple(module.Recommendation(source=ref, rationale="Private connection") for ref in refs))
    call = AsyncMock(return_value=result.model_dump_json())
    monkeypatch.setattr(module, "call_llm_with_prompt", call)
    assert await module.scout_scenes(data, "high", 31) == result
    assert "Visit a witch" in call.call_args.args[1].payload
    assert len(result.recommendations) == 8
    call.return_value = module.ScoutResult(recommendations=(result.recommendations[0], result.recommendations[0])).model_dump_json()
    with pytest.raises(ValueError, match="duplicate"):
        await module.scout_scenes(data, "high", 31)
    call.return_value = module.ScoutResult(
        recommendations=(module.Recommendation(source=module.SceneRef(session_id=uuid.uuid4(), scene_index=0), rationale="Invented"),)
    ).model_dump_json()
    with pytest.raises(ValueError, match="Unknown Scene"):
        await module.scout_scenes(data, "high", 31)
    call.return_value = '{"recommendations": []}'
    assert not (await module.scout_scenes(data, "high", 31)).recommendations


@pytest.mark.anyio
async def test_starting_situation_alone_is_insufficient(history: module.CampaignHistory, monkeypatch: pytest.MonkeyPatch) -> None:
    call = AsyncMock()
    monkeypatch.setattr(module, "call_llm_with_prompt", call)
    data = module.ScoutInput(history=history, starting_situation="Known opening", selected_ingredients=(), upcoming_notes=" \n ")
    with pytest.raises(ValueError, match="notes or select"):
        await module.scout_scenes(data, "high", 12)
    call.assert_not_called()


@pytest.mark.anyio
async def test_editor_context_boundary_chronology_and_verbatim_export(
    history: module.CampaignHistory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    refs = list(history.scene_catalog())
    selected = frozenset((refs[-1], refs[0]))
    data = module.editor_input(history, selected, "GM edited opening")
    destination = tmp_path / "recap.md"
    # Intentionally malformed/whitespace output still belongs to the GM to review.
    output = "  ```\nanything\n```  \n"
    call = AsyncMock(return_value=output)
    monkeypatch.setattr(llm_helper, "call_llm", call)
    await module.write_recap(data, destination, "configured-high", 39)
    assert destination.read_text() == output
    system, prompt, _model = call.call_args.args
    payload = json.loads(prompt[prompt.index("{") :])
    assert set(payload) == {"selected_scenes", "starting_situation", "glossary"}
    assert [scene["title"] for scene in payload["selected_scenes"]] == ["Session 1 0", "Session 7 3"]
    assert "Session 1 1" not in prompt
    assert "GM edited opening" in prompt
    assert "George" in prompt
    assert "brief and concise" in system
    assert call.call_args.kwargs["response_format"] is None
    assert call.call_args.kwargs["timeout"] == 39
    assert list(tmp_path.iterdir()) == [destination]


def test_selection_validation_and_filename(history: module.CampaignHistory) -> None:
    assert history.suggested_filename == "Brandonsford-008-previously-on.md"
    assert history.starting_situation == "Ending of Session 7."
    with pytest.raises(ValueError, match="at least one"):
        module.editor_input(history, frozenset(), "Opening")
    with pytest.raises(ValueError, match="Unknown Scene"):
        module.editor_input(history, frozenset({module.SceneRef(session_id=uuid.uuid4(), scene_index=0)}), "Opening")


@pytest.mark.anyio
async def test_failed_generation_and_write_preserve_existing_file(
    history: module.CampaignHistory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = module.editor_input(history, frozenset(history.scene_catalog()), "Opening")
    target = tmp_path / "recap.md"
    target.write_text("original")
    call = AsyncMock(side_effect=RuntimeError("Provider unavailable"))
    monkeypatch.setattr(module, "call_llm_with_prompt", call)
    with pytest.raises(FileExistsError, match="Confirm replacement"):
        await module.write_recap(data, target, "high", 30)
    call.assert_not_called()
    with pytest.raises(RuntimeError, match="Provider unavailable"):
        await module.write_recap(data, target, "high", 30, overwrite=True)
    assert target.read_text() == "original"
    call.side_effect = None
    call.return_value = "replacement"

    def fail_replace(self: Path, target: Path) -> Path:
        raise OSError("Disk failure")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "replace", fail_replace)
        with pytest.raises(OSError, match="Disk failure"):
            await module.write_recap(data, target, "high", 30, overwrite=True)
    assert target.read_text() == "original"
    assert list(tmp_path.iterdir()) == [target]
    await module.write_recap(data, target, "high", 30, overwrite=True)
    assert target.read_text() == "replacement"


def _ready_campaign(tmp_path: Path) -> tuple[Application, uuid.UUID, tuple[Path, ...]]:
    app = Application(tmp_path)
    campaign = app.create_campaign(Campaign(name="Brandonsford"))
    app.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="George", description="Woodsman"))
    folders: list[Path] = []
    for name in ("Old warning", "Last session"):
        session = app.create_session(campaign.id, name)
        folder = app.session_folder(session.id)
        for artifact in (
            ArtifactName.INPUT_AUDIO,
            ArtifactName.TRANSCRIPT,
            ArtifactName.TRANSCRIPT_TEXT,
            ArtifactName.CLEANED_TRANSCRIPT,
            ArtifactName.NAME_CORRECTED_TRANSCRIPT,
            ArtifactName.NEW_SPEAKER_ASSIGNMENTS,
            ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS,
            ArtifactName.SPEAKER_ENHANCED_TRANSCRIPT,
            ArtifactName.SPELLCHECKED_TRANSCRIPT,
            ArtifactName.REVIEWED_TRANSCRIPT,
            ArtifactName.ROLE_TRANSCRIPT,
            ArtifactName.TRANSCRIPT_SECTIONS,
            ArtifactName.LEDGER,
        ):
            (folder / ARTIFACTS[artifact].filename).write_text("fixture")
        (folder / "ledger.md").write_text("fixture")
        (folder / "scene_breakdown.json").write_text(_breakdown(session.id, name).model_dump_json())
        timestamp = time.time_ns() + 2_000_000_000
        for file in folder.iterdir():
            os.utime(file, ns=(timestamp, timestamp))
        folders.append(folder)
    return app, campaign.id, tuple(folders)


def test_history_uses_real_freshness_graph_without_mutating_campaign(tmp_path: Path) -> None:
    app, campaign_id, folders = _ready_campaign(tmp_path)
    original = {file: file.read_bytes() for folder in folders for file in folder.iterdir()}
    history = app.previously_on_history(campaign_id)
    assert [session.sequence_number for session in history.sessions] == [1, 2]
    assert history.starting_situation == "Ending of Last session."
    assert history.glossary[0].term == "George"
    assert {file: file.read_bytes() for folder in folders for file in folder.iterdir()} == original
    assert len(app.list_sessions(campaign_id)) == 2


def test_campaign_scene_recap_brackets_every_scene_with_campaign_endpoints(tmp_path: Path) -> None:
    app, campaign_id, _ = _ready_campaign(tmp_path)

    recap = app.create_campaign_scene_recap(campaign_id)

    assert recap.campaign_id == campaign_id
    assert recap.campaign_name == "Brandonsford"
    assert recap.starting_situation == "Outside the gate."
    assert [scene.title for scene in recap.scenes] == [
        "Old warning 0",
        "Old warning 1",
        "Old warning 2",
        "Old warning 3",
        "Last session 0",
        "Last session 1",
        "Last session 2",
        "Last session 3",
    ]
    assert set(recap.model_dump()["scenes"][0]) == {
        "title",
        "location",
        "participants",
        "situation",
        "outcome",
        "carry_forward",
        "signature_detail",
        "ledger_ranges",
    }
    assert recap.ending_situation == "Ending of Last session."


@pytest.mark.parametrize("problem", ["missing", "invalid", "incomplete", "stale", "interrupted", "wrong-session", "gap"])
def test_history_blocks_any_bad_session_and_lists_all_affected(tmp_path: Path, problem: str) -> None:
    app, campaign_id, folders = _ready_campaign(tmp_path)
    for folder in folders:
        file = folder / "scene_breakdown.json"
        if problem == "missing":
            file.unlink()
        elif problem == "invalid":
            file.write_text("not json")
            timestamp = time.time_ns() + 3_000_000_000
            os.utime(file, ns=(timestamp, timestamp))
        elif problem == "incomplete":
            (folder / "ledger.md").unlink()
        elif problem == "stale":
            timestamp = time.time_ns() + 10_000_000_000
            os.utime(folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename, ns=(timestamp, timestamp))
        elif problem == "interrupted":
            (folder / LEDGER_PAIR_MARKER).touch()
        else:
            value = json.loads(file.read_text())
            if problem == "wrong-session":
                value["session_id"] = str(uuid.uuid4())
            else:
                value["scenes"].pop(1)
            file.write_text(json.dumps(value))
            timestamp = time.time_ns() + 2_000_000_000
            os.utime(file, ns=(timestamp, timestamp))
    with pytest.raises(ValueError, match="Regenerate All Outputs") as exc:
        app.previously_on_history(campaign_id)
    assert "Session 001 — Old warning" in str(exc.value)
    assert "Session 002 — Last session" in str(exc.value)
    if problem == "invalid":
        assert "Invalid JSON" in str(exc.value)


def test_empty_campaign_is_blocked(tmp_path: Path) -> None:
    app = Application(tmp_path)
    campaign = app.create_campaign(Campaign(name="Empty"))
    with pytest.raises(ValueError, match="no Sessions"):
        app.previously_on_history(campaign.id)


def test_application_settings_and_export_boundary(history: module.CampaignHistory, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = AppSettings(
        llm_model_high="chosen-model", previously_on=PreviouslyOnSettings(ingredient_timeout=11, scout_timeout=12, editor_timeout=13)
    )
    app = Application(tmp_path, settings)
    refs = tuple(history.scene_catalog())
    ingredients = _ingredients(refs[0])
    responses = iter([ingredients.model_dump_json(), '{"recommendations": []}', "raw Markdown"])
    calls: list[dict[str, Any]] = []

    async def respond(prompt: PromptName, data: module.PromptData, model: str, **kwargs: Any) -> str:
        calls.append({"prompt": prompt, "model": model, **kwargs})
        return next(responses)

    monkeypatch.setattr(module, "call_llm_with_prompt", respond)
    assert app.previously_on_ingredients(history) == ingredients
    app.previously_on_scout(
        module.ScoutInput(history=history, starting_situation="Opening", upcoming_notes="Plan", selected_ingredients=())
    )
    target = tmp_path / "previously-on.md"
    app.export_previously_on(module.editor_input(history, frozenset(refs), "Opening"), target)
    assert target.read_text() == "raw Markdown"
    assert [call["timeout"] for call in calls] == [11, 12, 13]
    assert all(call["model"] == "chosen-model" for call in calls)
    for path in (tmp_path / "wrong.txt", tmp_path / "campaigns" / "bad.md", tmp_path / "missing" / "recap.md"):
        with pytest.raises(ValueError):
            app.previously_on_destination(path)
