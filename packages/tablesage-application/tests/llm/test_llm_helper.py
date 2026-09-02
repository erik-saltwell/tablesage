from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import jinja2
import pytest
from pydantic import BaseModel
from tablesage_application.llm import DEFAULT_LLM_MODEL, PromptName, call_llm_with_prompt
from tablesage_application.llm._prompts import read_prompt_template, read_system_prompt


@dataclass
class _SummaryPromptData:
    ledger: str
    attendees: list[dict[str, object]] = field(default_factory=list)
    glossary: list[dict[str, str | None]] = field(default_factory=list)
    campaign_name: str = "Iron Pact"
    session_date: str | None = None
    game_system: str | None = None


class _SummaryResult(BaseModel):
    summary: str


def test_read_system_prompt_and_template_for_summarize_session() -> None:
    system_prompt = read_system_prompt(PromptName.SUMMARIZE_SESSION)
    template = read_prompt_template(PromptName.SUMMARIZE_SESSION)

    assert "# Overview" in system_prompt
    assert "# Input Description" in system_prompt
    assert "{{ ledger }}" in template
    assert "{{ campaign_name }}" in template


def test_read_system_prompt_and_template_for_generate_ledger() -> None:
    system_prompt = read_system_prompt(PromptName.GENERATE_LEDGER)
    template = read_prompt_template(PromptName.GENERATE_LEDGER)

    assert "Ledger Format v3" in system_prompt
    assert "{% for role in known_roles %}" in template
    assert "{% for attendee in attendees %}" in template
    assert "{% for entry in glossary %}" in template
    assert "{{ transcript }}" in template


@pytest.mark.anyio
async def test_call_llm_with_prompt_renders_template_and_forwards_to_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_llm(
        system_prompt: str, user_prompt: str, model: str, response_format: Any = None, timeout: float | None = None
    ) -> str:
        captured["system_prompt"] = system_prompt
        captured["user_prompt"] = user_prompt
        captured["model"] = model
        captured["response_format"] = response_format
        return "the summary"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    result = await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        _SummaryPromptData(ledger='{"utterances": []}'),
        model="anthropic/claude-sonnet-4-5",
        response_model=_SummaryResult,
    )

    assert result == "the summary"
    assert captured["model"] == "anthropic/claude-sonnet-4-5"
    assert captured["response_format"] is _SummaryResult
    assert '{"utterances": []}' in captured["user_prompt"]
    assert "<glossary>" in captured["user_prompt"]  # glossary section is present even when empty
    assert "Campaign: Iron Pact" in captured["user_prompt"]
    assert "Game system: unspecified" in captured["user_prompt"]  # None renders as "unspecified", not the literal "None"
    assert "Session date: unknown" in captured["user_prompt"]  # None renders as "unknown", not the literal "None"
    assert captured["system_prompt"] == read_system_prompt(PromptName.SUMMARIZE_SESSION)


@pytest.mark.anyio
async def test_call_llm_with_prompt_accepts_pydantic_template_data(monkeypatch: pytest.MonkeyPatch) -> None:
    class _PydanticPromptData(BaseModel):
        ledger: str
        attendees: list[dict[str, object]]
        glossary: list[dict[str, str | None]]
        campaign_name: str
        session_date: str | None
        game_system: str | None

    captured: dict[str, Any] = {}

    async def fake_call_llm(
        system_prompt: str, user_prompt: str, model: str, response_format: Any = None, timeout: float | None = None
    ) -> str:
        captured["user_prompt"] = user_prompt
        return "ok"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    await call_llm_with_prompt(
        PromptName.SUMMARIZE_SESSION,
        _PydanticPromptData(
            ledger='{"utterances": []}',
            attendees=[{"player_name": "Alice", "roles": ["Zaria"]}],
            glossary=[
                {"term": "Aldor", "description": None},
                {"term": "Eldoria", "description": "a kingdom"},
            ],
            campaign_name="Iron Pact",
            session_date=None,
            game_system=None,
        ),
    )

    assert "- Aldor\n" in captured["user_prompt"]
    assert "Eldoria: a kingdom" in captured["user_prompt"]
    assert "None" not in captured["user_prompt"]


@pytest.mark.anyio
async def test_call_llm_with_prompt_uses_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_llm(
        system_prompt: str, user_prompt: str, model: str, response_format: Any = None, timeout: float | None = None
    ) -> str:
        captured["model"] = model
        return "ok"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    await call_llm_with_prompt(PromptName.SUMMARIZE_SESSION, _SummaryPromptData(ledger="x"))

    assert captured["model"] == DEFAULT_LLM_MODEL


@pytest.mark.anyio
async def test_call_llm_with_prompt_forwards_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def fake_call_llm(
        system_prompt: str, user_prompt: str, model: str, response_format: Any = None, timeout: float | None = None
    ) -> str:
        captured["timeout"] = timeout
        return "ok"

    monkeypatch.setattr("tablesage_application.llm.llm_helper.call_llm", fake_call_llm)

    await call_llm_with_prompt(PromptName.SUMMARIZE_SESSION, _SummaryPromptData(ledger="x"), timeout=1200)

    assert captured["timeout"] == 1200


def test_missing_template_variable_raises() -> None:
    template = jinja2.Template(
        read_prompt_template(PromptName.SUMMARIZE_SESSION),
        undefined=jinja2.StrictUndefined,
    )

    with pytest.raises(jinja2.UndefinedError):
        template.render()
