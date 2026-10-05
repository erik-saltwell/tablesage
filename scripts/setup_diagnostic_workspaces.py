"""Create four offline, disposable workspaces for source-independent agent diagnosis.

From the repository root:
    uv run python scripts/setup_diagnostic_workspaces.py --output /tmp/tablesage-diagnostics

The output must not exist and must be outside this checkout and existing workspaces.
No API calls, model downloads, real voice prints, or production data are used.
Authored outputs reuse seed_docs_data's writers. Completion records and expected
states come from the existing application, not a second freshness implementation.
Case names are neutral; keep this script and its README outside diagnosing agents' context.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import uuid
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

import widelog
import yaml
from sqlmodel import Session as DatabaseSession
from tablesage_application.configuration import SETTINGS_VERSION
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import processing_state
from tablesage_application.session_pipeline.artifact_graph import ArtifactRef, ArtifactStatus
from tablesage_model.model import Campaign, Player
from tablesage_model.settings import AppSettings
from tablesage_tui.agent_help import refresh_agent_files

if TYPE_CHECKING:
    from tablesage_application import Application

CASES = ((False, False), (True, False), (False, True), (True, True))
REVIEW_PRODUCERS = (ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS, ArtifactName.TRANSCRIPT_REVIEW_EDITS)
AUDIO_INPUT = "artifact:normalized_review_audio"


def create_baseline(cwd: Path) -> tuple[Application, uuid.UUID]:
    # Delay the application/LLM imports until main has selected bundled, offline data.
    from seed_docs_data import PLAYERS, STORIES, write_session
    from tablesage_application import Application

    app = Application(cwd)
    campaign = app.create_campaign(Campaign(name="Iron Pact", game_system="Fictional diagnostic example"))
    game_session = app.create_session(campaign.id, "The Descent Begins", date(2026, 9, 27))
    for role, player_name in PLAYERS.items():
        player = app.create_player(Player(name=player_name))
        app.add_attendance_with_roles(game_session.id, player.id, [role])

    write_session(app, game_session, STORIES[0], previous_recap="")
    folder = app.session_folder(game_session.id)
    source = cwd / "recording.wav"
    shutil.copyfile(folder / "input_audio.wav", source)
    shutil.copyfile(source, folder / "normalized_review_audio.wav")
    # These are authored, silent audio and synthetic transcript outputs, not results of model runs.
    # Initialize current-format state before asking the app for its graph, avoiding legacy import.
    section_values = {
        "import_request": {"source_path": str(source), "clean_audio": False},
        "name_correction_suggestions": {"suggestions": []},
        "name_correction_decisions": {"corrections": []},
        "new_speaker_assignments": {"players": [], "evidence": []},
        "reviewed_new_speaker_assignments": {"players": []},
        "seeded_voice_samples": {"players": []},
        "glossary_suggestions": {"proposals": []},
        "glossary_decisions": {"entries": []},
        "extracted_glossary_terms": {"entries": []},
        "spelling_suggestions": {"suggestions": []},
        "spelling_decisions": {"corrections": []},
        "transcript_review_edits": {"edits": [], "removed_indices": [], "find_replacements": []},
        "voice_print_decision": {"accepted": False},
        "voice_print_enhancement": {"enhanced_player_count": 0, "clip_count": 0},
    }

    def seed_sections(state: processing_state.ProcessingState) -> None:
        state.sections.update(section_values)

    processing_state.update(folder, seed_sections, reason="offline_fixture")
    with DatabaseSession(app._engine) as database:
        steps = app._artifact_graph(database, campaign.id).steps
    for step in steps:
        for output in step.outputs:
            if isinstance(output, ArtifactRef) and output.is_section:
                continue
            if not output.path.exists():
                # All un-authored file outputs here are intermediate copies of the synthetic transcript.
                if output.path.name not in {
                    "cleaned_transcript.json",
                    "name_corrected_transcript.json",
                    "identified_transcript.json",
                    "spellchecked_transcript.json",
                }:
                    raise ValueError(f"No synthetic writer for {output.path.name}; update fixture setup.")
                shutil.copyfile(folder / "transcript.json", output.path)
        app._record_completion(game_session.id, step.name)

    states = app.session_artifact_states(game_session.id)
    if any(status is not ArtifactStatus.CURRENT for status in states.values()):
        raise ValueError(f"Baseline is not fully current: {states}")
    settings = AppSettings(settings_version=SETTINGS_VERSION)
    (cwd / ".tablesage" / "settings.yaml").write_text(yaml.safe_dump(settings.model_dump(mode="json")), encoding="utf-8")
    status = refresh_agent_files(cwd)
    if status.error:
        raise ValueError(status.error)
    return app, game_session.id


def create_case(cwd: Path, *, missing_audio: bool, missing_fingerprints: bool) -> None:
    app, session_id = create_baseline(cwd)
    try:
        folder = app.session_folder(session_id)
        if missing_audio:
            (folder / ARTIFACTS[ArtifactName.NORMALIZED_REVIEW_AUDIO].filename).unlink()
        if missing_fingerprints:

            def remove_inputs(state: processing_state.ProcessingState) -> None:
                for name in REVIEW_PRODUCERS:
                    del state.records[name.value].inputs[AUDIO_INPUT]

            processing_state.update(folder, remove_inputs, reason="offline_fixture")

        states = app.session_artifact_states(session_id)
        expected_import = ArtifactStatus.STALE if missing_audio else ArtifactStatus.CURRENT
        expected_review = ArtifactStatus.STALE if missing_audio or missing_fingerprints else ArtifactStatus.CURRENT
        if states[ArtifactName.INPUT_AUDIO] is not expected_import:
            raise ValueError("Unexpected Import Audio state.")
        for name in (*REVIEW_PRODUCERS, ArtifactName.REVIEWED_TRANSCRIPT, ArtifactName.SUMMARY, ArtifactName.LEDGER):
            if states[name] is not expected_review:
                raise ValueError(f"Unexpected {name.value} state: {states[name]}")
        # Keep evaluator results outside each workspace so agents do not receive an answer key.
        print(json.dumps({"workspace": str(cwd), "states": {name.value: value.value for name, value in states.items()}}))
    finally:
        app._engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--output", type=Path, required=True, help="New parent directory outside the checkout and existing workspaces")
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    checkout = Path(__file__).resolve().parents[1]
    if output.exists():
        parser.error(f"Output already exists; use a new directory. Nothing was changed: {output}")
    if output.is_relative_to(checkout):
        parser.error("Create fixtures outside the source checkout so diagnostic agents do not inherit repository context.")
    if any((parent / ".tablesage").exists() for parent in (output, *output.parents)):
        parser.error("Do not create fixtures inside an existing TableSage workspace.")
    # LiteLLM otherwise fetches its model cost map on import, even without an LLM call.
    os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    # Setup uses real state writers, but their event payloads would flood the terminal with
    # fixture records. Exceptions still propagate; only the four evaluator summaries are printed.
    widelog.init(sink=lambda event: None)
    output.mkdir(parents=True)
    for index, (missing_audio, missing_fingerprints) in enumerate(CASES, 1):
        cwd = output / f"case-{index:02d}"
        cwd.mkdir()
        create_case(cwd, missing_audio=missing_audio, missing_fingerprints=missing_fingerprints)
    print(f"Created four verified workspaces in {output}. Start a fresh agent in each; see scripts/README.md for instructions.")


if __name__ == "__main__":
    main()
