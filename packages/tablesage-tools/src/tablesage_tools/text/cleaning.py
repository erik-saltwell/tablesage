from __future__ import annotations

import asyncio
from typing import cast

import jiwer
from mathspell import analyze_text

_AT_TOKEN = "{[at]}"


def _wrap_for_mathspell_issues(text: str) -> str:
    return text.replace("@", _AT_TOKEN)


def _unwrap_for_mathspell_issues(text: str) -> str:
    return text.replace(_AT_TOKEN, "@")


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


def clean_text_for_evaluation(text: str, do_mathspell: bool) -> str:
    if text is None or len(text) == 0:
        return text
    retVal: str = text
    if do_mathspell:
        retVal = _wrap_for_mathspell_issues(retVal)
        retVal = analyze_text(retVal)
        retVal = _unwrap_for_mathspell_issues(retVal)

    transform: jiwer.Compose = _create_jiwer_compose()
    jiwer_result = transform(retVal)
    return cast(str, jiwer_result)


async def clean_multiple_texts(texts: list[str]) -> list[str]:
    transform: jiwer.Compose = _create_jiwer_compose()
    jiwer_result: list[str] = await asyncio.to_thread(transform, texts)
    return jiwer_result
