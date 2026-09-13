from __future__ import annotations

import asyncio
from typing import cast

import jiwer


def _create_jiwer_compose() -> jiwer.Compose:
    return_value: jiwer.Compose = jiwer.Compose(
        [
            jiwer.ToLowerCase(),
            jiwer.RemovePunctuation(),
            jiwer.RemoveMultipleSpaces(),
            jiwer.Strip(),
        ]
    )
    return return_value


def clean_text_for_evaluation(text: str) -> str:
    if text is None or len(text) == 0:
        return text
    transform: jiwer.Compose = _create_jiwer_compose()
    jiwer_result = transform(text)
    return cast(str, jiwer_result)


async def clean_multiple_texts(texts: list[str]) -> list[str]:
    transform: jiwer.Compose = _create_jiwer_compose()
    jiwer_result: list[str] = await asyncio.to_thread(transform, texts)
    return jiwer_result
