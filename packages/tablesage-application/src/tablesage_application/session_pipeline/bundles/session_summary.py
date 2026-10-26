"""Standalone Summary input and deterministic assembly; no application imports."""

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass
class SessionSummaryPromptInputs:
    scene_log: dict[str, Any]

    def to_template_context(self) -> dict[str, str]:
        return {
            "opening_situation": json.dumps(self.scene_log["opening_situation"], ensure_ascii=False),
            "scenes": json.dumps(
                [{"scene_number": i, "scene": scene} for i, scene in enumerate(self.scene_log["scenes"], 1)], ensure_ascii=False, indent=2
            ),
        }

    def assemble(self, generated: dict[str, Any]) -> dict[str, Any]:
        if set(generated) != {"scenes"}:
            raise ValueError("Expected only scenes in the generated response")
        entries = generated["scenes"]
        numbers = [entry["scene_number"] for entry in entries]
        if numbers != list(range(1, len(self.scene_log["scenes"]) + 1)):
            raise ValueError("Require exactly one bullet-list entry per source scene in source order")
        scenes = []
        for source, entry in zip(self.scene_log["scenes"], entries, strict=True):
            bullets = entry["bullets"]
            if not isinstance(bullets, list) or not bullets:
                raise ValueError("Scene bullets must be a nonempty list")
            for bullet in bullets:
                if not isinstance(bullet, str) or not bullet.strip() or "\n" in bullet or "\r" in bullet:
                    raise ValueError("Each bullet must be nonempty single-line text")
                if bullet.lstrip().startswith(("- ", "* ", "# ", "• ")):
                    raise ValueError("Bullet markers and headings are caller-owned")
            scenes.append({"scene_number": entry["scene_number"], "title": source["title"], "bullets": deepcopy(bullets)})
        return {
            "opening_situation": self.scene_log["opening_situation"],
            "scenes": scenes,
            "endcap": deepcopy(self.scene_log["endcap"]),
        }
