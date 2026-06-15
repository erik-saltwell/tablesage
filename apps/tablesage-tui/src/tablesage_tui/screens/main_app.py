from __future__ import annotations

from dotenv import load_dotenv
from textual.app import App

from ..viewmodel import ModelStore


class TableSageApp(App):
    CSS_PATH = ["../styles/app.tcss"]

    ENABLE_COMMAND_PALETTE = False

    def __init__(self, model_store: ModelStore | None = None) -> None:
        super().__init__()
        self.model_store = model_store or ModelStore()

    @property
    def store(self) -> ModelStore:
        return self.model_store


def main() -> None:
    load_dotenv()
    app = TableSageApp()
    app.run()


if __name__ == "__main__":
    main()
