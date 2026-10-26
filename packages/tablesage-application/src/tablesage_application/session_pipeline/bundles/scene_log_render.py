"""Rendering and structural checks preserved from the handcrafted workflow."""

import json
import re

GAME_MASTER = "Game Master"

LOCATION_WORDS = 8

TIME_WORDS = re.compile(r"\b(morning|evening|night|sunset|dawn|dusk|day|noon|afternoon|later)\b", re.I)

POSITION_WORDS = re.compile(r"\b(north|south|east|west|outside|inside|beneath|near|across|down|beyond|miles?)\b", re.I)


def party_roles(attendees: list[dict]) -> list[str]:
    return [role for attendee in attendees for role in attendee["roles"] if role != GAME_MASTER]


def check_scene_log(data: dict, attendees: list[dict]) -> tuple[list[str], dict]:
    """Structural checks only; they do not assess fidelity or completeness."""
    if data["session_cue"] not in [scene["scene_cue"] for scene in data["scenes"]]:
        raise ValueError("session_cue must exactly match one of the session scene cues")
    party = set(party_roles(attendees))
    players = {attendee["player_name"] for attendee in attendees}
    problems, seen = [], set()
    for number, scene in enumerate(data["scenes"], 1):
        for member in scene["participants"]["party_members"]:
            if member["name"] not in party:
                problems.append(f"scene {number}: party member {member['name']!r} is not an attending player character")
            seen.add(member["name"])
        for npc in scene["participants"]["non_player_characters"]:
            if npc["name"] in party or npc["name"] == GAME_MASTER:
                problems.append(f"scene {number}: {npc['name']!r} listed as a non-player character")
        text = json.dumps(scene, ensure_ascii=False)
        problems.extend(f"scene {number}: player name {name!r} appears" for name in players if name in text)
        location = scene["location"]
        if "," in location or len(location.split()) > LOCATION_WORDS or TIME_WORDS.search(location) or POSITION_WORDS.search(location):
            problems.append(f"scene {number}: location may describe rather than name the place: {location!r}")
        if len(scene["overview"].split()) > 20:
            problems.append(f"scene {number}: overview exceeds 20 words")
    problems.extend(f"party member {name!r} appears in no scene" for name in sorted(party - seen))
    # The empty second value keeps the (problems, labels) shape; open matter labels are no longer recorded.
    return problems, {}


SHOW_IMPORTANCE = True


def to_markdown(data: dict, label: str) -> str:
    # Review layout: cue as the title, low-importance items omitted, outcome as the final event.
    def tag(item: dict) -> str:
        return f"[{item['importance']}] " if SHOW_IMPORTANCE else ""

    lines = [f"# Scene log: {label}", "", f"**Session cue:** {data['session_cue']}", ""]
    for number, scene in enumerate(data["scenes"], 1):
        lines += [f"## {number}. {scene['scene_cue']}", f"**{scene['location']}:** {scene['overview']}", "", "**Events**"]
        lines += [f"- {tag(e)}{e['text']}" for e in scene["events"] if e["importance"] != "low"]
        lines.append(f"- **Outcome:** {scene['outcome']}")
        discoveries = [d for d in scene.get("discoveries", []) if d["importance"] != "low"]
        if discoveries:
            lines += ["", "**Discoveries**"] + [f"- {tag(d)}{d['text']}" for d in discoveries]
        lines.append("")
    return "\n".join(lines)
