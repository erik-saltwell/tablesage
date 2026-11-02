"""Pass 2 runner: Unified Matters Pipeline steps 1 to 3 on Brandonsford Session 004.

Experiment code, not the pipeline. It reads the deployment workspace read-only and writes
only under this folder's `runs/`. Run with the repository's virtual environment:

    .venv/bin/python <this folder>/run.py step1 --out r1
    .venv/bin/python <this folder>/run.py step2 --scenes hand --out r2
    .venv/bin/python <this folder>/run.py step3 --scenes hand --threads hand --out r3 [--only thread_12]
    .venv/bin/python <this folder>/run.py check --run r3
    .venv/bin/python <this folder>/run.py show --run r3

`--scenes` and `--threads` take `hand` (pass 1's files) or a run name under `runs/`.
"""

from __future__ import annotations

import argparse
import asyncio
import difflib
import json
import os
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
HAND = HERE.parent
REPO = HERE.parents[4]
WORKSPACE = REPO / "deployment"
SESSION = WORKSPACE / "campaigns" / "Brandonsford" / "004"
PREVIOUS = WORKSPACE / "campaigns" / "Brandonsford" / "003"
SEED = HAND / "seed_campaign_state.json"
SESSION_LABEL = "004"
RUNS = HERE / "runs"
PROMPTS = HERE / "prompts"

MODEL = "anthropic/claude-opus-5-5"  # llm_model_high in deployment/.tablesage/settings.yaml
TIMEOUT = 2400  # generate_artifacts.timeout
EFFORT = {"step1": "high", "step2": "high", "step3": "medium", "step3-single": "medium", "step2b": "high", "step3-homes": "medium"}  # narrative_effort; matters_effort for facts
STEP_FOLDERS = {"step1": "step1_scenes", "step2": "step2_threads", "step3": "step3_facts", "step3-single": "step3_facts_single", "step2b": "step2b_homes", "step3-homes": "step3_facts_homes"}
STEP3_CONCURRENCY = 6
FIRST_NEW_FACT = 20  # the seed holds fact_1 to fact_19
FIRST_NEW_THREAD = 11  # the seed holds thread_1 to thread_10


# ---------------------------------------------------------------- inputs


def load_credentials() -> None:
    env = Path.home() / ".config" / "tablesage" / ".env"
    for line in env.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() and value.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def ledger() -> dict[str, Any]:
    return json.loads((SESSION / "ledger.json").read_text())


def attendees() -> list[dict[str, Any]]:
    return ledger()["attendees"]


def party() -> list[str]:
    return [r for a in attendees() for r in a["roles"] if r != "Game Master"]


def glossary() -> list[dict[str, Any]]:
    db = sqlite3.connect(f"file:{WORKSPACE / '.tablesage' / 'tablesage.db'}?mode=ro", uri=True)
    rows = db.execute(
        "SELECT g.term, g.description FROM glossary_entry g JOIN campaign c ON c.id = g.campaign_id WHERE c.name = 'Brandonsford'"
    ).fetchall()
    return [{"term": t, "description": d} for t, d in sorted(rows, key=lambda r: r[0].casefold())]


def starting_situation() -> str | None:
    """The Scene Log's choice: the Ledger's own framing, else where the previous Session stopped.

    A chained Session uses the previous Session's unified stopping situation from seeds/<label>.starting.txt."""
    if ledger().get("starting_situation"):
        return ledger()["starting_situation"]
    chained = HERE / "seeds" / f"{SESSION_LABEL}.starting.txt"
    if chained.exists():
        return chained.read_text().strip()
    present = json.loads((PREVIOUS / "present_matters.json").read_text())["present_matters"]
    parts = [f"Current position: {present['current_position']}"]
    if present.get("present_danger"):
        parts.append("Present danger: " + " ".join(present["present_danger"]))
    return "\n".join(parts)


def seed() -> dict[str, Any]:
    return json.loads(SEED.read_text())


