"""Experiment #1 driver: sweep `similarity_margin_threshold` and score each value against the
frozen benchmark sessions, to see whether production's default (0.1) is actually optimal.

Not a permanent harness feature -- .documentation/speaker_identification_benchmark.md defers a
"first-class threshold-sweep mode" (curve instead of point comparisons) out of v1 scope on
purpose. This script reuses the harness's existing embedder/centroid/matcher/scoring stages as a
library, the same way candidates.py's Workflow section says threshold variations should be
compared ("just additional registered candidates"), just swept programmatically instead of by
hand-typing dozens of entries into the permanent CANDIDATES list.

Embeddings and centroids are computed once per session (they don't depend on the threshold) and
reused across every swept threshold -- only the cheap matching + scoring step reruns per value.

Usage (from the repo root, inside the venv):

    uv run python .scratch/speaker-id-experiments/threshold_sweep.py
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
from benchmarks.speaker_id.embedders import Eres2NetV2Embedder  # noqa: E402
from benchmarks.speaker_id.harness import REPO_ROOT as HARNESS_REPO_ROOT  # noqa: E402
from benchmarks.speaker_id.harness import _embed_utterances, load_sessions  # noqa: E402
from benchmarks.speaker_id.matchers import MarginThresholdMatcher  # noqa: E402
from benchmarks.speaker_id.scoring import SessionScore, pool, score_session  # noqa: E402

THRESHOLDS = [round(0.02 * i, 2) for i in range(26)]  # 0.00 .. 0.50 step 0.02
OUTPUT_CSV = Path(__file__).resolve().parent / "threshold-sweep-results.csv"


def main() -> None:
    import asyncio

    # This sandbox can't reach modelscope.cn's API (times out), so point at the model's already
    # -downloaded local snapshot dir instead of the bare model_id -- ModelScope's read_config()
    # only skips its online lookup when passed a real filesystem path. Same weights either way;
    # this just avoids the embedder cache_key it derives from model_id, so this run doesn't reuse
    # the harness's existing embedding cache and recomputes everything from scratch.
    local_model_dir = Path.home() / ".cache/modelscope/hub/models/iic/speech_eres2netv2_sv_zh-cn_16k-common"
    embedder = Eres2NetV2Embedder(model_id=str(local_model_dir)) if local_model_dir.is_dir() else Eres2NetV2Embedder()
    cache = EmbeddingCache()
    sessions = load_sessions()

    # Precompute once per session -- independent of threshold.
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

    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    header = f"{'threshold':>9}{'score':>9}{'accuracy':>10}{'unassigned%':>13}{'error%':>9}{'misattrib.s':>13}"
    print(header)
    print("-" * len(header))
    for row in rows:
        print(
            f"{row['threshold']:>9.2f}{row['score']:>9.3f}{row['accuracy']:>9.1%}"
            f"{row['unassigned_rate']:>13.1%}{row['error_rate']:>9.1%}{row['misattributed_seconds']:>13.1f}"
        )

    best = max(rows, key=lambda r: r["score"])
    print(f"\nBest by headline score: threshold={best['threshold']:.2f}, score={best['score']:.3f}")
    print(f"Wrote {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
