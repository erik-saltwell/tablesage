"""Current-contract publications and completion records for application integration tests."""

from __future__ import annotations

import json
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest
from sqlmodel import Session
from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS
from tablesage_application.session_pipeline import campaign_matters, narrative, post_session_matters, processing_state
from tablesage_application.session_pipeline.artifact_graph import FileRef, current_fingerprints


@pytest.fixture
def complete_campaign() -> Callable[[Application, uuid.UUID], None]:
    def complete(application: Application, campaign_id: uuid.UUID) -> None:
        for item in application.list_sessions(campaign_id):
            folder = application.session_folder(item.id)
            for spec in ARTIFACTS.values():
                if spec.is_file and spec.filename:
                    path = folder / spec.filename
                    if not path.exists():
                        path.write_text("fixture", encoding="utf-8")

            def initialize(state: processing_state.ProcessingState) -> None:
                state.legacy_imported_at = state.legacy_imported_at or processing_state.now()
                for name, spec in ARTIFACTS.items():
                    if not spec.is_file:
                        state.sections.setdefault(name.value, {})

            processing_state.update(folder, initialize, reason="test_fixture")
        with Session(application._engine) as session:
            graph = application._artifact_graph(session, campaign_id)
        # Materialize missing outputs first, then snapshot all producer inputs as a completed run would.
        for step in graph.steps:
            for output in step.outputs:
                path = output.path if isinstance(output, FileRef) or not output.is_section else None
                if path is not None and not path.exists():
                    path.write_text("fixture", encoding="utf-8")
        for step in graph.steps:
            record = processing_state.CompletionRecord(completed_at=processing_state.now(), inputs=current_fingerprints(step))

            def apply(
                state: processing_state.ProcessingState, name: str = step.name.value, record: processing_state.CompletionRecord = record
            ) -> None:
                state.records[name] = record

            processing_state.update(step.folder, apply, reason="test_fixture")

    return complete


@pytest.fixture
def summary_sources() -> Callable[[Application, uuid.UUID], Path]:
    def write(application: Application, session_id: uuid.UUID) -> Path:
        folder = application.session_folder(session_id)
        item = application.get_session(session_id)
        (folder / "role_transcript.json").write_text("fixture")
        with Session(application._engine) as session:
            previous = application._previous_recorded_session(session, item)
        sections = {section: campaign_matters.empty(section) for section in post_session_matters.INPUT_SECTIONS}
        sections["present_matters"] = {"current_position": "The party stands before the gate", "present_danger": ["The gate is burning"]}
        for section, content in sections.items():
            (folder / f"{section}.json").write_text(json.dumps({section: content}))
            (folder / f"{section}.evidence.json").write_text("{}")
        post_session_matters.persist(folder, post_session_matters.assemble(session_id, sections))
        scene = narrative.LogScene(
            location="Gate",
            participants=narrative.SceneParticipants(party_members=[], non_player_characters=[]),
            overview="The party reaches the gate.",
            scene_cue="The burning gate",
            events=[narrative.SceneEvent(text="The gate burns.", importance="high")],
            outcome="The party waits.",
        )
        log = narrative.SceneLog(
            session_id=session_id,
            session_name=item.name,
            previous_session_id=previous.id if previous else None,
            scenes=[scene],
            session_cue=scene.scene_cue,
        )
        narrative.persist_record(folder, "scene_log", log, narrative.render_scene_log(log))
        return folder

    return write