def use_session(label: str) -> None:
    """Point the runner at another Session; its seed lives in seeds/<label>.json, except 004's pass 1 seed."""
    global SESSION, PREVIOUS, SEED, SESSION_LABEL, FIRST_NEW_FACT, FIRST_NEW_THREAD
    campaign = WORKSPACE / "campaigns" / "Brandonsford"
    SESSION, PREVIOUS, SESSION_LABEL = campaign / label, campaign / f"{int(label) - 1:03d}", label
    SEED = HAND / "seed_campaign_state.json" if label == "004" else HERE / "seeds" / f"{label}.json"
    state = seed()
    FIRST_NEW_FACT = max((int(f["id"].split("_")[1]) for f in state["facts"]), default=0) + 1
    FIRST_NEW_THREAD = max((int(t["id"].split("_")[1]) for t in state["threads"]), default=0) + 1


def load_scenes(source: str) -> dict[str, Any]:
    return json.loads(((HAND if source == "hand" else RUNS / source) / "scenes.json").read_text())


def load_threads(source: str) -> dict[str, Any]:
    data = json.loads(((HAND if source == "hand" else RUNS / source) / "threads.json").read_text())
    data["standalone_beats"] = [b if isinstance(b, dict) else {"beat": b, "reason": ""} for b in data["standalone_beats"]]
    return data


# ---------------------------------------------------------------- LLM


