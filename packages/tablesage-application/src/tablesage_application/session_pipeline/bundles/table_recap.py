"""Standalone Table Recap input and assembly; no application imports."""

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class TableRecapPromptInputs:
    scene_log: dict[str, Any]
    target_words: int | None = None
    orientation_words: int | None = None

    def __post_init__(self) -> None:
        if (self.target_words is None) != (self.orientation_words is None):
            raise ValueError("target_words and orientation_words must be given together or both omitted")
        if self.target_words is None:
            return
        for name in ("target_words", "orientation_words"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        assert self.orientation_words is not None
        if self.orientation_words >= self.target_words:
            raise ValueError("orientation_words must be smaller than target_words")

    def to_template_context(self) -> dict[str, str]:
        endcap = self.scene_log["endcap"]
        return {
            "target_words": "" if self.target_words is None else str(self.target_words),
            "orientation_words": "" if self.orientation_words is None else str(self.orientation_words),
            "end_situation": endcap["end_situation"],
            "session_matters": json.dumps(endcap["session_matters"], ensure_ascii=False, indent=2),
            "scene_moments": json.dumps(
                [{"scene_title": scene["title"], "moments": scene["scene_moments"]} for scene in self.scene_log["scenes"]],
                ensure_ascii=False,
                indent=2,
            ),
        }

    def assemble(self, generated: dict[str, Any]) -> dict[str, Any]:
        if set(generated) != {"orientation", "threads"}:
            raise ValueError("Expected only orientation and threads in the generated response")
        texts = [generated["orientation"]]
        for thread in generated["threads"]:
            if set(thread) != {"label", "text"}:
                raise ValueError("Each thread needs only a label and text")
            texts += [thread["label"], thread["text"]]
        for text in texts:
            if not isinstance(text, str) or not text.strip() or "\n" in text or "\r" in text:
                raise ValueError("Recap text must be nonempty single-line strings")
        return {"orientation": generated["orientation"], "threads": list(generated["threads"])}


def word_counts(recap: dict[str, Any]) -> dict[str, int]:
    orientation = len(recap["orientation"].split())
    threads = sum(len(t["label"].split()) + len(t["text"].split()) for t in recap["threads"])
    return {"orientation": orientation, "threads": threads, "total": orientation + threads}
