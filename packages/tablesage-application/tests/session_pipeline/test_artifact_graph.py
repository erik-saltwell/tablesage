from __future__ import annotations

import os
import time
from datetime import date
from pathlib import Path

from sqlmodel import Session
from tablesage_application import Application
from tablesage_application.llm import PromptName, system_prompt_path
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.artifact_graph import (
    ArtifactGraph,
    ArtifactRef,
    ArtifactStatus,
    BuildStep,
    FileRef,
    GenerationTask,
    SystemPromptInput,
    TimestampInput,
)
from tablesage_model.model import Campaign


def _ref(folder: Path, name: ArtifactName) -> ArtifactRef:
    return ArtifactRef(folder, name)


def _write_at(folder: Path, name: ArtifactName, modified_ns: int) -> None:
    path = folder / ARTIFACTS[name].filename
    path.write_text("artifact", encoding="utf-8")
    os.utime(path, ns=(modified_ns, modified_ns))


def test_staleness_propagates_through_a_newer_transitive_dependency(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    recap = _ref(tmp_path, ArtifactName.RECAP_SUMMARY)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 300)
    _write_at(tmp_path, ArtifactName.SCENE_BREAKDOWN, 100)
    _write_at(tmp_path, ArtifactName.RECAP_SUMMARY, 200)
    graph = ArtifactGraph(
        (
            BuildStep(ArtifactName.SCENE_BREAKDOWN, (scene,), (role,)),
            BuildStep(ArtifactName.RECAP_SUMMARY, (recap,), (scene,)),
        )
    )

    assert graph.status(scene) is ArtifactStatus.STALE
    assert graph.status(recap) is ArtifactStatus.STALE


def test_shared_outputs_are_siblings_not_dependencies(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 300)
    _write_at(tmp_path, ArtifactName.SCENE_BREAKDOWN, 200)
    graph = ArtifactGraph((BuildStep(ArtifactName.LEDGER, (ledger, scene), (role,)),))

    assert graph.status(ledger) is ArtifactStatus.CURRENT
    assert graph.status(scene) is ArtifactStatus.CURRENT


def test_missing_shared_output_stales_existing_sibling(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 200)
    graph = ArtifactGraph((BuildStep(ArtifactName.LEDGER, (ledger, scene), (role,)),))

    assert graph.status(ledger) is ArtifactStatus.STALE
    assert graph.status(scene) is ArtifactStatus.MISSING


def test_missing_physical_companion_stales_logical_output(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 200)
    graph = ArtifactGraph((BuildStep(ArtifactName.LEDGER, (ledger, FileRef(tmp_path / "ledger.md")), (role,)),))

    assert graph.status(ledger) is ArtifactStatus.STALE


def test_database_timestamp_is_a_regular_build_input(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)

    graph = ArtifactGraph((BuildStep(ArtifactName.ROLE_TRANSCRIPT, (role,), (TimestampInput(200),)),))

    assert graph.status(role) is ArtifactStatus.STALE


def test_newer_system_prompt_makes_llm_output_stale(tmp_path: Path) -> None:
    output = _ref(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS)
    prompt_path = tmp_path / "system.md"
    _write_at(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS, 100)
    prompt_path.write_text("instructions", encoding="utf-8")
    os.utime(prompt_path, ns=(200, 200))
    graph = ArtifactGraph((BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (output,), (SystemPromptInput(prompt_path),)),))

    assert graph.status(output) is ArtifactStatus.STALE


def test_missing_system_prompt_makes_llm_output_stale(tmp_path: Path) -> None:
    output = _ref(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS)
    _write_at(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS, 100)
    graph = ArtifactGraph((BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (output,), (SystemPromptInput(tmp_path / "missing.md"),)),))

    assert graph.status(output) is ArtifactStatus.STALE


def _write_complete_session(folder: Path, modified_ns: int) -> None:
    for name in ArtifactName:
        _write_at(folder, name, modified_ns)
    for spec in ARTIFACTS.values():
        for filename in spec.companion_filenames:
            path = folder / filename
            path.write_text("artifact", encoding="utf-8")
            os.utime(path, ns=(modified_ns, modified_ns))


