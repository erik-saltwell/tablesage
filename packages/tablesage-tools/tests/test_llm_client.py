from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Annotated, Any, Literal

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic import BaseModel, Field
from tablesage_tools.llm import call_llm


class _Answer(BaseModel):
    value: str


class _Cat(BaseModel):
    type: Literal["cat"]
    lives: int


class _Dog(BaseModel):
    type: Literal["dog"]
    friendly: bool


class _DiscriminatedAnswer(BaseModel):
    animal: Annotated[_Cat | _Dog, Field(discriminator="type")]


class _FakeWideEvent:
    def __init__(self, fields: dict[str, Any]) -> None:
        self.fields = fields

    def set(self, **fields: Any) -> None:
        self.fields.update(fields)


def _capture_wide_events(monkeypatch: MonkeyPatch) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    @contextmanager
    def fake_wide_event(**fields: Any) -> Iterator[_FakeWideEvent]:
        event = _FakeWideEvent(fields)
        events.append(event.fields)
        yield event

    import tablesage_tools.llm.client as client

    monkeypatch.setattr(client.widelog, "wide_event", fake_wide_event)
    return events


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
async def test_call_llm_logs_unstructured_markdown_as_text_without_false_json_error(monkeypatch: MonkeyPatch) -> None:
    events = _capture_wide_events(monkeypatch)

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": "completion-123",
            "model": "claude-test",
            "choices": [{"finish_reason": "stop", "message": {"content": "## Recap\n\n- The gate opened."}}],
        }

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    await call_llm("system", "user", "anthropic/claude-test", prompt_name="generate_recap_summary")

    event = events[0]
    assert event["prompt_name"] == "generate_recap_summary"
    assert event["response_kind"] == "text"
    assert event["response_content_nonempty"] is True
    assert "response_json_valid" not in event
    assert "response_json_error" not in event
    assert "response_json_shape" not in event


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
    assert captured["response_format"] == {
        "type": "json_schema",
        "json_schema": {"name": "_Answer", "schema": _Answer.model_json_schema()},
    }


@pytest.mark.anyio
async def test_call_llm_logs_structured_output_contract_and_valid_response_shape(monkeypatch: MonkeyPatch) -> None:
    events = _capture_wide_events(monkeypatch)

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": "completion-123",
            "model": "claude-test",
            "choices": [{"finish_reason": "stop", "message": {"content": '{"value": "x"}'}}],
        }

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)
    monkeypatch.setattr(litellm, "supports_response_schema", lambda model: True)

    await call_llm("secret system prompt", "private transcript", "anthropic/claude-test", response_format=_Answer)

    assert len(events) == 1
    event = events[0]
    assert event["op"] == "call_llm"
    assert event["model"] == "anthropic/claude-test"
    assert event["provider"] == "anthropic"
    assert event["response_kind"] == "structured_json"
    assert event["response_schema_name"] == "_Answer"
    assert event["response_schema"] == _Answer.model_json_schema()
    assert len(event["response_schema_sha256"]) == 64
    assert event["response_schema_supported"] is True
    assert event["structured_response_valid"] is True
    assert event["response_json_shape"] == {"type": "object", "fields": {"value": {"type": "string", "length": 1}}}
    assert event["system_prompt_chars"] == len("secret system prompt")
    assert event["user_prompt_chars"] == len("private transcript")
    assert "secret system prompt" not in str(event)
    assert "private transcript" not in str(event)


@pytest.mark.anyio
async def test_call_llm_logs_validation_errors_without_response_content(monkeypatch: MonkeyPatch) -> None:
    events = _capture_wide_events(monkeypatch)

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        return {"choices": [{"message": {"content": '{"value": {"sensitive": "text"}}'}}]}

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    result = await call_llm("sys", "usr", "anthropic/claude-test", response_format=_Answer)

    assert result == '{"value": {"sensitive": "text"}}'
    event = events[0]
    assert event["structured_response_valid"] is False
    assert event["structured_response_errors"] == [
        {"type": "string_type", "location": ["value"], "message": "Input should be a valid string"}
    ]
    assert event["response_json_shape"] == {
        "type": "object",
        "fields": {"value": {"type": "object", "fields": {"sensitive": {"type": "string", "length": 4}}}},
    }
    assert "text" not in str(event)


@pytest.mark.anyio
async def test_call_llm_removes_discriminator_from_provider_schema(monkeypatch: MonkeyPatch) -> None:
    events = _capture_wide_events(monkeypatch)
    captured: dict[str, Any] = {}

    async def fake_acompletion(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"choices": [{"message": {"content": '{"animal": {"type": "cat", "lives": 9}}'}}]}

    import litellm

    monkeypatch.setattr(litellm, "acompletion", fake_acompletion)

    await call_llm("sys", "usr", "anthropic/claude-fable-5", response_format=_DiscriminatedAnswer)

    provider_format = captured["response_format"]
    provider_schema = provider_format["json_schema"]["schema"]
    assert provider_format["json_schema"]["name"] == "_DiscriminatedAnswer"
    assert "discriminator" not in str(provider_schema)
    assert provider_schema["properties"]["animal"]["oneOf"]
    assert events[0]["response_schema"] == provider_schema
    assert events[0]["structured_response_valid"] is True
