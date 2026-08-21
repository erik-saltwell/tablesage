from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jinja2
import pytest
from pydantic import BaseModel
from tablesage_application.llm import DEFAULT_LLM_MODEL, PromptName, call_llm_with_prompt
from tablesage_application.llm._prompts import read_prompt_template, read_system_prompt


@dataclass
class _SummaryPromptData:
    discourse: str
    glossary: str = ""


class _SummaryResult(BaseModel):
    summary: str


def test_read_system_prompt_and_template_for_summarize_session() -> None:
    system_prompt = read_system_prompt(PromptName.SUMMARIZE_SESSION)
    template = read_prompt_template(PromptName.SUMMARIZE_SESSION)

    assert "summariz" in system_prompt.lower()
    assert "{{ discourse }}" in template


@pytest.mark.anyio
async def test_call_llm_with_prompt_renders_template_and_forwards_to_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_llm(system_prompt: str, user_prompt: str, model: str, response_format: Any = None) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        captured["model"] = model
        captured["response_format"] = response_format
        return "the summary"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    result = await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        _SummaryPromptData(discourse="Alice: Hello.\nBob: Hi."),
        model="anthropic/claude-sonnet-4-5",
        response_model=_SummaryResult,
    )

    assert result == "the summary"
    assert captured["model"] == "anthropic/claude-sonnet-4-5"
    assert captured["response_format"] is _SummaryResult
    assert "Alice: Hello." in captured["user_prompt"]
    assert "Proper nouns" not in captured["user_prompt"]  # empty glossary omitted
    assert captured["system_prompt"] == read_system_prompt(PromptName.SUMMARIZE_SESSION)


@pytest.mark.anyio
async def test_call_llm_with_prompt_accepts_pydantic_template_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PydanticPromptData(BaseModel):
        discourse: str
        glossary: str = ""

    captured: dict[str, Any] = {}

    async def fake_call_llm(system_prompt: str, user_prompt: str, model: str, response_format: Any = None) -> str:
        captured["user_prompt"] = user_prompt
        return "ok"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        _PydanticPromptData(discourse="Alice: Hello.", glossary="Eldoria: a kingdom"),
    )

    assert "Eldoria: a kingdom" in captured["user_prompt"]


@pytest.mark.anyio
async def test_call_llm_with_prompt_uses_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_llm(system_prompt: str, user_prompt: str, model: str, response_format: Any = None) -> str:
        captured["model"] = model
        return "ok"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    await call_llm_with_prompt(PromptName.SUMMARIZE_SESSION, _SummaryPromptData(discourse="x"))

    assert captured["model"] == DEFAULT_LLM_MODEL


def test_missing_template_variable_raises() -> None:
    template = jinja2.Template(
        read_prompt_template(PromptName.SUMMARIZE_SESSION),
        undefined=jinja2.StrictUndefined,
    )

    with pytest.raises(jinja2.UndefinedError):
        template.render()
