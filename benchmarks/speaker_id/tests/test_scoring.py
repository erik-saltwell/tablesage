from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from ..scoring import CORRECT_COST, UNASSIGNED_COST, WRONG_COST, pool, score_session


def test_score_session_costs_correct_unassigned_wrong_as_specified() -> None:
    ground_truth = {
        0: ("alice", 1.0),
        1: ("alice", 2.0),
        2: ("bob", 3.0),
        3: ("bob", 4.0),
    }
    predictions = {
        0: "alice",  # correct
        1: UNASSIGNED_SPEAKER,  # unassigned
        2: "alice",  # wrong
        3: "carol",  # wrong
    }

    score = score_session("session-1", "candidate-1", ground_truth, predictions)

    assert score.correct_count == 1
    assert score.unassigned_count == 1
    assert score.wrong_count == 2
    assert score.total_cost == CORRECT_COST + UNASSIGNED_COST + 2 * WRONG_COST
    assert score.misattributed_seconds == 3.0 + 4.0
    assert score.confusion[("bob", "alice")] == 1
    assert score.confusion[("bob", "carol")] == 1


def test_two_unassigned_cost_less_than_one_wrong() -> None:
    """Pins the exact tradeoff requested: two abstentions should cost a little less than one
    error (0.4 * 2 = 0.8 < 1.0)."""
    assert UNASSIGNED_COST * 2 < WRONG_COST


def test_score_is_one_when_every_utterance_correct() -> None:
    ground_truth = {0: ("alice", 1.0), 1: ("bob", 1.0)}
    predictions = {0: "alice", 1: "bob"}

    score = score_session("session-1", "candidate-1", ground_truth, predictions)

    assert score.score == 1.0
    assert score.accuracy == 1.0
    assert score.unassigned_rate == 0.0
    assert score.error_rate == 0.0


def test_pool_sums_across_sessions() -> None:
    ground_truth_a = {0: ("alice", 1.0)}
    ground_truth_b = {0: ("bob", 1.0), 1: ("bob", 1.0)}
    score_a = score_session("session-a", "candidate-1", ground_truth_a, {0: "bob"})  # wrong
    score_b = score_session("session-b", "candidate-1", ground_truth_b, {0: "bob", 1: UNASSIGNED_SPEAKER})  # correct, unassigned

    pooled = pool([score_a, score_b], "candidate-1")

    assert pooled.utterance_count == 3
    assert pooled.correct_count == 1
    assert pooled.unassigned_count == 1
    assert pooled.wrong_count == 1
    assert pooled.session_name == "pooled"
