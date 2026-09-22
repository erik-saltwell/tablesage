"""Deterministic, settings-agnostic selection of provisional voice seeds."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from itertools import combinations

from .types import Embedding


@dataclass(frozen=True)
class BootstrapCandidate:
    clip_id: str
    player_id: str
    exchange_id: str
    speech_seconds: float
    embedding: Embedding


@dataclass(frozen=True)
class BootstrapSelectionConfig:
    min_clips: int
    min_independent_exchanges: int
    min_total_speech_seconds: float
    max_clips_per_exchange: int
    pairwise_similarity_threshold: float
    leave_one_out_similarity_threshold: float
    competitor_margin: float


@dataclass(frozen=True)
class BootstrapCandidateDiagnostic:
    clip_id: str
    accepted: bool
    reason: str | None
    leave_one_out_similarity: float | None
    competitor_similarity: float | None
    competitor_margin: float | None


@dataclass(frozen=True)
class BootstrapSelection:
    player_id: str
    selected_clip_ids: tuple[str, ...]
    centroid: Embedding | None
    diagnostics: tuple[BootstrapCandidateDiagnostic, ...]
    reason: str | None
    independent_exchange_count: int
    total_speech_seconds: float


def select_bootstrap_candidates(
    player_id: str,
    candidates: Sequence[BootstrapCandidate],
    established_references: Mapping[str, Embedding],
    config: BootstrapSelectionConfig,
) -> BootstrapSelection:
    """Select a mutually coherent, independently evidenced provisional voice core.

    Every decision is deterministic: candidates are ordered by their stable ID and ties are
    resolved using that order. Invalid vectors and clips are retained in diagnostics but never
    enter a core or centroid.
    """
    ordered = sorted((item for item in candidates if item.player_id == player_id), key=lambda item: item.clip_id)
    dimensions: dict[int, int] = {}
    for item in ordered:
        if _valid_candidate(item):
            dimensions[len(item.embedding)] = dimensions.get(len(item.embedding), 0) + 1
    expected_dimension = max(dimensions, key=lambda dimension: (dimensions[dimension], dimension)) if dimensions else None
    invalid = {
        item.clip_id
        for item in ordered
        if not _valid_candidate(item) or expected_dimension is None or len(item.embedding) != expected_dimension
    }
    viable = [item for item in ordered if item.clip_id not in invalid]
    cores = _coherent_cores(viable, config.pairwise_similarity_threshold)
    if not cores:
        return _rejected(player_id, ordered, invalid, "no_coherent_core")

    best = cores[0]
    # Two independent, equally strong incompatible cores are a conflict, not a vote.
    if len(cores) > 1 and _core_strength(cores[0])[:3] == _core_strength(cores[1])[:3] and not _overlap(cores[0], cores[1]):
        return _rejected(player_id, ordered, invalid, "conflicting_coherent_cores")

    kept = _cap_per_exchange(best, config.max_clips_per_exchange)
    rejected: dict[str, str] = {item.clip_id: "invalid_embedding_or_duration" for item in ordered if item.clip_id in invalid}
    rejected.update({item.clip_id: "outside_coherent_core" for item in viable if item not in best})
    rejected.update({item.clip_id: "exchange_cap" for item in best if item not in kept})

    while len(kept) > 1:
        similarities = {item.clip_id: _leave_one_out_similarity(item, kept) for item in kept}
        worst = min(kept, key=lambda item: (similarities[item.clip_id], item.clip_id))
        if similarities[worst.clip_id] >= config.leave_one_out_similarity_threshold:
            break
        rejected[worst.clip_id] = "leave_one_out_similarity"
        kept.remove(worst)

    if kept:
        centroid = _centroid(kept)
        for item in list(kept):
            competitor = _highest_similarity(item.embedding, established_references.values())
            own = _leave_one_out_similarity(item, kept) if len(kept) > 1 else None
            if competitor is not None and own is not None and own - competitor < config.competitor_margin:
                kept.remove(item)
                rejected[item.clip_id] = "established_reference_margin"
        centroid = _centroid(kept) if kept else None
    else:
        centroid = None

    exchanges = len({item.exchange_id for item in kept})
    duration = sum(item.speech_seconds for item in kept)
    reason: str | None = None
    if exchanges < config.min_independent_exchanges:
        reason = "insufficient_independent_exchanges"
    elif len(kept) < config.min_clips:
        reason = "insufficient_clips"
    elif duration < config.min_total_speech_seconds:
        reason = "insufficient_speech_duration"
    if reason is not None:
        centroid = None

    diagnostics = tuple(
        BootstrapCandidateDiagnostic(
            clip_id=item.clip_id,
            accepted=item in kept and reason is None,
            reason=rejected.get(item.clip_id) if item not in kept else reason,
            leave_one_out_similarity=_leave_one_out_similarity(item, kept) if item in kept and len(kept) > 1 else None,
            competitor_similarity=_highest_similarity(item.embedding, established_references.values()) if item in kept else None,
            competitor_margin=_competitor_margin(item, kept, established_references.values()),
        )
        for item in ordered
    )
    return BootstrapSelection(
        player_id,
        tuple(item.clip_id for item in kept) if reason is None else (),
        centroid,
        diagnostics,
        reason,
        exchanges,
        duration,
    )


def find_bootstrap_collisions(selections: Sequence[BootstrapSelection], threshold: float) -> tuple[tuple[str, str], ...]:
    """Return sorted pairs of provisional profiles too similar to safely distinguish."""
    collisions = [
        (min(left.player_id, right.player_id), max(left.player_id, right.player_id))
        for left, right in combinations(selections, 2)
        if left.centroid is not None and right.centroid is not None and _cosine(left.centroid, right.centroid) >= threshold
    ]
    return tuple(sorted(collisions))


def _valid_candidate(item: BootstrapCandidate) -> bool:
    return item.speech_seconds > 0 and bool(item.embedding.root) and all(math.isfinite(value) for value in item.embedding.root)


def _coherent_cores(items: Sequence[BootstrapCandidate], threshold: float) -> list[list[BootstrapCandidate]]:
    cores: list[list[BootstrapCandidate]] = []
    for seed in items:
        core = [seed]
        for candidate in items:
            if candidate is seed:
                continue
            if all(_cosine(candidate.embedding, member.embedding) >= threshold for member in core):
                core.append(candidate)
        cores.append(sorted(core, key=lambda item: item.clip_id))
    unique = {tuple(item.clip_id for item in core): core for core in cores}
    return sorted(unique.values(), key=lambda core: (_core_strength(core), tuple(item.clip_id for item in core)), reverse=True)


def _core_strength(core: Sequence[BootstrapCandidate]) -> tuple[int, int, float]:
    pairs = [_cosine(left.embedding, right.embedding) for left, right in combinations(core, 2)]
    return (len({item.exchange_id for item in core}), len(core), sum(pairs) / len(pairs) if pairs else 1.0)


def _cap_per_exchange(items: Sequence[BootstrapCandidate], maximum: int) -> list[BootstrapCandidate]:
    counts: dict[str, int] = {}
    result: list[BootstrapCandidate] = []
    for item in items:
        if counts.get(item.exchange_id, 0) < maximum:
            result.append(item)
            counts[item.exchange_id] = counts.get(item.exchange_id, 0) + 1
    return result


def _leave_one_out_similarity(item: BootstrapCandidate, items: Sequence[BootstrapCandidate]) -> float:
    others = [other for other in items if other is not item]
    return _cosine(item.embedding, _centroid(others)) if others else 1.0


def _highest_similarity(embedding: Embedding, references: Iterable[Embedding]) -> float | None:
    return max((_cosine(embedding, reference) for reference in references), default=None)


def _competitor_margin(item: BootstrapCandidate, kept: Sequence[BootstrapCandidate], references: Iterable[Embedding]) -> float | None:
    if item not in kept or len(kept) < 2:
        return None
    competitor = _highest_similarity(item.embedding, references)
    return _leave_one_out_similarity(item, kept) - competitor if competitor is not None else None


def _centroid(items: Sequence[BootstrapCandidate]) -> Embedding:
    dimensions = len(items[0].embedding)
    mean = [sum(item.embedding.root[index] for item in items) / len(items) for index in range(dimensions)]
    magnitude = math.sqrt(sum(value * value for value in mean))
    return Embedding(root=tuple(value / magnitude for value in mean))


def _cosine(left: Embedding, right: Embedding) -> float:
    return sum(a * b for a, b in zip(left.root, right.root, strict=True))


def _overlap(left: Sequence[BootstrapCandidate], right: Sequence[BootstrapCandidate]) -> bool:
    return bool({item.clip_id for item in left} & {item.clip_id for item in right})


def _rejected(player_id: str, ordered: Sequence[BootstrapCandidate], invalid: set[str], reason: str) -> BootstrapSelection:
    return BootstrapSelection(
        player_id=player_id,
        selected_clip_ids=(),
        centroid=None,
        diagnostics=tuple(
            BootstrapCandidateDiagnostic(
                item.clip_id,
                False,
                "invalid_embedding_or_duration" if item.clip_id in invalid else reason,
                None,
                None,
                None,
            )
            for item in ordered
        ),
        reason=reason,
        independent_exchange_count=0,
        total_speech_seconds=0,
    )
