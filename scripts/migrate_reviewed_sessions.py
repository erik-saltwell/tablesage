"""Preview or adopt backed-up human reviews, then optionally regenerate only downstream outputs.

Run from the checkout with uv run python scripts/migrate_reviewed_sessions.py --help.
TableSage must be closed. Preview is the default; --apply writes checkpoints; --generate calls models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import uuid
from pathlib import Path
from typing import Any, cast

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from tablesage_application import Application
from tablesage_application.configuration import Configuration
from tablesage_application.paths import ARTIFACTS, ArtifactName, database_path
from tablesage_application.session_pipeline import artifact_graph, processing_state
from tablesage_model.setup import ensure_settings
from tablesage_tools.model import Transcript
from tablesage_tui.resources import load_resource

REPO = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True)


def write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def path_argument(value: str) -> Path:
    return Path(value).expanduser().resolve()


def collect(app: Application, backup: Path, campaign_name: str) -> list[dict[str, Any]]:
    if not database_path(backup).is_file():
        raise ValueError("Backup must point to the copied workspace containing .tablesage/.")
    campaigns = [c for c in app.list_campaigns() if c.name == campaign_name]
    if len(campaigns) != 1:
        raise ValueError("Specify exactly one existing Campaign by name.")
    sessions = app.list_sessions(campaigns[0].id)
    if not sessions or any(s.session_date is None for s in sessions):
        raise ValueError("Every Session must have a date for chronological regeneration.")
    dates = [s.session_date for s in sessions]
    if len(set(dates)) != len(dates):
        raise ValueError("Session dates must be distinct for unambiguous prior recap selection.")
    rows = []
    generated_names = {ARTIFACTS[name].filename for name in (*artifact_graph.GENERATION_ORDER, ArtifactName.SCENE_BREAKDOWN)} | {
        "ledger.md",
        ".summary-inputs.json",
    }
    for session in sorted(sessions, key=lambda s: s.session_date):
        assert session.session_date is not None
        folder = app.session_folder(session.id)
        relative = folder.relative_to(app._cwd)
        previous = backup / relative
        reviewed = folder / ARTIFACTS[ArtifactName.REVIEWED_TRANSCRIPT].filename
        original = previous / reviewed.name
        if not original.is_file() or digest(reviewed) != digest(original):
            raise ValueError(f"Reviewed transcript is missing or differs from the backup: {session.name}")
        state = processing_state.ProcessingState.model_validate_json(processing_state.state_path(folder).read_bytes())
        old_state = processing_state.ProcessingState.model_validate_json(processing_state.state_path(previous).read_bytes())
        if state.sections != old_state.sections or state.drafts != old_state.drafts:
            raise ValueError(f"Review decisions or drafts differ from backup: {session.name}")
        transcript = Transcript.load(reviewed)
        if not transcript.utterances:
            raise ValueError(f"Empty reviewed transcript: {session.name}")
        blockers = app.session_processing_blockers(session.id)
        if blockers:
            raise ValueError(f"Session metadata blocks processing: {session.name}")
        protected = {}
        for source in folder.iterdir():
            if source.is_file() and source.suffix in {".json", ".md"} and source.name not in generated_names:
                if source.name == processing_state.STATE_FILENAME:
                    continue
                if not (previous / source.name).is_file() or digest(source) != digest(previous / source.name):
                    raise ValueError(f"Protected input differs from backup: {session.name}/{source.name}")
                protected[str(source.relative_to(app._cwd))] = digest(source)
        rows.append(
            {
                "id": str(session.id),
                "name": session.name,
                "date": session.session_date.isoformat(),
                "folder": str(relative),
                "reviewed_sha256": digest(reviewed),
                "utterances": len(transcript.utterances),
                "adjusted_utterances": sum(u.adjusted for u in transcript.utterances),
                "protected": protected,
                "historical_sections": old_state.sections,
                "historical_drafts": old_state.drafts,
            }
        )
    return rows


def verify_preserved(workspace: Path, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        for name, expected in row["protected"].items():
            if digest(workspace / name) != expected:
                raise ValueError(f"Protected input changed: {name}")
        state = processing_state.ProcessingState.model_validate_json(processing_state.state_path(workspace / row["folder"]).read_bytes())
        if state.sections != row["historical_sections"] or state.drafts != row["historical_drafts"]:
            raise ValueError(f"Historical review decisions changed: {row['name']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=path_argument)
    parser.add_argument("--backup", required=True, type=path_argument, help="The copied workspace, usually BACKUP/workspace.")
    parser.add_argument("--campaign", required=True)
    parser.add_argument("--output", type=path_argument, help="New receipt directory inside summary_experiment/migrations/.")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--generate", action="store_true", help="Requires --apply; rebuilds all downstream outputs using deployed settings."
    )
    parser.add_argument("--resume", action="store_true", help="Continue the same applied receipt, keeping completed outputs.")
    args = parser.parse_args()
    try:
        if args.backup == args.workspace or args.workspace.is_relative_to(args.backup) or args.backup.is_relative_to(args.workspace):
            raise ValueError("Backup and workspace must be separate directories.")
        if args.generate and not args.apply or args.resume and not args.apply:
            raise ValueError("Generation and resume require --apply.")
        if args.apply:
            parent = args.workspace / "summary_experiment" / "migrations"
            if args.output is None or args.output == parent or not args.output.is_relative_to(parent):
                raise ValueError(f"Supply a new --output directory inside {parent}.")
        if args.workspace == REPO or args.workspace.is_relative_to(REPO) or not database_path(args.workspace).is_file():
            raise ValueError("Use an existing test workspace outside the checkout.")
        settings = ensure_settings(args.workspace, load_resource("settings.yaml"))
        app = Application(args.workspace, settings=settings)
        rows = collect(app, args.backup, args.campaign)
        public_rows = [{k: v for k, v in row.items() if k not in {"historical_sections", "historical_drafts", "protected"}} for row in rows]
        preview = {
            "workspace": str(args.workspace),
            "backup": str(args.backup),
            "campaign": args.campaign,
            "sessions": public_rows,
            "configured_model": app.settings.llm_model_high,
            "generation_timeout": app.settings.generate_artifacts.timeout,
            "rebuild_order": [n.value for n in artifact_graph.GENERATION_ORDER],
            "provider_calls_started": False,
            "code_sha256": {
                str(p.relative_to(REPO)): digest(p)
                for p in (
                    Path(__file__).resolve(),
                    REPO / "packages/tablesage-application/src/tablesage_application/application.py",
                    REPO / "packages/tablesage-application/src/tablesage_application/processing_steps.py",
                    REPO / "packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py",
                    REPO / "packages/tablesage-application/src/tablesage_application/session_pipeline/processing_state.py",
                )
            },
        }
        if not args.apply:
            print(json.dumps(preview, indent=2))
            return
        if args.generate:
            Configuration(args.workspace)
            app.require_credentials("llm_model_high")
        receipt: Any
        if args.resume:
            receipt = read_json(args.output / "receipt.json")
            for key in ("workspace", "backup", "campaign", "sessions", "configured_model", "generation_timeout", "code_sha256"):
                if receipt[key] != preview[key]:
                    raise ValueError(f"Resume inputs changed: {key}")
        else:
            args.output.mkdir(parents=True, exist_ok=False)
            receipt = {
                **preview,
                "source_revision": git("rev-parse", "HEAD").strip(),
                "working_tree_changes": git("diff", "--name-only").splitlines(),
                "status": "started",
                "tasks_completed": [],
                "outputs_reopened": False,
            }
            write_json(args.output / "receipt.json", receipt)
        try:
            for row in rows:
                app.adopt_reviewed_transcript(
                    uuid.UUID(row["id"]),
                    expected_sha256=row["reviewed_sha256"],
                    source_revision=cast(str, receipt["source_revision"]),
                    backup_reference=str(args.backup),
                )
            verify_preserved(args.workspace, rows)
            receipt["status"] = "adopted"
            write_json(args.output / "receipt.json", receipt)
            if args.generate:
                os.chdir(args.workspace)
                if not receipt["outputs_reopened"]:
                    for row in rows:
                        for name in artifact_graph.GENERATION_ORDER:
                            app.reopen_artifact(uuid.UUID(row["id"]), name)
                    receipt["outputs_reopened"] = True
                receipt["provider_calls_started"] = True
                write_json(args.output / "receipt.json", receipt)
                for row in rows:
                    session_id = uuid.UUID(row["id"])
                    print(f"Updating {row['name']}...", flush=True)
                    plan = app.generation_plan(session_id)
                    for task in plan:
                        print(f"  {task.artifact_name.value}", flush=True)

                    def entered(task: artifact_graph.GenerationTask, completed: int, total: int) -> None:
                        receipt["current_task"] = {"session": str(task.session_id), "artifact": task.artifact_name.value}
                        write_json(args.output / "receipt.json", receipt)
                        print(f"  Running {task.artifact_name.value} ({completed + 1}/{total})", flush=True)

                    app.generate_outputs(session_id, on_stage=entered)
                    verify_preserved(args.workspace, rows)
                    states = app.session_artifact_states(session_id)
                    required = (*artifact_graph.GENERATION_ORDER, ArtifactName.SCENE_BREAKDOWN, ArtifactName.REVIEWED_TRANSCRIPT)
                    if any(states[n] is not artifact_graph.ArtifactStatus.CURRENT for n in required):
                        raise ValueError(f"Some regenerated outputs are still stale: {row['name']}")
                    cast(list[dict[str, str]], receipt["tasks_completed"]).extend(
                        {"session": str(t.session_id), "artifact": t.artifact_name.value} for t in plan
                    )
                    write_json(args.output / "receipt.json", receipt)
                receipt["status"] = "complete"
            write_json(args.output / "receipt.json", receipt)
        except Exception as exc:
            receipt["status"] = "failed"
            receipt["error_type"] = type(exc).__name__
            write_json(args.output / "receipt.json", receipt)
            verify_preserved(args.workspace, rows)
            raise ValueError(
                f"Migration stopped ({type(exc).__name__}); receipt saved. Completed outputs remain; resume the same receipt."
            ) from None
        print(f"{receipt['status']}: {args.output}; reviewed transcripts and historical decisions unchanged.")
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
