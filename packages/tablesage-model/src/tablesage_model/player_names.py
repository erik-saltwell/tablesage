import unicodedata


def validate_player_name(name: object) -> str:
    """Validate a player name used verbatim as a single directory component."""
    if not isinstance(name, str):
        raise ValueError("name must be a string")
    if not name.strip():
        raise ValueError("name must not be blank")
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("name must not contain path separators or be '.' or '..'")
    if any(unicodedata.category(character) in {"Cc", "Cs"} for character in name):
        raise ValueError("name must not contain control characters or invalid Unicode")
    if len(name.encode("utf-8")) > 255:
        raise ValueError("name must be at most 255 UTF-8 bytes")
    return name


def player_name_key(name: str) -> str:
    """The form player names are compared in: two names with the same key are the same player name."""
    return name.strip().casefold()
