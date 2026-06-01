from __future__ import annotations

from dotenv import load_dotenv
from tablesage_model.model import CampaignSet
from textual.app import App

from ..viewmodel import ModelStore
from .campaigns import CampaignsScreen
from .no_campaigns import NoCampaignsScreen


class TableSageApp(App):
    CSS_PATH = ["../styles/app.tcss"]

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, model_store: ModelStore | None = None) -> None:
        super().__init__()
        self.model_strore = model_store or ModelStore()
        self.model_strore.prepare_tablesage_dir()

    async def switch_to_campaign_screen(self) -> None:
        campaigns: CampaignSet = self.model_strore.load_campaigns()
        if len(campaigns.campaigns) == 0:
            await self.push_screen(NoCampaignsScreen())
        else:
            await self.push_screen(CampaignsScreen(campaigns))

    async def on_mount(self) -> None:
        await self.switch_to_campaign_screen()

    async def on_screen_resume(self) -> None:
        await self.switch_to_campaign_screen()


def main() -> None:
    load_dotenv()
    app = TableSageApp()
    app.run()


if __name__ == "__main__":
    main()
