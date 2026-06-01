from pathlib import Path

import pytest
from tablesage_model.setup import setup_root_dir


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    data_dir = tmp_path / "tablesage-data"
    data_dir.mkdir()

    monkeypatch.setenv("TABLESAGE_DATA_DIR", str(data_dir))

    return data_dir


@pytest.fixture(autouse=True)
def setup_data_dir(isolated_data_dir: Path) -> None:
    setup_root_dir()
