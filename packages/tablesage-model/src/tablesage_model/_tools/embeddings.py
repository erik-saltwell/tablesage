from __future__ import annotations

import asyncio
import sys
import types
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import torch
import torchaudio

from ..model.cast import Embedding


def _patch_torchaudio_sox_effects() -> None:
    """Shim torchaudio.sox_effects for torchaudio 2.10+ where it was removed.

    ModelScope's speaker verification pipeline calls
    torchaudio.sox_effects.apply_effects_tensor() to resample audio.
    We replace it with torchaudio.functional.resample.
    """
    if "torchaudio.sox_effects" in sys.modules or hasattr(torchaudio, "sox_effects"):
        return

    def apply_effects_tensor(tensor: torch.Tensor, sample_rate: int, effects: list[list[str]]) -> tuple[torch.Tensor, int]:
        for effect in effects:
            if effect[0] == "rate":
                new_rate = int(effect[1])
                tensor = torchaudio.functional.resample(tensor, sample_rate, new_rate)
                sample_rate = new_rate
                continue
            msg = f"Unsupported torchaudio sox effect: {effect[0]}"
            raise NotImplementedError(msg)
        return tensor, sample_rate

    sox = types.ModuleType("torchaudio.sox_effects")
    sox.apply_effects_tensor = apply_effects_tensor  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[unresolved-attribute]
    torchaudio.sox_effects = sox  # pyright: ignore[reportAttributeAccessIssue]  # ty: ignore[unresolved-attribute]
    sys.modules["torchaudio.sox_effects"] = sox


_patch_torchaudio_sox_effects()


@dataclass
class EmbeddingFactory:
    """Speaker embedding extractor using ModelScope's ERes2NetV2 model.

    Produces a 192-dimensional L2-normalized speaker embedding from a WAV file.
    Model: iic/speech_eres2netv2_sv_zh-cn_16k-common (downloaded on first use).

    The pipeline is initialized once at construction and reused across extract() calls.
    """

    model_id: str = "iic/speech_eres2netv2_sv_zh-cn_16k-common"
    device: str = "cuda"
    _pipe: Any = field(init=False, repr=False)

    def __post_init__(self) -> None:
        from modelscope.pipelines import pipeline
        from modelscope.utils.constant import Tasks

        self._pipe = pipeline(task=Tasks.speaker_verification, model=self.model_id, device=self.device)

    def extract(self, audio_path: Path) -> Embedding:
        with torch.no_grad():
            result: Any = self._pipe([str(audio_path.resolve())], output_emb=True)
        # result['embs'] is a numpy array of shape [N, 192]; take the first (and only) row
        emb = result["embs"][0]
        embedding = Embedding(root=tuple(float(x) for x in emb))
        return embedding

    async def extract_async(self, audio_path: Path) -> Embedding:
        return await asyncio.to_thread(self.extract, audio_path)


def compute_centroid(embeddings: Sequence[Embedding]) -> Embedding:
    """Return the L2-normalized mean of the given embeddings.

    All embeddings must share the same dimensionality. The result is suitable
    for use as a single reference vector in cosine-similarity comparisons.
    """
    if not embeddings:
        msg = "Cannot compute centroid of empty embedding collection."
        raise ValueError(msg)
    stacked = torch.tensor([e.root for e in embeddings], dtype=torch.float32)
    mean = stacked.mean(dim=0)
    normalized = torch.nn.functional.normalize(mean, p=2, dim=0)
    return Embedding(root=tuple(float(x) for x in normalized))


@dataclass
class SimilarityResult:
    best_match_index: int
    best_match_similarity: float
    mean_similarity: float
    margin: float


@dataclass
class SimilarityComputer:
    references: tuple[Embedding, ...]
    references_tensor: torch.Tensor = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if len(self.references) < 2:
            msg = "Cannot compute similarity with less than 2 embeddings."
            raise ValueError(msg)
        self.references_tensor = torch.tensor([r.root for r in self.references], dtype=torch.float32)

    def compute_similarity(self, candidate: Embedding) -> SimilarityResult:
        test_tensor = torch.tensor(candidate.root, dtype=torch.float32).unsqueeze(0)
        similarities: list[float] = [float(s) for s in torch.nn.functional.cosine_similarity(test_tensor, self.references_tensor)]
        avg_similarity: float = sum(similarities) / len(similarities)
        ranked = sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)
        best_match_index, best_similarity = ranked[0]
        second_best_similarity = ranked[1][1]
        return SimilarityResult(
            best_match_index=best_match_index,
            mean_similarity=avg_similarity,
            margin=best_similarity - second_best_similarity,
            best_match_similarity=best_similarity,
        )
