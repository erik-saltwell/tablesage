from __future__ import annotations

from dataclasses import dataclass

import widelog
from pydantic import BaseModel
from tablesage_tools.backchannels import find_backchannel_candidates
from tablesage_tools.model import Transcript

from ..llm import PromptName, call_llm_with_prompt


class BackchannelJudgment(BaseModel):
    candidate_id: int
    # True: `utterance` answers a question in `previous_utterance` -- keep it.
    # False: pure backchannel -- remove it. Matches `_prompts/classify_backchannels/system.md`'s
    # `<output_format>` exactly (field names, field order, `scratchpad` first).
    is_answer: bool


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


async def remove_backchannels(transcript: Transcript, max_words: int, llm_model: str) -> Transcript:
    """Drop utterances that are pure backchannels ("yeah", "mhm", "right", ...) from *transcript*.

    A cheap word-list + word-count heuristic (`find_backchannel_candidates`) proposes candidates;
    a batched LLM call then confirms each one isn't actually answering a question posed in the
    utterance immediately before it (a real short answer like "Yeah." to "Are you coming?" must
    not be deleted). The first utterance in the transcript is never a candidate outcome here even
    if the heuristic flags it -- there is no previous utterance for it to be answering, and with
    no context to disambiguate it, it is left in place (fail open, matching the LLM-failure case
    below).

    If the LLM call fails or returns a malformed response, no utterances are removed for this run
    (fail open) -- removal is destructive and unrecoverable, so an infrastructure hiccup should
    degrade to a no-op, not to over-eager deletion.
    """
    candidate_indices = [index for index in find_backchannel_candidates(transcript, max_words) if index > 0]
    if not candidate_indices:
        return transcript

    candidates = [
        _Candidate(
            candidate_id=index,
            previous_utterance=_utterance_text(index - 1, transcript),
            utterance=_utterance_text(index, transcript),
        )
        for index in candidate_indices
    ]

    to_remove = await _classify(candidates, llm_model)
    if not to_remove:
        return transcript

    kept = [utterance for index, utterance in enumerate(transcript.utterances) if index not in to_remove]
    return Transcript(utterances=kept)


async def _classify(candidates: list[_Candidate], llm_model: str) -> set[int]:
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
            )
            judgments = BackchannelJudgments.model_validate_json(raw).judgments
        except Exception as exc:  # fail open: any LLM/parsing failure removes nothing.
            log.set(failed=True, error=str(exc), removed_count=0)
            return set()

        to_remove = {judgment.candidate_id for judgment in judgments if not judgment.is_answer and judgment.candidate_id in valid_ids}
        log.set(failed=False, removed_count=len(to_remove))
        return to_remove
