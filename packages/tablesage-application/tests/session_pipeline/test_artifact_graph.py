from __future__ import annotations

import os
import time
import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlmodel import Session
from tablesage_application import Application
from tablesage_application.llm import PromptName, system_prompt_path
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import campaign_matters, post_session_matters, processing_state, session_summary
from tablesage_application.session_pipeline.artifact_graph import (
    ArtifactGraph,
    ArtifactRef,
    ArtifactStatus,
    BuildStep,
    FileRef,
    GenerationTask,
    SystemPromptInput,
    current_fingerprints,
)
from tablesage_model.model import Campaign


def _ref(folder: Path, name: ArtifactName) -> ArtifactRef:
    return ArtifactRef(folder, name)


def _write_at(folder: Path, name: ArtifactName, modified_ns: int, content: str = "artifact") -> None:
    path = folder / ARTIFACTS[name].filename
    path.write_text(content, encoding="utf-8")
    os.utime(path, ns=(modified_ns, modified_ns))


def _complete(*steps: BuildStep) -> None:
    """Record each step complete against its inputs as they are now, as a producer would."""
    for step in steps:
        record = processing_state.CompletionRecord(completed_at=processing_state.now(), inputs=current_fingerprints(step))

        def apply(
            state: processing_state.ProcessingState, name: str = step.name.value, record: processing_state.CompletionRecord = record
        ) -> None:
            state.records[name] = record

        processing_state.update(step.folder, apply, reason="test")


def test_staleness_propagates_through_a_changed_transitive_dependency(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    recap = _ref(tmp_path, ArtifactName.RECAP_SUMMARY)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.SCENE_BREAKDOWN, 100)
    _write_at(tmp_path, ArtifactName.RECAP_SUMMARY, 200)
    scene_step = BuildStep(ArtifactName.SCENE_BREAKDOWN, (scene,), (role,))
    recap_step = BuildStep(ArtifactName.RECAP_SUMMARY, (recap,), (scene,))
    _complete(scene_step, recap_step)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 300, content="changed")
    graph = ArtifactGraph((scene_step, recap_step))

    assert graph.status(scene) is ArtifactStatus.STALE
    assert graph.status(recap) is ArtifactStatus.STALE


def test_shared_outputs_are_siblings_not_dependencies(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 300)
    _write_at(tmp_path, ArtifactName.SCENE_BREAKDOWN, 200)
    step = BuildStep(ArtifactName.LEDGER, (ledger, scene), (role,))
    _complete(step)
    graph = ArtifactGraph((step,))

    assert graph.status(ledger) is ArtifactStatus.CURRENT
    assert graph.status(scene) is ArtifactStatus.CURRENT


def test_missing_shared_output_stales_existing_sibling(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    scene = _ref(tmp_path, ArtifactName.SCENE_BREAKDOWN)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 200)
    step = BuildStep(ArtifactName.LEDGER, (ledger, scene), (role,))
    _complete(step)
    graph = ArtifactGraph((step,))

    assert graph.status(ledger) is ArtifactStatus.STALE
    assert graph.status(scene) is ArtifactStatus.MISSING


def test_missing_physical_companion_stales_logical_output(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    ledger = _ref(tmp_path, ArtifactName.LEDGER)
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)
    _write_at(tmp_path, ArtifactName.LEDGER, 200)
    step = BuildStep(ArtifactName.LEDGER, (ledger, FileRef(tmp_path / "ledger.md")), (role,))
    _complete(step)
    graph = ArtifactGraph((step,))

    assert graph.status(ledger) is ArtifactStatus.STALE


def test_declared_input_missing_from_the_record_makes_output_stale(tmp_path: Path) -> None:
    role = _ref(tmp_path, ArtifactName.ROLE_TRANSCRIPT)
    sections = _ref(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS)
    _write_at(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS, 100)
    _complete(BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (sections,), ()))
    _write_at(tmp_path, ArtifactName.ROLE_TRANSCRIPT, 100)

    graph = ArtifactGraph((BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (sections,), (role,)),))

    assert graph.status(sections) is ArtifactStatus.STALE


def test_changed_system_prompt_makes_llm_output_stale(tmp_path: Path) -> None:
    output = _ref(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS)
    prompt_path = tmp_path / "system.md"
    _write_at(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS, 100)
    prompt_path.write_text("instructions", encoding="utf-8")
    step = BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (output,), (SystemPromptInput(prompt_path),))
    _complete(step)
    prompt_path.write_text("revised instructions", encoding="utf-8")
    graph = ArtifactGraph((step,))

    assert graph.status(output) is ArtifactStatus.STALE


