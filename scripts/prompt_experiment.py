"""Run one isolated Ledger or Summary prompt experiment using production generators."""

# Capture start time before application imports.
# ruff: noqa: E402
from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import shutil
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_STARTED = datetime.now(UTC)

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from summary_experiment import application, digest, git, outside_checkout, read_json, seal, verify, word_count, write_json
from tablesage_application.configuration import Configuration
from tablesage_application.llm import PromptName, read_prompt_template, read_system_prompt
from tablesage_application.llm.llm_helper import PromptExecution, render_prompt
from tablesage_application.paths import ARTIFACTS, SUMMARY_INPUTS_FILENAME, ArtifactName
from tablesage_application.session_pipeline import generate_ledger as ledger_pipeline
from tablesage_application.session_pipeline import generate_summary as summary_pipeline
from tablesage_application.session_pipeline.generate_player_introductions import (
    Attendee,
    PlayerIntroductions,
    validate_player_introductions,
)
from tablesage_application.session_pipeline.transcript_sections import (
    RoleTranscript,
    RoutedUtterance,
    load_current_transcript_sections,
    route_transcript,
)

PROMPTS = {"ledger": PromptName.GENERATE_LEDGER, "summary": PromptName.SUMMARIZE_SESSION}
OPTIONS = {"temperature", "top_p", "max_tokens", "reasoning_effort", "seed"}


def prepare(args: argparse.Namespace) -> None:
    """Freeze source data once. Never regenerate, replace canonical outputs, or overwrite inputs."""
    app = application(args.workspace)
    current, prior = app.get_session(args.current), app.get_session(args.prior)
    if (
        current.campaign_id != prior.campaign_id
        or not current.session_date
        or not prior.session_date
        or prior.session_date >= current.session_date
    ):
        raise ValueError("Select a strictly earlier recap Session in the same Campaign.")
    folder, prior_folder = app.session_folder(current.id), app.session_folder(prior.id)
    if read_json(folder / SUMMARY_INPUTS_FILENAME).get("previous_session_id") != str(prior.id):
        raise ValueError("Prior Session differs from recorded Summary composition provenance.")
    campaign = app.get_campaign(current.campaign_id)
    attendees = sorted(app.list_attendance(current.id), key=lambda row: row.player_name.casefold())
    roster = [{"player_name": row.player_name, "roles": list(row.roles)} for row in attendees]
    glossary = [
        {"term": row.term, "description": row.description}
        for row in sorted(app.list_glossary_entries(campaign.id), key=lambda row: row.term.casefold())
    ]
    role_path = folder / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    sections_path = folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename
    routed = route_transcript(RoleTranscript.load(role_path), load_current_transcript_sections(role_path, sections_path))
    good = ledger_pipeline.Ledger.load(args.good_ledger)
    if good.session_name != current.name:
        raise ValueError("Good Ledger Session name does not match the selected Session.")
    intros_path = folder / ARTIFACTS[ArtifactName.PLAYER_INTRODUCTIONS].filename
    intros = PlayerIntroductions.load(intros_path)
    if intros.session_id != current.id:
        raise ValueError("Player Introductions belong to a different Session.")
    validate_player_introductions(intros, [Attendee(player_name=a.player_name, roles=a.roles) for a in attendees])
    recap_path = prior_folder / ARTIFACTS[ArtifactName.RECAP_SUMMARY].filename
    sources = {
        "role_transcript.json": role_path,
        "transcript_sections.json": sections_path,
        "player_introductions.json": intros_path,
        "prior-recap.md": recap_path,
        "good-ledger.json": args.good_ledger,
        "bad-summary.md": args.bad_summary,
    }
    if args.good_summary:
        sources["good-summary.md"] = args.good_summary
    initial_hashes = {name: digest(source) for name, source in sources.items()}
    destination = args.workspace / "inputs"
    destination.mkdir(exist_ok=False)
    try:
        (destination / "sources").mkdir()
        for name, source in sources.items():
            shutil.copyfile(source, destination / "sources" / name)
        write_json(
            destination / "ledger.json",
            {
                "starting_context": [u.model_dump() for u in routed.starting_context],
                "session_utterances": [u.model_dump() for u in routed.session],
                "known_roles": sorted({role for row in roster for role in row["roles"]}),
                "attendees": roster,
                "glossary": glossary,
                "session_id": str(current.id),
                "session_name": current.name,
            },
        )
        write_json(
            destination / "summary.json",
            {
                "ledger": args.good_ledger.read_text(encoding="utf-8"),
                "attendees": roster,
                "glossary": glossary,
                "campaign_name": campaign.name,
                "session_date": current.session_date.isoformat(),
                "game_system": campaign.game_system,
            },
        )
        composition = {"recap": recap_path.read_text(encoding="utf-8"), "introductions": intros.to_markdown()}
        summary_pipeline.compose_summary(
            "<!-- RECAP -->\n<!-- PLAYER_INTRODUCTIONS -->",
            **{"recap_summary": composition["recap"], "player_introductions": composition["introductions"]},
        )
        write_json(destination / "composition.json", composition)
        for name, source in sources.items():
            if digest(source) != initial_hashes[name] or digest(destination / "sources" / name) != initial_hashes[name]:
                raise ValueError("Source changed during preparation; use a new input snapshot.")
        seal(
            destination,
            {
                "kind": "prompt-inputs",
                "prepared_at": datetime.now(UTC).isoformat(),
                "current_session_id": str(current.id),
                "prior_session_id": str(prior.id),
                "source_revision": git("rev-parse", "HEAD").strip(),
                "sources": {name: {"path": str(source), "sha256": initial_hashes[name]} for name, source in sources.items()},
                "model": app.settings.llm_model_high,
                "timeout": app.settings.generate_artifacts.timeout,
                "baselines": {"ledger": "sources/good-ledger.json", "summary": "sources/bad-summary.md"},
                "reference_note": (
                    "User-selected baselines; original Ledger timing/model/prompt provenance unknown. "
                    "Good Ledger UUID may belong to its original workspace."
                ),
            },
        )
    except Exception:
        # Keep partial evidence for inspection; never present it as sealed inputs.
        raise
    for kind, prompt in PROMPTS.items():
        candidate = args.workspace / "prompts" / kind / "candidate"
        candidate.mkdir(parents=True, exist_ok=True)
        for name, content in (("system.md", read_system_prompt(prompt)), ("template.j2", read_prompt_template(prompt))):
            target = candidate / name
            if not target.exists():
                target.write_text(content, encoding="utf-8")
    print(f"Frozen inputs: {destination}\nEditable prompts: {args.workspace / 'prompts'}")


