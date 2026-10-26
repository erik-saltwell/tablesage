"""Independent Matters producers: validated evidence, filtered state and Campaign IDs."""

from __future__ import annotations

import json
import re
import sqlite3
import uuid
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import jsonschema
import widelog

from ..artifact_registry import ArtifactName
from ..llm import PromptName, call_llm_with_prompt
from .atomic_files import atomic_write
from .bundles import campaign_matters as inputs

MATTERS = {section: ArtifactName(section) for section in inputs.SECTIONS}
PROMPTS = {section: PromptName(f"generate_matter_{section}") for section in inputs.SECTIONS}
PRIOR_DEPENDENCIES = {
    section: ()
    if section == "developments"
    else inputs.REVELATION_MATTER_KINDS
    if section == "revelations"
    else (section, *inputs.ASSET_MATTER_KINDS)
    if section == "new_assets"
    else (section,)
    for section in inputs.SECTIONS
}
NORMALIZERS = {
    "goals": ("goal", inputs.normalize_goal_ids),
    "goal_impediments": ("impediment", inputs.normalize_impediment_ids),
    "opportunities": ("opportunity", inputs.normalize_opportunity_ids),
}
TROUBLE_EVALUATIONS = (
    "negative_outcome_clarity",
    "outcome_severity",
    "evidentiary_strength",
    "evidence_of_progression",
    "preventability",
)
DISABLED_MESSAGE = "Temporarily unavailable while Matters artifacts are being ported."


def empty(section: str) -> Any:
    if section == "present_matters":
        return {"current_position": None, "immediate_goals": [], "present_danger": []}
    return []


def validate(section: str, response: dict[str, Any]) -> None:
    from .narrative import schema

    jsonschema.Draft202012Validator(schema(PROMPTS[section])).validate(response)


def load(folder: Path, section: str) -> Any:
    from .narrative import marker_name

    if (folder / marker_name(section)).exists():
        raise ValueError(f"{section} replacement was interrupted; regenerate it first.")
    data = json.loads((folder / f"{section}.json").read_text())
    validate(section, data)
    result = data[section]
    if section in NORMALIZERS:
        prefix = NORMALIZERS[section][0]
        if any(not re.fullmatch(prefix + r"_[0-9]+", entry["id"]) for entry in result):
            raise ValueError(f"Stored {section} must use permanent IDs.")
    return result


def allocate_ids(campaign_folder: Path, section: str, entries: list[dict], previous: list[dict]) -> list[dict]:
    """Reserve Campaign IDs before publication; failed/crashed builds leave gaps, never reuse.

    The Campaign-local database travels with exports/renames and survives Session cleanup.
    BEGIN IMMEDIATE serializes allocation across processes. Existing state/evidence seeds
    a Campaign without counters. The counter is allocation metadata, not a build input.
    """
    prefix, normalize = NORMALIZERS[section]
    with sqlite3.connect(campaign_folder / ".matter-ids.sqlite3", timeout=30) as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS counters (section TEXT PRIMARY KEY, high_water INTEGER NOT NULL)")
        row = connection.execute("SELECT high_water FROM counters WHERE section = ?", (section,)).fetchone()
        high_water = row[0] if row else 0
        if row is None:
            for pattern in (f"*/{section}.json", f"*/{section}.evidence.json"):
                for path in campaign_folder.glob(pattern):
                    document = json.loads(path.read_text())
                    rows = document.get("normalized_response", document).get(section, [])
                    for entry in rows:
                        match = re.fullmatch(prefix + r"_([0-9]+)", entry.get("id", ""))
                        if match:
                            high_water = max(high_water, int(match[1]))
        normalized = normalize(entries, previous, high_water=high_water)
        high_water = max([high_water, *(int(entry["id"].rsplit("_", 1)[1]) for entry in normalized)])
        connection.execute(
            "INSERT INTO counters VALUES (?, ?) ON CONFLICT(section) DO UPDATE SET high_water = excluded.high_water",
            (section, high_water),
        )
    return normalized


def select(section: str, entries: Any) -> Any:
    """Standalone filters; preserve every retained field and relative order."""
    if section == "obligations":
        return [e for e in entries if e["lifecycle"] == "outstanding" and e["burden"] != "trivial" and e["consequence"] != "trivial"]
    if section == "goals":
        return [
            e
            for e in entries
            if e["lifecycle"] == "open" and e["significance"] in {"adventure_goal", "side_goal"} and e["parent_goal_id"] is None
        ]
    if section == "brewing_troubles":
        return [e for e in entries if e["harm_origin"] != "party" and all(e[k]["rank"] != "Low" for k in TROUBLE_EVALUATIONS)]
    if section == "goal_impediments":
        return [e for e in entries if e["lifecycle"] == "active"]
    if section == "opportunities":
        return [e for e in entries if e["parent_opportunity_id"] is None and e["lifecycle"] == "available"]
    if section == "mysteries":
        return inputs.filter_mysteries(entries)
    if section == "new_assets":
        return [e for e in entries if not (e["goal_support"] in {"low", "trivial"} and e["acquired_from_opportunity"] is False)]
    if section == "revelations":
        return [
            e
            for e in entries
            if (e["inclusion_basis"] == "reframing" or e["mystery_progress"] in {"substantial", "resolved"})
            and all(e[k] in {"high", "medium"} for k in ("impact", "evidentiary_strength", "unexpectedness"))
        ]
    return entries


def postprocess(section: str, response: dict, previous: Any, current: dict, campaign_folder: Path) -> dict:
    validate(section, response)
    entries = response[section]
    if section in NORMALIZERS:
        entries = allocate_ids(campaign_folder, section, entries, previous)
    if section == "goal_impediments":
        inputs.validate_goal_impediment_links(entries, current["goals"], previous)
    elif section == "opportunities":
        inputs.validate_opportunity_links(entries, current["goals"], current["goal_impediments"], previous)
    elif section == "mysteries":
        inputs.validate_mystery_links(entries, **current)
    elif section == "new_assets":
        inputs.validate_new_asset_links(entries, **current)
    normalized = {section: entries}
    validate(section, normalized)
    return normalized


async def generate(
    folder: Path, prompt_inputs: inputs.CampaignMattersPromptInputs, model: str, timeout: float, model_options: Mapping[str, Any]
) -> None:
    from .narrative import persist, schema

    section = prompt_inputs.section
    prompt = PROMPTS[section]
    with widelog.wide_event(op="generate_matters", section=section, model=model) as log:
        raw = await call_llm_with_prompt(
            prompt,
            prompt_inputs,
            model,
            response_model=schema(prompt),
            timeout=timeout,
            model_options=model_options,
        )
        # Keep rejected responses without ever using them as downstream state.
        atomic_write(folder / ".generation-records" / section / f"{uuid.uuid4().hex}.json", raw.encode())
        response = json.loads(raw)
        normalized = postprocess(section, response, prompt_inputs.previous, prompt_inputs.current_sections, folder.parent)
        selected = {section: select(section, normalized[section])}
        validate(section, selected)
        evidence = {"raw_response": response, "normalized_response": normalized, "model": model, "options": dict(model_options)}
        persist(
            folder,
            section,
            {
                f"{section}.json": (json.dumps(selected, ensure_ascii=False, indent=2) + "\n").encode(),
                f"{section}.evidence.json": (json.dumps(evidence, ensure_ascii=False, indent=2) + "\n").encode(),
            },
        )
        log.set(returned=len(normalized[section]), retained=len(selected[section]))
