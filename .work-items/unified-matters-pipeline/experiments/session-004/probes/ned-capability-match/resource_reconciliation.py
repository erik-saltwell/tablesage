"""Validate explicit publication equivalence without changing stored source facts."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def fingerprint(candidates: list[dict[str, Any]]) -> str:
    return hashlib.sha256(json.dumps(candidates, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def validate_reconciliation(data: dict[str, Any], candidates: list[dict[str, Any]]) -> None:
    """Reject stale mappings, overlapping groups and incompatible resources.

    Semantic equivalence and preservation of useful terms are model judgments;
    the source records, mapping reasons and combined wording remain reviewable.
    """
    if data.get("input_fingerprint") != fingerprint(candidates):
        raise ValueError("Resource reconciliation is stale; rerun chain --from 3")
    facts = {f["id"]: f for f in candidates}
    seen: set[str] = set()
    for group in data["groups"]:
        members = group["members"]
        if len(members) < 2 or len(set(members)) != len(members):
            raise ValueError("Equivalence requires at least two distinct facts")
        if group["canonical"] not in members:
            raise ValueError("Canonical fact must be a member")
        if any(m not in facts or m in seen for m in members):
            raise ValueError("Unknown, ineligible or overlapping resource member")
        if not group["basis"].strip() or not group["text"].strip():
            raise ValueError("Resource resolution needs evidence basis and complete text")
        signatures = {
            (f["classification"]["form"], f["classification"]["helps_thread"],
             f["certainty"], f["uncertain_reason"])
            for f in (facts[m] for m in members)
        }
        if len(signatures) != 1:
            raise ValueError("Do not merge distinct uses or uncertainty")
        evidence = {e for m in members for e in facts[m]["evidence"]}
        if set(group["evidence"]) != evidence:
            raise ValueError("Combined resource must preserve every member's evidence")
        seen.update(members)
