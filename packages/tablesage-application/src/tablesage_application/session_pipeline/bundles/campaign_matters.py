"""Category contracts and isolated inputs for the Campaign Matters dependency graph."""

import json
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

OPEN_MATTER_KINDS = ["goals", "mysteries", "obligations", "brewing_troubles", "opportunities", "goal_impediments"]
PRESENT_KINDS = ["immediate_goals", "present_danger"]

WAVES = (
    ("present_matters", "obligations", "goals"),
    ("brewing_troubles", "goal_impediments"),
    ("opportunities",),
    ("mysteries", "new_assets"),
    ("revelations",),
    ("developments",),
)
SECTIONS = tuple(section for wave in WAVES for section in wave)
REVELATION_MATTER_KINDS = ("goals", "mysteries", "goal_impediments", "obligations", "opportunities")
ASSET_MATTER_KINDS = ("goals", "goal_impediments", "opportunities")

DEPENDENCIES = {
    "present_matters": (),
    "obligations": (),
    "brewing_troubles": ("goals",),
    "goal_impediments": ("goals",),
    "new_assets": ASSET_MATTER_KINDS,
    "goals": (),
    "mysteries": ("goals", "goal_impediments", "opportunities"),
    "opportunities": ("goals", "goal_impediments"),
    "revelations": REVELATION_MATTER_KINDS,
    "developments": ("new_assets", "revelations"),
}


@dataclass
class CampaignMattersPromptInputs:
    """One category's evidence, prior state, and explicitly declared current dependencies."""

    party: list[str]
    scenes: list[dict]
    section: str
    previous: Any = None
    current_sections: dict = field(default_factory=dict)
    previous_matters: dict | None = None

    def to_template_context(self) -> dict[str, object]:
        if set(self.current_sections) != set(DEPENDENCIES[self.section]):
            raise ValueError(f"Incorrect current inputs for {self.section}")
        if self.section not in ("revelations", "new_assets") and self.previous_matters is not None:
            raise ValueError("Only Revelations and New Assets receive prior matter context")
        if self.section == "revelations" and (self.previous_matters is None or set(self.previous_matters) != set(REVELATION_MATTER_KINDS)):
            raise ValueError("Revelations requires all five prior matter categories; use empty arrays for no prior state")
        if self.section == "opportunities" and self.previous is not None:
            validate_previous_opportunities(self.previous)
        if self.section == "new_assets":
            if self.previous_matters is None or set(self.previous_matters) != set(ASSET_MATTER_KINDS):
                raise ValueError("New Assets requires all three prior matter arrays; use empty arrays for no prior state")
            if not isinstance(self.previous, list):
                raise ValueError("New Assets requires a previous-assets array")
            validate_asset_matter_context(self.current_sections)
            validate_asset_matter_context(self.previous_matters)
        return {
            "section": self.section,
            "party": self.party,
            "scene_log": json.dumps([{"scene": n, **s} for n, s in enumerate(self.scenes, 1)], ensure_ascii=False, indent=2),
            "previous": json.dumps({self.section: self.previous}, ensure_ascii=False, indent=2),
            "current_sections": json.dumps(self.current_sections, ensure_ascii=False, indent=2),
            **(
                {key: json.dumps(self.current_sections[key], ensure_ascii=False, indent=2) for key in DEPENDENCIES["developments"]}
                if self.section == "developments"
                else {}
            ),
            "previous_assets": json.dumps(self.previous, ensure_ascii=False, indent=2),
            "previous_matters": (
                json.dumps(self.previous_matters, ensure_ascii=False, indent=2) if self.previous_matters is not None else None
            ),
        }


PERMANENT_GOAL_ID = re.compile(r"goal_([0-9]+)")
NEW_GOAL_ID = re.compile(r"goal_new_[0-9]+")


