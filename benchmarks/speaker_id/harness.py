"""Orchestration: load the frozen ground-truth sessions, run each registered candidate, score,
report. See run.py for the entrypoint and .documentation/speaker_identification_benchmark.md for
the design this implements.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from tablesage_application.paths import players_root
from tablesage_tools.audio.ffmpeg import extract_clip
from tablesage_tools.embeddings.types import Embedding
from tablesage_tools.model import Transcript

from .cache import EmbeddingCache, utterance_cache_key
from .centroid import build_centroids
from .scoring import SessionScore, print_report, score_session
from .types import Candidate, Embedder

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class GroundTruthSession:
    name: str
    audio_path: Path
    transcript: Transcript

    @property
    def attendees(self) -> list[str]:
        return sorted({utterance.speaker for utterance in self.transcript.utterances})


def load_sessions(data_root: Path = DATA_ROOT) -> list[GroundTruthSession]:
    sessions = []
    for session_dir in sorted(p for p in data_root.iterdir() if p.is_dir()):
        transcript = Transcript.load(session_dir / "ground_truth.json")
        sessions.append(GroundTruthSession(name=session_dir.name, audio_path=session_dir / "audio.wav", transcript=transcript))
    return sessions


async def _embed_utterances(session: GroundTruthSession, embedder: Embedder, cache: EmbeddingCache) -> dict[int, Embedding]:
    embeddings: dict[int, Embedding] = {}
    with TemporaryDirectory() as tmpdir:
        tmp_file = Path(tmpdir) / "tmp.wav"
        for index, utterance in enumerate(session.transcript.utterances):
            key = utterance_cache_key(embedder, session.name, index)
            cached = cache.get(key)
            if cached is not None:
                embeddings[index] = cached
                continue
            await extract_clip(session.audio_path, tmp_file, utterance.start, utterance.end)
            embedding = embedder.embed(tmp_file)
            cache.set(key, embedding)
            embeddings[index] = embedding
    return embeddings


def run_candidate(candidate: Candidate, sessions: list[GroundTruthSession], cache: EmbeddingCache) -> list[SessionScore]:
    scores = []
    for session in sessions:
        centroids = build_centroids(session.attendees, players_root(REPO_ROOT), candidate.embedder, cache)
        embeddings = asyncio.run(_embed_utterances(session, candidate.embedder, cache))
        predictions = candidate.matcher.match(embeddings, centroids)
        ground_truth = {
            index: (utterance.speaker, utterance.end - utterance.start) for index, utterance in enumerate(session.transcript.utterances)
        }
        scores.append(score_session(session.name, candidate.name, ground_truth, predictions))
    return scores


def run(candidates: list[Candidate]) -> None:
    sessions = load_sessions()
    cache = EmbeddingCache()
    scores_by_candidate: dict[str, list[SessionScore]] = {}
    for candidate in candidates:
        scores_by_candidate[candidate.name] = run_candidate(candidate, sessions, cache)
        cache.save()  # after each candidate, not just at the end -- a slow run shouldn't lose progress if interrupted
    print_report(scores_by_candidate)
