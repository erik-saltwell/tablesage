"""Experiment #7 driver: sweep `MarginAndSimilarityMatcher`'s three knobs (base margin,
best-similarity OR-gate, and a duration-conditioned margin override) against `production`, using
production's actual embedder (`wespeaker-resnet34`). See
`.scratch/speaker-id-experiments/experiments-log.md`'s experiment #7 row and
`benchmarks/speaker_id/matchers.py`'s `MarginAndSimilarityMatcher` docstring.

Reuses the cached embeddings from prior experiments -- no new embedding computation, this is a
pure matching/scoring sweep, same method as experiment #1's threshold_sweep.py.

Usage (from the repo root, inside the venv):

    uv run python .scratch/speaker-id-experiments/run_experiment_7.py
"""

from __future__ import annotations

import asyncio
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE_ROOT))

from tablesage_application.paths import players_root  # noqa: E402
from tablesage_tools.embeddings.types import Embedding  # noqa: E402

from benchmarks.speaker_id.cache import EmbeddingCache  # noqa: E402
from benchmarks.speaker_id.centroid import build_centroids  # noqa: E402
from benchmarks.speaker_id.embedders import WeSpeakerResNet34Embedder  # noqa: E402
from benchmarks.speaker_id.harness import REPO_ROOT, GroundTruthSession, _embed_utterances, load_sessions  # noqa: E402
from benchmarks.speaker_id.matchers import MarginAndSimilarityMatcher, MarginThresholdMatcher  # noqa: E402
from benchmarks.speaker_id.scoring import SessionScore, pool, score_session  # noqa: E402
from benchmarks.speaker_id.types import Embedder, Matcher  # noqa: E402

MARGIN_THRESHOLDS = [0.06, 0.07, 0.08, 0.09, 0.10]
BEST_SIMILARITY_THRESHOLDS = [None, 0.30, 0.325, 0.35, 0.375, 0.40, 0.425, 0.45]
DURATION_MINIMUMS_SECONDS = [1.0, 1.5, 2.0, 2.5, 3.0]
DURATION_MARGIN_THRESHOLDS = [0.0, 0.02, 0.04, 0.06]
OUTPUT_CSV = Path(__file__).resolve().parent / "experiment-7-grid-results.csv"


@dataclass(frozen=True)
class GridPoint:
    margin_threshold: float
    best_similarity_threshold: float | None
    duration_minimum_seconds: float | None
    duration_margin_threshold: float | None

    @property
    def duration_overrides(self) -> tuple[tuple[float, float], ...]:
        if self.duration_minimum_seconds is None or self.duration_margin_threshold is None:
            return ()
        return ((self.duration_minimum_seconds, self.duration_margin_threshold),)


@dataclass(frozen=True)
class PreparedSession:
    session: GroundTruthSession
    embeddings: dict[int, Embedding]
    centroids: dict[str, Embedding]
    durations: dict[int, float]
    ground_truth: dict[int, tuple[str, float]]


def _grid() -> list[GridPoint]:
    duration_options: list[tuple[float | None, float | None]] = [(None, None)]
    duration_options.extend((minimum, threshold) for minimum in DURATION_MINIMUMS_SECONDS for threshold in DURATION_MARGIN_THRESHOLDS)
    return [
        GridPoint(margin, best_similarity, duration_minimum, duration_margin)
        for margin in MARGIN_THRESHOLDS
        for best_similarity in BEST_SIMILARITY_THRESHOLDS
        for duration_minimum, duration_margin in duration_options
    ]


def _prepare_sessions(sessions: list[GroundTruthSession], embedder: Embedder, cache: EmbeddingCache) -> list[PreparedSession]:
    prepared = []
    for session in sessions:
        durations = {index: utterance.end - utterance.start for index, utterance in enumerate(session.transcript.utterances)}
        prepared.append(
            PreparedSession(
                session=session,
                embeddings=asyncio.run(_embed_utterances(session, embedder, cache)),
                centroids=build_centroids(session.attendees, players_root(REPO_ROOT), embedder, cache),
                durations=durations,
                ground_truth={
                    index: (utterance.speaker, durations[index]) for index, utterance in enumerate(session.transcript.utterances)
                },
            )
        )
    return prepared