class Evidence:
    def __init__(self, kind: str, prompt: Path, output: Path, receipt: dict[str, Any], inputs: dict[str, Any]) -> None:
        self.kind, self.prompt, self.output, self.receipt, self.inputs = kind, prompt, output, receipt, inputs

    def save(self) -> None:
        write_json(self.output / "run.json", self.receipt)

    def observe(self, event: dict[str, Any]) -> None:
        if event["phase"] == "started":
            attempt = len(self.receipt["attempts"]) + 1
            self.receipt["attempts"].append({"attempt": attempt, "status": "running"})
            for name in ("system", "user"):
                (self.prompt / f"attempt-{attempt}-{name}.md").write_text(event[name], encoding="utf-8")
            if event["schema"] is not None:
                write_json(self.prompt / f"attempt-{attempt}-schema.json", event["schema"])
            self.receipt["strict_schema"] = event["strict_schema"]
        else:
            item = self.receipt["attempts"][-1]
            item["elapsed_seconds"] = event["elapsed_seconds"]
            item["status"] = event["phase"]
            if "error_type" in event:
                item["error_type"] = event["error_type"]
            if "raw" in event:
                raw = event["raw"]
                (self.output / f"attempt-{item['attempt']}-raw.txt").write_text(raw, encoding="utf-8")
                try:
                    if self.kind == "ledger":
                        response = ledger_pipeline.LedgerGenerationResponse.model_validate_json(raw)
                        players = frozenset(a["player_name"].strip() for a in self.inputs["attendees"])
                        item["attendee_warnings"] = ledger_pipeline._attendee_warning_count(response, players)
                        item["ledger_entries"] = len(response.ledger.utterances)
                    else:
                        summary_pipeline.validate_summary_markers(raw)
                    item["validation"] = "valid"
                except ValueError as exc:
                    item["validation"] = "invalid"
                    item["validation_error"] = str(exc)
        self.save()


