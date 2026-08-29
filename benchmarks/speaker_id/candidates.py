"""Registered candidates. Add a new algorithm/threshold/embedder by adding one entry here -- see
.documentation/speaker_identification_benchmark.md's "Workflow" section for why this is a plain
list in code rather than a CLI.
"""

from __future__ import annotations

from .embedders import Eres2NetV2Embedder, WeSpeakerResNet34Embedder
from .matchers import MarginAndSimilarityMatcher, MarginThresholdMatcher
from .types import Candidate

# Shared across candidates that use the same embedder so their utterance/reference embeddings
# come from one cache-key namespace instead of silently duplicating work.
_wespeaker_resnet34 = WeSpeakerResNet34Embedder()
_eres2netv2 = Eres2NetV2Embedder()

CANDIDATES: list[Candidate] = [
    # Matches apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml's shipped defaults --
    # experiment #7's duration-conditioned margin rule on the WeSpeaker embedder. This is the
    # permanent baseline every later candidate is compared against.
    Candidate(
        name="production",
        embedder=_wespeaker_resnet34,
        matcher=MarginAndSimilarityMatcher(
            margin_threshold=0.10,
            duration_overrides=((1.0, 0.04),),
        ),
    ),
    # Same embedder and threshold, but never abstains -- demonstrates the allow_unassigned=False
    # knob against the same data, for comparison against "production" above.
    Candidate(
        name="forced-assignment",
        embedder=_wespeaker_resnet34,
        matcher=MarginThresholdMatcher(similarity_margin_threshold=0.08, allow_unassigned=False),
    ),
    # Historical baseline -- production's embedder before experiment #3 (see the docstring on
    # Eres2NetV2Embedder). Kept registered so future experiments still have this comparison point.
    Candidate(
        name="eres2netv2-baseline",
        embedder=_eres2netv2,
        matcher=MarginThresholdMatcher(similarity_margin_threshold=0.07, allow_unassigned=True),
    ),
    # Historical production baseline before experiment #7's duration-conditioned rule.
    Candidate(
        name="pre-experiment-7-margin-only",
        embedder=_wespeaker_resnet34,
        matcher=MarginThresholdMatcher(similarity_margin_threshold=0.08, allow_unassigned=True),
    ),
]
