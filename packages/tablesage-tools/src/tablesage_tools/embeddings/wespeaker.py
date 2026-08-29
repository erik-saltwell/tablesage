from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .types import Embedding


def _patch_torchaudio_set_audio_backend() -> None:
    """`wespeaker` (via s3prl, an unused-here transitive import in its package `__init__.py`)
    calls the removed `torchaudio.set_audio_backend` at import time. Same class of torchaudio
    2.10+ removal as `eres2netv2._patch_torchaudio_sox_effects`; shim it the same way (a no-op,
    since backend selection is meaningless post-dispatcher-removal) rather than pin an older
    torchaudio.
    """
    import torchaudio

    if not hasattr(torchaudio, "set_audio_backend"):
        torchaudio.set_audio_backend = lambda *args, **kwargs: None  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[unresolved-attribute]


_patch_torchaudio_set_audio_backend()

# eres2netv2's own patch is needed too -- wespeaker's transitive s3prl import also hits the
# removed torchaudio.sox_effects API.
from .eres2netv2 import _patch_torchaudio_sox_effects  # noqa: E402

_patch_torchaudio_sox_effects()

_MODEL_SOURCE = "Wespeaker/wespeaker-voxceleb-resnet34-LM"


def _local_model_dir() -> Path:
    """Download `config.yaml` + `avg_model` from the model's Hugging Face repo (there's no
    official PyPI `wespeaker` hub alias for this specific checkpoint -- its bundled `"english"`
    shortcut resolves to a different, larger model) into our own stable cache directory, renaming
    `avg_model` -> `avg_model.pt` to match `wespeaker.load_model_pt`'s expected layout. Writing
    into `huggingface_hub`'s own managed cache dir alongside its snapshot would work too, but this
    keeps us independent of that cache's internal layout.
    """
    from huggingface_hub import hf_hub_download

    local_dir = Path.home() / ".cache" / "tablesage" / "wespeaker-voxceleb-resnet34-lm"
    local_dir.mkdir(parents=True, exist_ok=True)
    if not (local_dir / "avg_model.pt").exists():
        config_path = Path(hf_hub_download(_MODEL_SOURCE, "config.yaml"))
        avg_model_path = Path(hf_hub_download(_MODEL_SOURCE, "avg_model"))
        (local_dir / "config.yaml").write_bytes(config_path.read_bytes())
        (local_dir / "avg_model.pt").write_bytes(avg_model_path.read_bytes())
    return local_dir


@dataclass
class EmbeddingFactory:
    """Speaker embedding extractor using WeSpeaker's ResNet34-LM (VoxCeleb2-trained, English) --
    see `.scratch/speaker-id-experiments/03-wespeaker-resnet34-embedder.md` and
    `05-threshold-sweep-leaders.md` for why this replaced `eres2netv2.EmbeddingFactory` (a
    Mandarin-trained model previously used off-domain on English speech) as the production
    embedder.

    Produces a 256-dimensional L2-normalized speaker embedding from a WAV file. No `device`
    parameter, unlike `eres2netv2.EmbeddingFactory` -- always runs on CPU: `wespeaker`'s fbank
    feature-extraction path doesn't move its output tensor to the model's device before the
    forward pass, so moving the model to CUDA via `Speaker.set_device` causes a device-mismatch
    error. The pipeline is initialized once at construction and reused across extract() calls.
    """

    _speaker: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        import contextlib
        import io

        import wespeaker

        local_dir = _local_model_dir()
        # wespeaker.load_model_pt (called internally) does a bare print(config) -- harmless in a
        # normal terminal, but the TUI renders to Textual's alternate screen buffer, where a
        # stray direct-to-stdout print corrupts the display. Swallow it rather than let it leak.
        with contextlib.redirect_stdout(io.StringIO()):
            self._speaker = wespeaker.load_model(str(local_dir))

    def extract(self, audio_path: Path) -> Embedding:
        import soundfile
        import torch

        # Not self._speaker.extract_embedding(path) -- it calls torchaudio.load, which in this
        # torchaudio version dispatches to a torchcodec backend that isn't installed. Read the
        # clip with soundfile instead and hand raw PCM to the lower-level API directly.
        pcm, sample_rate = soundfile.read(str(audio_path.resolve()), dtype="float32", always_2d=True)
        pcm_tensor = torch.from_numpy(pcm.T)  # (channels, samples), matching torchaudio.load's layout
        with torch.no_grad():
            raw = self._speaker.extract_embedding_from_pcm(pcm_tensor, sample_rate)
            normalized = torch.nn.functional.normalize(raw, p=2, dim=0)
        return Embedding(root=tuple(float(x) for x in normalized))

    async def extract_async(self, audio_path: Path) -> Embedding:
        return await asyncio.to_thread(self.extract, audio_path)
