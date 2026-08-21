from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from ..audio.ffmpeg import extract_clip
from ..embeddings.eres2netv2 import EmbeddingFactory
from ..embeddings.similarity import SimilarityComputer, SimilarityResult
from ..embeddings.types import Embedding
from ..model.transcript import Transcript, Utterance

UNASSIGNED_SPEAKER: Final[str] = "Unassigned Speaker"


async def identify_speakers(
    transcript: Transcript,
    audio_path: Path,
    centroids: dict[str, Embedding],
    embed: EmbeddingFactory,
    similarity_margin_threshold: float,
    on_progress: Callable[[int, int], None] | None = None,
) -> Transcript:
    """Relabel each utterance's speaker with the best-matching player name, or UNASSIGNED_SPEAKER.

    For each utterance, extracts its audio clip from `audio_path`, embeds it, and compares it
    against every player's centroid in `centroids`. If the margin between the best and
    second-best match is below `similarity_margin_threshold`, the utterance is left as
    UNASSIGNED_SPEAKER rather than guessed. Raises ValueError if `centroids` has fewer than 2
    entries (see SimilarityComputer).
    """
    names = list(centroids)
    similarity_computer = SimilarityComputer(tuple(centroids[name] for name in names))

    total = len(transcript.utterances)
    new_utterances: list[Utterance] = []
    with TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "tmp.wav"
        for index, utterance in enumerate(transcript.utterances):
            await extract_clip(audio_path, tmp_file, utterance.start, utterance.end)

            embedding = await embed.extract_async(tmp_file)
            result: SimilarityResult = similarity_computer.compute_similarity(embedding)
            speaker = UNASSIGNED_SPEAKER if result.margin < similarity_margin_threshold else names[result.best_match_index]
            new_utterances.append(utterance.model_copy(update={"speaker": speaker}))

            if on_progress is not None:
                on_progress(index + 1, total)

    return Transcript(utterances=new_utterances)
