"""Prepare and run isolated Summary comparisons without replacing Session outputs.

From the checkout: uv run python scripts/summary_experiment.py --help
All narrative evidence stays in the explicitly selected external workspace.
No provider calls occur unless `run --execute` is explicitly requested.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

# Preparation must not fetch provider pricing metadata at import time.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import jinja2
from tablesage_application import Application
from tablesage_application.configuration import Configuration
from tablesage_application.paths import ARTIFACTS, SUMMARY_INPUTS_FILENAME, ArtifactName, database_path
from tablesage_application.session_pipeline.generate_player_introductions import (
    Attendee,
    PlayerIntroductions,
    validate_player_introductions,
)
from tablesage_application.session_pipeline.generate_summary import (
    PLAYER_INTRODUCTIONS_MARKER,
    RECAP_MARKER,
    SummaryCompositionError,
    SummaryValidationError,
    compose_summary,
    validate_summary_markers,
)
from tablesage_model.setup import ensure_settings
from tablesage_tools.llm import call_llm
from tablesage_tui.agent_help import refresh_agent_files
from tablesage_tui.resources import load_resource

REPO = Path(__file__).resolve().parents[1]
PROMPT_PATH = "packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session"
REQUIRED = (
    ArtifactName.REVIEWED_TRANSCRIPT,
    ArtifactName.ROLE_TRANSCRIPT,
    ArtifactName.TRANSCRIPT_SECTIONS,
    ArtifactName.LEDGER,
    ArtifactName.SCENE_BREAKDOWN,
    ArtifactName.PLAYER_INTRODUCTIONS,
    ArtifactName.RECAP_SUMMARY,
    ArtifactName.SUMMARY,
)
OPTIONS = {"temperature", "top_p", "max_tokens", "reasoning_effort", "seed"}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def new_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True)


def evidence_root(workspace: Path) -> Path:
    return workspace / "summary_experiment"


def outside_checkout(path: Path) -> None:
    if path == REPO or REPO in path.parents:
        raise ValueError("Use a workspace outside the source checkout.")


def application(workspace: Path) -> Application:
    outside_checkout(workspace)
    if not database_path(workspace).is_file():
        raise ValueError("Not an initialized workspace. Use init first.")
    settings = ensure_settings(workspace, load_resource("settings.yaml"))
    return Application(workspace, settings=settings)


def seal(directory: Path, metadata: dict[str, Any]) -> None:
    metadata["files"] = {
        str(p.relative_to(directory)): digest(p) for p in sorted(directory.rglob("*")) if p.is_file() and p.name != "manifest.json"
    }
    write_json(directory / "manifest.json", metadata)


def verify(directory: Path) -> dict[str, Any]:
    manifest = read_json(directory / "manifest.json")
    expected = set(manifest["files"])
    actual = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file() and p.name != "manifest.json"}
    if actual != expected:
        raise ValueError(f"Evidence file set changed: {directory}")
    for name, expected_hash in manifest["files"].items():
        path = directory / name
        if path.resolve().is_relative_to(directory.resolve()) and digest(path) == expected_hash:
            continue
        raise ValueError(f"Evidence changed: {name}")
    return manifest


def initialize(workspace: Path) -> None:
    outside_checkout(workspace)
    if workspace.exists():
        raise ValueError("Initialization requires a new destination; existing data will not be overwritten.")
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise ValueError(f"Required media tool is missing: {executable}")
    new_directory(workspace)
    settings = ensure_settings(workspace, load_resource("settings.yaml"))
    app = Application(workspace, settings=settings)
    assert not app.list_campaigns()
    status = refresh_agent_files(workspace)
    if status.error:
        raise ValueError(status.error)
    root = evidence_root(workspace)
    for name in ("references", "snapshots", "prompts", "runs", "review", "reveal"):
        new_directory(root / name)
    launcher = workspace / "launch-tablesage.sh"
    launcher.write_text(
        '#!/bin/sh\nset -eu\ncd -- "$(dirname -- "$0")"\n' + f'exec "{REPO / ".venv/bin/tablesage"}" "$@"\n', encoding="utf-8"
    )
    launcher.chmod(0o755)
    write_json(
        root / "setup.json",
        {
            "source_revision": git("rev-parse", "HEAD").strip(),
            "workspace": str(workspace),
            "launcher": str(launcher),
            "generation_started": False,
        },
    )
    print(f"Initialized {workspace}\nLaunch: {launcher}")


def status_report(app: Application) -> dict[str, Any]:
    result = []
    for campaign in app.list_campaigns():
        for session in app.list_sessions(campaign.id):
            states = app.session_artifact_states(session.id)
            result.append(
                {
                    "campaign": campaign.name,
                    "session": session.name,
                    "id": str(session.id),
                    "date": str(session.session_date) if session.session_date else None,
                    "artifacts": {name.value: states[name].value for name in REQUIRED},
                }
            )
    return {"sessions": result}


def require_current(app: Application, session_id: uuid.UUID) -> None:
    states = app.session_artifact_states(session_id)
    problems = [f"{name.value}: {states[name].value}" for name in REQUIRED if states[name].value != "current"]
    if problems:
        raise ValueError("Session is not ready: " + ", ".join(problems))
    blockers = app.session_processing_blockers(session_id)
    if blockers:
        raise ValueError("Session has processing blockers.")


def freeze(workspace: Path, prior_id: uuid.UUID, current_id: uuid.UUID, destination: Path) -> None:
    app = application(workspace)
    prior, current = app.get_session(prior_id), app.get_session(current_id)
    if (
        prior.campaign_id != current.campaign_id
        or not prior.session_date
        or not current.session_date
        or prior.session_date >= current.session_date
    ):
        raise ValueError("Select two Sessions in the same Campaign with strictly ordered dates.")
    for session_id in (prior_id, current_id):
        require_current(app, session_id)
    current_folder = app.session_folder(current_id)
    provenance = read_json(current_folder / SUMMARY_INPUTS_FILENAME)
    if provenance.get("previous_session_id") != str(prior_id):
        raise ValueError("The current Summary did not use the selected prior Session. Regenerate it first.")
    campaign = app.get_campaign(current.campaign_id)
    attendees = sorted(app.list_attendance(current_id), key=lambda row: row.player_name.casefold())
    introductions = PlayerIntroductions.load(current_folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename)
    if introductions.session_id != current_id:
        raise ValueError("Player Introductions belong to a different Session.")
    validate_player_introductions(introductions, [Attendee(player_name=a.player_name, roles=a.roles) for a in attendees])
    new_directory(destination)
    for label, session_id in (("prior", prior_id), ("current", current_id)):
        folder = app.session_folder(session_id)
        new_directory(destination / label)
        for source in folder.iterdir():
            if source.is_file() and source.suffix in {".json", ".md"}:
                shutil.copyfile(source, destination / label / source.name)
    inputs = {
        "ledger": (current_folder / ARTIFACTS[ArtifactName.LEDGER].filename).read_text(encoding="utf-8"),
        "attendees": [{"player_name": a.player_name, "roles": list(a.roles)} for a in attendees],
        "glossary": [
            {"term": e.term, "description": e.description}
            for e in sorted(app.list_glossary_entries(campaign.id), key=lambda e: e.term.casefold())
        ],
        "campaign_name": campaign.name,
        "session_date": current.session_date.isoformat(),
        "game_system": campaign.game_system,
    }
    write_json(destination / "inputs.json", inputs)
    write_json(
        destination / "composition.json",
        {
            "recap": (app.session_folder(prior_id) / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename).read_text(encoding="utf-8"),
            "introductions": introductions.to_markdown(),
        },
    )
    # SQLite's backup API gives a consistent database copy even when WAL is enabled.
    with sqlite3.connect(database_path(workspace)) as source, sqlite3.connect(destination / "workspace.db") as target:
        source.backup(target)
    for session_id in (prior_id, current_id):
        require_current(app, session_id)
    # Detect concurrent edits rather than sealing a mixed artifact copy.
    for label, session_id in (("prior", prior_id), ("current", current_id)):
        for copied in (destination / label).iterdir():
            if digest(copied) != digest(app.session_folder(session_id) / copied.name):
                raise ValueError("Session changed during snapshot; close processing and use a new destination.")
    seal(
        destination,
        {
            "kind": "snapshot",
            "source_revision": git("rev-parse", "HEAD").strip(),
            "prior_session_id": str(prior_id),
            "current_session_id": str(current_id),
            "configured_summary_model": app.settings.llm_model_high,
            "note": "Close TableSage before freezing. Files are hash-checked; hashes are not a tamper-proof signature.",
        },
    )
    print(f"Frozen inputs: {destination}")


def prepare_prompt(snapshot: Path, revision: str, note: str, destination: Path) -> None:
    verify(snapshot)
    commit = git("rev-parse", "--verify", f"{revision}^{{commit}}").strip()
    system = git("show", f"{commit}:{PROMPT_PATH}/system.md")
    template = git("show", f"{commit}:{PROMPT_PATH}/template.j2")
    if not note.strip():
        raise ValueError("Supply a compatibility note after reviewing the candidate's input/schema and output contract.")
    if RECAP_MARKER not in system or PLAYER_INTRODUCTIONS_MARKER not in system or "ledger" not in template:
        raise ValueError("Different input/composition contract: use a separate pipeline comparison.")
    environment = jinja2.Environment(undefined=jinja2.StrictUndefined, autoescape=False)
    user = environment.from_string(template).render(**read_json(snapshot / "inputs.json"))
    new_directory(destination)
    (destination / "system.md").write_text(system, encoding="utf-8")
    (destination / "template.j2").write_text(template, encoding="utf-8")
    (destination / "user.md").write_text(user, encoding="utf-8")
    seal(
        destination,
        {"kind": "prompt", "revision": commit, "snapshot_manifest_sha256": digest(snapshot / "manifest.json"), "compatibility_note": note},
    )
    print(f"Rendered without generation: {destination}")


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


async def generate(args: argparse.Namespace) -> None:
    snapshot, prompt = args.snapshot.resolve(), args.prompt.resolve()
    verify(snapshot)
    prompt_manifest = verify(prompt)
    if prompt_manifest["snapshot_manifest_sha256"] != digest(snapshot / "manifest.json"):
        raise ValueError("Prompt was rendered for a different snapshot.")
    options = json.loads(args.options)
    if not isinstance(options, dict) or set(options) - OPTIONS:
        raise ValueError(f"Only supported nonsecret model options are allowed: {sorted(OPTIONS)}")
    if args.model == "openai/gpt-6-astra" and "reasoning_effort" not in options:
        options["reasoning_effort"] = "medium"
    if args.execute and not args.model:
        raise ValueError("An explicit model is required for provider calls.")
    if args.execute and args.response_file:
        raise ValueError("Choose either a provider call or an offline response file.")
    if not args.execute and not args.response_file:
        print(json.dumps({"provider_calls": 2, "model": args.model, "options": options, "prompt": str(prompt)}, indent=2))
        return
    composition = read_json(snapshot / "composition.json")
    new_directory(args.output)
    for repeat in range(2):
        directory = args.output / f"repeat-{repeat + 1}"
        new_directory(directory)
        receipt = {
            "kind": "run",
            "snapshot_manifest_sha256": digest(snapshot / "manifest.json"),
            "prompt_manifest_sha256": digest(prompt / "manifest.json"),
            "prompt_revision": prompt_manifest["revision"],
            "model": args.model,
            "model_options": options,
            "timeout": args.timeout,
            "offline_fixture": bool(args.response_file),
            "status": "failed",
            "attempts": [],
            "usage_cost": "Unavailable through the text-only shared LLM interface; consult provider/log records.",
        }
        for attempt in range(1, 4):
            started = time.monotonic()
            try:
                raw = (
                    args.response_file.read_text(encoding="utf-8")
                    if args.response_file
                    else await call_llm(
                        (prompt / "system.md").read_text(encoding="utf-8"),
                        (prompt / "user.md").read_text(encoding="utf-8"),
                        args.model,
                        timeout=args.timeout,
                        model_options=options,
                        prompt_name="summary_experiment",
                    )
                )
                (directory / f"attempt-{attempt}.md").write_text(raw, encoding="utf-8")
                template = validate_summary_markers(raw)
                composed = compose_summary(template, composition["recap"], composition["introductions"])
            except Exception as exc:
                receipt["attempts"].append(
                    {"attempt": attempt, "error_type": type(exc).__name__, "elapsed_seconds": time.monotonic() - started}
                )
                # Retry invalid output only; provider errors terminate this repetition.
                if isinstance(exc, (SummaryValidationError, SummaryCompositionError)) and attempt < 3 and not args.response_file:
                    continue
                break
            receipt["attempts"].append({"attempt": attempt, "elapsed_seconds": time.monotonic() - started})
            (directory / "summary.md").write_text(composed, encoding="utf-8")
            body = template.replace(RECAP_MARKER, "").replace(PLAYER_INTRODUCTIONS_MARKER, "")
            receipt["words"] = {
                "body": word_count(body),
                "recap": word_count(composition["recap"]),
                "introductions": word_count(composition["introductions"]),
                "complete": word_count(composed),
            }
            receipt["status"] = "success"
            break
        seal(directory, receipt)
        if receipt["status"] != "success":
            raise ValueError(f"Generation failed; retained attempts in {directory}. No successful repetition was replaced.")
    print(f"Two repetitions saved to {args.output}")


def blind_packet(workspace: Path, runs: list[Path], name: str) -> None:
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", name):
        raise ValueError("Use a simple round name.")
    manifests = [verify(run) for run in runs]
    if len(runs) != 4 or any(m["status"] != "success" for m in manifests):
        raise ValueError("Supply exactly four successful repetitions.")
    for key in ("snapshot_manifest_sha256", "model", "model_options", "timeout", "offline_fixture"):
        if any(m[key] != manifests[0][key] for m in manifests):
            raise ValueError(f"Controlled comparison differs on {key}.")
    counts = [m["prompt_manifest_sha256"] for m in manifests]
    if len(set(counts)) != 2 or any(counts.count(value) != 2 for value in set(counts)) or len({str(r.resolve()) for r in runs}) != 4:
        raise ValueError("Require two distinct repetitions for each of two prompts.")
    root = evidence_root(workspace)
    review, reveal = root / "review" / name, root / "reveal" / name
    if review.exists() or reveal.exists():
        raise ValueError("Round already exists; choose a new name.")
    new_directory(review)
    new_directory(reveal)
    shuffled = list(runs)
    random.SystemRandom().shuffle(shuffled)
    mapping = {}
    for index, run in enumerate(shuffled):
        label = f"candidate-{index + 1}"
        shutil.copyfile(run / "summary.md", review / f"{label}.md")
        (review / f"{label}-observations.md").write_text(
            "Useful details:\n\nImportant omissions:\n\nRepetition or excess detail:\n\n"
            "Consequences and ending situation:\n\nOther observations:\n",
            encoding="utf-8",
        )
        mapping[label] = {"run": str(run.resolve()), "manifest_sha256": digest(run / "manifest.json")}
    write_json(reveal / "mapping.json", mapping)
    (review / "README.md").write_text(
        "Review these candidates without opening run or reveal files. "
        "Record observations before revealing identities. Use a clean reviewer context.\n",
        encoding="utf-8",
    )
    print(f"Blind packet: {review}\nMapping is kept separately until review is recorded.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=lambda s: Path(s).expanduser().resolve(), required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("--prior", type=uuid.UUID, required=True)
    freeze_parser.add_argument("--current", type=uuid.UUID, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    prompt_parser = sub.add_parser("prompt")
    prompt_parser.add_argument("--snapshot", type=Path, required=True)
    prompt_parser.add_argument("--revision", required=True)
    prompt_parser.add_argument("--compatibility-note", required=True)
    prompt_parser.add_argument("--output", type=Path, required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument("--snapshot", type=Path, required=True)
    run_parser.add_argument("--prompt", type=Path, required=True)
    run_parser.add_argument("--model")
    run_parser.add_argument("--options", default="{}")
    run_parser.add_argument("--timeout", type=float, default=600)
    run_parser.add_argument("--output", type=Path, required=True)
    run_parser.add_argument("--execute", action="store_true")
    run_parser.add_argument("--response-file", type=Path, help="Offline fixture replay; never call a provider.")
    packet = sub.add_parser("packet")
    packet.add_argument("--runs", nargs=4, type=Path, required=True)
    packet.add_argument("--name", required=True)
    reveal = sub.add_parser("reveal")
    reveal.add_argument("--name", required=True)
    reveal.add_argument("--review-complete", action="store_true", required=True)
    args = parser.parse_args()
    try:
        outside_checkout(args.workspace)
        for attribute in ("output", "snapshot", "prompt", "response_file"):
            value = getattr(args, attribute, None)
            if value is not None:
                setattr(args, attribute, value.expanduser().resolve())
        output_groups = {"freeze": "snapshots", "prompt": "prompts", "run": "runs"}
        if args.command in output_groups:
            parent = evidence_root(args.workspace) / output_groups[args.command]
            if args.output == parent or not args.output.is_relative_to(parent.resolve()):
                raise ValueError(f"Output must be a new directory inside {parent}.")
        if args.command == "init":
            initialize(args.workspace)
        elif args.command == "status":
            print(json.dumps(status_report(application(args.workspace)), indent=2))
        elif args.command == "freeze":
            freeze(args.workspace, args.prior, args.current, args.output.resolve())
        elif args.command == "prompt":
            prepare_prompt(args.snapshot.resolve(), args.revision, args.compatibility_note, args.output.resolve())
        elif args.command == "run":
            if args.execute:
                Configuration(args.workspace)
                os.chdir(args.workspace)
            asyncio.run(generate(args))
        elif args.command == "packet":
            blind_packet(args.workspace, args.runs, args.name)
        elif args.command == "reveal":
            if not re.fullmatch(r"[a-zA-Z0-9_-]+", args.name):
                raise ValueError("Use a simple round name.")
            print(json.dumps(read_json(evidence_root(args.workspace) / "reveal" / args.name / "mapping.json"), indent=2))
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