def render(step: str, variables: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    folder = PROMPTS / STEP_FOLDERS[step]
    system = (folder / "system.md").read_text()
    user = jinja2.Template((folder / "template.j2").read_text(), undefined=jinja2.StrictUndefined).render(**variables)
    return system, user, json.loads((folder / "schema.json").read_text())


async def ask(step: str, variables: dict[str, Any], out: Path, label: str) -> dict[str, Any]:
    system, user, schema = render(step, variables)
    records = out / "records"
    records.mkdir(parents=True, exist_ok=True)
    (records / f"{label}.user.md").write_text(user)
    started = time.monotonic()
    raw = await call_llm(
        system,
        user,
        MODEL,
        response_format=schema,
        timeout=TIMEOUT,
        prompt_name=f"unified_pass2_{step}",
        model_options={"reasoning_effort": EFFORT[step], "drop_params": False},
        system_prompt_cache_ttl="5m" if step in ("step3", "step3-homes") else None,
    )
    elapsed = time.monotonic() - started
    (records / f"{label}.raw.json").write_text(raw)
    data = json.loads(raw)
    jsonschema.Draft202012Validator(schema).validate(data)
    print(f"  {label}: {elapsed:.0f}s, {len(user):,} prompt chars, {len(raw):,} response chars", flush=True)
    return data


def snapshot_prompts(out: Path, steps: list[str]) -> None:
    """Keep the exact prompt texts each run used, so runs stay comparable after prompts change."""
    for step in steps:
        folder = PROMPTS / STEP_FOLDERS[step]
        target = out / "prompts" / folder.name
        target.mkdir(parents=True, exist_ok=True)
        for f in folder.iterdir():
            (target / f.name).write_text(f.read_text())


# ---------------------------------------------------------------- step 1


def ledger_text() -> str:
    return "\n".join(json.dumps({"i": i, **entry}, ensure_ascii=False) for i, entry in enumerate(ledger()["utterances"]))


async def step1(out: Path) -> None:
    variables = {"attendees": attendees(), "glossary": glossary(), "starting_situation": starting_situation(), "ledger": ledger_text()}
    data = await ask("step1", variables, out, "step1")
    beat_n = 0
    scenes = []
    for n, scene in enumerate(data["scenes"], 1):
        beats = []
        for beat in scene["beats"]:
            beat_n += 1
            beats.append({"id": f"beat_{beat_n}", **beat})
        scenes.append({"id": f"scene_{n}", "location": scene["location"], "people": scene["people"], "cue": scene["cue"], "beats": beats})
    (out / "scenes.json").write_text(json.dumps({"session": SESSION_LABEL, "ledger_index": "0-based positions in ledger.json utterances", "scenes": scenes}, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- step 2


def scenes_for_prompt(scenes: dict[str, Any], mark: set[str] | None = None) -> str:
    rows = []
    for scene in scenes["scenes"]:
        beats = []
        for b in scene["beats"]:
            beat = {"id": b["id"], "kind": b["kind"], "text": b["text"], "importance": b["importance"]}
            if mark is not None:
                beat["this_thread"] = b["id"] in mark
            beats.append(beat)
        rows.append({"id": scene["id"], "location": scene["location"], "people": scene["people"], "beats": beats})
    return json.dumps(rows, indent=1, ensure_ascii=False)


def prior_threads_for_prompt(state: dict[str, Any]) -> str:
    rows = []
    for t in state["threads"]:
        facts = [{"id": f["id"], "kind": f["kind"], "text": f["text"]} for f in state["facts"] if f["thread"] == t["id"]]
        rows.append({"id": t["id"], "name": t["name"], "parent": t["parent"], "facts": facts})
    return json.dumps(rows, indent=1, ensure_ascii=False)


async def step2(out: Path, scenes_source: str) -> None:
    scenes = load_scenes(scenes_source)
    state = seed()
    variables = {
        "attendees": attendees(),
        "prior_threads": prior_threads_for_prompt(state),
        "starting_situation": starting_situation(),
        "scenes": scenes_for_prompt(scenes),
    }
    data = await ask("step2", variables, out, "step2")
    problems = []
    beat_ids = [b["id"] for s in scenes["scenes"] for b in s["beats"]]
    order = {b: i for i, b in enumerate(beat_ids)}
    prior_ids = [t["id"] for t in state["threads"]]
    seen = [t["id"] for t in data["prior_threads"]]
    if sorted(seen) != sorted(prior_ids):
        problems.append(f"prior threads accounted for {sorted(seen)} != {sorted(prior_ids)}")
    temp = {t["id"]: f"thread_{FIRST_NEW_THREAD + i}" for i, t in enumerate(data["new_threads"])}
    if len(temp) != len(data["new_threads"]):
        problems.append("duplicate temporary thread IDs")
    names = {t["id"]: t["name"] for t in state["threads"]}
    threads = []
    for t in data["prior_threads"]:
        source = next((s for s in state["threads"] if s["id"] == t["id"]), None)
        threads.append({"id": t["id"], "name": names.get(t["id"], "?"), "parent": source["parent"] if source else None, "origin": "earlier", "status": t["status"], "touched_by": t["beats"], "note": t["reason"]})
    for t in data["new_threads"]:
        parent = temp.get(t["parent"], t["parent"]) if t["parent"] else None
        if parent and parent not in prior_ids and parent not in temp.values():
            problems.append(f"{t['id']}: unknown parent {t['parent']}")
        threads.append({"id": temp[t["id"]], "name": t["name"], "parent": parent, "origin": "new", "status": t["status"], "touched_by": t["beats"], "note": t["reason"]})
    for t in threads:
        for b in t["touched_by"]:
            if b not in order:
                problems.append(f"{t['id']}: unknown beat {b}")
        t["touched_by"] = sorted(set(t["touched_by"]) & set(order), key=order.get)
    for s in data["standalone_beats"]:
        if s["beat"] not in order:
            problems.append(f"standalone: unknown beat {s['beat']}")
    shared = [
        sub | {"home": temp.get(sub["home"], sub["home"]), "other_threads": [temp.get(x, x) for x in sub["other_threads"]]}
        for sub in data.get("shared_subjects", [])
    ]
    known = set(prior_ids) | set(temp.values())
    problems += [f"shared subject: unknown thread {x}" for sub in shared for x in [sub["home"], *sub["other_threads"]] if x not in known]
    (out / "shared_subjects.json").write_text(json.dumps({"scenes": scenes_source, "shared_subjects": shared}, indent=1, ensure_ascii=False))
    result = {"session": SESSION_LABEL, "scenes": scenes_source, "threads": threads, "standalone_beats": data["standalone_beats"], "temporary_ids": temp, "problems": problems}
    (out / "threads.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    for p in problems:
        print("  PROBLEM:", p)


# ---------------------------------------------------------------- step 3


def needs_facts(thread: dict[str, Any]) -> bool:
    """Every prior thread must account for its facts; a new thread that already ended has none."""
    return thread["origin"] == "earlier" or thread["status"] in ("open", "changed")


def prior_facts_for(state: dict[str, Any], thread_id: str) -> list[dict[str, Any]]:
    return [{"id": f["id"], "kind": f["kind"], "text": f["text"]} for f in state["facts"] if f["thread"] == thread_id]


async def step2b(out: Path, scenes_source: str, threads_source: str) -> None:
    """Variant: name one home thread for each subject several threads bear on, before parallel step 3."""
    scenes = load_scenes(scenes_source)
    threads = load_threads(threads_source)
    state = seed()
    rows = [
        {k: t[k] for k in ("id", "name", "parent", "status")} | {"reason": t["note"], "beats": t["touched_by"], "prior_facts": prior_facts_for(state, t["id"])}
        for t in threads["threads"]
    ]
    data = await ask("step2b", {"threads": json.dumps(rows, indent=1, ensure_ascii=False), "scenes": scenes_for_prompt(scenes)}, out, "step2b")
    ids = {t["id"] for t in threads["threads"]}
    problems = [f"unknown thread {x}" for sub in data["shared_subjects"] for x in [sub["home"], *sub["other_threads"]] if x not in ids]
    (out / "shared_subjects.json").write_text(json.dumps({"scenes": scenes_source, "threads": threads_source, **data, "problems": problems}, indent=1, ensure_ascii=False))
    for sub in data["shared_subjects"]:
        print(f"  {sub['home']} <- {sub['other_threads']}: {sub['subject']}")
    for pr in problems:
        print("  PROBLEM:", pr)


async def step3(out: Path, scenes_source: str, threads_source: str, only: list[str] | None, homes: str | None = None) -> None:
    scenes = load_scenes(scenes_source)
    threads = load_threads(threads_source)
    state = seed()
    all_threads = json.dumps(
        [{"id": t["id"], "name": t["name"], "parent": t["parent"], "status": t["status"], "beats": t["touched_by"]} for t in threads["threads"]],
        indent=1,
        ensure_ascii=False,
    )
    targets = [t for t in threads["threads"] if needs_facts(t) and (not only or t["id"] in only)]
    shared = None
    step = "step3"
    if homes:
        subjects = json.loads((RUNS / homes / "shared_subjects.json").read_text())["shared_subjects"]
        shared = json.dumps([{k: s[k] for k in ("subject", "home", "other_threads")} for s in subjects], indent=1, ensure_ascii=False)
        step = "step3-homes"
    semaphore = asyncio.Semaphore(STEP3_CONCURRENCY)

    async def one(thread: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        variables = {
            "party": party(),
            "thread": json.dumps({k: thread[k] for k in ("id", "name", "parent", "status")} | {"reason": thread["note"]}, ensure_ascii=False),
            "prior_facts": json.dumps(prior_facts_for(state, thread["id"]), indent=1, ensure_ascii=False),
            "all_threads": all_threads,
            "scenes": scenes_for_prompt(scenes, set(thread["touched_by"])),
        }
        if shared is not None:
            variables["shared_subjects"] = shared
        async with semaphore:
            return thread["id"], await ask(step, variables, out, f"step3_{thread['id']}")

    results = dict(await asyncio.gather(*(one(t) for t in targets)))
    write_facts(out, scenes_source, threads_source, threads, results)


async def step3_single(out: Path, scenes_source: str, threads_source: str) -> None:
    """Comparison variant: one call writes every thread's facts, so it can see every home decision."""
    scenes = load_scenes(scenes_source)
    threads = load_threads(threads_source)
    state = seed()
    targets = [t for t in threads["threads"] if needs_facts(t)]
    rows = [
        {k: t[k] for k in ("id", "name", "parent", "status")} | {"reason": t["note"], "beats": t["touched_by"], "prior_facts": prior_facts_for(state, t["id"])}
        for t in targets
    ]
    others = [{k: t[k] for k in ("id", "name", "parent", "status")} | {"beats": t["touched_by"]} for t in threads["threads"] if not needs_facts(t)]
    variables = {
        "party": party(),
        "threads": json.dumps(rows, indent=1, ensure_ascii=False),
        "other_threads": json.dumps(others, indent=1, ensure_ascii=False),
        "scenes": scenes_for_prompt(scenes),
    }
    data = await ask("step3-single", variables, out, "step3_single")
    results = {t["id"]: {"facts": t["facts"]} for t in data["threads"]}
    missing = [t["id"] for t in targets if t["id"] not in results]
    if missing:
        print("  PROBLEM: threads missing from output:", missing)
    write_facts(out, scenes_source, threads_source, threads, results)


def write_facts(out: Path, scenes_source: str, threads_source: str, threads: dict[str, Any], results: dict[str, Any]) -> None:
    facts = []
    next_fact = FIRST_NEW_FACT
    for t in threads["threads"]:
        if t["id"] not in results:
            continue
        for f in results[t["id"]]["facts"]:
            fact = {"thread": t["id"], **f}
            if f["id"].startswith("fact_new_"):
                fact["temporary_id"] = f["id"]
                fact["id"] = f"fact_{next_fact}"
                next_fact += 1
            facts.append(fact)
    (out / "thread_facts.json").write_text(json.dumps({"session": SESSION_LABEL, "scenes": scenes_source, "threads": threads_source, "facts": facts}, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- checks


def similar(a: str, b: str) -> float:
    words = lambda s: [w for w in re.findall(r"[a-z']+", s.lower()) if len(w) > 3]
    return difflib.SequenceMatcher(None, words(a), words(b)).ratio()


def check(run: str, scenes_source: str | None = None) -> None:
    folder = RUNS / run
    report: list[str] = []
    ledger_len = len(ledger()["utterances"])
    scenes = load_scenes(run) if (folder / "scenes.json").exists() else None
    if scenes:
        beats = [b for s in scenes["scenes"] for b in s["beats"]]
        bad = [b["id"] for b in beats if any(i < 0 or i >= ledger_len for i in b["ledger"])]
        cited = {i for b in beats for i in b["ledger"]}
        kinds = {k: sum(b["kind"] == k for b in beats) for k in ("event", "learned")}
        report.append(f"step1: {len(scenes['scenes'])} scenes, {len(beats)} beats {kinds}, ledger coverage {len(cited)}/{ledger_len}, out-of-range refs {bad or 'none'}")
        for s in scenes["scenes"]:
            report.append(f"  {s['id']} {s['location']} ({len(s['beats'])} beats) cue: {s['cue']}")
    threads_file = folder / "threads.json"
    threads = load_threads(run) if threads_file.exists() else None
    if threads and not scenes and (threads.get("scenes") or scenes_source):
        scenes = load_scenes(threads.get("scenes") or scenes_source)
    if threads:
        report.append(f"step2: {len(threads['threads'])} threads, standalone {[s['beat'] for s in threads['standalone_beats']]}, problems {threads.get('problems') or 'none'}")
        for t in threads["threads"]:
            report.append(f"  {t['id']} [{t['origin']}/{t['status']}] {t['name']} parent={t['parent']} beats={len(t['touched_by'])}")
        if scenes:
            used = {b for t in threads["threads"] for b in t["touched_by"]} | {s["beat"] for s in threads["standalone_beats"]}
            loose = [b["id"] for s in scenes["scenes"] for b in s["beats"] if b["id"] not in used and b["importance"] != "low"]
            report.append(f"  medium/high beats on no thread and not standalone: {loose or 'none'}")
    facts_file = folder / "thread_facts.json"
    if facts_file.exists():
        data = json.loads(facts_file.read_text())
        facts = data["facts"]
        threads = threads or load_threads(data["threads"])
        scenes = scenes or load_scenes(data["scenes"])
        beat_ids = {b["id"] for s in scenes["scenes"] for b in s["beats"]}
        thread_ids = {t["id"]: t for t in threads["threads"]}
        state = seed()
        problems = []
        for t in threads["threads"]:
            if not needs_facts(t):
                continue
            mine = [f for f in facts if f["thread"] == t["id"]]
            if not mine and not any(f["thread"] == t["id"] for f in facts):
                pass
            prior = {f["id"]: f for f in state["facts"] if f["thread"] == t["id"]}
            got = [f["id"] for f in mine if not f.get("temporary_id")]
            if sorted(got) != sorted(prior):
                problems.append(f"{t['id']}: prior facts {sorted(got)} != {sorted(prior)}")
            open_facts = [f for f in mine if f["state"] == "open"]
            if t["status"] in ("resolved", "abandoned") and open_facts:
                problems.append(f"{t['id']}: {t['status']} but {len(open_facts)} open facts")
            if t["status"] in ("open", "changed") and not open_facts:
                problems.append(f"{t['id']}: {t['status']} but no open facts")
        for f in facts:
            tag = f"{f['id']} ({f['thread']})"
            if (f["kind"] == "owe") != (f["definite_end"] is not None):
                problems.append(f"{tag}: definite_end {f['definite_end']} on {f['kind']}")
            if (f["certainty"] == "uncertain") != (f["uncertain_reason"] is not None):
                problems.append(f"{tag}: certainty {f['certainty']} with reason {f['uncertain_reason']!r}")
            if (f["state"] == "ended") != (f["ended_how"] is not None) or (f["state"] == "ended") != (f["change"] == "ended"):
                problems.append(f"{tag}: state {f['state']} change {f['change']} ended_how {f['ended_how']!r}")
            if f["change"] == "carried":
                original = next((s for s in state["facts"] if s["id"] == f["id"]), None)
                if original and original["text"] != f["text"]:
                    problems.append(f"{tag}: carried text changed")
            if f.get("temporary_id") and f["change"] != "new":
                problems.append(f"{tag}: new ID but change {f['change']}")
            if f.get("temporary_id") and not any(e in beat_ids for e in f["evidence"]):
                problems.append(f"{tag}: new fact cites no beat")
            for e in f["evidence"]:
                if e != "prior" and e not in beat_ids:
                    problems.append(f"{tag}: unknown beat {e}")
            if f["about_thread"] and (f["about_thread"] not in thread_ids or f["about_thread"] == f["thread"]):
                problems.append(f"{tag}: bad about_thread {f['about_thread']}")
            for other in f.get("also_bears_on", []):
                if other not in thread_ids or other == f["thread"]:
                    problems.append(f"{tag}: bad also_bears_on {other}")
        open_facts = [f for f in facts if f["state"] == "open"]
        counts = {k: sum(f["kind"] == k for f in open_facts) for k in ("want", "owe", "blocked_by", "could_use", "unknown", "threat")}
        report.append(f"step3: {len(facts)} facts ({len(open_facts)} open) {counts}")
        report.append(f"  possibly moot: {[f['id'] for f in facts if f['possibly_moot']]}")
        report.append(f"  definite_end false: {[f['id'] for f in facts if f['definite_end'] is False]}")
        report.append(f"  uncertain: {[f['id'] for f in facts if f['certainty'] == 'uncertain']}")
        report.append(f"  problems: {problems or 'none'}")
        pairs = []
        for i, a in enumerate(open_facts):
            for b in open_facts[i + 1 :]:
                score = similar(a["text"], b["text"])
                if score >= 0.35:
                    pairs.append((score, a, b))
        report.append("  similar open fact pairs (review for restatement):")
        for score, a, b in sorted(pairs, key=lambda p: -p[0]):
            report.append(f"    {score:.2f} {a['id']} ({a['thread']}, {a['kind']}) ~ {b['id']} ({b['thread']}, {b['kind']})")
            report.append(f"         {a['text']}")
            report.append(f"         {b['text']}")
        shared = []
        grams = lambda t: {tuple(w) for w in zip(*(re.findall(r"[a-z']+", t.lower())[k:] for k in range(4)))}
        for i, a in enumerate(open_facts):
            for b in open_facts[i + 1 :]:
                if a["thread"] != b["thread"]:
                    common = grams(a["text"]) & grams(b["text"])
                    if common:
                        shared.append(f"    {a['id']} ({a['thread']}) & {b['id']} ({b['thread']}): {sorted(' '.join(g) for g in common)[:3]}")
        report.append("  cross-thread facts sharing 4-word phrases:")
        report.extend(shared)
    text = "\n".join(report)
    (folder / "check.txt").write_text(text + "\n")
    print(text)


def show(run: str) -> None:
    folder = RUNS / run
    data = json.loads((folder / "thread_facts.json").read_text())
    threads = load_threads(data["threads"]) if not (folder / "threads.json").exists() else load_threads(run)
    lines = []
    for t in threads["threads"]:
        lines.append(f"\n## {t['id']} {t['name']} [{t['origin']}/{t['status']}] parent={t['parent']}")
        lines.append(f"   {t['note']}")
        for f in data["facts"]:
            if f["thread"] != t["id"]:
                continue
            flags = [f["change"]]
            if f["state"] == "ended":
                flags.append(f"ENDED: {f['ended_how']}")
            if f["learned_this_session"]:
                flags.append("learned")
            if f["definite_end"] is False:
                flags.append("no definite end")
            if f["possibly_moot"]:
                flags.append(f"MOOT? {f['possibly_moot']}")
            if f["certainty"] == "uncertain":
                flags.append(f"UNCERTAIN: {f['uncertain_reason']}")
            if f["about_thread"]:
                flags.append(f"about {f['about_thread']}")
            if f.get("also_bears_on"):
                flags.append(f"also {','.join(f['also_bears_on'])}")
            lines.append(f" - {f['id']} {f['kind']} [{f['importance']}/{f['actionability']}] {f['text']}")
            lines.append(f"     {'; '.join(flags)} | {', '.join(f['evidence'])}")
    lines.append(f"\nstandalone: {threads['standalone_beats']}")
    text = "\n".join(lines)
    (folder / "facts.md").write_text(text + "\n")
    print(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["step1", "step2", "step2b", "step3", "step3-single", "step3-homes", "check", "show"])
    parser.add_argument("--homes")
    parser.add_argument("--session", default="004")
    parser.add_argument("--out")
    parser.add_argument("--run")
    parser.add_argument("--scenes", default="hand")
    parser.add_argument("--threads", default="hand")
    parser.add_argument("--only", nargs="*")
    args = parser.parse_args()
    use_session(args.session)
    if args.command in ("check", "show"):
        check(args.run, args.scenes if args.scenes != "hand" else None) if args.command == "check" else show(args.run)
        return
    load_credentials()
    out = RUNS / args.out
    out.mkdir(parents=True, exist_ok=True)
    snapshot_prompts(out, [args.command])
    if args.command == "step1":
        asyncio.run(step1(out))
    elif args.command == "step2":
        asyncio.run(step2(out, args.scenes))
    elif args.command == "step2b":
        asyncio.run(step2b(out, args.scenes, args.threads))
    elif args.command == "step3-homes":
        asyncio.run(step3(out, args.scenes, args.threads, args.only, args.homes))
    elif args.command == "step3-single":
        asyncio.run(step3_single(out, args.scenes, args.threads))
    else:
        asyncio.run(step3(out, args.scenes, args.threads, args.only))
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
