"""Build the next Session's seed from a unified run: its open threads and facts, and its stopping situation."""
import json
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
facts_run, threads_run, pass3_chain, label = sys.argv[1:5]
runs2 = here.parent / "pass-2" / "runs"
threads = json.loads((runs2 / threads_run / "threads.json").read_text())["threads"]
facts = json.loads((runs2 / facts_run / "thread_facts.json").read_text())["facts"]
stop = json.loads((here / "runs" / pass3_chain / "stopping_situation.json").read_text())
open_facts = [f for f in facts if f["state"] == "open"]
keep = {f["thread"] for f in open_facts} | {t["id"] for t in threads if t["status"] in ("open", "changed")}
seed = {
    "note": f"Chained from the unified run of the previous Session ({threads_run}, {facts_run}).",
    "threads": [{"id": t["id"], "name": t["name"], "parent": t["parent"]} for t in threads if t["id"] in keep],
    "facts": [{"id": f["id"], "thread": f["thread"], "kind": f["kind"], "text": f["text"]} for f in open_facts],
}
seeds = here.parent / "pass-2" / "seeds"
(seeds / f"{label}.json").write_text(json.dumps(seed, indent=1, ensure_ascii=False))
parts = [f"Current position: {stop['where_you_are']}"]
if stop["immediate_danger"]:
    parts.append("Present danger: " + " ".join(d["text"] for d in stop["immediate_danger"]))
(seeds / f"{label}.starting.txt").write_text("\n".join(parts) + "\n")
print(f"seed {label}: {len(seed['threads'])} threads, {len(seed['facts'])} facts")