def test_missing_system_prompt_makes_llm_output_stale(tmp_path: Path) -> None:
    output = _ref(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS)
    prompt_path = tmp_path / "system.md"
    _write_at(tmp_path, ArtifactName.TRANSCRIPT_SECTIONS, 100)
    prompt_path.write_text("instructions", encoding="utf-8")
    step = BuildStep(ArtifactName.TRANSCRIPT_SECTIONS, (output,), (SystemPromptInput(prompt_path),))
    _complete(step)
    prompt_path.unlink()
    graph = ArtifactGraph((step,))

    assert graph.status(output) is ArtifactStatus.STALE


def _write_complete_session(folder: Path, modified_ns: int) -> None:
    for name, spec in ARTIFACTS.items():
        if spec.filename:
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
        if step.folder == application.session_folder(game_session.id)
    }
    expected: dict[ArtifactName, tuple[Path, ...]] = {
        ArtifactName.IMPORT_REQUEST: (),
        ArtifactName.INPUT_AUDIO: (),
        ArtifactName.TRANSCRIPT: (),
        ArtifactName.CLEANED_TRANSCRIPT: (system_prompt_path(PromptName.CLASSIFY_BACKCHANNELS),),
        ArtifactName.NAME_CORRECTION_SUGGESTIONS: (system_prompt_path(PromptName.SUGGEST_NAME_CORRECTIONS),),
        ArtifactName.NAME_CORRECTION_DECISIONS: (),
        ArtifactName.NAME_CORRECTED_TRANSCRIPT: (),
        ArtifactName.NEW_SPEAKER_ASSIGNMENTS: (system_prompt_path(PromptName.ISOLATE_NEW_SPEAKERS),),
        ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS: (),
        ArtifactName.SEEDED_VOICE_SAMPLES: (),
        ArtifactName.IDENTIFIED_TRANSCRIPT: (),
        ArtifactName.GLOSSARY_SUGGESTIONS: (system_prompt_path(PromptName.EXTRACT_GLOSSARY),),
        ArtifactName.GLOSSARY_DECISIONS: (),
        ArtifactName.EXTRACTED_GLOSSARY_TERMS: (),
        ArtifactName.SPELLING_SUGGESTIONS: (system_prompt_path(PromptName.SUGGEST_SPELLING_CORRECTIONS),),
        ArtifactName.SPELLING_DECISIONS: (),
        ArtifactName.SPELLCHECKED_TRANSCRIPT: (),
        ArtifactName.TRANSCRIPT_REVIEW_EDITS: (),
        ArtifactName.REVIEWED_TRANSCRIPT: (),
        ArtifactName.ROLE_TRANSCRIPT: (),
        ArtifactName.VOICE_PRINT_DECISION: (),
        ArtifactName.VOICE_PRINT_ENHANCEMENT: (),
    }
    for name, prompt in {
        ArtifactName.TRANSCRIPT_SECTIONS: PromptName.SECTION_TRANSCRIPT,
        ArtifactName.PLAYER_INTRODUCTIONS: PromptName.GENERATE_PLAYER_INTRODUCTIONS,
    }.items():
        expected[name] = tuple(
            path for path in sorted(system_prompt_path(prompt).parent.iterdir()) if path.suffix in (".md", ".j2", ".json")
        )
    for name, prompt in {
        ArtifactName.LEDGER: PromptName.GENERATE_LEDGER,
        ArtifactName.SCENE_LOG: PromptName.GENERATE_SCENE_LOG,
        ArtifactName.TABLE_RECAP: PromptName.GENERATE_SPOKEN_TABLE_RECAP,
        **{name: campaign_matters.PROMPTS[section] for section, name in campaign_matters.MATTERS.items()},
    }.items():
        resources = ("system.md", "template.j2", "schema.json") + (("schema-first-session.json",) if name is ArtifactName.LEDGER else ())
        expected[name] = tuple(system_prompt_path(prompt).parent / resource for resource in resources)
    expected[ArtifactName.POST_SESSION_MATTERS] = (post_session_matters.SCHEMA_PATH,)
    expected[ArtifactName.SUMMARY] = (session_summary.TEMPLATE_PATH,)
    assert prompt_paths_by_step == expected


NARRATIVE_OUTPUTS = (
    ArtifactName.LEDGER,
    ArtifactName.SCENE_LOG,
    ArtifactName.PRESENT_MATTERS,
    ArtifactName.GOALS,
    ArtifactName.BREWING_TROUBLES,
    ArtifactName.GOAL_IMPEDIMENTS,
    ArtifactName.OPPORTUNITIES,
    ArtifactName.MYSTERIES,
    ArtifactName.NEW_ASSETS,
    ArtifactName.OBLIGATIONS,
    ArtifactName.REVELATIONS,
    ArtifactName.DEVELOPMENTS,
    ArtifactName.POST_SESSION_MATTERS,
    ArtifactName.SUMMARY,
    ArtifactName.TABLE_RECAP,
)


