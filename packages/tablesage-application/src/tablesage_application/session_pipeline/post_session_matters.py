"""Lossless, provider-free assembly of a Session's filtered Matters publications."""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from importlib.resources import files
from pathlib import Path
from typing import Any

import jsonschema

from . import campaign_matters, narrative

HISTORICAL_SECTIONS = ("developments", "revelations", "new_assets")
OPEN_SECTIONS = ("goals", "goal_impediments", "opportunities", "mysteries", "obligations", "brewing_troubles")
INPUT_SECTIONS = (*HISTORICAL_SECTIONS, "present_matters", *OPEN_SECTIONS)
SCHEMA_PATH = Path(__file__).with_suffix(".schema.json")
FILENAME = "post_session_matters.json"


def _scope_references(value: Any, section: str) -> Any:
    """Namespace source definitions so each category can retain its own Text/rating types."""
    if isinstance(value, list):
        return [_scope_references(item, section) for item in value]
    if isinstance(value, dict):
        result = {key: _scope_references(item, section) for key, item in value.items()}
        if "$ref" in result:
            reference = result["$ref"]
            if not reference.startswith("#/$defs/"):
                raise ValueError(f"Unsupported category schema reference: {reference}")
            result["$ref"] = reference.replace("#/$defs/", f"#/$defs/{section}_", 1)
        return result
    return value


def schema() -> dict[str, Any]:
    """Build a complete standalone schema from the envelope and authoritative category schemas."""
    resource = files(__package__).joinpath(SCHEMA_PATH.name)
    result = json.loads(resource.read_text("utf-8"))
    definitions = result.setdefault("$defs", {})
    for section in INPUT_SECTIONS:
        source = narrative.schema(campaign_matters.PROMPTS[section])
        definitions[section] = _scope_references(source["properties"][section], section)
        for name, definition in source.get("$defs", {}).items():
            definitions[f"{section}_{name}"] = _scope_references(definition, section)
    return result


def validate(document: dict[str, Any]) -> None:
    jsonschema.Draft202012Validator(schema(), format_checker=jsonschema.FormatChecker()).validate(document)
    for section, (prefix, _) in campaign_matters.NORMALIZERS.items():
        entries = document["open_matters"][section]
        ids = [entry["id"] for entry in entries]
        if len(set(ids)) != len(ids) or any(not re.fullmatch(prefix + r"_[0-9]+", value) for value in ids):
            raise ValueError(f"Post-Session Matters {section} requires unique permanent IDs.")


def assemble(session_id: uuid.UUID, sections: dict[str, Any]) -> dict[str, Any]:
    if set(sections) != set(INPUT_SECTIONS):
        raise ValueError("Post-Session Matters requires exactly all ten current Matters publications.")
    for section, content in sections.items():
        campaign_matters.validate(section, {section: content})
    document = {
        "version": 1,
        "session_id": str(session_id),
        "historical_matters": {section: deepcopy(sections[section]) for section in HISTORICAL_SECTIONS},
        "present_matters": deepcopy(sections["present_matters"]),
        "open_matters": {section: deepcopy(sections[section]) for section in OPEN_SECTIONS},
    }
    validate(document)
    return document


def persist(folder: Path, document: dict[str, Any]) -> None:
    validate(document)
    narrative.persist(folder, "post_session_matters", {FILENAME: (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode()})


def load(folder: Path) -> dict[str, Any]:
    if (folder / narrative.marker_name("post_session_matters")).exists():
        raise ValueError("Post-Session Matters replacement was interrupted; regenerate it first.")
    document = json.loads((folder / FILENAME).read_text())
    validate(document)
    return document
