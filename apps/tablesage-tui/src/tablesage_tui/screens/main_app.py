from __future__ import annotations

from textual.app import App
from textual.containers import Container

from .no_campaigns import NoCampaignsScreen


class Empty(Container): ...


class TableSageApp(App):
    CSS_PATH = ["../styles/app.tcss"]

    ENABLE_COMMAND_PALETTE = False

    async def switch_to_campaign_screen(self) -> None:
        await self.push_screen(NoCampaignsScreen())

    async def on_mount(self) -> None:
        await self.switch_to_campaign_screen()

    async def on_screen_resume(self) -> None:
        await self.switch_to_campaign_screen()


def main() -> None:
    app = TableSageApp()
    app.run()


if __name__ == "__main__":
    main()