def test_application_declares_every_llm_system_prompt_dependency(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")

    with Session(application._engine) as session:
        graph = application._artifact_graph(session, campaign.id)

    prompt_paths_by_step = {
        step.name: tuple(dependency.path for dependency in step.dependencies if isinstance(dependency, SystemPromptInput))
        for step in graph.steps
        if step.outputs[0].path.parent == application.session_folder(game_session.id)
    }
    assert prompt_paths_by_step == {
        ArtifactName.TRANSCRIPT: (),
        ArtifactName.NAME_CORRECTED_TRANSCRIPT: (system_prompt_path(PromptName.SUGGEST_NAME_CORRECTIONS),),
        ArtifactName.NEW_SPEAKER_ASSIGNMENTS: (system_prompt_path(PromptName.ISOLATE_NEW_SPEAKERS),),
        ArtifactName.CLEANED_TRANSCRIPT: (system_prompt_path(PromptName.CLASSIFY_BACKCHANNELS),),
        ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS: (),
        ArtifactName.SEEDED_VOICE_SAMPLES: (),
        ArtifactName.IDENTIFIED_TRANSCRIPT: (),
        ArtifactName.SPELLCHECKED_TRANSCRIPT: (system_prompt_path(PromptName.SUGGEST_SPELLING_CORRECTIONS),),
        ArtifactName.REVIEWED_TRANSCRIPT: (),
        ArtifactName.ROLE_TRANSCRIPT: (),
        ArtifactName.TRANSCRIPT_SECTIONS: (system_prompt_path(PromptName.SECTION_TRANSCRIPT),),
        ArtifactName.LEDGER: (system_prompt_path(PromptName.GENERATE_LEDGER),),
        ArtifactName.PLAYER_INTRODUCTIONS: (system_prompt_path(PromptName.GENERATE_PLAYER_INTRODUCTIONS),),
        ArtifactName.RECAP_SUMMARY: (system_prompt_path(PromptName.GENERATE_RECAP_SUMMARY),),
        ArtifactName.SUMMARY: (system_prompt_path(PromptName.SUMMARIZE_SESSION),),
    }


def test_application_plan_propagates_staleness_through_dependencies(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    baseline = time.time_ns() + 1_000_000_000
    _write_complete_session(folder, baseline)
    _write_at(folder, ArtifactName.ROLE_TRANSCRIPT, baseline + 10)
    _write_at(folder, ArtifactName.RECAP_SUMMARY, baseline + 20)
    _write_at(folder, ArtifactName.SUMMARY, baseline + 20)

    assert application.generation_plan(game_session.id) == (
        GenerationTask(game_session.id, ArtifactName.TRANSCRIPT_SECTIONS),
        GenerationTask(game_session.id, ArtifactName.LEDGER),
        GenerationTask(game_session.id, ArtifactName.PLAYER_INTRODUCTIONS),
        GenerationTask(game_session.id, ArtifactName.RECAP_SUMMARY),
        GenerationTask(game_session.id, ArtifactName.SUMMARY),
    )


def test_hand_edited_ledger_rebuilds_only_its_true_consumer(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    baseline = time.time_ns() + 1_000_000_000
    _write_complete_session(folder, baseline)
    _write_at(folder, ArtifactName.LEDGER, baseline + 10)

    states = application.session_artifact_states(game_session.id)
    assert states[ArtifactName.LEDGER] is ArtifactStatus.CURRENT
    assert states[ArtifactName.SCENE_BREAKDOWN] is ArtifactStatus.CURRENT
    assert states[ArtifactName.RECAP_SUMMARY] is ArtifactStatus.CURRENT
    assert states[ArtifactName.SUMMARY] is ArtifactStatus.STALE
    assert application.generation_plan(game_session.id) == (GenerationTask(game_session.id, ArtifactName.SUMMARY),)


def test_hand_edited_scene_rebuilds_only_its_true_consumer(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    baseline = time.time_ns() + 1_000_000_000
    _write_complete_session(folder, baseline)
    _write_at(folder, ArtifactName.SCENE_BREAKDOWN, baseline + 10)

    states = application.session_artifact_states(game_session.id)
    assert states[ArtifactName.LEDGER] is ArtifactStatus.CURRENT
    assert states[ArtifactName.SCENE_BREAKDOWN] is ArtifactStatus.CURRENT
    assert states[ArtifactName.RECAP_SUMMARY] is ArtifactStatus.STALE
    assert states[ArtifactName.SUMMARY] is ArtifactStatus.CURRENT
    assert application.generation_plan(game_session.id) == (GenerationTask(game_session.id, ArtifactName.RECAP_SUMMARY),)


def test_glossary_changes_do_not_stale_session_artifacts(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    baseline = time.time_ns() + 1_000_000_000
    _write_complete_session(application.session_folder(game_session.id), baseline)
    with Session(application._engine) as session:
        stored = session.get(Campaign, campaign.id)
        assert stored is not None
        stored.glossary_updated_at = stored.glossary_updated_at.replace(year=stored.glossary_updated_at.year + 1)
        session.commit()

    states = application.session_artifact_states(game_session.id)
    assert all(status is ArtifactStatus.CURRENT for status in states.values())


def test_force_rebuilds_selected_step_and_its_downstream_consumers(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    _write_complete_session(application.session_folder(game_session.id), time.time_ns() + 1_000_000_000)

    assert application.generation_plan(game_session.id, force=ArtifactName.LEDGER) == (
        GenerationTask(game_session.id, ArtifactName.LEDGER),
        GenerationTask(game_session.id, ArtifactName.RECAP_SUMMARY),
        GenerationTask(game_session.id, ArtifactName.SUMMARY),
    )


def test_current_summary_plan_recursively_repairs_previous_session_recap(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    previous = application.create_session(campaign.id, "Previous", date(2026, 1, 1))
    current = application.create_session(campaign.id, "Current", date(2026, 1, 8))
    baseline = time.time_ns() + 1_000_000_000
    _write_complete_session(application.session_folder(previous.id), baseline)
    _write_complete_session(application.session_folder(current.id), baseline + 20)
    (application.session_folder(current.id) / ".summary-inputs.json").write_text(
        f'{{"previous_session_id": "{previous.id}"}}\n', encoding="utf-8"
    )
    _write_at(application.session_folder(previous.id), ArtifactName.ROLE_TRANSCRIPT, baseline + 10)

    assert application.generation_plan(current.id) == (
        GenerationTask(previous.id, ArtifactName.TRANSCRIPT_SECTIONS),
        GenerationTask(previous.id, ArtifactName.LEDGER),
        GenerationTask(previous.id, ArtifactName.RECAP_SUMMARY),
        GenerationTask(current.id, ArtifactName.SUMMARY),
    )
