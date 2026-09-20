"""Provider authentication checks without workspace or settings knowledge."""

from __future__ import annotations

import os
from dataclasses import dataclass


class MissingCredential(ValueError):
    def __init__(self, provider: str, model: str) -> None:
        self.provider = provider
        self.model = model
        super().__init__(f"No {provider} API key is configured for {model}. Open Settings to add one.")


def require_credential(provider: str, model: str) -> None:
    key = {
        "elevenlabs": "ELEVENLABS_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider)
    if key and not os.environ.get(key, "").strip():
        raise MissingCredential(provider, model)


@dataclass(frozen=True)
class ConnectionTestResult:
    ok: bool
    message: str


async def test_connection(provider: str, models: list[str], timeout: int) -> ConnectionTestResult:
    """Exercise saved models; do not return raw exceptions that may contain secrets."""
    try:
        require_credential(provider, ", ".join(models) or "account")
        if provider == "elevenlabs":
            from elevenlabs import AsyncElevenLabs

            client = AsyncElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"], timeout=timeout)
            await client.user.get(request_options={"timeout_in_seconds": timeout})
            return ConnectionTestResult(True, "Success: ElevenLabs account is accessible. Transcription was not run.")
        if not models:
            return ConnectionTestResult(False, "No saved model role uses this provider. Select and save a model before testing.")
        import litellm

        # LiteLLM prints help banners to stdout on failures, which corrupts the TUI's screen.
        litellm.suppress_debug_info = True
        for model in dict.fromkeys(models):
            await litellm.acompletion(model=model, messages=[{"role": "user", "content": "Reply OK."}], timeout=timeout)
        return ConnectionTestResult(True, "Success: " + ", ".join(dict.fromkeys(models)))
    except MissingCredential as exc:
        return ConnectionTestResult(False, str(exc))
    except Exception as exc:
        status = getattr(exc, "status_code", None)
        name = type(exc).__name__.lower()
        if status in (401, 403) or "authentication" in name or "permission" in name:
            return ConnectionTestResult(False, "Authentication or permission failed. Check the key and its model/account access.")
        if status == 429 or "ratelimit" in name:
            return ConnectionTestResult(False, "Quota or rate limit reached. Check billing and retry later.")
        if "timeout" in name or "connection" in name:
            return ConnectionTestResult(False, "Network connection failed or timed out. Check connectivity and retry.")
        return ConnectionTestResult(False, "Provider request failed. Check the saved model ID and account access.")
