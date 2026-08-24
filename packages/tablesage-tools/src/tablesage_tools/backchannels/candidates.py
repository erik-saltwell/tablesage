from __future__ import annotations

from functools import cache
from importlib.resources import files

from ..model import Transcript
from ..text import clean_text_for_evaluation

_RESOURCE_PACKAGE = __name__.rsplit(".", maxsplit=1)[0]


@cache
def _wordlist() -> frozenset[str]:
    raw = files(_RESOURCE_PACKAGE).joinpath("wordlist.txt").read_text("utf-8")
    return frozenset(line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#"))


def find_backchannel_candidates(transcript: Transcript, max_words: int) -> list[int]:
    """Return the indices into `transcript.utterances` of utterances that are candidate backchannels.

    A candidate is an utterance with `max_words` words or fewer whose normalized text (lowercase,
    punctuation stripped, whitespace collapsed) exactly matches an entry in `wordlist.txt`. Word
    count is taken from `len(utterance.words)`, not a split of the text, since punctuation
    restoration can re-tokenize a word (e.g. "uh-huh" as two `words` entries).

    This is a cheap, high-recall pre-filter -- it does not distinguish a pure acknowledgment
    ("Yeah.") from a short answer to a question ("Yeah." in response to "Are you coming?"); that
    disambiguation is left to an LLM call over the candidates this returns.
    """
    wordlist = _wordlist()
    candidates: list[int] = []
    for index, utterance in enumerate(transcript.utterances):
        if len(utterance.words) > max_words:
            continue
        text = utterance.punctuated_text if utterance.punctuated_text is not None else utterance.text
        normalized = clean_text_for_evaluation(text, do_mathspell=False)
        if normalized in wordlist:
            candidates.append(index)
    return candidates
