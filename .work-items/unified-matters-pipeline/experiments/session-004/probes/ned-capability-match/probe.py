"""Pass 10 runner: pass 9 with prompts rewritten from the general patterns (PREF-045 to PREF-052) and code-side filtering of low standalone beats (PREF-014).

Experiment code, not the pipeline. Reads the deployment workspace read-only and writes only under this folder.
Reuses pass 2's runner for inputs and steps 1 to 3, pointed at this folder's prompts, runs and seeds. Run with the
repository's virtual environment, in order:

    .venv/bin/python <this folder>/run10.py step1 --session 001 --out s001-step1
    .venv/bin/python <this folder>/run10.py step2 --session 001 --scenes s001-step1 --out s001-step2
    .venv/bin/python <this folder>/run10.py step2c --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step2c
    .venv/bin/python <this folder>/run10.py step3 --session 001 --scenes s001-step1 --threads s001-step2 --out s001-step3
    .venv/bin/python <this folder>/run10.py check --session 001 --run s001-step3
    # chain defaults to --from 3: resource reconciliation, then stopping/selection/writing.
    .venv/bin/python <this folder>/run10.py chain s001
    .venv/bin/python <this folder>/run10.py seed s001 002
    ... then the same for 002 with s002-* names.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

import jinja2
import jsonschema
from tablesage_tools.llm import call_llm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from historical_coverage import check_history, historical_inputs, select_history, standalone_split  # noqa: E402
from resource_reconciliation import fingerprint, validate_reconciliation  # noqa: E402

sys.path.insert(0, str(HERE.parent.parent / "pass-2"))
import run as r2  # noqa: E402

# Point pass 2's runner at this folder.
r2.HERE = HERE
r2.RUNS = HERE / "runs"
r2.PROMPTS = HERE / "prompts"
r2.STEP_FOLDERS["step2c"] = "step2c_changes"
r2.EFFORT["step2c"] = "medium"

RUNS = r2.RUNS
PROMPTS = r2.PROMPTS
EFFORT = {"step3r": "high", "step4": "medium", "step6": "high", "step8": "high"}

# Chains: (Session, scenes run, threads run, changes run, facts run)
CHAINS = {
    f"s{label}": (label, f"s{label}-step1", f"s{label}-step2", f"s{label}-step2c", f"s{label}-step3")
    for label in ("001", "002", "003", "004")
}


def use_session(label: str) -> None:
    """Use this pass's chained seed for every Session, including 004.

    Pass 2's original helper special-cases 004 to a hand-made seed. That is
    inappropriate for a fresh four-Session chain. Preserve ID high-water marks
    even when the highest-numbered prior facts or threads have ended.
    """
    campaign = r2.WORKSPACE / "campaigns" / "Brandonsford"
    r2.SESSION, r2.PREVIOUS = campaign / label, campaign / f"{int(label) - 1:03d}"
    r2.SESSION_LABEL, r2.SEED = label, HERE / "seeds" / f"{label}.json"
    state = r2.seed()
    r2.FIRST_NEW_FACT = max(state.get("fact_high_water", 0),
                            max((int(f["id"].split("_")[1]) for f in state["facts"]), default=0)) + 1
    r2.FIRST_NEW_THREAD = max(state.get("thread_high_water", 0),
                              max((int(t["id"].split("_")[1]) for t in state["threads"]), default=0)) + 1


r2.use_session = use_session


def prior_facts_for(state: dict[str, Any], thread_id: str) -> list[dict[str, Any]]:
    """Pass 2's helper strips classifications; keep pass 10 continuity evidence."""
    return [f for f in state["facts"] if f["thread"] == thread_id]


r2.prior_facts_for = prior_facts_for

