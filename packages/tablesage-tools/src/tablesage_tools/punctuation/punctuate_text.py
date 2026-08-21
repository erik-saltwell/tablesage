from __future__ import annotations

from ..model.transcript import Transcript
from ..text.punctuation import punctuate_text


async def punctuate_transcript(transcript: Transcript) -> Transcript:
    """Punctuate every utterance's text, returning a new Transcript with `punctuated_text` set."""
    texts = [utterance.text for utterance in transcript.utterances]
    punctuated_texts = await punctuate_text(texts)

    new_utterances = [
        utterance.model_copy(update={"punctuated_text": punctuated_text})
        for utterance, punctuated_text in zip(transcript.utterances, punctuated_texts, strict=True)
    ]
    return Transcript(utterances=new_utterances)
