"""Pass 3 runner: Unified Matters Pipeline steps 4 to 8 on pass 2's final step 1 to 3 outputs.

Experiment code, not the pipeline. Reads pass 2's runs and the deployment workspace read-only and
writes only under this folder's `runs/`. Run with the repository's virtual environment:

    .venv/bin/python <this folder>/run3.py chain f1      # one named chain, steps 4 to 8
    .venv/bin/python <this folder>/run3.py chain f1 --from 6   # rerun from step 6, reusing step 4

Chains are defined in CHAINS below.
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
PASS2 = HERE.parent / "pass-2"
sys.path.insert(0, str(PASS2))
import run as r2  # noqa: E402

RUNS = HERE / "runs"
PROMPTS = HERE / "prompts"
MODEL = r2.MODEL
TIMEOUT = r2.TIMEOUT
EFFORT = {"step4": "medium", "step6": "high", "step8": "high"}  # matters_effort for step 4, as Present Matters; narrative_effort for writing

# Chains: (Session, pass 2 scenes run, threads run, facts run)
CHAINS = {
    "f1": ("004", "r1-step1", "z-f1-step2", "q-f1-step3"),
    "f2": ("004", "f2-step1", "z-f2-step2", "q-f2-step3"),
    "s003": ("003", "s003-step1", "s003b-step2", "q-s003-step3"),
    "s001": ("001", "s001-step1", "s001-step2", "s001-step3"),
    "s002": ("002", "s002-step1", "s002-step2", "s002-step3"),
}

# Step 5 selection. Version 1 was fixed before any Summary was rendered and proved far too loose (14 Last session
# bullets, up to 35 open facts). Version 2 was set after reading the version 1 Summaries; its caps dropped the recruits
# and three self-contained stories. Version 3 raised those caps and ranked plain-open earlier threads last. Version 4
# 2026-10-29, let standalone beats rated medium fill spare places; on Session 003 they were mostly trivia, so version 5
# (below) returns to version 3's rule. The step 6 length limit added alongside version 4 is kept.
SELECTION_VERSION = 5
LAST_SESSION_RULE = "touched threads with at least one high beat and standalone beats rated high, at most 10, ranked by number of high beats, then threads whose situation changed or began this Session before earlier threads still plainly open, then story order; shown in story order"
OPEN_RULE = "every want and every owe with a definite end; blocked_by, unknown and threat facts rated high or medium, could_use facts rated high or medium with high actionability, ranked by importance then actionability, capped per heading; never possibly moot facts, open-ended promises or facts covered by an immediate danger"
LAST_SESSION_CAP = 10
OPEN_CAPS = {"blocked_by": 4, "could_use": 8, "unknown": 5, "threat": 3}
RECAP_TARGET_WORDS = 450  # generate_artifacts.recap_target_words in the workspace settings
RECAP_CLOSING_WORDS = 50  # generate_artifacts.recap_orientation_words, used here for the closing
HEADINGS = [
    ("want", "Your goals"),
    ("blocked_by", "Standing in your way"),
    ("could_use", "What could help"),
    ("unknown", "Still unanswered"),
    ("owe", "Promises and debts"),
    ("threat", "Meanwhile"),
]
RANK = {"high": 0, "medium": 1, "low": 2}


def ask(step: str, variables: dict[str, Any], out: Path) -> dict[str, Any]:
    folder = PROMPTS / {"step4": "step4_stopping", "step6": "step6_writing", "step8": "step8_recap"}[step]
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
            MODEL,
            response_format=schema,
            timeout=TIMEOUT,
            prompt_name=f"unified_pass3_{step}",
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


# ---------------------------------------------------------------- step 4


def step4(out: Path, scenes: dict[str, Any], threads: dict[str, Any], facts: list[dict[str, Any]]) -> dict[str, Any]:
    last = scenes["scenes"][-1]
    start = min(i for b in last["beats"] for i in b["ledger"])
    entries = r2.ledger()["utterances"]
    tail = "\n".join(json.dumps({"i": i, **entries[i]}, ensure_ascii=False) for i in range(start, len(entries)))
    names = {t["id"]: t["name"] for t in threads["threads"]}
    threats = [{"id": f["id"], "thread": names[f["thread"]], "text": f["text"]} for f in facts if f["state"] == "open" and f["kind"] == "threat"]
    final_scene = {"location": last["location"], "people": last["people"], "beats": [{"kind": b["kind"], "text": b["text"]} for b in last["beats"]]}
    data = ask(
        "step4",
        {
            "attendees": r2.attendees(),
            "starting_situation": r2.starting_situation(),
            "final_scene": json.dumps(final_scene, indent=1, ensure_ascii=False),
            "ledger_tail": tail,
            "open_threat_facts": json.dumps(threats, indent=1, ensure_ascii=False),
        },
        out,
    )
    known = {f["id"] for f in threats}
    for d in data["immediate_danger"]:
        bad = [x for x in d["covers_facts"] if x not in known]
        if bad:
            print("  PROBLEM: danger covers unknown threat facts", bad)
    (out / "stopping_situation.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    return data


# ---------------------------------------------------------------- step 5


def select(scenes: dict[str, Any], threads: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any]) -> dict[str, Any]:
    beats = {b["id"]: b for s in scenes["scenes"] for b in s["beats"]}
    order = {b: i for i, b in enumerate(beats)}
    thread_order = {t["id"]: i for i, t in enumerate(threads["threads"])}
    last_session = []
    for t in threads["threads"]:
        highs = sum(beats[b]["importance"] == "high" for b in t["touched_by"])
        if highs:
            plain = t["origin"] == "earlier" and t["status"] == "open"
            last_session.append({"id": t["id"], "kind": "thread", "first": order[t["touched_by"][0]], "highs": highs, "plain": plain})
    for s in threads["standalone_beats"]:
        if beats[s["beat"]]["importance"] == "high":
            last_session.append({"id": s["beat"], "kind": "beat", "first": order[s["beat"]], "highs": 1, "plain": False})
    dropped_last = [x["id"] for x in sorted(last_session, key=lambda x: (-x["highs"], x["plain"], x["first"]))[LAST_SESSION_CAP:]]
    last_session = sorted((x for x in last_session if x["id"] not in dropped_last), key=lambda x: x["first"])
    covered = {x for d in stopping["immediate_danger"] for x in d["covers_facts"]}
    excluded = {"possibly_moot": [], "open_ended": [], "covered_by_danger": [], "below_threshold": [], "over_cap": [], "last_session_over_cap": dropped_last}
    chosen = []
    for f in facts:
        if f["state"] != "open":
            continue
        if f["possibly_moot"]:
            excluded["possibly_moot"].append(f["id"])
        elif f["kind"] == "owe" and f["definite_end"] is False:
            excluded["open_ended"].append(f["id"])
        elif f["id"] in covered:
            excluded["covered_by_danger"].append(f["id"])
        elif f["kind"] in ("want", "owe") or (
            f["importance"] in ("high", "medium") and (f["kind"] != "could_use" or f["importance"] == "high" or f["actionability"] == "high")
        ):
            chosen.append(f)
        else:
            excluded["below_threshold"].append(f["id"])
    open_sections = []
    for kind, heading in HEADINGS:
        items = sorted(
            (f for f in chosen if f["kind"] == kind),
            key=lambda f: (RANK[f["importance"]], RANK[f["actionability"]], thread_order[f["thread"]], int(f["id"].split("_")[1])),
        )
        cap = OPEN_CAPS.get(kind)
        if cap is not None and len(items) > cap:
            excluded["over_cap"] += [f["id"] for f in items[cap:]]
            items = items[:cap]
        if items:
            open_sections.append({"heading": heading, "kind": kind, "facts": [f["id"] for f in items]})
    return {"version": SELECTION_VERSION, "rules": {"last_session": LAST_SESSION_RULE, "open": OPEN_RULE}, "last_session": last_session, "open": open_sections, "excluded": excluded}


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
        else:
            last.append({"id": item["id"], "kind": "beat", "text": beats[item["id"]]["text"]})
    sections = []
    for sec in selection["open"]:
        items = []
        for fid in sec["facts"]:
            f = fmap[fid]
            item = {"id": fid, "text": f["text"], "thread": tmap[f["thread"]]["name"]}
            if f["learned_this_session"]:
                item["learned_this_session"] = True
            if f["certainty"] == "uncertain":
                item["certainty"] = f"uncertain: {f['uncertain_reason']}"
            items.append(item)
        sections.append({"heading": sec["heading"], "items": items})
    cues = [{"id": s["id"], "location": s["location"], "cue": s["cue"]} for s in scenes["scenes"]]
    data = ask(
        "step6",
        {
            "last_session": json.dumps(last, indent=1, ensure_ascii=False),
            "open_headings": json.dumps(sections, indent=1, ensure_ascii=False),
            "current_tier": json.dumps({"where_you_are": stopping["where_you_are"], "immediate_danger": [d["text"] for d in stopping["immediate_danger"]]}, indent=1, ensure_ascii=False),
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
    lines += ["## Where you are", f"- {clean(stopping['where_you_are'])}", ""]
    if stopping["immediate_danger"]:
        lines += ["## Immediate danger"] + [f"- {clean(d['text'])}" for d in stopping["immediate_danger"]] + [""]
    (out / "summary.md").write_text("\n".join(lines))
    matters = {
        "session": label,
        "session_cue": {"scene": writing["session_cue_scene"], "text": cue},
        "previous": [{"id": x["id"], "text": texts[x["id"]]} for x in selection["last_session"]],
        "current": stopping,
        "open": {sec["heading"]: [{"fact": fid, "text": texts[fid]} for fid in sec["facts"]] for sec in selection["open"]},
        "excluded_from_open": selection["excluded"],
        "campaign_state": {"threads": threads["threads"], "facts": facts},
    }
    (out / "matters.json").write_text(json.dumps(matters, indent=1, ensure_ascii=False))
    return {"cue": cue, "date": date, "texts": texts}


# ---------------------------------------------------------------- step 8


def step8(out: Path, threads: dict[str, Any], facts: list[dict[str, Any]], stopping: dict[str, Any], selection: dict[str, Any], rendered: dict[str, Any], scenes: dict[str, Any]) -> None:
    texts = rendered["texts"]
    fmap = {f["id"]: f for f in facts}
    heading_of = {fid: sec["heading"] for sec in selection["open"] for fid in sec["facts"]}
    beats = {b["id"] for s in scenes["scenes"] for b in s["beats"]}
    view = []
    last_ids = {x["id"] for x in selection["last_session"]}
    standalone_first = {x["id"]: x["first"] for x in selection["last_session"] if x["kind"] == "beat"}
    for t in threads["threads"]:
        opens = [{"heading": heading_of[fid], "importance": fmap[fid]["importance"], "text": texts[fid]} for fid in heading_of if fmap[fid]["thread"] == t["id"]]
        if t["id"] in last_ids or opens:
            entry = {"name": t["name"]}
            if t["id"] in last_ids:
                entry["last_session"] = texts[t["id"]]
            entry["open"] = opens
            view.append(entry)
    for bid in standalone_first:
        if bid in beats:
            view.append({"name": "Standalone event", "last_session": texts[bid], "open": []})
    where = {"where_you_are": clean(stopping["where_you_are"]), "immediate_danger": [clean(d["text"]) for d in stopping["immediate_danger"]]}
    data = ask(
        "step8",
        {
            "target_words": RECAP_TARGET_WORDS,
            "closing_words": RECAP_CLOSING_WORDS,
            "threads": json.dumps(view, indent=1, ensure_ascii=False),
            "where_you_are": json.dumps(where, indent=1, ensure_ascii=False),
        },
        out,
    )
    lines = ["# Brandonsford", f"**{rendered['date'] + ': ' if rendered['date'] else ''}{rendered['cue']}**", ""]
    for t in data["threads"]:
        lines.append(f"- **{t['label'].rstrip('.')}.** {clean(t['text'])}")
    lines += ["", "## Where you are", "", clean(data["closing"]), ""]
    (out / "table_recap.md").write_text("\n".join(lines))
    words = sum(len(t["label"].split()) + len(t["text"].split()) for t in data["threads"]) + len(data["closing"].split())
    print(f"  recap: {len(data['threads'])} threads, {words} words (target {RECAP_TARGET_WORDS}), closing {len(data['closing'].split())} words")


def chain(name: str, start: int) -> None:
    label, scenes_run, threads_run, facts_run = CHAINS[name]
    r2.use_session(label)
    r2.load_credentials()
    out = RUNS / name
    out.mkdir(parents=True, exist_ok=True)
    scenes = r2.load_scenes(scenes_run)
    threads = r2.load_threads(threads_run)
    facts = json.loads((r2.RUNS / facts_run / "thread_facts.json").read_text())["facts"]
    stopping = step4(out, scenes, threads, facts) if start <= 4 else json.loads((out / "stopping_situation.json").read_text())
    selection = select(scenes, threads, facts, stopping)
    (out / "selection.json").write_text(json.dumps(selection, indent=1, ensure_ascii=False))
    print(f"  step5: {len(selection['last_session'])} Last session items, {sum(len(s['facts']) for s in selection['open'])} open facts; excluded {{{', '.join(f'{k}: {len(v)}' for k, v in selection['excluded'].items())}}}")
    writing = step6(out, scenes, threads, facts, stopping, selection) if start <= 6 else json.loads((out / "writing.json").read_text())
    rendered = step7(out, label, scenes, threads, facts, stopping, selection, writing)
    step8(out, threads, facts, stopping, selection, rendered, scenes)
    print(f"wrote {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["chain"])
    parser.add_argument("name", choices=sorted(CHAINS))
    parser.add_argument("--from", dest="start", type=int, default=4)
    args = parser.parse_args()
    chain(args.name, args.start)


if __name__ == "__main__":
    main()
