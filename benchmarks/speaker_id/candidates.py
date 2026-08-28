"""Registered candidates. Add a new algorithm/threshold/embedder by adding one entry here -- see
.documentation/speaker_identification_benchmark.md's "Workflow" section for why this is a plain
list in code rather than a CLI.
"""

from __future__ import annotations

from .embedders import Eres2NetV2Embedder
from .matchers import MarginThresholdMatcher
from .types import Candidate

# Shared across candidates that use the same embedder so their utterance/reference embeddings
# come from one cache-key namespace instead of silently duplicating work.
_eres2netv2 = Eres2NetV2Embedder()

CANDIDATES: list[Candidate] = [
    # Matches apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml's shipped defaults
    # (similarity_margin_threshold: 0.07, allow_unassigned: true) -- the permanent baseline every
    # other candidate is compared against. 0.07 replaced the original 0.1 default per
    # .scratch/speaker-id-experiments/01-similarity-threshold-sweep.md (experiment #1).
    Candidate(
        name="production", embedder=_eres2netv2, matcher=MarginThresholdMatcher(similarity_margin_threshold=0.07, allow_unassigned=True)
    ),
    # Same embedder and threshold, but never abstains -- demonstrates the allow_unassigned=False
    # knob against the same data, for comparison against "production" above.
    Candidate(
        name="forced-assignment",
        embedder=_eres2netv2,
        matcher=MarginThresholdMatcher(similarity_margin_threshold=0.07, allow_unassigned=False),
    ),
]