async def run(args: argparse.Namespace) -> None:
    directory = args.inputs or args.workspace / "inputs"
    manifest = verify(directory)
    data = read_json(directory / f"{args.prompt_type}.json")
    prompt_source = args.prompt_dir or args.workspace / "prompts" / args.prompt_type / "candidate"
    system = (prompt_source / "system.md").read_text(encoding="utf-8")
    template = (prompt_source / "template.j2").read_text(encoding="utf-8")
    model, timeout = args.model or manifest["model"], args.timeout if args.timeout is not None else manifest["timeout"]
    options = json.loads(args.options)
    if not isinstance(options, dict) or set(options) - OPTIONS:
        raise ValueError(f"Allowed nonsecret options: {sorted(OPTIONS)}")
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("Timeout must be positive and finite.")
    if args.execute and args.response_file:
        raise ValueError("Use either --execute or --response-file.")
    if args.execute:
        Configuration(args.workspace)
    stamp = args.started.strftime("%Y-%m-%d_%H-%M-%S-%fZ")
    stem = f"{args.prompt_type}-{stamp}"
    prompt = args.workspace / "prompts" / args.prompt_type / stem
    output = args.workspace / "output" / stem
    prompt.mkdir(parents=True, exist_ok=False)
    output.mkdir(parents=True, exist_ok=False)
    (prompt / "system.md").write_text(system, encoding="utf-8")
    (prompt / "template.j2").write_text(template, encoding="utf-8")
    receipt = {
        "prompt_type": args.prompt_type,
        "started_at": args.started.isoformat(),
        "status": "running",
        "mode": "live" if args.execute else "offline" if args.response_file else "dry-run",
        "model": model,
        "model_options": options,
        "timeout": timeout,
        "input_manifest_sha256": digest(directory / "manifest.json"),
        "input_hashes": manifest["files"],
        "inputs": str(directory),
        "prompt_source": str(prompt_source),
        "saved_prompt": str(prompt),
        "source_revision": git("rev-parse", "HEAD").strip(),
        "working_tree_dirty": bool(git("status", "--porcelain")),
        "code_hashes": code_hashes(),
        "attempts": [],
        "usage_cost": "Not exposed by the production text-only interface.",
        "quality": "Unassessed; schema/marker validity does not establish content quality.",
    }
    evidence = Evidence(args.prompt_type, prompt, output, receipt, data)
    evidence.save()
    fixture = args.response_file.read_text(encoding="utf-8") if args.response_file else None
    if args.response_file:
        receipt["response_fixture_sha256"] = digest(args.response_file)

    async def replay(*unused: Any, **kwargs: Any) -> str:
        if fixture is not None:
            return fixture
        raise ValueError("Offline replay requires a response fixture.")

    execution = PromptExecution(system, template, evidence.observe, None if args.execute else replay)
    started = time.monotonic()
    try:
        if not args.execute and not args.response_file:
            if args.prompt_type == "ledger":
                prompt_data = ledger_pipeline.prepare_ledger_prompt_data(
                    [RoutedUtterance.model_validate(u) for u in data["starting_context"]],
                    [RoutedUtterance.model_validate(u) for u in data["session_utterances"]],
                    data["known_roles"],
                    [ledger_pipeline.Attendee.model_validate(a) for a in data["attendees"]],
                    [ledger_pipeline.GlossaryPromptEntry(**g) for g in data["glossary"]],
                )
                schema = ledger_pipeline.LedgerGenerationResponse.model_json_schema()
            else:
                prompt_data = summary_pipeline.SummaryPromptData(
                    data["ledger"],
                    [summary_pipeline.Attendee(a["player_name"], tuple(a["roles"])) for a in data["attendees"]],
                    [summary_pipeline.GlossaryPromptEntry(**g) for g in data["glossary"]],
                    data["campaign_name"],
                    data["session_date"],
                    data["game_system"],
                )
                schema = None
            rendered_system, rendered_user = render_prompt(PROMPTS[args.prompt_type], prompt_data, execution)
            evidence.observe(
                {"phase": "started", "system": rendered_system, "user": rendered_user, "schema": schema, "strict_schema": False}
            )
            receipt["attempts"][-1]["status"] = "not-called"
            receipt["status"] = "prepared"
            return
        if args.prompt_type == "ledger":
            result = await ledger_pipeline.generate_ledger(
                [RoutedUtterance.model_validate(u) for u in data["starting_context"]],
                [RoutedUtterance.model_validate(u) for u in data["session_utterances"]],
                data["known_roles"],
                [ledger_pipeline.Attendee.model_validate(a) for a in data["attendees"]],
                [ledger_pipeline.GlossaryPromptEntry(**g) for g in data["glossary"]],
                model,
                timeout,
                execution=execution,
                model_options=options or None,
            )
            write_json(output / "generation.json", result.model_dump(mode="json"))
            ledger = ledger_pipeline.Ledger(
                session_id=data["session_id"],
                session_name=data["session_name"],
                attendees=tuple(ledger_pipeline.Attendee.model_validate(a) for a in data["attendees"]),
                starting_situation=result.starting_situation,
                utterances=result.ledger.utterances,
            )
            ledger.save(output / f"{stem}.json")
            (output / f"{stem}.md").write_text(ledger.to_markdown(), encoding="utf-8")
            write_json(output / "scene-breakdown-content.json", result.scene_breakdown.model_dump(mode="json"))
            receipt["ledger_entries"] = len(result.ledger.utterances)
            receipt["scenes"] = len(result.scene_breakdown.scenes)
            for item in receipt["attempts"]:
                raw = output / f"attempt-{item['attempt']}-raw.txt"
                if (
                    item.get("validation") == "valid"
                    and ledger_pipeline.LedgerGenerationResponse.model_validate_json(raw.read_text(encoding="utf-8")) == result
                ):
                    receipt["selected_attempt"] = item["attempt"]
                    break
        else:
            result = await summary_pipeline.generate_summary(
                data["ledger"],
                [summary_pipeline.Attendee(a["player_name"], tuple(a["roles"])) for a in data["attendees"]],
                [summary_pipeline.GlossaryPromptEntry(**g) for g in data["glossary"]],
                data["campaign_name"],
                data["session_date"],
                data["game_system"],
                model,
                timeout,
                execution=execution,
                model_options=options or None,
            )
            composition = read_json(directory / "composition.json")
            composed = summary_pipeline.compose_summary(result, composition["recap"], composition["introductions"])
            (output / "summary-template.md").write_text(result, encoding="utf-8")
            (output / f"{stem}.md").write_text(composed, encoding="utf-8")
            body = result.replace(summary_pipeline.RECAP_MARKER, "").replace(summary_pipeline.PLAYER_INTRODUCTIONS_MARKER, "")
            receipt["words"] = {
                "body": word_count(body),
                "recap": word_count(composition["recap"]),
                "introductions": word_count(composition["introductions"]),
                "complete": word_count(composed),
            }
            receipt["selected_attempt"] = len(receipt["attempts"])
        receipt["status"] = "success"
    except BaseException as exc:
        receipt["status"] = "interrupted" if isinstance(exc, (KeyboardInterrupt, asyncio.CancelledError)) else "failed"
        receipt["error_type"] = type(exc).__name__
        raise
    finally:
        receipt["elapsed_seconds"] = time.monotonic() - started
        receipt["finished_at"] = datetime.now(UTC).isoformat()
        seal(prompt, {"kind": "prompt-bundle", "started_at": args.started.isoformat()})
        receipt["prompt_manifest_sha256"] = digest(prompt / "manifest.json")
        evidence.save()
        seal(output, {"kind": "prompt-run", "status": receipt["status"], "started_at": args.started.isoformat()})
        print(f"{receipt['status']}: {output}")


