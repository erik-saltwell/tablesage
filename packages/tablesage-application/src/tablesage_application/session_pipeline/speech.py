"""Measures of how much speech an utterance holds."""

from __future__ import annotations

from tablesage_tools.model import Utterance


def speech_duration(utterance: Utterance) -> float:
    """Speech duration from the union of word intervals, excluding gaps."""
    intervals = sorted((word.start, word.end) for word in utterance.words if word.end > word.start)
    if not intervals:
        return 0.0
    total = 0.0
    start, end = intervals[0]
    for next_start, next_end in intervals[1:]:
        if next_start > end:
            total += end - start
            start, end = next_start, next_end
        else:
            end = max(end, next_end)
    return total + end - start