def normalize_goal_ids(goals: list[dict], previous: list[dict], *, high_water: int = 0) -> list[dict]:
    """Replace temporary `goal_new_*` IDs with permanent `goal_<n>` IDs, numbered in response order.

    Numbering starts after the highest permanent ID among the previous and returned goals, so IDs of
    concluded goals are never reused. References to temporary IDs are rewritten. Duplicate, unknown
    or dangling IDs, missing previous goals and circular parents are rejected rather than repaired.
    """
    previous_ids = []
    for goal in previous:
        if not isinstance(goal, dict) or not PERMANENT_GOAL_ID.fullmatch(goal.get("id", "")):
            raise ValueError("Previous Goals must be goal objects with permanent goal_<n> IDs; regenerate the previous session")
        previous_ids.append(goal["id"])
    ids = [goal["id"] for goal in goals]
    duplicates = sorted({goal_id for goal_id in ids if ids.count(goal_id) > 1})
    if duplicates:
        raise ValueError(f"Duplicate goal IDs: {', '.join(duplicates)}")
    unknown = [goal_id for goal_id in ids if not NEW_GOAL_ID.fullmatch(goal_id) and goal_id not in previous_ids]
    if unknown:
        raise ValueError(f"Goal IDs are neither previous goals nor goal_new_*: {', '.join(unknown)}")
    missing = [goal_id for goal_id in previous_ids if goal_id not in ids]
    if missing:
        raise ValueError(f"Previous goals missing from the response: {', '.join(missing)}")
    highest = max(
        (int(goal_id.rsplit("_", 1)[1]) for goal_id in previous_ids + ids if PERMANENT_GOAL_ID.fullmatch(goal_id)),
        default=0,
    )
    renamed = {
        goal_id: f"goal_{number}"
        for number, goal_id in enumerate((goal_id for goal_id in ids if NEW_GOAL_ID.fullmatch(goal_id)), max(high_water, highest) + 1)
    }

    def final(goal_id: str) -> str:
        return renamed.get(goal_id, goal_id)

    result = [
        {
            **goal,
            "id": final(goal["id"]),
            "parent_goal_id": goal["parent_goal_id"] and final(goal["parent_goal_id"]),
            "superseded_by_goal_id": goal["superseded_by_goal_id"] and final(goal["superseded_by_goal_id"]),
        }
        for goal in goals
    ]
    parents = {goal["id"]: goal["parent_goal_id"] for goal in result}
    for goal in result:
        for key in ("parent_goal_id", "superseded_by_goal_id"):
            if goal[key] is not None and goal[key] not in parents:
                raise ValueError(f"{goal['id']} {key} refers to an unknown goal: {goal[key]}")
        seen, current = {goal["id"]}, goal["parent_goal_id"]
        while current is not None:
            if current in seen:
                raise ValueError(f"Circular parent goals involving {goal['id']}")
            seen.add(current)
            current = parents[current]
    return result


def validate_goal_impediment_links(entries: list[dict], goals: list[dict], previous: Sequence[dict] = ()) -> list[dict]:
    """Reject unknown links and anticipated/active impediments linked to concluded goals."""
    by_id = {goal["id"]: goal for goal in goals}
    prior_ids = {goal_id for entry in previous for goal_id in entry["goal_ids"]}
    for entry in entries:
        for goal_id in entry["goal_ids"]:
            if goal_id not in by_id and not (entry["lifecycle"] in {"resolved", "obsolete"} and goal_id in prior_ids):
                raise ValueError(f"Goal Impediment refers to unknown goal: {goal_id}")
            if entry["lifecycle"] in {"anticipated", "active"} and by_id[goal_id]["lifecycle"] != "open":
                raise ValueError(f"Open Goal Impediment refers to concluded goal: {goal_id}")
    return entries


def validate_opportunity_links(
    entries: list[dict], goals: list[dict], goal_impediments: list[dict], previous: Sequence[dict] = ()
) -> list[dict]:
    """Validate available links strictly; preserve established references on ended entries."""
    by_id = {goal["id"]: goal for goal in goals}
    prior_links = {
        (entry["goal_id"], entry["goal_impediment_title"]) for entry in previous if isinstance(entry, dict) and "goal_id" in entry
    }
    prior_goal_ids = {goal_id for goal_id, _ in prior_links}
    for entry in entries:
        goal_id = entry["goal_id"]
        available = entry["lifecycle"] == "available"
        if goal_id not in by_id and (available or goal_id not in prior_goal_ids):
            raise ValueError(f"Opportunity refers to unknown goal: {goal_id}")
        if available and by_id[goal_id]["lifecycle"] != "open":
            raise ValueError(f"Available Opportunity refers to concluded goal: {goal_id}")
        title = entry["goal_impediment_title"]
        if title is None:
            continue
        if not available and (goal_id, title) in prior_links:
            continue
        matches = [
            impediment
            for impediment in goal_impediments
            if impediment["title"] == title
            and goal_id in impediment["goal_ids"]
            and (not available or impediment["lifecycle"] in {"anticipated", "active"})
        ]
        if len(matches) != 1:
            raise ValueError(
                f"Opportunity must link to exactly one {'anticipated or active ' if available else ''}Goal Impediment "
                f"for {goal_id}: {title}"
            )
    return entries