def code_hashes() -> dict[str, str]:
    from tablesage_application.llm import llm_helper
    from tablesage_tools.llm import client

    modules = [llm_helper, ledger_pipeline, summary_pipeline, client]
    paths = [Path(module.__file__) for module in modules] + [Path(__file__)]
    return {str(path): digest(path) for path in paths}


def main() -> None:
    started = SCRIPT_STARTED
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare")
    prep.add_argument("--current", type=uuid.UUID, required=True)
    prep.add_argument("--prior", type=uuid.UUID, required=True)
    prep.add_argument("--good-ledger", type=Path, required=True)
    prep.add_argument("--bad-summary", type=Path, required=True)
    prep.add_argument("--good-summary", type=Path)
    runner = sub.add_parser("run")
    runner.add_argument("prompt_type", choices=tuple(PROMPTS))
    runner.add_argument("--inputs", type=Path)
    runner.add_argument("--prompt-dir", type=Path)
    runner.add_argument("--model")
    runner.add_argument("--timeout", type=float)
    runner.add_argument("--options", default="{}")
    runner.add_argument("--execute", action="store_true", help="Call the provider; omitted means render only.")
    runner.add_argument("--response-file", type=Path, help="Offline replay, clearly labeled as non-provider evidence.")
    args = parser.parse_args()
    for name, value in vars(args).items():
        if isinstance(value, Path):
            setattr(args, name, value.expanduser().resolve())
    args.started = started
    try:
        outside_checkout(args.workspace)
        if args.command == "prepare":
            prepare(args)
        else:
            asyncio.run(run(args))
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
