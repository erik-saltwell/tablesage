"""Process Session's Isolate New Speakers step: high-confidence utterances for each new player.

An LLM reads the name-corrected transcript and, showing its evidence, lists the utterances it is
confident each new player spoke, and names the player who spoke most of each diarized label.
Only utterances claimed for no other player and long enough to serve as voice samples are kept;
`_REQUIRE_EVIDENCE` optionally also requires each to be backed by that player's evidence. A player
left with too little speech falls back to the labels the LLM gave them, unless another player's
picks also fall on that label (then it is mixed): the label's unlisted utterances are added,
trimmed to a speech cap (shortest first, then voice outliers, then those least like the player's
own picks). The LLM's picks are never trimmed. Anyone still short is left for manual assignment
in Review Transcript.

The LLM sees and answers with player names, never ids; a schema enum restricts it to the
supplied names, which are mapped back to ids here.
"""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from collections import Counter
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import widelog
from pydantic import BaseModel, create_model
from tablesage_tools.audio import extract_clip
from tablesage_tools.embeddings import Embedding, compute_centroid, cosine_similarity
from tablesage_tools.model import Transcript

from ..llm import PromptName, call_llm_with_prompt
from ..paths import ARTIFACTS, ArtifactName
from .atomic_files import atomic_write
from .speech import speech_duration

OnProgress = Callable[[str, int, int], None]

# When True, a listed utterance is kept only if the LLM also cited it in that player's evidence.
_REQUIRE_EVIDENCE = False

# A speaker label's owner when it is not one supplied player. Parenthesized so no player name can collide.
MIXED_LABEL = "(mixed)"
OTHER_LABEL = "(other)"


# LLM response. `player_name` and `speaker_id` are narrowed per call (`_constrained_response_model`).


class EvidenceResponse(BaseModel, frozen=True):
    player_name: str
    utterance_indices: tuple[int, ...]
    explanation: str


class PlayerUtterancesResponse(BaseModel, frozen=True):
    player_name: str
    utterance_indices: tuple[int, ...]


class SpeakerLabelResponse(BaseModel, frozen=True):
    speaker_id: str
    # A supplied player's name, `MIXED_LABEL`, or `OTHER_LABEL`.
    player_name: str
    explanation: str


class IsolateNewSpeakersResponse(BaseModel, frozen=True):
    evidence: tuple[EvidenceResponse, ...]
    players: tuple[PlayerUtterancesResponse, ...]
    speaker_labels: tuple[SpeakerLabelResponse, ...]


# Artifact


class EvidenceEntry(BaseModel, frozen=True):
    player_id: uuid.UUID
    utterance_indices: tuple[int, ...]
    explanation: str


class NewSpeakerAssignment(BaseModel, frozen=True):
    player_id: uuid.UUID
    player_name: str
    utterance_indices: tuple[int, ...]
    # Records how the list was built; it cannot be derived later.
    used_voice_fallback: bool
    # The labels the LLM said this player spoke most of (before the mixed-label check).
    proposed_speaker_ids: tuple[str, ...]


class NewSpeakerAssignments(BaseModel, frozen=True):
    """`new_speaker_assignments.json`: indices refer to `name_corrected_transcript.json`.

    Derived facts (speech seconds, whether a player met the threshold) are deliberately not
    stored, so they follow the current transcript and settings.
    """

    players: tuple[NewSpeakerAssignment, ...]
    evidence: tuple[EvidenceEntry, ...]

    @classmethod
    def load(cls, path: Path) -> NewSpeakerAssignments:
        return cls.model_validate_json(path.read_bytes())


@dataclass(frozen=True)
class NewPlayer:
    player_id: uuid.UUID
    player_name: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class IsolationSettings:
    model: str
    timeout: float
    max_attempts: int
    min_speech_seconds: float
    min_total_speech_seconds: float
    target_total_speech_seconds: float
    fallback_short_clip_seconds: float
    fallback_max_speech_seconds: float
    min_seed_speech_seconds: float
    outlier_min_sample_similarity: float
    outlier_min_samples: int