PERMANENT_OPPORTUNITY_ID = re.compile(r"opportunity_([0-9]+)")
NEW_OPPORTUNITY_ID = re.compile(r"opportunity_new_[0-9]+")


def normalize_opportunity_ids(entries: list[dict], previous: list[dict], *, high_water: int = 0) -> list[dict]:
    """Assign permanent IDs to new entries and rewrite parents, retaining established IDs.

    Historical entries without IDs remain valid prior context; their reassessed entries
    receive new IDs. Historical publications are never rewritten by this conversion.
    """
    validate_previous_opportunities(previous)
    previous_ids = [entry["id"] for entry in previous if isinstance(entry, dict) and "id" in entry]
    ids = [entry["id"] for entry in entries]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate Opportunity IDs")
    unknown = [value for value in ids if value not in previous_ids and not NEW_OPPORTUNITY_ID.fullmatch(value)]
    if unknown:
        raise ValueError(f"Opportunity IDs are neither previous IDs nor opportunity_new_*: {', '.join(unknown)}")
    missing = set(previous_ids) - set(ids)
    if missing:
        raise ValueError(f"Previous Opportunities missing from response: {', '.join(sorted(missing))}")
    highest = max((int(value.rsplit("_", 1)[1]) for value in previous_ids), default=0)
    renamed = {
        value: f"opportunity_{number}"
        for number, value in enumerate((value for value in ids if NEW_OPPORTUNITY_ID.fullmatch(value)), max(high_water, highest) + 1)
    }
    result = [
        {
            **entry,
            "id": renamed.get(entry["id"], entry["id"]),
            "parent_opportunity_id": renamed.get(entry["parent_opportunity_id"], entry["parent_opportunity_id"]),
        }
        for entry in entries
    ]
    validate_opportunity_hierarchy(result)
    return result


def validate_opportunity_hierarchy(entries: list[dict]) -> list[dict]:
    """Reject ambiguous identities, dangling parents, cycles and different-goal parent links."""
    by_id = {entry["id"]: entry for entry in entries}
    if len(by_id) != len(entries):
        raise ValueError("Duplicate Opportunity IDs")
    for entry in entries:
        parent = entry["parent_opportunity_id"]
        if parent is not None:
            if parent not in by_id:
                raise ValueError(f"{entry['id']} refers to unknown parent Opportunity: {parent}")
            if by_id[parent]["goal_id"] != entry["goal_id"]:
                raise ValueError(f"{entry['id']} and parent {parent} must link to the same goal")
        seen = {entry["id"]}
        while parent is not None:
            if parent in seen:
                raise ValueError(f"Circular parent Opportunities involving {entry['id']}")
            seen.add(parent)
            if parent not in by_id:
                raise ValueError(f"Unknown parent Opportunity: {parent}")
            parent = by_id[parent]["parent_opportunity_id"]
    return entries


def validate_previous_opportunities(previous: list[dict]) -> list[dict]:
    """Check identified prior entries before rendering, without inventing legacy IDs or parents."""
    if not isinstance(previous, list):
        raise ValueError("Previous Opportunities must be a list")
    identified = [entry for entry in previous if isinstance(entry, dict) and "id" in entry]
    for entry in identified:
        if not isinstance(entry["id"], str) or not PERMANENT_OPPORTUNITY_ID.fullmatch(entry["id"]):
            raise ValueError(f"Invalid previous Opportunity ID: {entry['id']}")
    validate_opportunity_hierarchy(identified)
    return previous


MYSTERY_DIMENSIONS = ("grounding", "investigative_depth", "narrative_payoff", "investigative_potential")


def filter_mysteries(entries: list[dict]) -> list[dict]:
    """Standalone saving policy: exclude low/trivial ranks, ended and closed-ended entries.

    Call only after complete response validation. Require medium/high ranks in
    every dimension. Preserve order and all fields.
    """
    return [
        entry
        for entry in entries
        if entry["lifecycle"] == "open"
        and entry["question_type"] == "open_ended"
        and all(entry[key]["rank"] in {"medium", "high"} for key in MYSTERY_DIMENSIONS)
    ]


PERMANENT_IMPEDIMENT_ID = re.compile(r"impediment_([0-9]+)")
NEW_IMPEDIMENT_ID = re.compile(r"impediment_new_[0-9]+")


