"""Validated, independently generated narrative artifacts and exact continuity assembly."""

from __future__ import annotations

import hashlib
import json
import uuid
from collections.abc import Callable, Mapping
from importlib.resources import files
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, Any, Literal

import jsonschema
import widelog
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from ..llm import PromptName, call_llm_with_prompt
from .atomic_files import atomic_write
from .bundles import ledger as ledger_inputs
from .bundles import ledger_render, scene_log_render, session_summary_render, table_recap_render
from .bundles import scene_log as scene_inputs
from .bundles import session_summary as summary_inputs
from .bundles import table_recap as recap_inputs
from .generate_ledger import Ledger, LedgerContent

CONTRACT_VERSION = 2
Text = Annotated[str, StringConstraints(min_length=1)]
KINDS = ["active_goal", "unresolved_mystery", "outstanding_obligation", "developing_threat", "available_opportunity"]
KIND_LABELS = ["Active Goals", "Unresolved Mysteries", "Outstanding Obligations", "Developing Threats", "Available Opportunities"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Moment(Record):
    matter: Text
    change: Literal["opened", "advanced", "resolved"]
    text: Text


class Matter(Record):
    matter: Text
    kind: Literal["active_goal", "unresolved_mystery", "outstanding_obligation", "developing_threat", "available_opportunity"]
    thread: Text
    text: Text


class Endcap(Record):
    end_situation: Text
    session_matters: list[Matter]


class Scene(Record):
    title: Text
    location: Text
    node_description: Text
    group: list[Text] = Field(min_length=1)
    goals: list[Text]
    obstacle: Text | None
    approach: Text | None
    outcome: Text
    scene_moments: list[Moment]

    @property
    def situation(self) -> str:
        """Concise display description for the campaign scene picker."""
        return self.node_description


class LegacySceneLog(Record):
    """Read types retained for the temporarily disabled campaign preparation tools."""

    version: Literal[1] = 1
    session_id: uuid.UUID
    session_name: Text
    previous_session_id: uuid.UUID | None
    opening_situation: Text
    scenes: list[Scene] = Field(min_length=1)
    endcap: Endcap

    @property
    def starting_situation(self) -> str:
        return self.opening_situation

    @property
    def ending_situation(self) -> str:
        return self.endcap.end_situation


class SceneParticipant(Record):
    name: Text
    note: Text | None


class SceneParticipants(Record):
    party_members: list[SceneParticipant]
    non_player_characters: list[SceneParticipant]


class SceneEvent(Record):
    text: Text
    importance: Literal["high", "medium", "low"]


class LogScene(Record):
    location: Text
    participants: SceneParticipants
    overview: Text
    scene_cue: Text
    events: list[SceneEvent] = Field(min_length=1)
    discoveries: list[SceneEvent] | None = None
    outcome: Text


class SceneLog(Record):
    version: Literal[2] = 2
    session_id: uuid.UUID
    session_name: Text
    previous_session_id: uuid.UUID | None
    scenes: list[LogScene] = Field(min_length=1)
    session_cue: Text

    def content(self) -> dict[str, Any]:
        return self.model_dump(
            mode="json", exclude_none=False, exclude={"version", "session_id", "session_name", "previous_session_id"}, exclude_unset=True
        )

    @classmethod
    def load(cls, folder: Path) -> SceneLog:
        if (folder / marker_name("scene_log")).exists():
            raise ValueError("Scene Log replacement was interrupted; regenerate it first.")
        data = cls.model_validate_json((folder / "scene_log.json").read_bytes())
        validate(PromptName.GENERATE_SCENE_LOG, data.content())
        validate_scene_content(data.content())
        return data


class SummaryScene(Record):
    scene_number: int = Field(ge=1, strict=True)
    title: Text
    bullets: list[Text] = Field(min_length=1)


class SessionSummary(Record):
    version: Literal[1] = 1
    session_id: uuid.UUID
    opening_situation: Text
    scenes: list[SummaryScene]
    endcap: Endcap


class RecapThread(Record):
    label: Text
    text: Text


class TableRecap(Record):
    version: Literal[1] = 1
    session_id: uuid.UUID
    orientation: Text
    threads: list[RecapThread]


class LedgerResponse(Record):
    ledger: LedgerContent
    starting_situation: Text | None = None

    @model_validator(mode="after")
    def nonempty_bootstrap(self) -> LedgerResponse:
        if self.starting_situation is not None and not self.starting_situation.strip():
            raise ValueError("The bootstrap Situation must not be blank.")
        return self


def schema(prompt: PromptName, filename: str = "schema.json") -> dict[str, Any]:
    resource = files("tablesage_application.llm._prompts").joinpath(prompt.value, filename)
    return json.loads(resource.read_text("utf-8"))


def validate(prompt: PromptName, content: dict[str, Any], filename: str = "schema.json") -> None:
    jsonschema.Draft202012Validator(schema(prompt, filename)).validate(content)


def validate_scene_content(data: dict[str, Any]) -> None:
    if data["session_cue"] not in [scene["scene_cue"] for scene in data["scenes"]]:
        raise ValueError("session_cue must exactly match a scene_cue.")


async def generate(
    prompt: PromptName,
    inputs: Any,
    model: str,
    timeout: float,
    assemble: Callable[[dict[str, Any]], dict[str, Any]],
    *,
    generation_schema: str = "schema-generation.json",
    model_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bounded retries preserve every rejected attempt in diagnostics, never in persisted artifacts."""
    last_error: Exception | None = None
    with widelog.wide_event(op="generate_narrative", prompt=prompt.value, model=model) as log:
        for attempt in range(1, 4):
            raw = await call_llm_with_prompt(
                prompt, inputs, model, response_model=schema(prompt, generation_schema), timeout=timeout, model_options=model_options
            )
            try:
                generated = json.loads(raw)
                validate(prompt, generated, generation_schema)
                content = assemble(generated)
                validate(prompt, content)
                if prompt is PromptName.GENERATE_SCENE_LOG:
                    validate_scene_content(content)
            except (ValueError, jsonschema.ValidationError) as exc:
                last_error = exc
                log.set(attempt=attempt, validation_error=str(exc))
                continue
            log.set(attempt=attempt, failed=False)
            return content
    raise ValueError(f"{prompt.value} failed validation after three attempts: {last_error}") from last_error


async def request_once(
    prompt: PromptName,
    inputs: Any,
    model: str,
    timeout: float,
    model_options: Mapping[str, Any] | None,
    *,
    filename: str = "schema.json",
    folder: Path | None = None,
) -> dict[str, Any]:
    raw = await call_llm_with_prompt(
        prompt,
        inputs,
        model,
        response_model=schema(prompt, filename),
        timeout=timeout,
        model_options=model_options,
    )
    if folder is not None:
        atomic_write(folder / ".generation-records" / prompt.value / f"{uuid.uuid4().hex}.json", raw.encode())
    response = json.loads(raw)
    validate(prompt, response, filename)
    return response


async def generate_ledger(
    inputs: ledger_inputs.LedgerPromptInputs,
    model: str,
    timeout: float,
    model_options: Mapping[str, Any] | None = None,
    *,
    folder: Path | None = None,
) -> LedgerResponse:
    filename = "schema-first-session.json" if inputs.starting_context is not None else "schema.json"
    data = await request_once(PromptName.GENERATE_LEDGER, inputs, model, timeout, model_options, filename=filename, folder=folder)
    with widelog.wide_event(op="ledger_structure") as log:
        log.set(problems=ledger_render.check_ledger(data, [vars(a) for a in inputs.attendees]))
    return LedgerResponse.model_validate(data)


async def generate_scene_log(
    ledger: Ledger,
    inputs: scene_inputs.SceneLogPromptInputs,
    previous_session_id: uuid.UUID | None,
    model: str,
    timeout: float,
    model_options: Mapping[str, Any] | None = None,
    *,
    folder: Path | None = None,
) -> SceneLog:
    if not ledger.utterances:
        raise ValueError("No active play to generate a Scene Log. The Ledger and transcript have been retained.")
    data = await request_once(PromptName.GENERATE_SCENE_LOG, inputs, model, timeout, model_options, folder=folder)
    with widelog.wide_event(op="scene_log_structure") as log:
        problems, _ = scene_log_render.check_scene_log(data, [vars(a) for a in inputs.attendees])
        log.set(problems=problems)
    return SceneLog(
        version=2, session_id=ledger.session_id, session_name=ledger.session_name, previous_session_id=previous_session_id, **data
    )


def render_ledger(source: Ledger) -> str:
    data = {"ledger": {"utterances": [entry.model_dump() for entry in source.utterances]}, "starting_situation": source.starting_situation}
    return ledger_render.to_markdown(data, source.session_name)


async def generate_summary(
    source: SceneLog, model: str, timeout: float, model_options: Mapping[str, Any] | None = None
) -> tuple[SessionSummary, str]:
    inputs = summary_inputs.SessionSummaryPromptInputs(source.content())
    data = await generate(PromptName.SUMMARIZE_SESSION, inputs, model, timeout, inputs.assemble, model_options=model_options)
    result = SessionSummary(session_id=source.session_id, **data)
    return result, session_summary_render.render_markdown(data, source.session_name)


async def generate_recap(
    source: SceneLog,
    model: str,
    timeout: float,
    target_words: int | None,
    orientation_words: int | None,
    model_options: Mapping[str, Any] | None = None,
) -> tuple[TableRecap, str]:
    inputs = recap_inputs.TableRecapPromptInputs(source.content(), target_words, orientation_words)
    data = await generate(
        PromptName.GENERATE_TABLE_RECAP,
        inputs,
        model,
        timeout,
        inputs.assemble,
        generation_schema="schema.json",
        model_options=model_options,
    )
    result = TableRecap(session_id=source.session_id, **data)
    with widelog.wide_event(op="table_recap_length", session_id=str(source.session_id)) as log:
        log.set(target_words=target_words, orientation_words=orientation_words, actual=recap_inputs.word_counts(data))
    return result, table_recap_render.render_markdown(data, f"{source.session_name}: Table Recap")


def render_scene_log(source: SceneLog) -> str:
    return scene_log_render.to_markdown(source.content(), source.session_name)


def marker_name(artifact: str) -> str:
    return ".ledger-v5-generation-incomplete" if artifact == "ledger" else f".{artifact}-generation-incomplete"


def persist(folder: Path, artifact: str, outputs: dict[str, bytes]) -> None:
    """Rollback-safe multi-file replacement with durable backups for process-interruption recovery."""
    marker = folder / marker_name(artifact)
    if marker.exists():
        recover(folder, artifact)
    originals = {name: (folder / name).read_bytes() if (folder / name).exists() else None for name in outputs}
    with TemporaryDirectory(prefix=f".{artifact}-", dir=folder) as temporary:
        stage = Path(temporary)
        for name, content in outputs.items():
            atomic_write(stage / name, content)
            old = originals[name]
            if old is not None:
                atomic_write(folder / f".{artifact}-{name}.bak", old)
        atomic_write(marker, json.dumps({"originals": {n: b is not None for n, b in originals.items()}}).encode())
        try:
            for name in outputs:
                (stage / name).replace(folder / name)
        except BaseException:
            recover(folder, artifact)
            raise
        marker.unlink()
    for name in outputs:
        (folder / f".{artifact}-{name}.bak").unlink(missing_ok=True)


def recover(folder: Path, artifact: str) -> None:
    marker = folder / marker_name(artifact)
    for name, existed in json.loads(marker.read_text())["originals"].items():
        if existed:
            atomic_write(folder / name, (folder / f".{artifact}-{name}.bak").read_bytes())
        else:
            (folder / name).unlink(missing_ok=True)
    marker.unlink()


def persist_record(folder: Path, artifact: str, record: BaseModel, markdown: str, *, markdown_filename: str | None = None) -> None:
    # Retain the old narrative contract before the first requested replacement.
    # Later same-contract regenerations use the normal recoverable pair backups.
    legacy = artifact == "summary" and (folder / "summary.md").exists() and not (folder / "summary.json").exists()
    if artifact == "ledger" and (folder / "ledger.json").exists():
        try:
            legacy = json.loads((folder / "ledger.json").read_text()).get("version") == 4
        except (ValueError, AttributeError):
            legacy = True
    if legacy:
        old_files = [folder / f"{artifact}.json", folder / f"{artifact}.md"]
        if artifact == "summary":
            old_files.append(folder / ".summary-inputs.json")
        for path in old_files:
            if path.exists():
                content = path.read_bytes()
                digest = hashlib.sha256(content).hexdigest()[:16]
                archived = folder / "legacy" / "narrative" / digest / path.name
                if not archived.exists():
                    atomic_write(archived, content)
    persist(
        folder,
        artifact,
        {
            f"{artifact}.json": (record.model_dump_json(indent=2, exclude_unset=isinstance(record, SceneLog)) + "\n").encode(),
            markdown_filename or f"{artifact}.md": markdown.encode(),
        },
    )
