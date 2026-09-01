from __future__ import annotations

import asyncio
from collections.abc import Callable
from dataclasses import dataclass

import widelog
from pydantic import BaseModel
from tablesage_tools.backchannels import find_backchannel_candidates
from tablesage_tools.model import Transcript

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


OnBatchProgress = Callable[[int, int], None]


def _utterance_text(index: int, transcript: Transcript) -> str:
    utterance = transcript.utterances[index]
    return utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text


def _batches(items: list[int], batch_size: int) -> list[list[int]]:
    return [items[start : start + batch_size] for start in range(0, len(items), batch_size)]


async def remove_backchannels(
    transcript: Transcript,
    max_words: int,
    llm_model: str,
    question_timeout: float,
    batch_size: int,
    max_concurrent_batches: int,
    on_progress: OnBatchProgress | None = None,
) -> Transcript:
    """Drop utterances that are pure backchannels ("yeah", "mhm", "right", ...) from *transcript*.

    This is the pre-review pass, run automatically as part of Transcribe -- before a human ever
    sees the transcript in Manual Review, so speaker assignment here is not yet human-confirmed.
    Because of that, every wordlist-matched candidate (`find_backchannel_candidates`, `max_words`)
    is judged the same way regardless of its current speaker label: a batched LLM call
    (`llm_model`) asks only whether the utterance immediately before it was a question. A
    candidate following a real question is kept (it may be a real short answer, like "Yeah." to
    "Are you coming?"); one following anything else (narration, description, another backchannel)
    is removed. The first utterance in the transcript is never sent to the LLM even if the
    heuristic flags it -- there is no previous utterance to judge, and with no context to
    disambiguate it, it is left in place (fail open).

    Candidates are split into batches of `batch_size` and judged with up to `max_concurrent_batches`
    LLM calls in flight at once, each given `question_timeout` seconds -- a large session can
    propose hundreds of candidates, and sending them as one call is what caused a real production
    timeout. Batches are independent: if one batch's call fails or returns a malformed response,
    only that batch's candidates are left unresolved (kept); every other batch's judgments still
    apply (partial fail-open) -- one transient failure shouldn't discard every other batch's real,
    successful work. `on_progress`, if given, is called as `(completed_batches, total_batches)`
    each time a batch finishes, in completion order (not submission order).

    The post-review pass (`clean_transcript.py`) is a separate, much simpler mechanical filter and
    does not use this function -- see that module.
    """
    candidate_indices = find_backchannel_candidates(transcript, max_words)
    question_check_indices = [index for index in candidate_indices if index > 0]

    if not question_check_indices:
        return transcript

    batches = _batches(question_check_indices, batch_size)
    total_batches = len(batches)
    completed_batches = 0
    semaphore = asyncio.Semaphore(max_concurrent_batches)

    async def _run_batch(batch_indices: list[int]) -> set[int]:
        nonlocal completed_batches
        candidates = [
            _Candidate(
                candidate_id=index,
                previous_utterance=_utterance_text(index - 1, transcript),
                utterance=_utterance_text(index, transcript),
            )
            for index in batch_indices
        ]
        async with semaphore:
            result = await _classify(candidates, llm_model, question_timeout)
        completed_batches += 1
        if on_progress is not None:
            on_progress(completed_batches, total_batches)
        return result

    results = await asyncio.gather(*(_run_batch(batch) for batch in batches))
    to_remove: set[int] = set().union(*results) if results else set()

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
        except Exception as exc:  # fail open: this batch's failure removes nothing from this batch.
            log.set(failed=True, error=str(exc), removed_count=0)
            return set()

        to_remove = {judgment.candidate_id for judgment in judgments if not judgment.is_question and judgment.candidate_id in valid_ids}
        log.set(failed=False, removed_count=len(to_remove))
        return to_remove
