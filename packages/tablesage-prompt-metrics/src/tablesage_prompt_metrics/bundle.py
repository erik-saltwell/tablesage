from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, cast

import jinja2
from pydantic import TypeAdapter
from tablesage_application import Application
from tablesage_application.llm import PromptName, read_prompt_template, read_system_prompt
from tablesage_application.session_pipeline import clean_transcript, generate_ledger
from tablesage_model.model import Session as GameSession

from .models import BundleFile, BundleManifest, CompletenessQuestion

MANIFEST_FILENAME = "manifest.json"
SYSTEM_PROMPT_FILENAME = "system-prompt.md"
USER_PROMPT_FILENAME = "user-prompt.txt"
TRANSCRIPT_FILENAME = "transcript.md"
RESPONSE_SCHEMA_FILENAME = "response-schema.json"
QUESTIONS_FILENAME = "questions.json"


class _Named(Protocol):
    name: str


def _find_named[NamedT: _Named](items: Sequence[NamedT], name: str, *, kind: str) -> NamedT:
    matches: list[NamedT] = [item for item in items if item.name == name]
    if len(matches) == 1:
        return matches[0]
    available: str = ", ".join(sorted(repr(item.name) for item in items)) or "(none)"
    if not matches:
        raise ValueError(f"{kind} {name!r} was not found. Available {kind.lower()}s: {available}")
    raise ValueError(f"More than one {kind.lower()} is named {name!r}; use a unique name.")


def _find_session(sessions: Sequence[GameSession], sequence: str) -> GameSession:
    matches: list[GameSession] = [session for session in sessions if f"{session.sequence_number:03d}" == sequence]
    if len(matches) == 1:
        return matches[0]
    available: str = ", ".join(sorted(f"{session.sequence_number:03d}" for session in sessions)) or "(none)"
    if not matches:
        raise ValueError(f"Session {sequence!r} was not found. Available session IDs: {available}")
    raise ValueError(f"More than one session has sequence {sequence!r}.")


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _write_text(path: Path, content: str) -> BundleFile:
    encoded: bytes = content.encode("utf-8")
    path.write_bytes(encoded)
    return BundleFile(path=path.name, sha256=_sha256(encoded))


class EvaluationBundle:
    def __init__(self, root: Path) -> None:
        self.root: Path = root.resolve()
        self.manifest: BundleManifest = BundleManifest.model_validate_json((self.root / MANIFEST_FILENAME).read_text(encoding="utf-8"))
        self._validate_hashes()

    def _validate_hashes(self) -> None:
        for label, expected in self.manifest.files.items():
            path: Path = self.root / expected.path
            if not path.is_file():
                raise ValueError(f"Bundle file {label!r} is missing: {path}")
            actual: str = _sha256(path.read_bytes())
            if actual != expected.sha256:
                raise ValueError(f"Bundle file {label!r} has changed since export: {path}")

    @property
    def system_prompt(self) -> str:
        return (self.root / self.manifest.files["system_prompt"].path).read_text(encoding="utf-8")

    @property
    def user_prompt(self) -> str:
        return (self.root / self.manifest.files["user_prompt"].path).read_text(encoding="utf-8")

    @property
    def transcript(self) -> str:
        return (self.root / self.manifest.files["transcript"].path).read_text(encoding="utf-8")

    @property
    def response_schema(self) -> dict[str, object]:
        value: object = json.loads((self.root / self.manifest.files["response_schema"].path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Bundle response schema must be a JSON object.")
        if not all(isinstance(key, str) for key in value):
            raise ValueError("Bundle response schema keys must be strings.")
        return cast(dict[str, object], value)

    @property
    def questions(self) -> list[CompletenessQuestion]:
        path: Path = self.root / QUESTIONS_FILENAME
        if not path.exists():
            return []
        return TypeAdapter(list[CompletenessQuestion]).validate_json(path.read_text(encoding="utf-8"))


def export_ledger_bundle(
    repo_root: Path,
    campaign_name: str,
    session_sequence: str,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> EvaluationBundle:
    if len(session_sequence) != 3 or not session_sequence.isdigit():
        raise ValueError("Session sequence must contain exactly three digits, such as '001'.")

    application = Application(repo_root.resolve())
    campaign = _find_named(application.list_campaigns(), campaign_name, kind="Campaign")
    game_session = _find_session(application.list_sessions(campaign.id), session_sequence)
    attendees: tuple[generate_ledger.Attendee, ...] = tuple(
        sorted(
            (
                generate_ledger.Attendee(
                    player_name=attendee.player_name.strip(),
                    roles=tuple(sorted({role.strip() for role in attendee.roles if role.strip()})),
                )
                for attendee in application.list_attendance(game_session.id)
            ),
            key=lambda attendee: attendee.player_name.casefold(),
        )
    )
    known_roles: tuple[str, ...] = tuple(sorted({role for attendee in attendees for role in attendee.roles}))
    glossary: tuple[generate_ledger.GlossaryPromptEntry, ...] = tuple(
        generate_ledger.GlossaryPromptEntry(term=entry.term, description=entry.description)
        for entry in sorted(application.list_glossary_entries(campaign.id), key=lambda entry: entry.term.casefold())
    )
    transcript: str = clean_transcript.render_role_transcript_text(application.session_folder(game_session.id))
    prompt_data = generate_ledger.LedgerPromptData(
        transcript=transcript,
        known_roles=known_roles,
        attendees=attendees,
        glossary=glossary,
    )
    system_prompt: str = read_system_prompt(PromptName.GENERATE_LEDGER)
    template = jinja2.Template(read_prompt_template(PromptName.GENERATE_LEDGER), undefined=jinja2.StrictUndefined)
    user_prompt: str = template.render(**vars(prompt_data)).rstrip() + "\n"
    schema_text: str = json.dumps(generate_ledger.LedgerGenerationResponse.model_json_schema(), indent=2, sort_keys=True) + "\n"

    destination: Path = output_dir.resolve()
    if destination.exists():
        if not overwrite:
            raise FileExistsError(f"Evaluation bundle already exists: {destination}")
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    files: dict[str, BundleFile] = {
        "system_prompt": _write_text(destination / SYSTEM_PROMPT_FILENAME, system_prompt.rstrip() + "\n"),
        "user_prompt": _write_text(destination / USER_PROMPT_FILENAME, user_prompt),
        "transcript": _write_text(destination / TRANSCRIPT_FILENAME, transcript),
        "response_schema": _write_text(destination / RESPONSE_SCHEMA_FILENAME, schema_text),
    }
    manifest = BundleManifest(
        campaign_name=campaign.name,
        session_sequence=session_sequence,
        session_uuid=str(game_session.id),
        files=files,
    )
    (destination / MANIFEST_FILENAME).write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return EvaluationBundle(destination)
