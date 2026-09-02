from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def _jsonable(value: object) -> object:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, str | int | float | bool) or value is None:
        return value
    return repr(value)


class LedgerRunObserver:
    """Persist generic Prompt Forge lifecycle events for later human review."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir: Path = output_dir.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._event_path: Path = self.output_dir / "events.jsonl"

    def _append(self, event_type: str, event: object) -> None:
        record: dict[str, Any] = {
            "recorded_at": datetime.now(UTC).isoformat(),
            "type": event_type,
            "event": _jsonable(event),
        }
        with self._event_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")

    def target_completed(self, event: object) -> None:
        self._append("target_completed", event)

    def metrics_completed(self, event: object) -> None:
        self._append("metrics_completed", event)

    def optimization_completed(self, event: object) -> None:
        self._append("optimization_completed", event)
        (self.output_dir / "result.json").write_text(
            json.dumps(_jsonable(event), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def optimization_failed(self, event: object) -> None:
        self._append("optimization_failed", event)
