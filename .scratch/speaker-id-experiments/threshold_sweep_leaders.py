"""Experiment #5 driver: sweep `similarity_margin_threshold` for the two tied leaders from
experiments #3 and #4 (`wespeaker-resnet34`, `titanet-large`) to see whether threshold-tuning
reorders their near-tied pooled scores (0.902 vs. 0.906 at the shared threshold of 0.07, itself
tuned for a different embedder -- eres2netv2 -- not either of these).

Same method as experiment #1's threshold_sweep.py: reuses the harness's existing
embedder/centroid/matcher/scoring stages as a library rather than building a first-class sweep
mode (deferred out of scope -- see .documentation/speaker_identification_benchmark.md's
"Deferred" section). Does not import benchmarks/speaker_id/candidates.py -- that module eagerly
constructs an Eres2NetV2Embedder() at import time using the plain "iic/..." model_id, which hangs
retrying against modelscope.cn in this sandbox (see threshold_sweep.py's note); this sweep doesn't
need eres2netv2 at all, so it just builds the two embedders it does need directly.

Usage (from the repo root, inside the venv):

    uv run python .scratch/speaker-id-experiments/threshold_sweep_leaders.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from tablesage_application.paths import players_root  # noqa: E402

from benchmarks.speaker_id.cache import EmbeddingCache  # noqa: E402
from benchmarks.speaker_id.centroid import build_centroids  # noqa: E402
from benchmarks.speaker_id.embedders import TitanetLargeEmbedder, WeSpeakerResNet34Embedder  # noqa: E402
from benchmarks.speaker_id.harness import REPO_ROOT as HARNESS_REPO_ROOT  # noqa: E402
from benchmarks.speaker_id.harness import _embed_utterances, load_sessions  # noqa: E402
from benchmarks.speaker_id.matchers import MarginThresholdMatcher  # noqa: E402
from benchmarks.speaker_id.scoring import SessionScore, pool, score_session  # noqa: E402
from benchmarks.speaker_id.types import Embedder  # noqa: E402

THRESHOLDS = [round(0.01 * i, 2) for i in range(41)]  # 0.00 .. 0.40 step 0.01
OUTPUT_DIR = Path(__file__).resolve().parent


def sweep(embedder_name: str, embedder: Embedder) -> list[dict[str, object]]:
    import asyncio

    cache = EmbeddingCache()
    sessions = load_sessions()

    per_session_embeddings = {}
    per_session_centroids = {}
    per_session_ground_truth = {}
    for session in sessions:
        per_session_centroids[session.name] = build_centroids(session.attendees, players_root(HARNESS_REPO_ROOT), embedder, cache)
        per_session_embeddings[session.name] = asyncio.run(_embed_utterances(session, embedder, cache))
        per_session_ground_truth[session.name] = {
            index: (utterance.speaker, utterance.end - utterance.start) for index, utterance in enumerate(session.transcript.utterances)
        }
    cache.save()

    rows: list[dict[str, object]] = []
    for threshold in THRESHOLDS:
        matcher = MarginThresholdMatcher(similarity_margin_threshold=threshold, allow_unassigned=True)
        session_scores: list[SessionScore] = []
        for session in sessions:
            predictions = matcher.match(per_session_embeddings[session.name], per_session_centroids[session.name])
            session_scores.append(score_session(session.name, matcher.name, per_session_ground_truth[session.name], predictions))
        pooled = pool(session_scores, matcher.name)
        rows.append(
            {
                "threshold": threshold,
                "score": pooled.score,
                "accuracy": pooled.accuracy,
                "unassigned_rate": pooled.unassigned_rate,
                "error_rate": pooled.error_rate,
                "misattributed_seconds": pooled.misattributed_seconds,
            }
        )

    output_csv = OUTPUT_DIR / f"threshold-sweep-{embedder_name}.csv"
    with output_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    header = f"{'threshold':>9}{'score':>9}{'accuracy':>10}{'unassigned%':>13}{'error%':>9}{'misattrib.s':>13}"
    print(f"\n=== {embedder_name} ===")
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['threshold']:>9.2f}{row['score']:>9.3f}{row['accuracy']:>9.1%}"
            f"{row['unassigned_rate']:>13.1%}{row['error_rate']:>9.1%}{row['misattributed_seconds']:>13.1f}"
        )
    best = max(rows, key=lambda r: r["score"])
    print(f"Best by headline score: threshold={best['threshold']:.2f}, score={best['score']:.3f}")
    print(f"Wrote {output_csv}")
    return rows


def main() -> None:
    sweep("wespeaker-resnet34", WeSpeakerResNet34Embedder())
    sweep("titanet-large", TitanetLargeEmbedder())


if __name__ == "__main__":
    main()
