"""Historical event coverage independent of open-matter significance."""

from __future__ import annotations

from typing import Any


def historical_inputs(scenes: dict[str, Any], threads: dict[str, Any]) -> list[dict[str, Any]]:
    beats = {b["id"]: b for s in scenes["scenes"] for b in s["beats"]}
    def evidence(ids: list[str]) -> list[dict[str, str]]:
        return [{"id": bid, "kind": beats[bid]["kind"], "text": beats[bid]["text"]} for bid in ids]
    items = [{"id": t["id"], "kind": "thread", "name": t["name"], "origin": t["origin"],
              "status": t["status"], "reason": t["note"], "beats": evidence(t["touched_by"])}
             for t in threads["threads"] if t["touched_by"]]
    items += [{"id": x["beat"], "kind": "beat", "name": "Standalone event",
               "beats": evidence([x["beat"]])} for x in threads["standalone_beats"]]
    items += [{"id": s["id"], "kind": "encounter", "name": s["location"],
               "people": s["people"], "beats": evidence([b["id"] for b in s["beats"]])}
              for s in scenes["scenes"]]
    return items


def check_history(data: dict[str, Any], scenes: dict[str, Any], threads: dict[str, Any]) -> list[str]:
    expected = historical_inputs(scenes, threads)
    ids = [x["id"] for x in data["items"]]
    problems = [] if ids == [x["id"] for x in expected] else ["Historical IDs/order do not match inputs"]
    source = {x["id"]: x for x in expected}
    base_ids = {x["id"] for x in expected if x["kind"] != "encounter"}
    for item in data["items"]:
        row = source.get(item["id"])
        if row is None:
            continue
        if row["kind"] == "encounter":
            if item["encounter_value"] not in {"none", "low", "medium", "high"} or not item["encounter_basis"].strip():
                problems.append(f"{item['id']}: encounter needs an honest value and basis")
            if not set(item["focus_beats"]) <= {b["id"] for b in row["beats"]}:
                problems.append(f"{item['id']}: focus cites beats outside this encounter")
            if item["encounter_value"] in {"medium", "high"} and not item["focus_beats"]:
                problems.append(f"{item['id']}: noteworthy encounter needs supporting beats")
            if not set(item["represented_by"]) <= base_ids:
                problems.append(f"{item['id']}: unknown historical representative")
        elif (item["encounter_value"] is not None or item["encounter_basis"]
              or item["focus_beats"] or item["represented_by"]):
            problems.append(f"{item['id']}: encounter-only fields set on a thread/event")
    return problems


def select_history(changes: dict[str, Any], scenes: dict[str, Any], threads: dict[str, Any]) -> list[dict[str, Any]]:
    problems = check_history(changes, scenes, threads)
    if problems:
        raise ValueError("Invalid historical coverage: " + "; ".join(problems))
    source = {x["id"]: x for x in historical_inputs(scenes, threads)}
    order = {b["id"]: i for i, b in enumerate(b for s in scenes["scenes"] for b in s["beats"])}
    good = {"medium", "high"}
    shown_base = {x["id"] for x in changes["items"] if source[x["id"]]["kind"] != "encounter"
                  and x["narrative_impact"] in good and x["lasting_consequence"] in good}
    result = []
    for item in changes["items"]:
        row = source[item["id"]]
        encounter = row["kind"] == "encounter"
        represented = set(item["represented_by"]) & shown_base
        if encounter:
            shown = item["encounter_value"] in good and not represented
            reason = ("same main event represented by " + ", ".join(sorted(represented)) if represented else
                      "encounter value " + item["encounter_value"] + "; independent of lasting consequence")
        else:
            shown = item["id"] in shown_base
            reason = "thread/event requires impact and lasting consequence both medium or high"
        focus = item["focus_beats"] if encounter else [b["id"] for b in row["beats"]]
        position = min(order[b] for b in focus) if focus else order[row["beats"][0]["id"]]
        result.append(item | {"kind": row["kind"], "name": row["name"], "first": position,
                              "beats": len(focus), "shown": shown, "publication_reason": reason})
    return sorted(result, key=lambda x: x["first"])