# Step 5: approved EX-070–EX-078 refinements; Last session threshold unchanged.
# Open headings: the filters the user set for the per-matter prompts (session_pipeline/campaign_matters.py), mapped to
# fact kinds. "Last session...": PROVISIONAL, the agent's threshold on the step 2c ratings; the user has set none.
SELECTION_VERSION = 11
RULES = {
    "last_session": "standalone beats rated low importance are dropped by code before assessment; threads/standalone events retain medium-or-high impact AND lasting consequence; an otherwise unrepresented encounter may also qualify with medium-or-high historical value, regardless of enduring consequence; no scene or character quota",
    "want": "ongoing pursuit; adventure before side, then importance and actionability; serves_thread is null (an end, not a means) and significance is not incidental (Goals: parent_goal_id null, significance not incidental)",
    "owe": "definite_end; commitment_type is not general_agreement; stake, burden and consequence are not trivial (Obligations filter)",
    "blocked_by": "active, persists beyond the scene, not covered by immediate danger, and blocks a thread holding a shown want, debt or opening",
    "could_use": "openings only; supported enabling action toward a shown want/debt; direct role; equivalent offers/plans use validated canonical fact references; assets stay in state/history",
    "unknown": "question_type open_ended and all four dimensions medium or high (Mysteries filter)",
    "threat": "harm_origin is not party and no evaluation is low (Brewing Troubles filter); not covered by an immediate danger",
    "all": "never possibly moot facts; no caps; no assets in open matters",
}
HEADINGS = [
    ("want", "Your goals"),
    ("blocked_by", "Standing in your way"),
    ("could_use", "What could help"),
    ("unknown", "Still unanswered"),
    ("owe", "Promises and debts"),
    ("threat", "Meanwhile"),
]
RANK = {"high": 0, "medium": 1, "low": 2}
GOOD = {"medium", "high"}
MYSTERY_DIMENSIONS = ("grounding", "investigative_depth", "narrative_payoff", "investigative_potential")
THREAT_EVALUATIONS = ("negative_outcome_clarity", "outcome_severity", "evidentiary_strength", "evidence_of_progression", "preventability")
CLASS_KEYS = {
    "want": {"serves_thread", "significance"},
    "owe": {"commitment_type", "stake_basis", "stake", "burden", "consequence"},
    "blocked_by": {"blocks_thread", "in_effect", "scope_basis", "persists_beyond_scene"},
    "could_use": {"form", "opening_basis", "opening_type", "helps_thread", "role", "support_basis", "goal_support", "action_basis", "action_supported", "acquired_by_acting_on_opening"},
    "unknown": set(MYSTERY_DIMENSIONS) | {"question_type"},
    "threat": set(THREAT_EVALUATIONS) | {"harm_origin"},
}
RECAP_THREAD_WORDS = 35
RATED = set(MYSTERY_DIMENSIONS) | set(THREAT_EVALUATIONS)


def kind_class(f: dict[str, Any]) -> dict[str, Any]:
    """The flat classification (every kind's fields, nullable) reduced to the fact's own kind, rated fields nested."""
    flat = {k: (None if k in {"serves_thread", "blocks_thread", "helps_thread"} and v == "" else v)
            for k, v in f["classification"].items()}
    return {k: ({"justification": flat.get(f"{k}_justification"), "rank": flat.get(k)} if k in RATED else flat.get(k)) for k in CLASS_KEYS[f["kind"]]}
RECAP_CLOSING_WORDS = 50


# ---------------------------------------------------------------- LLM


def ask(step: str, variables: dict[str, Any], out: Path) -> dict[str, Any]:
    folder = PROMPTS / {"step3r": "step3r_resources", "step4": "step4_stopping", "step6": "step6_writing", "step8": "step8_recap"}[step]
    system = (folder / "system.md").read_text()
    user = jinja2.Template((folder / "template.j2").read_text(), undefined=jinja2.StrictUndefined).render(**variables)
    schema = json.loads((folder / "schema.json").read_text())
    records = out / "records"
    records.mkdir(parents=True, exist_ok=True)
    (records / f"{step}.user.md").write_text(user)
    target = out / "prompts" / folder.name
    target.mkdir(parents=True, exist_ok=True)
    for f in folder.iterdir():
        (target / f.name).write_text(f.read_text())
    started = time.monotonic()
    raw = asyncio.run(
        call_llm(
            system,
            user,
            r2.MODEL,
            response_format=schema,
            timeout=r2.TIMEOUT,
            prompt_name=f"unified_pass10_{step}",
            model_options={"reasoning_effort": EFFORT[step], "drop_params": False},
        )
    )
    (records / f"{step}.raw.json").write_text(raw)
    data = json.loads(raw)
    jsonschema.Draft202012Validator(schema).validate(data)
    print(f"  {step}: {time.monotonic() - started:.0f}s", flush=True)
    return data


