import math

from tablesage_tools.embeddings.types import Embedding
from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from ..matchers import MarginAndSimilarityMatcher, MarginThresholdMatcher

CENTROIDS = {
    "alice": Embedding(root=(1.0, 0.0)),
    "bob": Embedding(root=(0.0, 1.0)),
}


def test_margin_threshold_matcher_ignores_optional_duration_metadata() -> None:
    # alice=0.743, bob=0.669: strong absolute match but only a ~0.074 margin.
    embeddings = {0: Embedding(root=(1.0, 0.9))}
    matcher = MarginThresholdMatcher(similarity_margin_threshold=0.08)

    assert matcher.match(embeddings, CENTROIDS, durations={0: 10.0}) == {0: UNASSIGNED_SPEAKER}


def test_richer_matcher_can_assign_by_absolute_best_similarity() -> None:
    embeddings = {0: Embedding(root=(1.0, 0.9))}
    matcher = MarginAndSimilarityMatcher(margin_threshold=0.08, best_similarity_threshold=0.7)

    assert matcher.match(embeddings, CENTROIDS) == {0: "alice"}


def test_richer_matcher_can_relax_margin_for_long_utterances_only() -> None:
    embeddings = {
        0: Embedding(root=(1.0, 0.9)),
        1: Embedding(root=(1.0, 0.9)),
    }
    matcher = MarginAndSimilarityMatcher(margin_threshold=0.08, duration_overrides=((2.0, 0.0),))

    assert matcher.match(embeddings, CENTROIDS, durations={0: 1.9, 1: 2.0}) == {
        0: UNASSIGNED_SPEAKER,
        1: "alice",
    }


def test_richer_matcher_keeps_nan_similarity_unassigned() -> None:
    embeddings = {0: Embedding(root=(math.nan, 0.0))}
    matcher = MarginAndSimilarityMatcher(
        margin_threshold=0.08,
        best_similarity_threshold=0.0,
        duration_overrides=((2.0, 0.0),),
    )

    assert matcher.match(embeddings, CENTROIDS, durations={0: 3.0}) == {0: UNASSIGNED_SPEAKER}
