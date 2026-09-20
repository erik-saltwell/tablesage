from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..local_models import WESPEAKER_DIR, download_wespeaker, wespeaker_downloaded
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


def _local_model_dir() -> Path:
    if not wespeaker_downloaded():
        download_wespeaker()
    return WESPEAKER_DIR


@dataclass
class EmbeddingFactory:
    """Speaker embedding extractor using WeSpeaker's ResNet34-LM (VoxCeleb2-trained, English) --
    see the locally archived WeSpeaker experiment record for why this replaced
    `eres2netv2.EmbeddingFactory` (a
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