def session_date(label: str) -> str | None:
    db = sqlite3.connect(f"file:{r2.WORKSPACE / '.tablesage' / 'tablesage.db'}?mode=ro", uri=True)
    row = db.execute(
        "SELECT s.session_date FROM session s JOIN campaign c ON c.id = s.campaign_id WHERE c.name = 'Brandonsford' AND s.sequence_number = ?",
        (int(label),),
    ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------- step 2c


async def step2c(out: Path, scenes_source: str, threads_source: str) -> None:
    scenes = r2.load_scenes(scenes_source)
    threads = r2.load_threads(threads_source)
    items = historical_inputs(scenes, threads)
    data = await r2.ask("step2c", {
        "party": r2.party(), "items": json.dumps(items, indent=1, ensure_ascii=False),
        "scenes": json.dumps(scenes["scenes"], indent=1, ensure_ascii=False),
    }, out, "step2c")
    problems = check_history(data, scenes, threads)
    (out / "changes.json").write_text(json.dumps({"scenes": scenes_source, "threads": threads_source, "items": data["items"], "problems": problems}, indent=1, ensure_ascii=False))
    if problems:
        raise ValueError("Invalid historical coverage: " + "; ".join(problems))



# ---------------------------------------------------------------- checks


def check_classification(run: str) -> list[str]:
    data = json.loads((RUNS / run / "thread_facts.json").read_text())
    threads = {t["id"] for t in r2.load_threads(data["threads"])["threads"]}
    problems = []
    spec = json.loads((HERE / "classification_schema.json").read_text())
    shared = json.loads((RUNS / data["threads"] / "shared_subjects.json").read_text())["shared_subjects"]
    subjects = {sub["subject"]: sub for sub in shared}
    problems.extend(check_continuity(data["facts"], r2.seed()["facts"]))
    if len(subjects) != len(shared):
        problems.append("shared resource subjects must have unique labels")
    for f in data["facts"]:
        if "resource_subject" not in f or not isinstance(f["resource_subject"], str):
            problems.append(f"{f['id']}: missing string resource_subject")
        elif f["resource_subject"]:
            subject = subjects.get(f["resource_subject"])
            if f["kind"] != "could_use" or subject is None:
                problems.append(f"{f['id']}: invalid shared resource subject")
            elif f["thread"] not in {subject["home"], *subject["other_threads"]}:
                problems.append(f"{f['id']}: shared resource subject does not bear on this thread")
            elif f["thread"] != subject["home"] and f["about_thread"] != subject["home"]:
                problems.append(f"{f['id']}: resource pointer does not name its home thread")
        c = kind_class(f)
        own = set(c) | {f"{k}_justification" for k in c if k in RATED}
        stray = [k for k, v in f["classification"].items() if k not in own and v not in (None, "", False)]
        if stray:
            problems.append(f"{f['id']} ({f['thread']}): {f['kind']} has other kinds' fields set: {stray}")
        schema = {"$defs": spec["$defs"], "$ref": f"#/$defs/{spec['kinds'][f['kind']]}"}
        errors = [e.message for e in jsonschema.Draft202012Validator(schema).iter_errors(c)]
        if errors:
            problems.append(f"{f['id']} ({f['thread']}): {f['kind']} classification invalid: {errors[:3]}")
            continue
        if set(c) != CLASS_KEYS[f["kind"]]:
            problems.append(f"{f['id']} ({f['thread']}): {f['kind']} with classification keys {sorted(c)}")
            continue
        for key in ("serves_thread", "blocks_thread", "helps_thread"):
            if c.get(key) and c[key] not in threads:
                problems.append(f"{f['id']}: unknown {key} {c[key]}")
        if c.get("serves_thread") == f["thread"]:
            problems.append(f"{f['id']}: serves its own thread")
    return problems


def check_continuity(facts: list[dict[str, Any]], prior: list[dict[str, Any]]) -> list[str]:
    """Carried substantive judgments cannot drift behind unchanged text."""
    previous = {f["id"]: f for f in prior}
    problems = []
    stable_fields = {
        "want": ("serves_thread", "significance"),
        "owe": ("commitment_type", "stake", "burden", "consequence"),
    }
    for fact in facts:
        basis = fact.get("classification_change_basis")
        if not isinstance(basis, str):
            problems.append(f"{fact['id']}: missing classification_change_basis")
            continue
        old = previous.get(fact["id"])
        if old is None or "classification" not in old or fact["state"] == "ended":
            continue
        changed = fact["kind"] != old["kind"] or any(
            fact["classification"].get(k) != old["classification"].get(k)
            for k in stable_fields.get(fact["kind"], ())
        )
        if changed and (fact["change"] != "updated" or not basis.strip()):
            problems.append(f"{fact['id']}: substantive reclassification needs updated and an evidence basis")
    return problems


# ---------------------------------------------------------------- step 4


def step4(out: Path, scenes: dict[str, Any], threads: dict[str, Any], facts: list[dict[str, Any]]) -> dict[str, Any]:
    last = scenes["scenes"][-1]
    start = min(i for b in last["beats"] for i in b["ledger"])
    entries = r2.ledger()["utterances"]
    tail = "\n".join(json.dumps({"i": i, **entries[i]}, ensure_ascii=False) for i in range(start, len(entries)))
    names = {t["id"]: t["name"] for t in threads["threads"]}
    threats = [{"id": f["id"], "thread": names[f["thread"]], "text": f["text"], "kind": f["kind"]} for f in facts if f["state"] == "open" and f["kind"] in ("threat", "blocked_by")]
    final_scene = {"location": last["location"], "people": last["people"], "beats": [{"kind": b["kind"], "text": b["text"]} for b in last["beats"]]}
    last_seen: dict[str, list[str]] = {}
    for pc in r2.party():
        scene = next((s for s in reversed(scenes["scenes"]) if pc in s["people"].get("party", [])), None)
        if scene:
            last_seen.setdefault(scene["id"], []).append(pc)
    party_last = [
        {"location": s["location"], "people": s["people"], "last_seen_here": last_seen[s["id"]], "beats": [{"kind": b["kind"], "text": b["text"]} for b in s["beats"]]}
        for s in scenes["scenes"]
        if s["id"] in last_seen
    ]
    data = ask(
        "step4",
        {
            "attendees": r2.attendees(),
            "starting_situation": r2.starting_situation(),
            "final_scene": json.dumps(final_scene, indent=1, ensure_ascii=False),
            "party_last_scenes": json.dumps(party_last, indent=1, ensure_ascii=False),
            "ledger_tail": tail,
            "open_danger_facts": json.dumps(threats, indent=1, ensure_ascii=False),
            "scenes": json.dumps(scenes["scenes"], indent=1, ensure_ascii=False),
        },
        out,
    )
    known_beats = {b["id"] for scene in scenes["scenes"] for b in scene["beats"]}
    intention = data["immediate_intention"]
    if intention is not None and not set(intention["evidence"]) <= known_beats:
        raise ValueError("Immediate intention cites unknown beats")
    known = {f["id"] for f in threats}
    for d in data["immediate_danger"]:
        bad = [x for x in d["covers_facts"] if x not in known]
        if bad:
            raise ValueError(f"Danger covers unknown danger facts: {bad}")
    (out / "stopping_situation.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


def resource_candidates(threads: dict[str, Any], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Only independently eligible openings can replace one another."""
    tmap = {t["id"]: t for t in threads["threads"]}
    goals = {f["thread"] for f in facts if f["state"] == "open" and f["kind"] in ("want", "owe")
             and decide(f, set(), set(), tmap)[0]}
    return [f for f in facts if f["state"] == "open" and f["kind"] == "could_use"
            and decide(f, set(), goals, tmap)[0]]


def step3r(out: Path, scenes: dict[str, Any], candidates: list[dict[str, Any]]) -> dict[str, Any]:
    data = ask("step3r", {
        "facts": json.dumps(candidates, indent=1, ensure_ascii=False),
        "scenes": json.dumps(scenes["scenes"], indent=1, ensure_ascii=False),
    }, out) if len(candidates) > 1 else {"groups": []}
    data["input_fingerprint"] = fingerprint(candidates)
    validate_reconciliation(data, candidates)
    (out / "resource_reconciliation.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


# ---------------------------------------------------------------- step 5


def ancestors(tid: str, tmap: dict[str, dict[str, Any]]) -> list[str]:
    chain, seen = [], set()
    while tid and tid in tmap and tid not in seen:
        seen.add(tid)
        chain.append(tid)
        tid = tmap[tid]["parent"]
    return chain


def decide(f: dict[str, Any], covered: set[str], goal_threads: set[str], tmap: dict[str, dict[str, Any]]) -> tuple[bool, str]:
    """Return (shown, reason). The reason names the field that decided."""
    c = kind_class(f)
    k = f["kind"]
    if f["possibly_moot"]:
        return False, f"possibly moot: {f['possibly_moot']}"
    if k == "want":
        if c["serves_thread"]:
            return False, f"means, not an end: serves {c['serves_thread']} ({tmap.get(c['serves_thread'], {}).get('name', '?')})"
        if c["significance"] == "incidental":
            return False, "significance incidental"
        return True, f"end; {c['significance']}"
    if k == "owe":
        if f["definite_end"] is False:
            return False, "no definite end"
        if c["commitment_type"] == "general_agreement":
            return False, "commitment_type general_agreement"
        trivial = [x for x in ("stake", "burden", "consequence") if c[x] == "trivial"]
        if trivial:
            return False, f"{', '.join(trivial)} trivial" + (f" (stake basis: {c['stake_basis']})" if "stake" in trivial else "")
        return True, f"{c['commitment_type']}; stake {c['stake']}, burden {c['burden']}, consequence {c['consequence']}"
    if k == "blocked_by":
        if f["id"] in covered:
            return False, "covered by an immediate danger"
        if c["in_effect"] != "active":
            return False, "anticipated, not yet in effect"
        if c["persists_beyond_scene"] is not True:
            return False, "scene-local obstruction; not a lasting impediment"
        if c["blocks_thread"] not in goal_threads:
            return False, "blocks no shown live want, debt or opening"
        return True, f"active beyond scene; blocks {c['blocks_thread']}"
    if k == "could_use":
        if c["form"] == "asset":
            return False, "asset retained in campaign state, not an open matter"
        if c["opening_type"] != "enabling":
            return False, f"not an extra enabling opening: {c['opening_type']} ({c['opening_basis']})"
        helps = c["helps_thread"]
        if not helps:
            return False, "helps no want or debt"
        if not set(ancestors(helps, tmap)) & goal_threads:
            return False, f"helps {helps} ({tmap.get(helps, {}).get('name', '?')}), which has no shown goal or debt"
        if c["role"] == "step":
            return False, "a step toward another opening"
        if c["form"] == "opening" and c["action_supported"] != "yes":
            return False, f"no supported action and concrete advantage ({c['action_basis']})"
        return True, f"{c['form']}; helps {helps}; support {c['goal_support']}"
    if k == "unknown":
        low = [d for d in MYSTERY_DIMENSIONS if c[d]["rank"] not in GOOD]
        if c["question_type"] != "open_ended" or low:
            parts = (["closed_ended"] if c["question_type"] != "open_ended" else []) + [f"{d} {c[d]['rank']}" for d in low]
            return False, "; ".join(parts)
        return True, "open_ended; " + ", ".join(f"{d} {c[d]['rank']}" for d in MYSTERY_DIMENSIONS)
    if k == "threat":
        if f["id"] in covered:
            return False, "covered by an immediate danger"
        if c["harm_origin"] == "party":
            return False, "harm_origin party"
        low = [e for e in THREAT_EVALUATIONS if c[e]["rank"] == "low"]
        if low:
            return False, "; ".join(f"{e} low" for e in low)
        return True, f"{c['harm_origin']}; " + ", ".join(f"{e} {c[e]['rank']}" for e in THREAT_EVALUATIONS)
    raise ValueError(k)


def select(scenes: dict[str, Any], threads: dict[str, Any], changes: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any], reconciliation: dict[str, Any]) -> dict[str, Any]:
    tmap = {t["id"]: t for t in threads["threads"]}
    thread_order = {t["id"]: i for i, t in enumerate(threads["threads"])}
    candidates = select_history(changes, scenes, threads)
    covered = {x for d in stopping["immediate_danger"] for x in d["covers_facts"]}
    open_facts = [f for f in facts if f["state"] == "open"]
    decisions: dict[str, tuple[bool, str]] = {}
    for f in open_facts:
        if f["kind"] in ("want", "owe"):
            decisions[f["id"]] = decide(f, covered, set(), tmap)
    goal_threads = {f["thread"] for f in open_facts if f["kind"] in ("want", "owe") and decisions[f["id"]][0]}
    # Assess eligibility first. A hidden home is never a replacement for a shown pointer.
    for f in open_facts:
        if f["id"] not in decisions and f["kind"] != "blocked_by":
            decisions[f["id"]] = decide(f, covered, goal_threads, tmap)
    resources = [f for f in open_facts if f["kind"] == "could_use"]
    resource_options = resource_candidates(threads, facts)
    validate_reconciliation(reconciliation, resource_options)
    resource_texts = {}
    for group in reconciliation["groups"]:
        canonical = group["canonical"]
        resource_texts[canonical] = group["text"]
        for member in group["members"]:
            if member != canonical:
                decisions[member] = (False, f"equivalent offer/plan shown as {canonical}: {group['basis']}")
    # An available opening may itself be obstructed. Use final resource decisions.
    live_threads = goal_threads | {
        f["thread"] for f in resources
        if kind_class(f)["form"] == "opening" and decisions[f["id"]][0]
    }
    for f in open_facts:
        if f["kind"] == "blocked_by":
            decisions[f["id"]] = decide(f, covered, live_threads, tmap)
    sections = []
    for kind, heading in HEADINGS:
        items = sorted(
            (f for f in open_facts if f["kind"] == kind and decisions[f["id"]][0]),
            key=lambda f: (({"adventure": 0, "side": 1, "incidental": 2}[kind_class(f)["significance"]] if kind == "want" else 0), RANK[f["importance"]], RANK[f["actionability"]], thread_order[f["thread"]], int(f["id"].split("_")[1])),
        )
        if items:
            sections.append({"heading": heading, "kind": kind, "facts": [f["id"] for f in items]})
    return {
        "version": SELECTION_VERSION,
        "resource_texts": resource_texts,
        "resource_reconciliation": reconciliation,
        "rules": RULES,
        "last_session": [{"id": c["id"], "kind": c["kind"], "first": c["first"], "focus_beats": c["focus_beats"]} for c in candidates if c["shown"]],
        "last_session_candidates": candidates,
        "dropped_standalone": standalone_split(scenes, threads)[1],
        "open": sections,
        "decisions": {fid: {"shown": s, "reason": r} for fid, (s, r) in decisions.items()},
    }


# ---------------------------------------------------------------- step 6


def step6(out: Path, scenes: dict[str, Any], threads: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any], selection: dict[str, Any]) -> dict[str, Any]:
    beats = {b["id"]: b for s in scenes["scenes"] for b in s["beats"]}
    tmap = {t["id"]: t for t in threads["threads"]}
    fmap = {f["id"]: f for f in facts}
    last = []
    for item in selection["last_session"]:
        if item["kind"] == "thread":
            t = tmap[item["id"]]
            last.append({"id": t["id"], "kind": "thread", "name": t["name"], "status": t["status"], "beats": [beats[b]["text"] for b in t["touched_by"]]})
        elif item["kind"] == "encounter":
            scene = next(s for s in scenes["scenes"] if s["id"] == item["id"])
            last.append({"id": item["id"], "kind": "encounter", "location": scene["location"],
                         "people": scene["people"], "beats": [beats[b]["text"] for b in item["focus_beats"]]})
        else:
            last.append({"id": item["id"], "kind": "beat", "text": beats[item["id"]]["text"]})
    sections = []
    for sec in selection["open"]:
        items = []
        for fid in sec["facts"]:
            f = fmap[fid]
            item = {"id": fid, "text": selection["resource_texts"].get(fid, f["text"]), "thread": tmap[f["thread"]]["name"]}
            if f["learned_this_session"]:
                item["learned_this_session"] = True
            if f["certainty"] == "uncertain":
                item["certainty"] = f"uncertain: {f['uncertain_reason']}"
            if f["kind"] == "could_use":
                item["form"] = f["classification"]["form"]
            items.append(item)
        sections.append({"heading": sec["heading"], "items": items})
    cues = [{"id": s["id"], "location": s["location"], "cue": s["cue"]} for s in scenes["scenes"]]
    data = ask(
        "step6",
        {
            "last_session": json.dumps(last, indent=1, ensure_ascii=False),
            "open_headings": json.dumps(sections, indent=1, ensure_ascii=False),
            "current_tier": json.dumps({"where_you_are": stopping["where_you_are"], "immediate_intention": stopping["immediate_intention"], "immediate_danger": [d["text"] for d in stopping["immediate_danger"]]}, indent=1, ensure_ascii=False),
            "scene_cues": json.dumps(cues, indent=1, ensure_ascii=False),
        },
        out,
    )
    problems = []
    want_last = [x["id"] for x in selection["last_session"]]
    want_open = [fid for sec in selection["open"] for fid in sec["facts"]]
    if [x["id"] for x in data["last_session"]] != want_last:
        problems.append(f"last_session IDs {[x['id'] for x in data['last_session']]} != {want_last}")
    if sorted(x["id"] for x in data["open"]) != sorted(want_open) or len(data["open"]) != len(want_open):
        problems.append("open IDs do not match the selection")
    if data["session_cue_scene"] not in {s["id"] for s in scenes["scenes"]}:
        problems.append(f"unknown cue scene {data['session_cue_scene']}")
    for p in problems:
        print("  PROBLEM:", p)
    data["problems"] = problems
    (out / "writing.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    if problems:
        raise ValueError("Invalid Summary writing: " + "; ".join(problems))
    return data


# ---------------------------------------------------------------- step 7


def clean(text: str) -> str:
    text = " ".join(text.split())
    return text if re.search(r"[.!?\"')]$", text) else text + "."


def step7(out: Path, label: str, scenes: dict[str, Any], threads: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any], selection: dict[str, Any], writing: dict[str, Any]) -> dict[str, Any]:
    cue = next(s["cue"] for s in scenes["scenes"] if s["id"] == writing["session_cue_scene"])
    date = session_date(label)
    texts = {x["id"]: clean(x["text"]) for x in writing["last_session"] + writing["open"]}
    lines = ["# Brandonsford", f"**{date + ': ' if date else ''}{cue}**", ""]
    if selection["last_session"]:
        lines += ["## Last session..."] + [f"- {texts[x['id']]}" for x in selection["last_session"]] + [""]
    for sec in selection["open"]:
        lines += [f"## {sec['heading']}"] + [f"- {texts[fid]}" for fid in sec["facts"]] + [""]
    lines += ["## Where you are", f"- {clean(stopping['where_you_are'])}"]
    if stopping["immediate_intention"] is not None:
        lines.append(f"- {clean(stopping['immediate_intention']['text'])}")
    lines.append("")
    if stopping["immediate_danger"]:
        lines += ["## Immediate danger"] + [f"- {clean(d['text'])}" for d in stopping["immediate_danger"]] + [""]
    (out / "summary.md").write_text("\n".join(lines))
    matters = {
        "session": label,
        "session_cue": {"scene": writing["session_cue_scene"], "text": cue},
        "previous": [{"id": x["id"], "text": texts[x["id"]]} for x in selection["last_session"]],
        "current": stopping,
        "open": {sec["heading"]: [{"fact": fid, "text": texts[fid]} for fid in sec["facts"]] for sec in selection["open"]},
        "decisions": selection["decisions"],
        "resource_reconciliation": selection["resource_reconciliation"],
        "campaign_state": {"threads": threads["threads"], "facts": facts},
    }
    (out / "matters.json").write_text(json.dumps(matters, indent=1, ensure_ascii=False))
    return {"cue": cue, "date": date, "texts": texts}


# ---------------------------------------------------------------- step 8


def step8(out: Path, threads: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any], selection: dict[str, Any], rendered: dict[str, Any]) -> None:
    texts = rendered["texts"]
    fmap = {f["id"]: f for f in facts}
    heading_of = {fid: sec["heading"] for sec in selection["open"] for fid in sec["facts"]}
    last_ids = {x["id"] for x in selection["last_session"]}
    view = []
    for t in threads["threads"]:
        opens = [{"heading": heading_of[fid], "importance": fmap[fid]["importance"], "text": texts[fid]} for fid in heading_of if fmap[fid]["thread"] == t["id"]]
        if t["id"] in last_ids or opens:
            entry = {"name": t["name"]}
            if t["id"] in last_ids:
                entry["last_session"] = texts[t["id"]]
            entry["open"] = opens
            view.append(entry)
    for x in selection["last_session"]:
        if x["kind"] in ("beat", "encounter"):
            view.append({"name": "Encounter" if x["kind"] == "encounter" else "Standalone event", "last_session": texts[x["id"]], "open": []})
    where = {"where_you_are": clean(stopping["where_you_are"]), "immediate_intention": stopping["immediate_intention"], "immediate_danger": [clean(d["text"]) for d in stopping["immediate_danger"]]}
    data = ask(
        "step8",
        {"thread_words": RECAP_THREAD_WORDS, "closing_words": RECAP_CLOSING_WORDS, "threads": json.dumps(view, indent=1, ensure_ascii=False), "where_you_are": json.dumps(where, indent=1, ensure_ascii=False)},
        out,
    )
    lines = ["# Brandonsford", f"**{rendered['date'] + ': ' if rendered['date'] else ''}{rendered['cue']}**", ""]
    over = []
    for t in data["threads"]:
        n = len(t["label"].split()) + len(t["text"].split())
        if n > RECAP_THREAD_WORDS:
            over.append(f"{t['label']} ({n} words)")
        lines.append(f"- **{t['label'].rstrip('.')}.** {clean(t['text'])}")
    lines += ["", "## Where you are", "", clean(data["closing"]), ""]
    (out / "table_recap.md").write_text("\n".join(lines))
    words = sum(len(t["label"].split()) + len(t["text"].split()) for t in data["threads"]) + len(data["closing"].split())
    print(f"  recap: {len(data['threads'])} bullets for {len(view)} threads, {words} words; over {RECAP_THREAD_WORDS} words: {over or 'none'}")


# ---------------------------------------------------------------- review file


def review(out: Path, label: str, threads: dict[str, Any], facts: list[dict[str, Any]], selection: dict[str, Any]) -> None:
    """Phone-readable list of every classification decision, hidden items first."""
    tmap = {t["id"]: t for t in threads["threads"]}
    fmap = {f["id"]: f for f in facts}
    dec = selection["decisions"]
    lines = [f"# Session {label}: what was kept and dropped", "", "Pass 10. Every tracked fact and every \"Last session...\" candidate, with the field that decided it. Assets are state, not open matters. Mark any you disagree with.", ""]
    lines += ["## Last session... candidates", "", f"Rule (provisional): {RULES['last_session']}.", ""]
    for c in selection["last_session_candidates"]:
        name = c["name"]
        mark = "SHOWN" if c["shown"] else "hidden"
        lines.append(f"- **{mark}** · impact {c['narrative_impact']}, lasting {c['lasting_consequence']}, {c['beats']} beats · encounter value {c['encounter_value']} · *{name}*: {c['change']} → {c['publication_reason']}")
    dropped = selection.get("dropped_standalone", [])
    if dropped:
        lines += ["", "### Standalone beats dropped by code", ""]
        lines += [f"- **hidden** · importance {d['importance']} · {d['beat']}: {d['text']} → standalone beat rated low importance (model's reason: {d['reason'] or 'none'})" for d in dropped]
    lines += ["", "## Hidden open facts", ""]
    hidden = [fid for fid, d in dec.items() if not d["shown"]]
    for kind, heading in HEADINGS:
        mine = [fid for fid in hidden if fmap[fid]["kind"] == kind
                and not (kind == "could_use" and kind_class(fmap[fid])["form"] == "asset")]
        if mine:
            lines += [f"### Would have been under \"{heading}\"", ""]
            for fid in mine:
                f = fmap[fid]
                lines.append(f"- {f['text']} *({tmap[f['thread']]['name']}; {fid})* → **{dec[fid]['reason']}**")
            lines.append("")
    assets = [f for f in facts if f["state"] == "open" and f["kind"] == "could_use"
              and kind_class(f)["form"] == "asset"]
    if assets:
        lines += ["## Stored assets (not open matters)", ""]
        lines += [f"- {f['text']} *({f['id']})*" for f in assets]
        lines.append("")
    lines += ["## Shown open facts", ""]
    for sec in selection["open"]:
        lines += [f"### {sec['heading']}", ""]
        for fid in sec["facts"]:
            f = fmap[fid]
            text = selection["resource_texts"].get(fid, f["text"])
            lines.append(f"- {text} *({tmap[f['thread']]['name']}; {fid})* → {dec[fid]['reason']}")
        lines.append("")
    ended = [f for f in facts if f["state"] == "ended" and f["change"] == "ended"]
    if ended:
        lines += ["## Facts that ended this Session", ""]
        lines += [f"- {f['text']} *({tmap[f['thread']]['name']}; {f['id']})* → {f['ended_how']}" for f in ended]
        lines.append("")
    (out / "review.md").write_text("\n".join(lines))


# ---------------------------------------------------------------- chain and seed


def chain(name: str, start: int) -> None:
    label, scenes_run, threads_run, changes_run, facts_run = CHAINS[name]
    r2.use_session(label)
    r2.load_credentials()
    out = RUNS / name
    out.mkdir(parents=True, exist_ok=True)
    scenes = r2.load_scenes(scenes_run)
    threads = r2.load_threads(threads_run)
    changes = json.loads((RUNS / changes_run / "changes.json").read_text())
    facts = json.loads((RUNS / facts_run / "thread_facts.json").read_text())["facts"]
    problems = check_classification(facts_run)
    if problems:
        raise ValueError("Invalid pass 10 facts; regenerate step 3: " + "; ".join(problems))
    candidates = resource_candidates(threads, facts)
    if start <= 3:
        reconciliation = step3r(out, scenes, candidates)
    else:
        reconciliation = json.loads((out / "resource_reconciliation.json").read_text())
        validate_reconciliation(reconciliation, candidates)
    stopping = step4(out, scenes, threads, facts) if start <= 4 else json.loads((out / "stopping_situation.json").read_text())
    selection = select(scenes, threads, changes, facts, stopping, reconciliation)
    (out / "selection.json").write_text(json.dumps(selection, indent=1, ensure_ascii=False))
    shown = sum(d["shown"] for d in selection["decisions"].values())
    print(f"  step5: {len(selection['last_session'])} of {len(selection['last_session_candidates'])} Last session candidates, {shown} of {len(selection['decisions'])} open facts shown")
    review(out, label, threads, facts, selection)
    writing = step6(out, scenes, threads, facts, stopping, selection) if start <= 6 else json.loads((out / "writing.json").read_text())
    rendered = step7(out, label, scenes, threads, facts, stopping, selection, writing)
    step8(out, threads, facts, stopping, selection, rendered)
    print(f"wrote {out}")


def seed(prev: str, label: str) -> None:
    """Build the next Session's seed from a chain: its open threads and facts, and its stopping situation."""
    prev_label, _, threads_run, _, facts_run = CHAINS[prev]
    r2.use_session(prev_label)
    threads = r2.load_threads(threads_run)["threads"]
    facts = json.loads((RUNS / facts_run / "thread_facts.json").read_text())["facts"]
    stop = json.loads((RUNS / prev / "stopping_situation.json").read_text())
    open_facts = [f for f in facts if f["state"] == "open"]
    keep = {f["thread"] for f in open_facts} | {t["id"] for t in threads if t["status"] in ("open", "changed")}
    data = {
        "note": f"Chained from pass 10's {prev} ({threads_run}, {facts_run}).",
        "fact_high_water": max(r2.FIRST_NEW_FACT - 1, max((int(f["id"].split("_")[1]) for f in facts), default=0)),
        "thread_high_water": max(r2.FIRST_NEW_THREAD - 1, max((int(t["id"].split("_")[1]) for t in threads), default=0)),
        "threads": [{"id": t["id"], "name": t["name"], "parent": t["parent"]} for t in threads if t["id"] in keep],
        "facts": open_facts,
    }
    (HERE / "seeds" / f"{label}.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    parts = [f"Current position: {stop['where_you_are']}"]
    if stop["immediate_intention"] is not None:
        parts.append("Immediate intention: " + stop["immediate_intention"]["text"])
    if stop["immediate_danger"]:
        parts.append("Present danger: " + " ".join(d["text"] for d in stop["immediate_danger"]))
    (HERE / "seeds" / f"{label}.starting.txt").write_text("\n".join(parts) + "\n")
    print(f"seed {label}: {len(data['threads'])} threads, {len(data['facts'])} facts")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["step1", "step2", "step2c", "step3", "check", "chain", "seed"])
    parser.add_argument("name", nargs="*")
    parser.add_argument("--session", default="001")
    parser.add_argument("--out")
    parser.add_argument("--run")
    parser.add_argument("--scenes")
    parser.add_argument("--threads")
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--from", dest="start", type=int, choices=[3, 4, 5, 6, 7], default=3)
    args = parser.parse_args()
    if args.command == "chain":
        chain(args.name[0], args.start)
        return
    if args.command == "seed":
        seed(args.name[0], args.name[1])
        return
    r2.use_session(args.session)
    if args.command == "check":
        r2.check(args.run)
        problems = check_classification(args.run) if (RUNS / args.run / "thread_facts.json").exists() else []
        print("classification problems:", problems or "none")
        if problems:
            raise ValueError("Invalid pass 10 fact classifications")
        return
    r2.load_credentials()
    out = RUNS / args.out
    out.mkdir(parents=True, exist_ok=True)
    folder = {"step3": "step3-homes"}.get(args.command, args.command)
    r2.snapshot_prompts(out, [folder])
    if args.command == "step1":
        asyncio.run(r2.step1(out))
    elif args.command == "step2":
        asyncio.run(r2.step2(out, args.scenes))
    elif args.command == "step2c":
        asyncio.run(step2c(out, args.scenes, args.threads))
    else:
        asyncio.run(r2.step3(out, args.scenes, args.threads, args.only, homes=args.threads))
        problems = check_classification(args.out)
        if problems:
            raise ValueError("Invalid pass 10 facts: " + "; ".join(problems))
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
