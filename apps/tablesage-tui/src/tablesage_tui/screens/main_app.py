from __future__ import annotations

from dotenv import load_dotenv
from tablesage_model.model import CampaignSummary
from textual.app import App

from ..viewmodel import ModelStore
from .campaigns import CampaignsScreen
from .no_campaigns import NoCampaignsScreen


class TableSageApp(App):
    CSS_PATH = ["../styles/app.tcss"]

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, model_store: ModelStore | None = None) -> None:
        super().__init__()
        self.model_store = model_store or ModelStore()
        self.model_store.prepare_tablesage_dir()

    async def switch_to_campaign_screen(self) -> None:
        campaigns: tuple[CampaignSummary, ...] = self.model_store.load_campaigns()
        if len(campaigns) == 0:
            await self.push_screen(NoCampaignsScreen())
        else:
            await self.push_screen(CampaignsScreen(campaigns))

    async def on_mount(self) -> None:
        await self.switch_to_campaign_screen()

    async def on_screen_resume(self) -> None:
        await self.switch_to_campaign_screen()

    @property
    def store(self) -> ModelStore:
        return self.model_store


def main() -> None:
    load_dotenv()
    app = TableSageApp()
    app.run()


if __name__ == "__main__":
    main()
