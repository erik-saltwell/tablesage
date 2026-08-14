from __future__ import annotations

from tablesage_model.model import Player
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.events import Click
from textual.message import Message
from textual.widgets import Static


class PlayerDetailWidget(Horizontal):
    class Selected(Message):
        def __init__(self, player_slug: str) -> None:
            super().__init__()
            self.player_slug = player_slug

    def __init__(self, player: Player) -> None:
        super().__init__(classes="player-detail-item")
        self.can_focus = True
        self.player = player

    @property
    def player_slug(self) -> str:
        return self.player.slug

    def compose(self) -> ComposeResult:
        yield Static(str(len(self.player.voice_samples)), classes="player-clip-count")
        yield Static(self.player.name, classes="player-name")

    def on_click(self, event: Click) -> None:
        event.stop()
        self.focus()
        self.post_message(self.Selected(self.player.slug))

    def on_focus(self) -> None:
        self.post_message(self.Selected(self.player.slug))


class PlayerList(VerticalScroll):
    def __init__(self, players: tuple[Player, ...], *, id: str | None = None) -> None:
        super().__init__(id=id)
        self.players = players

    def compose(self) -> ComposeResult:
        for player in self.players:
            yield PlayerDetailWidget(player)
