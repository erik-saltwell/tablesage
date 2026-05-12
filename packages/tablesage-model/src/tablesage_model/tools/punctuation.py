from __future__ import annotations

import asyncio
from typing import NamedTuple

from .text_cleaner import clean_text_for_evaluation


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
    return_values: list[str] = list(texts)
    cleaned = [IndexedString(clean_text_for_evaluation(text, False), idx) for idx, text in enumerate(return_values)]
    non_empties = [item for item in cleaned if item.text]

    if non_empties:
        to_process: list[str] = [item.text for item in non_empties]
        outputs = await asyncio.to_thread(_load_and_punctuate, to_process)
        assert len(outputs) == len(non_empties), f"Expected {len(non_empties)} outputs, got {len(outputs)}"
        for idx, output in enumerate(outputs):
            return_values[non_empties[idx].index] = output

    return return_values
