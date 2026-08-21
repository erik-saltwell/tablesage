from __future__ import annotations

from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic import BaseModel
from tablesage_tools.llm import call_llm


class _Answer(BaseModel):
    value: str


@pytest.mark.anyio
async def test_call_llm_builds_system_and_user_messages(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": "hello"}}]}

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_llm("system instructions", "user question", "some/model")

    assert result == "hello"
    assert captured["model"] == "some/model"
    assert captured["messages"] == [
        {"role": "system", "content": "system instructions"},
        {"role": "user", "content": "user question"},
    ]
    assert captured["response_format"] is None


@pytest.mark.anyio
async def test_call_llm_forwards_response_format(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": '{"value": "x"}'}}]}

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_llm("sys", "usr", "some/model", response_format=_Answer)

    assert result == '{"value": "x"}'
    assert captured["response_format"] is _Answer