@dataclass(frozen=True)
class _PromptUtterance:
    index: int
    speaker_id: str
    speech_seconds: float
    text: str


@dataclass(frozen=True)
class _PromptSpeakerLabel:
    speaker_id: str
    utterance_count: int
    speech_seconds: float


@dataclass(frozen=True)
class _PromptData:
    players: Sequence[NewPlayer]
    speaker_labels: Sequence[_PromptSpeakerLabel]
    utterances: Sequence[_PromptUtterance]
    target_total_speech_seconds: float
    min_speech_seconds: float


def assignments_path(session_folder: Path) -> Path:
    return session_folder / ARTIFACTS[ArtifactName.NEW_SPEAKER_ASSIGNMENTS].filename


def isolate_new_speakers(
    session_folder: Path,
    new_players: Sequence[NewPlayer],
    settings: IsolationSettings,
    embed: Callable[[Path], Embedding],
    on_progress: OnProgress | None = None,
) -> NewSpeakerAssignments:
    """Build and write `new_speaker_assignments.json` from `name_corrected_transcript.json`."""
    names = Counter(player.player_name for player in new_players)
    if duplicates := sorted(name for name, count in names.items() if count > 1 or name in (MIXED_LABEL, OTHER_LABEL)):
        raise ValueError(f"New players must have distinct names: {', '.join(duplicates)}")
    transcript = Transcript.load(session_folder / ARTIFACTS[ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
    with widelog.wide_event(op="isolate_new_speakers", session_folder=str(session_folder), new_player_count=len(new_players)) as log:
        speaker_counts = Counter(utterance.speaker for utterance in transcript.utterances)
        log.set(utterance_count=len(transcript.utterances), speaker_utterance_counts=dict(sorted(speaker_counts.items())))
        if not new_players:
            result = NewSpeakerAssignments(players=(), evidence=())
        else:
            _report(on_progress, "Finding new speakers' utterances…", 0, 0)
            response = asyncio.run(_ask_llm(transcript, new_players, settings))
            result, diagnostics, label_diagnostics = _build_assignments(
                transcript, new_players, response, settings, embed, session_folder, on_progress
            )
            proposed_labels = {label for player in result.players for label in player.proposed_speaker_ids}
            # Keyed by player name so a line can be read without looking up ids; no transcript text is logged.
            log.set(label_diagnostics)
            log.set(
                players=diagnostics,
                unassigned_speaker_utterance_counts={
                    label: count for label, count in sorted(speaker_counts.items()) if label not in proposed_labels
                },
            )
        atomic_write(assignments_path(session_folder), result.model_dump_json(indent=2).encode("utf-8") + b"\n")
        log.set(
            utterance_counts={player.player_name: len(player.utterance_indices) for player in result.players},
            voice_fallback_count=sum(player.used_voice_fallback for player in result.players),
        )
        return result


def _constrained_response_model(names: Sequence[str], labels: Sequence[str]) -> type[IsolateNewSpeakersResponse]:
    """`IsolateNewSpeakersResponse` whose schema only admits `names` as players and `labels` as speaker ids."""
    name_type = Literal[tuple(names)]  # ty: ignore[invalid-type-form]
    owner_type = Literal[(*names, MIXED_LABEL, OTHER_LABEL)]  # ty: ignore[invalid-type-form]
    label_type = Literal[tuple(labels)] if labels else str  # ty: ignore[invalid-type-form]
    evidence = create_model("EvidenceEntry", __base__=EvidenceResponse, player_name=(name_type, ...))
    player = create_model("PlayerUtterances", __base__=PlayerUtterancesResponse, player_name=(name_type, ...))
    speaker_label = create_model("SpeakerLabel", __base__=SpeakerLabelResponse, speaker_id=(label_type, ...), player_name=(owner_type, ...))
    return create_model(
        "IsolateNewSpeakersResponse",
        __base__=IsolateNewSpeakersResponse,
        evidence=(tuple[evidence, ...], ...),  # ty: ignore[invalid-type-form]
        players=(tuple[player, ...], ...),  # ty: ignore[invalid-type-form]
        speaker_labels=(tuple[speaker_label, ...], ...),  # ty: ignore[invalid-type-form]
    )


async def _ask_llm(transcript: Transcript, new_players: Sequence[NewPlayer], settings: IsolationSettings) -> IsolateNewSpeakersResponse:
    counts = Counter(utterance.speaker for utterance in transcript.utterances)
    seconds = Counter[str]()
    for utterance in transcript.utterances:
        seconds[utterance.speaker] += speech_duration(utterance)
    labels = sorted(counts)
    data = _PromptData(
        players=new_players,
        speaker_labels=[_PromptSpeakerLabel(label, counts[label], seconds[label]) for label in labels],
        utterances=[
            _PromptUtterance(
                index=index,
                speaker_id=utterance.speaker,
                speech_seconds=speech_duration(utterance),
                text=utterance.punctuated_text or utterance.text,
            )
            for index, utterance in enumerate(transcript.utterances)
        ],
        target_total_speech_seconds=settings.target_total_speech_seconds,
        min_speech_seconds=settings.min_speech_seconds,
    )
    response_model = _constrained_response_model([player.player_name for player in new_players], labels)
    error: Exception | None = None
    for _attempt in range(settings.max_attempts):
        try:
            response = await call_llm_with_prompt(
                PromptName.ISOLATE_NEW_SPEAKERS,
                data,
                model=settings.model,
                response_model=response_model,
                timeout=settings.timeout,
                # Without strict mode OpenAI treats the schema as a hint and the name enum is not enforced.
                strict_schema=True,
                # Diagnostic: the raw picks, before filtering, for checking why a player got few samples.
                trace_output=True,
            )
            return response_model.model_validate_json(response)
        except Exception as exc:
            error = exc
    assert error is not None
    raise RuntimeError(f"The LLM could not identify new speakers: {error}") from error


def _build_assignments(
    transcript: Transcript,
    new_players: Sequence[NewPlayer],
    response: IsolateNewSpeakersResponse,
    settings: IsolationSettings,
    embed: Callable[[Path], Embedding],
    session_folder: Path,
    on_progress: OnProgress | None,
) -> tuple[NewSpeakerAssignments, dict[str, dict[str, object]], dict[str, object]]:
    """Filter the LLM's picks into assignments, plus per-player and per-label diagnostics explaining each count."""
    utterance_count = len(transcript.utterances)
    player_ids = {player.player_name: player.player_id for player in new_players}
    unknown_names = Counter(entry.player_name for entry in (*response.evidence, *response.players) if entry.player_name not in player_ids)
    evidence = tuple(
        EvidenceEntry(
            player_id=player_ids[entry.player_name],
            utterance_indices=tuple(i for i in dict.fromkeys(entry.utterance_indices) if 0 <= i < utterance_count),
            explanation=entry.explanation,
        )
        for entry in response.evidence
        if entry.player_name in player_ids
    )
    cited: dict[uuid.UUID, set[int]] = {player_id: set() for player_id in player_ids.values()}
    for entry in evidence:
        cited[entry.player_id].update(entry.utterance_indices)

    listed: dict[uuid.UUID, list[int]] = {player_id: [] for player_id in player_ids.values()}
    llm_listed: dict[uuid.UUID, list[int]] = {player_id: [] for player_id in player_ids.values()}
    for answer in response.players:
        if answer.player_name not in player_ids:
            continue
        player_id = player_ids[answer.player_name]
        llm_listed[player_id].extend(i for i in dict.fromkeys(answer.utterance_indices) if 0 <= i < utterance_count)
        listed[player_id].extend(
            i
            for i in dict.fromkeys(answer.utterance_indices)
            if 0 <= i < utterance_count and (not _REQUIRE_EVIDENCE or i in cited[player_id])
        )

    # An utterance listed for two players is dropped from both.
    listed_counts = Counter(i for indices in listed.values() for i in set(indices))
    claimed = {i for i, count in listed_counts.items() if count == 1}

    def seconds(index: int) -> float:
        return speech_duration(transcript.utterances[index])

    def long_enough(index: int) -> bool:
        return seconds(index) >= settings.min_speech_seconds

    kept = {player_id: [i for i in indices if i in claimed and long_enough(i)] for player_id, indices in listed.items()}

    # The label -> owner mapping; a label whose owner is `MIXED_LABEL`, `OTHER_LABEL`, or unknown has none.
    labels_present = {utterance.speaker for utterance in transcript.utterances}
    label_owners: dict[str, str] = {}
    for entry in response.speaker_labels:
        if entry.speaker_id in labels_present:
            label_owners.setdefault(entry.speaker_id, entry.player_name)
    proposed: dict[uuid.UUID, tuple[str, ...]] = {
        player_id: tuple(sorted(label for label, owner in label_owners.items() if owner == name)) for name, player_id in player_ids.items()
    }
    # The LLM judged each label from text alone; a label that another player's picks also fall on is mixed.
    pick_labels = {player_id: {transcript.utterances[i].speaker for i in indices if i in claimed} for player_id, indices in listed.items()}
    demoted: dict[str, list[str]] = {}
    for player_id in player_ids.values():
        for label in proposed[player_id]:
            others = sorted(other for other, other_id in player_ids.items() if other_id != player_id and label in pick_labels[other_id])
            if others:
                demoted[label] = others
    assignments: list[NewSpeakerAssignment] = []
    diagnostics: dict[str, dict[str, object]] = {}
    for player in new_players:
        picks = kept[player.player_id]
        own = listed[player.player_id]
        diagnostic: dict[str, object] = {
            "llm_utterance_count": len(llm_listed[player.player_id]),
            "llm_utterance_speakers": dict(Counter(transcript.utterances[i].speaker for i in llm_listed[player.player_id])),
            "evidence_utterance_count": len(cited[player.player_id]),
            "dropped_not_in_evidence": len(llm_listed[player.player_id]) - len(own),
            "dropped_listed_for_another_player": sum(1 for i in own if i not in claimed),
            "dropped_too_short": sum(1 for i in own if i in claimed and not long_enough(i)),
            "kept_from_llm": len(picks),
            "kept_from_llm_seconds": round(sum(seconds(i) for i in picks), 1),
            "proposed_speaker_ids": list(proposed[player.player_id]),
        }
        additions: list[int] = []
        used_fallback = False
        if sum(seconds(i) for i in picks) < settings.min_total_speech_seconds:
            labels = {label for label in proposed[player.player_id] if label not in demoted}
            diagnostic["fallback_speaker_ids"] = sorted(labels)
            # The label's utterances, minus any the LLM listed for anyone.
            pool = [
                i
                for i, utterance in enumerate(transcript.utterances)
                if utterance.speaker in labels and i not in listed_counts and long_enough(i)
            ]
            diagnostic["fallback_pool_count"] = len(pool)
            if pool:
                additions = _capped_fallback(
                    transcript, picks, pool, settings, embed, session_folder, player.player_name, diagnostic, on_progress
                )
                used_fallback = True
        indices = sorted({*picks, *additions})
        assignments.append(
            NewSpeakerAssignment(
                player_id=player.player_id,
                player_name=player.player_name,
                utterance_indices=tuple(indices),
                used_voice_fallback=used_fallback,
                proposed_speaker_ids=proposed[player.player_id],
            )
        )
        diagnostic.update(
            used_voice_fallback=used_fallback,
            final_utterance_count=len(indices),
            final_speech_seconds=round(sum(seconds(i) for i in indices), 1),
            final_utterance_speakers=dict(Counter(transcript.utterances[i].speaker for i in indices)),
        )
        diagnostics[player.player_name] = diagnostic
    label_diagnostics: dict[str, object] = {
        "speaker_label_owners": dict(sorted(label_owners.items())),
        # Label -> the other players whose picks fall on it.
        "mixed_by_picks": demoted,
    }
    if unknown_names:
        label_diagnostics["unknown_player_names"] = dict(unknown_names)
    return NewSpeakerAssignments(players=tuple(assignments), evidence=evidence), diagnostics, label_diagnostics


def _capped_fallback(
    transcript: Transcript,
    picks: Sequence[int],
    pool: Sequence[int],
    settings: IsolationSettings,
    embed: Callable[[Path], Embedding],
    session_folder: Path,
    player_name: str,
    diagnostic: dict[str, object],
    on_progress: OnProgress | None,
) -> list[int]:
    """Trim a player's fallback additions to `fallback_max_speech_seconds`; `picks` only guide the ranking.

    Shortest additions go first, until the rest fit or all reach `fallback_short_clip_seconds`. Voice
    outliers go next. If still over the cap, the additions least like the player's picks go last
    (or least like the additions' own centroid, when the picks are too short to be a reference).
    """

    def seconds(index: int) -> float:
        return speech_duration(transcript.utterances[index])

    cap = settings.fallback_max_speech_seconds
    additions = sorted(pool, key=seconds)
    total = sum(seconds(i) for i in additions)
    dropped_short = 0
    while additions and total > cap and seconds(additions[0]) < settings.fallback_short_clip_seconds:
        total -= seconds(additions.pop(0))
        dropped_short += 1
    diagnostic["fallback_dropped_short"] = dropped_short

    message = f"Checking {player_name}'s voice samples…"
    audio_path = session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename
    with tempfile.TemporaryDirectory(dir=session_folder, prefix=".isolate-") as directory:

        async def extract_all(indices: Sequence[int]) -> dict[Path, int]:
            clips: dict[Path, int] = {}
            for index in indices:
                utterance = transcript.utterances[index]
                clip_path = Path(directory) / f"{index}.wav"
                await extract_clip(audio_path, clip_path, utterance.start, utterance.end)
                clips[clip_path] = index
            return clips

        addition_clips = asyncio.run(extract_all(additions))
        _report(on_progress, message, 0, len(addition_clips))
        result = compute_centroid(
            list(addition_clips),
            embed,
            on_progress=lambda done, total: _report(on_progress, message, done, total),
            min_sample_similarity=settings.outlier_min_sample_similarity,
            min_samples=settings.outlier_min_samples,
        )
        embeddings = {addition_clips[path]: embedding for path, embedding in result.embeddings.items()}
        diagnostic["voice_outliers_removed"] = len(additions) - len(embeddings)
        additions = [i for i in additions if i in embeddings]
        total = sum(seconds(i) for i in additions)

        reference = result.centroid
        seed_source = "not_needed"
        if total > cap:
            seed_source = "pool"
            if picks and sum(seconds(i) for i in picks) >= settings.min_seed_speech_seconds:
                seed_clips = asyncio.run(extract_all(picks))
                # min_samples = all of them: the LLM's picks are the reference, so none is pruned.
                reference = compute_centroid(list(seed_clips), embed, min_samples=len(seed_clips)).centroid
                seed_source = "picks"
    diagnostic["seed_source"] = seed_source

    dropped_dissimilar = 0
    if total > cap:
        for index in sorted(additions, key=lambda i: cosine_similarity(embeddings[i], reference)):
            if total <= cap:
                break
            additions.remove(index)
            total -= seconds(index)
            dropped_dissimilar += 1
    diagnostic["fallback_dropped_dissimilar"] = dropped_dissimilar
    diagnostic["fallback_added_seconds"] = round(total, 1)
    return additions


def _report(on_progress: OnProgress | None, message: str, completed: int, total: int) -> None:
    if on_progress is not None:
        on_progress(message, completed, total)