def _score_matcher(name: str, matcher: Matcher, sessions: list[PreparedSession]) -> list[SessionScore]:
    return [
        score_session(
            session.session.name,
            name,
            session.ground_truth,
            matcher.match(session.embeddings, session.centroids, session.durations),
        )
        for session in sessions
    ]


def _row(point: GridPoint | None, score: SessionScore) -> dict[str, object]:
    return {
        "candidate": score.candidate_name,
        "margin_threshold": None if point is None else point.margin_threshold,
        "best_similarity_threshold": None if point is None else point.best_similarity_threshold,
        "duration_minimum_seconds": None if point is None else point.duration_minimum_seconds,
        "duration_margin_threshold": None if point is None else point.duration_margin_threshold,
        "session": score.session_name,
        "utterance_count": score.utterance_count,
        "score": score.score,
        "accuracy": score.accuracy,
        "unassigned_rate": score.unassigned_rate,
        "error_rate": score.error_rate,
        "misattributed_seconds": score.misattributed_seconds,
        "correct_count": score.correct_count,
        "unassigned_count": score.unassigned_count,
        "wrong_count": score.wrong_count,
    }


def _describe(score: SessionScore) -> str:
    return (
        f"{score.candidate_name}: score={score.score:.3f}, accuracy={score.accuracy:.1%}, "
        f"unassigned={score.unassigned_rate:.1%}, error={score.error_rate:.1%}, "
        f"misattributed={score.misattributed_seconds:.1f}s"
    )


def main() -> None:
    embedder = WeSpeakerResNet34Embedder()
    sessions = load_sessions()
    cache = EmbeddingCache()
    prepared_sessions = _prepare_sessions(sessions, embedder, cache)
    cache.save()

    baseline_name = "production"
    baseline_matcher = MarginThresholdMatcher(
        similarity_margin_threshold=0.08,
        allow_unassigned=True,
    )
    rows: list[dict[str, object]] = []
    scores_by_candidate: dict[str, list[SessionScore]] = {}

    baseline_scores = _score_matcher(baseline_name, baseline_matcher, prepared_sessions)
    scores_by_candidate[baseline_name] = baseline_scores
    for score in [*baseline_scores, pool(baseline_scores, baseline_name)]:
        rows.append(_row(None, score))

    for point in _grid():
        matcher = MarginAndSimilarityMatcher(
            margin_threshold=point.margin_threshold,
            best_similarity_threshold=point.best_similarity_threshold,
            duration_overrides=point.duration_overrides,
        )
        session_scores = _score_matcher(matcher.name, matcher, prepared_sessions)
        scores_by_candidate[matcher.name] = session_scores
        for score in [*session_scores, pool(session_scores, matcher.name)]:
            rows.append(_row(point, score))

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    pooled_scores = [pool(scores, name) for name, scores in scores_by_candidate.items()]
    best_pooled = max(pooled_scores, key=lambda score: score.score)
    print(f"Evaluated {len(scores_by_candidate) - 1} grid points against {len(sessions)} sessions.")
    print(f"Baseline pooled: {_describe(pool(baseline_scores, baseline_name))}")
    print(f"Best pooled:     {_describe(best_pooled)}")
    for score in scores_by_candidate[best_pooled.candidate_name]:
        print(f"  {_describe(score)}")

    # With only two sessions, a cheap robustness check is to select the winner on each session
    # separately and show how that exact rule scores on the held-out session.
    print("Leave-one-session-out selection:")
    for training_index, training_session in enumerate(sessions):
        winner_name = max(
            (name for name in scores_by_candidate if name != baseline_name),
            key=lambda name: scores_by_candidate[name][training_index].score,
        )
        training_score = scores_by_candidate[winner_name][training_index]
        held_out_score = scores_by_candidate[winner_name][1 - training_index]
        print(f"  selected on {training_session.name}: {_describe(training_score)}")
        print(f"    held out: {_describe(held_out_score)}")

    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
