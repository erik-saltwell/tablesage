from __future__ import annotations

from dataclasses import dataclass

import widelog
from pydantic import BaseModel
from tablesage_tools.backchannels import find_backchannel_candidates
from tablesage_tools.model import Transcript
from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from ..llm import PromptName, call_llm_with_prompt


class BackchannelJudgment(BaseModel):
    candidate_id: int
    # True: `previous_utterance` is a question -- `utterance` is a plausible answer, keep it.
    # False: `previous_utterance` isn't a question -- pure backchannel, remove it. Matches
    # `_prompts/classify_backchannels/system.md`'s `<output_format>` exactly (field names, field
    # order, `scratchpad` first).
    is_question: bool


class BackchannelJudgments(BaseModel):
    scratchpad: str
    judgments: list[BackchannelJudgment]


@dataclass(frozen=True)
class _Candidate:
    candidate_id: int
    previous_utterance: str
    utterance: str


@dataclass(frozen=True)
class BackchannelClassificationPromptData:
    """`template_data` for `PromptName.CLASSIFY_BACKCHANNELS` -- see `_prompts/classify_backchannels/template.j2`."""

    candidates: list[dict[str, object]]


def _utterance_text(index: int, transcript: Transcript) -> str:
    utterance = transcript.utterances[index]
    return utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text


async def remove_backchannels(transcript: Transcript, max_words: int, llm_model: str, question_timeout: float) -> Transcript:
    """Drop utterances that are pure backchannels ("yeah", "mhm", "right", ...) from *transcript*.

    A cheap word-list + word-count heuristic (`find_backchannel_candidates`) proposes candidates.
    Two independent rules then decide removal:

    - A candidate spoken by `UNASSIGNED_SPEAKER` is removed outright, without an LLM call --
      there's no attributable speaker whose real answer could be lost by dropping it.
    - Every other candidate is confirmed by a batched LLM call (`llm_model`, given
      `question_timeout` seconds) that judges only whether the utterance immediately before it was
      a question. A candidate following a real question is kept (it may be a real short answer,
      like "Yeah." to "Are you coming?"); one following anything else (narration, description,
      another backchannel) is removed. The first utterance in the transcript is never sent to the
      LLM even if the heuristic flags it and its speaker is assigned -- there is no previous
      utterance to judge, and with no context to disambiguate it, it is left in place (fail open,
      matching the LLM-failure case below).

    If the LLM call fails or returns a malformed response, no utterances beyond the
    unassigned-speaker ones are removed for this run (fail open) -- removal is destructive and
    unrecoverable, so an infrastructure hiccup should degrade toward a no-op, not over-eager
    deletion.
    """
    candidate_indices = find_backchannel_candidates(transcript, max_words)
    unassigned_removal = {index for index in candidate_indices if transcript.utterances[index].speaker == UNASSIGNED_SPEAKER}
    question_check_indices = [index for index in candidate_indices if index not in unassigned_removal and index > 0]

    llm_removal: set[int] = set()
    if question_check_indices:
        candidates = [
            _Candidate(
                candidate_id=index,
                previous_utterance=_utterance_text(index - 1, transcript),
                utterance=_utterance_text(index, transcript),
            )
            for index in question_check_indices
        ]
        llm_removal = await _classify(candidates, llm_model, question_timeout)

    to_remove = unassigned_removal | llm_removal
    if not to_remove:
        return transcript

    kept = [utterance for index, utterance in enumerate(transcript.utterances) if index not in to_remove]
    return Transcript(utterances=kept)


async def _classify(candidates: list[_Candidate], llm_model: str, timeout: float) -> set[int]:
    valid_ids = {candidate.candidate_id for candidate in candidates}
    with widelog.wide_event(op="classify_backchannels", candidate_count=len(candidates)) as log:
        try:
            template_data = BackchannelClassificationPromptData(
                candidates=[
                    {
                        "candidate_id": candidate.candidate_id,
                        "previous_utterance": candidate.previous_utterance,
                        "utterance": candidate.utterance,
                    }
                    for candidate in candidates
                ]
            )
            raw = await call_llm_with_prompt(
                PromptName.CLASSIFY_BACKCHANNELS,
                template_data,
                llm_model,
                response_model=BackchannelJudgments,
                timeout=timeout,
            )
            judgments = BackchannelJudgments.model_validate_json(raw).judgments
        except Exception as exc:  # fail open: any LLM/parsing failure removes nothing extra.
            log.set(failed=True, error=str(exc), removed_count=0)
            return set()

        to_remove = {judgment.candidate_id for judgment in judgments if not judgment.is_question and judgment.candidate_id in valid_ids}
        log.set(failed=False, removed_count=len(to_remove))
        return to_remove
