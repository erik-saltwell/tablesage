from typing import Any

import pytest
from tablesage_tools.credentials import MissingCredential, require_credential
from tablesage_tools.credentials import test_connection as check_connection


def test_missing_key_identifies_provider_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(MissingCredential, match="gemini/test-model"):
        require_credential("gemini", "gemini/test-model")


@pytest.mark.anyio
async def test_model_checks_deduplicate_and_use_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    import litellm

    monkeypatch.setenv("GEMINI_API_KEY", "dummy-gemini-value")
    calls: list[dict[str, Any]] = []

    async def completion(**kwargs: Any) -> dict:
        calls.append(kwargs)
        return {}

    monkeypatch.setattr(litellm, "acompletion", completion)
    result = await check_connection("gemini", ["gemini/test-model", "gemini/test-model", "gemini/test-other"], 17)
    assert result.startswith("Success")
    assert [call["model"] for call in calls] == ["gemini/test-model", "gemini/test-other"]
    assert all(call["timeout"] == 17 for call in calls)


@pytest.mark.anyio
async def test_failed_test_does_not_leak_provider_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    import litellm

    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-value")

    async def completion(**kwargs: Any) -> None:
        raise RuntimeError("request failed with api_key=dummy-openai-value")

    monkeypatch.setattr(litellm, "acompletion", completion)
    result = await check_connection("openai", ["openai/test-model"], 30)
    assert "Provider request failed" in result
    assert "dummy-openai-value" not in result


@pytest.mark.anyio
async def test_unused_provider_does_not_make_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "dummy-anthropic-value")
    assert "No saved model" in await check_connection("anthropic", [], 30)