def test_application_plan_propagates_staleness_through_dependencies(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    _write_complete_session(folder, time.time_ns())
    complete_campaign(application, campaign.id)
    (folder / "role_transcript.json").write_text("changed role transcript")
    plan = application.generation_plan(game_session.id)
    assert set(plan) == {GenerationTask(game_session.id, name) for name in (ArtifactName.TRANSCRIPT_SECTIONS, *NARRATIVE_OUTPUTS)}
    names = [task.artifact_name for task in plan]
    assert names.index(ArtifactName.TRANSCRIPT_SECTIONS) < names.index(ArtifactName.LEDGER) < names.index(ArtifactName.SCENE_LOG)
    assert names.index(ArtifactName.POST_SESSION_MATTERS) < names.index(ArtifactName.SUMMARY) < names.index(ArtifactName.TABLE_RECAP)


def test_hand_edited_ledger_rebuilds_scene_log_and_downstream_matters(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    _write_complete_session(folder, time.time_ns())
    complete_campaign(application, campaign.id)
    (folder / "ledger.json").write_text("hand-edited ledger")
    states = application.session_artifact_states(game_session.id)
    assert states[ArtifactName.LEDGER] is ArtifactStatus.CURRENT
    assert states[ArtifactName.TRANSCRIPT_SECTIONS] is ArtifactStatus.CURRENT
    assert all(states[name] is ArtifactStatus.STALE for name in NARRATIVE_OUTPUTS if name is not ArtifactName.LEDGER)
    assert set(application.generation_plan(game_session.id)) == {
        GenerationTask(game_session.id, name) for name in NARRATIVE_OUTPUTS if name is not ArtifactName.LEDGER
    }


def test_hand_edited_scene_log_rebuilds_matters_and_summary(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    folder = application.session_folder(game_session.id)
    _write_complete_session(folder, time.time_ns())
    complete_campaign(application, campaign.id)
    (folder / "scene_log.json").write_text("hand-edited scene log")
    states = application.session_artifact_states(game_session.id)
    assert states[ArtifactName.LEDGER] is ArtifactStatus.CURRENT
    assert states[ArtifactName.SCENE_LOG] is ArtifactStatus.CURRENT
    expected = set(NARRATIVE_OUTPUTS) - {ArtifactName.LEDGER, ArtifactName.SCENE_LOG}
    assert all(states[name] is ArtifactStatus.STALE for name in expected)
    assert set(application.generation_plan(game_session.id)) == {GenerationTask(game_session.id, name) for name in expected}


def test_glossary_changes_stale_only_producers_that_consume_glossary(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    from tablesage_model.model import GlossaryEntry

    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    _write_complete_session(application.session_folder(game_session.id), time.time_ns())
    complete_campaign(application, campaign.id)
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Aldor", description="A wizard"))
    states = application.session_artifact_states(game_session.id)
    assert states[ArtifactName.ROLE_TRANSCRIPT] is ArtifactStatus.CURRENT
    assert states[ArtifactName.TRANSCRIPT_SECTIONS] is ArtifactStatus.CURRENT
    assert states[ArtifactName.PLAYER_INTRODUCTIONS] is ArtifactStatus.STALE
    assert all(states[name] is ArtifactStatus.STALE for name in NARRATIVE_OUTPUTS)


def test_force_rebuilds_selected_step_and_its_downstream_consumers(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    _write_complete_session(application.session_folder(game_session.id), time.time_ns())
    complete_campaign(application, campaign.id)
    plan = application.generation_plan(game_session.id, force=ArtifactName.LEDGER)
    assert set(plan) == {GenerationTask(game_session.id, name) for name in NARRATIVE_OUTPUTS}
    assert plan[0] == GenerationTask(game_session.id, ArtifactName.LEDGER)


def test_current_summary_plan_recursively_repairs_previous_matters(
    tmp_path: Path, complete_campaign: Callable[[Application, uuid.UUID], None]
) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    previous = application.create_session(campaign.id, "Previous", date(2026, 1, 1))
    current = application.create_session(campaign.id, "Current", date(2026, 1, 8))
    for item in (previous, current):
        _write_complete_session(application.session_folder(item.id), time.time_ns())
    complete_campaign(application, campaign.id)
    (application.session_folder(previous.id) / "role_transcript.json").write_text("changed transcript")
    plan = application.generation_plan(current.id, force=ArtifactName.SUMMARY)
    tasks = set(plan)
    assert GenerationTask(previous.id, ArtifactName.PRESENT_MATTERS) in tasks
    assert GenerationTask(previous.id, ArtifactName.LEDGER) in tasks
    assert GenerationTask(previous.id, ArtifactName.TABLE_RECAP) not in tasks
    assert GenerationTask(current.id, ArtifactName.SCENE_LOG) in tasks
    assert GenerationTask(current.id, ArtifactName.SUMMARY) in tasks
    assert GenerationTask(current.id, ArtifactName.TABLE_RECAP) in tasks
    assert plan.index(GenerationTask(previous.id, ArtifactName.PRESENT_MATTERS)) < plan.index(
        GenerationTask(current.id, ArtifactName.SCENE_LOG)
    )
