from __future__ import annotations

import asyncio
from typing import NamedTuple

from .text_cleaner import clean_multiple_texts


class IndexedString(NamedTuple):
    text: str
    index: int


def _load_and_punctuate(texts: list[str]) -> list[str]:
    # we delay load in order to enable console output supression
    from punctuators.models import PunctCapSegModelONNX

    # model is loaded every time to save memory pressure.  This is typically only called once or infrequently.
    model = PunctCapSegModelONNX.from_pretrained("pcs_en")
    outputs: list[str] = model.infer(texts, apply_sbd=False)  # type: ignore
    if len(outputs) != len(texts):
        raise RuntimeError(f"Expected {len(texts)} outputs, got {len(outputs)}")
    return outputs


async def punctuate_text(texts: list[str]) -> list[str]:
    """Cleans punctuates text, leaving empty strings and strings that get cleaned to empty unchanged."""
    return_values: list[str] = list(texts)
    cleaned_texts = await clean_multiple_texts(return_values)
    indexed_texts: list[IndexedString] = [IndexedString(text, idx) for idx, text in enumerate(cleaned_texts) if text]

    if indexed_texts:
        to_process: list[str] = [item.text for item in indexed_texts]
        outputs = await asyncio.to_thread(_load_and_punctuate, to_process)
        for item, output in zip(indexed_texts, outputs, strict=True):
            return_values[item.index] = output

    return return_values
