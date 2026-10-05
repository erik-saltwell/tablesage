"""Launch the real Player screens with isolated, fictional screenshot samples.

Run with the TableSage environment:
    .venv/bin/python scripts/preview_player_review.py

Textual MCP: launch this file with factory `create_app`, size 160 x 44.
All database/filesystem operations are real and confined to a new temporary workspace.
Audio is synthetic tone data and embeddings are deterministic illustration fixtures,
not evidence for speaker-recognition accuracy. No provider/model downloads are used.
"""

from __future__ import annotations

import inspect
import math
import shutil
import struct
import tempfile
import wave
from pathlib import Path

from tablesage_application import Application
from tablesage_application.paths import player_folder
from tablesage_model.model import Player
from tablesage_model.setup import ensure_settings
from tablesage_tools.embeddings import Embedding
from tablesage_tui.resources import load_resource
from tablesage_tui.screens.main_app import TableSageApp
from tablesage_tui.screens.player_detail import PlayerDetailScreen


class FixtureApplication(Application):
    def __init__(self, cwd: Path) -> None:
        self.embeddings: dict[str, Embedding] = {}
        self.embed_count = 0
        super().__init__(cwd, settings=ensure_settings(cwd, load_resource("settings.yaml")))

    def _embed_clip(self, path: Path) -> Embedding:
        self.embed_count += 1
        return self.embeddings[path.name]


def create_fixture() -> tuple[FixtureApplication, Player]:
    workspace = Path(tempfile.mkdtemp(prefix="tablesage-player-review-"))
    app = FixtureApplication(workspace)
    player = app.create_player(Player(name="Priya Patel"))
    folder = player_folder(workspace, player.name)
    folder.mkdir(parents=True, exist_ok=True)
    for index in range(45):
        angle = -0.72 + 1.44 * index / 44
        filename = f"session-iron-pact-flooded-cistern-{index + 1:03d}.wav"
        seconds = 1.4 + (index % 9) * 0.4
        with wave.open(str(folder / filename), "wb") as audio:
            audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
            audio.writeframes(
                b"".join(struct.pack("<h", int(100 * math.sin(i * (index + 1) / 100))) for i in range(round(seconds * 16000)))
            )
        app.embeddings[filename] = Embedding(root=(math.cos(angle), math.sin(angle)))
    # One excluded outlier and one exact duplicate exercise permanent preparation cleanup.
    duplicate = "session-iron-pact-duplicate.wav"
    source = "session-iron-pact-flooded-cistern-023.wav"
    shutil.copyfile(folder / source, folder / duplicate)
    app.embeddings[duplicate] = app.embeddings[source]
    outlier = "session-iron-pact-wrong-voice.wav"
    shutil.copyfile(folder / source, folder / outlier)
    with (folder / outlier).open("ab") as audio:
        audio.write(b"fixture-outlier")
    app.embeddings[outlier] = Embedding(root=(-1.0, 0.0))
    app.recompute_voice_print(player.id)
    return app, app.get_player(player.id)


class PlayerReviewPreview(TableSageApp):
    TITLE = "TableSage"
    CSS_PATH = [Path(inspect.getfile(TableSageApp)).parent.parent / "styles" / "app.tcss"]

    def __init__(self) -> None:
        application, self.player = create_fixture()
        super().__init__(application)

    def on_mount(self) -> None:
        self.push_screen(PlayerDetailScreen(self.player.id))


def create_app() -> PlayerReviewPreview:
    return PlayerReviewPreview()


if __name__ == "__main__":
    create_app().run()
