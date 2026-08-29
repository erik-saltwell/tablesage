"""Cost model and reporting. See .documentation/speaker_identification_benchmark.md's "Scoring"
section: correct=0, unassigned=0.4, wrong=1.0, unweighted per utterance -- two abstentions cost a
little less than one error, matching the requirement to penalize unassigned output but penalize
errors more.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from tablesage_tools.speakers import UNASSIGNED_SPEAKER

CORRECT_COST: float = 0.0
UNASSIGNED_COST: float = 0.4
WRONG_COST: float = 1.0

# Kept stable so every experiment exposes the short-duration failure modes that motivated
# experiment #9 instead of allowing a pooled score to hide them.
DURATION_BUCKETS: tuple[tuple[str, float, float], ...] = (
    ("<0.30s", 0.0, 0.3),
    ("0.30-0.50s", 0.3, 0.5),
    ("0.50-0.75s", 0.5, 0.75),
    ("0.75-1.00s", 0.75, 1.0),
    ("1.00-2.00s", 1.0, 2.0),
    (">=2.00s", 2.0, float("inf")),
)


@dataclass
class SessionScore:
    session_name: str
    candidate_name: str
    utterance_count: int
    correct_count: int
    unassigned_count: int
    wrong_count: int
    total_cost: float
    misattributed_seconds: float
    # (actual, predicted) -> count, wrong assignments only -- who gets mistaken for whom.
    confusion: Counter[tuple[str, str]] = field(default_factory=Counter)
    # bucket label -> outcome -> count. Outcome is correct, unassigned, or wrong.
    duration_buckets: dict[str, Counter[str]] = field(default_factory=dict)

    @property
    def score(self) -> float:
        return 1.0 - self.total_cost / self.utterance_count

    @property
    def accuracy(self) -> float:
        return self.correct_count / self.utterance_count

    @property
    def unassigned_rate(self) -> float:
        return self.unassigned_count / self.utterance_count

    @property
    def error_rate(self) -> float:
        return self.wrong_count / self.utterance_count


def score_session(
    session_name: str,
    candidate_name: str,
    ground_truth: Mapping[int, tuple[str, float]],
    predictions: Mapping[int, str],
) -> SessionScore:
    """`ground_truth` maps utterance index -> (actual speaker, duration in seconds).
    `predictions` maps the same indices -> predicted speaker (or `UNASSIGNED_SPEAKER`).
    """
    correct = unassigned = wrong = 0
    total_cost = 0.0
    misattributed_seconds = 0.0
    confusion: Counter[tuple[str, str]] = Counter()
    duration_buckets = {label: Counter() for label, _lower, _upper in DURATION_BUCKETS}

    for index, (actual, duration) in ground_truth.items():
        predicted = predictions[index]
        if predicted == actual:
            outcome = "correct"
            correct += 1
            total_cost += CORRECT_COST
        elif predicted == UNASSIGNED_SPEAKER:
            outcome = "unassigned"
            unassigned += 1
            total_cost += UNASSIGNED_COST
        else:
            outcome = "wrong"
            wrong += 1
            total_cost += WRONG_COST
            misattributed_seconds += duration
            confusion[(actual, predicted)] += 1
        bucket = next(label for label, lower, upper in DURATION_BUCKETS if lower <= duration < upper)
        duration_buckets[bucket][outcome] += 1

    return SessionScore(
        session_name=session_name,
        candidate_name=candidate_name,
        utterance_count=len(ground_truth),
        correct_count=correct,
        unassigned_count=unassigned,
        wrong_count=wrong,
        total_cost=total_cost,
        misattributed_seconds=misattributed_seconds,
        confusion=confusion,
        duration_buckets=duration_buckets,
    )


def pool(scores: Sequence[SessionScore], candidate_name: str) -> SessionScore:
    """Combine several sessions' scores for one candidate into a single pooled total."""
    confusion: Counter[tuple[str, str]] = Counter()
    duration_buckets = {label: Counter() for label, _lower, _upper in DURATION_BUCKETS}
    for s in scores:
        confusion.update(s.confusion)
        for label, counts in s.duration_buckets.items():
            duration_buckets[label].update(counts)
    return SessionScore(
        session_name="pooled",
        candidate_name=candidate_name,
        utterance_count=sum(s.utterance_count for s in scores),
        correct_count=sum(s.correct_count for s in scores),
        unassigned_count=sum(s.unassigned_count for s in scores),
        wrong_count=sum(s.wrong_count for s in scores),
        total_cost=sum(s.total_cost for s in scores),
        misattributed_seconds=sum(s.misattributed_seconds for s in scores),
        confusion=confusion,
        duration_buckets=duration_buckets,
    )


_ROW = "{:<32}{:<16}{:>6}{:>8}{:>10}{:>12}{:>10}{:>14}"
_HEADER = _ROW.format("candidate", "session", "N", "score", "accuracy", "unassigned%", "error%", "misattrib.s")
_BUCKET_ROW = "{:<30}{:<14}{:>6}{:>10}{:>12}{:>8}"
_BUCKET_HEADER = _BUCKET_ROW.format("candidate", "duration", "N", "correct", "unassigned", "wrong")


def print_report(scores_by_candidate: Mapping[str, list[SessionScore]]) -> None:
    """Print, per candidate: one row per session plus a pooled row, then that candidate's pooled
    confusion matrix (wrong assignments only, most-frequent first).
    """
    print(_HEADER)
    print("-" * len(_HEADER))
    for candidate_name, session_scores in scores_by_candidate.items():
        rows = [*session_scores, pool(session_scores, candidate_name)]
        for s in rows:
            print(
                _ROW.format(
                    candidate_name,
                    s.session_name,
                    s.utterance_count,
                    f"{s.score:.3f}",
                    f"{s.accuracy:.1%}",
                    f"{s.unassigned_rate:.1%}",
                    f"{s.error_rate:.1%}",
                    f"{s.misattributed_seconds:.1f}",
                )
            )
        print()

    for candidate_name, session_scores in scores_by_candidate.items():
        pooled = pool(session_scores, candidate_name)
        if not pooled.confusion:
            continue
        print(f"{candidate_name} -- confusion (actual -> predicted):")
        for (actual, predicted), count in pooled.confusion.most_common():
            print(f"  {actual} -> {predicted}: {count}")
        print()

    print("duration buckets (pooled):")
    print(_BUCKET_HEADER)
    print("-" * len(_BUCKET_HEADER))
    for candidate_name, session_scores in scores_by_candidate.items():
        pooled = pool(session_scores, candidate_name)
        for label, _lower, _upper in DURATION_BUCKETS:
            counts = pooled.duration_buckets[label]
            utterance_count = sum(counts.values())
            print(
                _BUCKET_ROW.format(
                    candidate_name,
                    label,
                    utterance_count,
                    counts["correct"],
                    counts["unassigned"],
                    counts["wrong"],
                )
            )
        print()
