"""Rendering and structural checks preserved from the handcrafted workflow."""

TEXT_FIELDS = {"narration": "fact", "action": "action", "speech": "statement", "expression": "sentiment", "correction": "revision"}


def check_ledger(data: dict, attendees: list[dict]) -> list[str]:
    """Structural checks only; they do not assess fidelity or completeness."""
    players = {attendee["player_name"] for attendee in attendees}
    problems = []
    for number, entry in enumerate(data["ledger"]["utterances"], 1):
        if any(isinstance(value, str) and not value.strip() for value in entry.values()):
            problems.append(f"entry {number}: blank text field")
        if entry["type"] == "question":
            if (entry["resolver"] is None) != (entry["resolution"] is None):
                problems.append(f"entry {number}: resolver and resolution must both be null or both have values")
            if entry["asker"] not in players or (entry["resolver"] is not None and entry["resolver"] not in players):
                problems.append(f"entry {number}: question attribution must use attendee player names")
    return problems


def entry_line(number: int, entry: dict) -> str:
    kind = entry["type"]
    if kind == "question":
        answer = f" → {entry['resolver']}: {entry['resolution']}" if entry["resolver"] else " → (unanswered)"
        return f"{number}. [question] {entry['asker']}: {entry['question']}{answer}"
    who = entry.get("entity") or entry["source"]
    via = f" (via {entry['source']})" if entry.get("entity") and entry["source"] != entry["entity"] else ""
    return f"{number}. [{kind}] {who}{via}: {entry[TEXT_FIELDS[kind]]}"


def to_markdown(data: dict, label: str) -> str:
    lines = [f"# Ledger: {label}", ""]
    if data.get("starting_situation"):
        lines.extend([f"**Starting situation:** {data['starting_situation']}", ""])
    lines.extend(entry_line(number, entry) for number, entry in enumerate(data["ledger"]["utterances"], 1))
    return "\n".join(lines) + "\n"