def prepare_previous_impediments(entries: list[dict]) -> list[dict]:
    """Assign IDs to id-less legacy prior entries on read, without rewriting saved evidence."""
    ids = [e["id"] for e in entries if "id" in e]
    if any(not isinstance(value, str) or not PERMANENT_IMPEDIMENT_ID.fullmatch(value) for value in ids):
        raise ValueError("Previous Goal Impediments require permanent impediment_<n> IDs")
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate prior Goal Impediment IDs")
    highest = max((int(value.rsplit("_", 1)[1]) for value in ids), default=0)
    result = []
    for entry in entries:
        if "id" not in entry:
            highest += 1
            entry = {**entry, "id": f"impediment_{highest}"}
        result.append(entry)
    return result


def normalize_impediment_ids(entries: list[dict], previous: list[dict], *, high_water: int = 0) -> list[dict]:
    """Preserve supplied identities and assign permanent IDs to validated new entries."""
    previous = prepare_previous_impediments(previous)
    prior_ids = {e["id"] for e in previous}
    ids = [e["id"] for e in entries]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate Goal Impediment IDs")
    if prior_ids - set(ids):
        raise ValueError("Previous Goal Impediments missing from response: " + ", ".join(sorted(prior_ids - set(ids))))
    if any(value not in prior_ids and not NEW_IMPEDIMENT_ID.fullmatch(value) for value in ids):
        raise ValueError("Goal Impediment IDs must be supplied prior IDs or new impediment_new_<n> IDs")
    highest = max((int(value.rsplit("_", 1)[1]) for value in prior_ids), default=0)
    renamed = {
        value: f"impediment_{n}" for n, value in enumerate((v for v in ids if NEW_IMPEDIMENT_ID.fullmatch(v)), max(high_water, highest) + 1)
    }
    return [{**e, "id": renamed.get(e["id"], e["id"])} for e in entries]


def validate_asset_matter_context(matters: dict[str, list[dict]]) -> None:
    """Require identifiable context without inventing IDs or dropping ended entries."""
    states = {
        "goals": {"open", "resolved", "obsolete", "abandoned", "superseded"},
        "goal_impediments": {"anticipated", "active", "resolved", "obsolete"},
        "opportunities": {"available", "captured", "lost", "obsolete"},
    }
    prefixes = {"goals": "goal", "goal_impediments": "impediment", "opportunities": "opportunity"}
    if set(matters) != set(ASSET_MATTER_KINDS):
        raise ValueError("New Assets matter context requires goals, goal_impediments and opportunities")
    for key, rows in matters.items():
        if not isinstance(rows, list):
            raise ValueError(f"New Assets {key} context must be an array")
        ids = []
        for row in rows:
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("id"), str)
                or not re.fullmatch(prefixes[key] + r"_[0-9]+", row["id"])
                or row.get("lifecycle") not in states[key]
            ):
                raise ValueError(f"New Assets {key} requires structured entries with permanent IDs and lifecycle")
            ids.append(row["id"])
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate New Assets context IDs in {key}")


def validate_new_asset_links(entries: list[dict], goals: list[dict], goal_impediments: list[dict], opportunities: list[dict]) -> list[dict]:
    """Validate current target state and same-goal relationships; never filter assets."""
    context = dict(goals=goals, goal_impediments=goal_impediments, opportunities=opportunities)
    validate_asset_matter_context(context)
    targets = {key: {row["id"]: row for row in rows} for key, rows in context.items()}
    for entry in entries:
        goal_id = entry["goal_id"]
        goal = targets["goals"].get(goal_id)
        if goal is None or goal["lifecycle"] != "open":
            raise ValueError(f"New Asset goal_id must identify a current open Goal: {goal_id}")
        if "impediment_id" in entry:
            impediment = targets["goal_impediments"].get(entry["impediment_id"])
            if impediment is None or impediment["lifecycle"] != "active" or goal_id not in impediment["goal_ids"]:
                raise ValueError(f"New Asset impediment_id must identify an active Impediment for {goal_id}")
        if "opportunity_id" in entry:
            opportunity = targets["opportunities"].get(entry["opportunity_id"])
            if opportunity is None or opportunity["lifecycle"] != "available" or opportunity["goal_id"] != goal_id:
                raise ValueError(f"New Asset opportunity_id must identify an available Opportunity for {goal_id}")
    return entries


def validate_mystery_links(entries: list[dict], goals: list[dict], goal_impediments: list[dict], opportunities: list[dict]) -> list[dict]:
    """Every optional relationship must point to exactly one supplied current target."""
    for key, rows in (("goal_id", goals), ("impediment_id", goal_impediments), ("opportunity_id", opportunities)):
        ids = [row["id"] for row in rows]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Ambiguous duplicate current target IDs for {key}")
        for entry in entries:
            if key in entry and entry[key] not in ids:
                raise ValueError(f"Mystery {key} refers to unknown current target: {entry[key]}")
    return entries
