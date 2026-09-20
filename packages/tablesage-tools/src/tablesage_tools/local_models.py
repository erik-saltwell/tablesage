"""Download-only checks for the local audio models, without loading any of them.

Each model is fetched into exactly the location its runtime loader reads, so a later
pipeline run finds it already present instead of downloading mid-run.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

_MOSSFORMER2_NAME = "MossFormer2_SE_48K"
# ClearVoice's packaged inference config uses this cwd-relative checkpoint directory.
_MOSSFORMER2_DIR = Path("checkpoints") / _MOSSFORMER2_NAME

WESPEAKER_SOURCE = "Wespeaker/wespeaker-voxceleb-resnet34-LM"
WESPEAKER_DIR = Path.home() / ".cache" / "tablesage" / "wespeaker-voxceleb-resnet34-lm"

# `punctuators`' "pcs_en" pretrained configuration.
_PUNCTUATION_REPO = "1-800-BAD-CODE/punct_cap_seg_en"
_PUNCTUATION_FILES = ("spe_32k_lc_en.model", "punct_cap_seg_en.onnx", "config.yaml")


@dataclass(frozen=True)
class LocalModel:
    name: str
    is_downloaded: Callable[[], bool]
    download: Callable[[], None]


def _mossformer2_downloaded() -> bool:
    return (_MOSSFORMER2_DIR / "last_best_checkpoint").is_file()


def _download_mossformer2() -> None:
    from huggingface_hub import snapshot_download

    _MOSSFORMER2_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(repo_id=f"alibabasglab/{_MOSSFORMER2_NAME}", local_dir=_MOSSFORMER2_DIR)


def wespeaker_downloaded() -> bool:
    return (WESPEAKER_DIR / "avg_model.pt").exists()


def download_wespeaker() -> None:
    """Download `config.yaml` + `avg_model` from the model's Hugging Face repo (there's no
    official PyPI `wespeaker` hub alias for this specific checkpoint -- its bundled `"english"`
    shortcut resolves to a different, larger model) into our own stable cache directory, renaming
    `avg_model` -> `avg_model.pt` to match `wespeaker.load_model_pt`'s expected layout. Writing
    into `huggingface_hub`'s own managed cache dir alongside its snapshot would work too, but this
    keeps us independent of that cache's internal layout.
    """
    from huggingface_hub import hf_hub_download

    WESPEAKER_DIR.mkdir(parents=True, exist_ok=True)
    config_path = Path(hf_hub_download(WESPEAKER_SOURCE, "config.yaml"))
    avg_model_path = Path(hf_hub_download(WESPEAKER_SOURCE, "avg_model"))
    (WESPEAKER_DIR / "config.yaml").write_bytes(config_path.read_bytes())
    (WESPEAKER_DIR / "avg_model.pt").write_bytes(avg_model_path.read_bytes())


def _punctuation_downloaded() -> bool:
    from huggingface_hub import try_to_load_from_cache

    return all(isinstance(try_to_load_from_cache(_PUNCTUATION_REPO, filename), str) for filename in _PUNCTUATION_FILES)


def _download_punctuation() -> None:
    from huggingface_hub import hf_hub_download

    for filename in _PUNCTUATION_FILES:
        hf_hub_download(repo_id=_PUNCTUATION_REPO, filename=filename)


LOCAL_MODELS: tuple[LocalModel, ...] = (
    LocalModel("MossFormer2 noise removal", _mossformer2_downloaded, _download_mossformer2),
    LocalModel("WeSpeaker voice embeddings", wespeaker_downloaded, download_wespeaker),
    LocalModel("Punctuation", _punctuation_downloaded, _download_punctuation),
)


def missing_local_models() -> list[LocalModel]:
    return [model for model in LOCAL_MODELS if not model.is_downloaded()]
