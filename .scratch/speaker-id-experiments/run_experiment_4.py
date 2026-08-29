"""Experiment #4 driver: run the `titanet-large` candidate (NVIDIA NeMo TitaNet-Large embedder,
`benchmarks/speaker_id/embedders.py`'s `TitanetLargeEmbedder`) against the frozen benchmark
sessions, alongside `production` for comparison.

Not `uv run python -m benchmarks.speaker_id.run` directly: this sandbox can't reach modelscope.cn
(see threshold_sweep.py's note), so `production`'s eres2netv2 embedder needs the same
local-model-dir override used there. `titanet-large` itself needs no such override -- NeMo pulls
from huggingface.co, which this sandbox can reach.

Usage (from the repo root, inside the venv):

    uv run python .scratch/speaker-id-experiments/run_experiment_4.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from benchmarks.speaker_id.cache import EmbeddingCache  # noqa: E402
from benchmarks.speaker_id.embedders import Eres2NetV2Embedder, TitanetLargeEmbedder  # noqa: E402
from benchmarks.speaker_id.harness import load_sessions, run_candidate  # noqa: E402
from benchmarks.speaker_id.matchers import MarginThresholdMatcher  # noqa: E402
from benchmarks.speaker_id.scoring import print_report  # noqa: E402
from benchmarks.speaker_id.types import Candidate  # noqa: E402

LOCAL_ERES2NETV2_DIR = Path.home() / ".cache/modelscope/hub/models/iic/speech_eres2netv2_sv_zh-cn_16k-common"


def main() -> None:
    eres2netv2 = Eres2NetV2Embedder(model_id=str(LOCAL_ERES2NETV2_DIR)) if LOCAL_ERES2NETV2_DIR.is_dir() else Eres2NetV2Embedder()
    titanet_large = TitanetLargeEmbedder()

    candidates = [
        Candidate(
            name="production",
            embedder=eres2netv2,
            matcher=MarginThresholdMatcher(similarity_margin_threshold=0.07, allow_unassigned=True),
        ),
        Candidate(
            name="titanet-large",
            embedder=titanet_large,
            matcher=MarginThresholdMatcher(similarity_margin_threshold=0.07, allow_unassigned=True),
        ),
    ]

    sessions = load_sessions()
    cache = EmbeddingCache()
    scores_by_candidate = {}
    for candidate in candidates:
        scores_by_candidate[candidate.name] = run_candidate(candidate, sessions, cache)
        cache.save()
    print_report(scores_by_candidate)


if __name__ == "__main__":
    main()
