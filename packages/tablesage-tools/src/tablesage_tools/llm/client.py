from __future__ import annotations

import asyncio
import hashlib
import json
import re
from collections.abc import Mapping
from copy import deepcopy
from importlib.metadata import version
from typing import Any

import widelog
from pydantic import BaseModel, ValidationError

_ASTRA_MODEL = "openai/gpt-6-astra"
_ASTRA_MEDIUM_THINKING_OPTIONS = {"reasoning_effort": "medium", "allowed_openai_params": ["reasoning_effort"]}
_ANTHROPIC_MODEL_METADATA = {
    "claude-opus-5-5": {
        "litellm_provider": "anthropic",
        "mode": "chat",
        "supports_native_structured_output": True,
        "supports_reasoning": True,
        "supports_adaptive_thinking": True,
        "max_output_tokens": 128_000,
        "max_input_tokens": 1_000_000,
    }
}


def supports_openai_explicit_prompt_caching(model: str) -> bool:
    """Direct GPT-5.6+ models expose explicit breakpoints; older models stay implicit.

    Use the documented model generation rather than LiteLLM's older parameter catalog,
    which does not yet list prompt_cache_options for Chat Completions.
    """
    match = re.match(r"^openai/gpt-(\d+)(?:\.(\d+))?(?:-|$)", model)
    return match is not None and (int(match[1]), int(match[2] or 0)) >= (5, 6)


def _remove_schema_keyword(value: Any, keyword: str) -> None:
    """Remove a provider-unsupported annotation from a generated schema in place."""
    if isinstance(value, dict):
        value.pop(keyword, None)
        for child in value.values():
            _remove_schema_keyword(child, keyword)
    elif isinstance(value, list):
        for child in value:
            _remove_schema_keyword(child, keyword)


def _make_strict(value: Any) -> None:
    """Close every object schema in place and require all of its properties, as OpenAI's strict mode demands."""
    if isinstance(value, dict):
        if isinstance(value.get("properties"), dict):
            value["additionalProperties"] = False
            value["required"] = list(value["properties"])
        for child in value.values():
            _make_strict(child)
    elif isinstance(value, list):
        for child in value:
            _make_strict(child)


def _adapt_anthropic_schema(value: Any) -> None:
    """Adapt schema features that Anthropic cannot reliably compile.

    Regex and object-level conditional checks become guidance. Required fields,
    types and enums still constrain decoding. Callers validate the
    returned document against the untouched source schema, including these conditions.
    Standalone unions (such as nullable fields) remain provider-enforced.
    """
    if isinstance(value, dict):
        if "pattern" in value:
            pattern = value.pop("pattern")
            value["description"] = (value.get("description", "") + f" Must match this regular expression: {pattern}").strip()
        if value.get("type") == "object" and "properties" in value and "anyOf" in value:
            conditions = value.pop("anyOf")
            guidance = "Must satisfy at least one of these additional constraints: " + json.dumps(conditions, ensure_ascii=False)
            value["description"] = (value.get("description", "") + " " + guidance).strip()
        types = value.get("type")
        if isinstance(types, list) and set(types) == {"string", "null"} and isinstance(value.get("enum"), list):
            # The provider rejects mixed-type enums attached to a type array.
            # Typed alternatives retain the exact allowed string/null values.
            alternatives = []
            strings = [item for item in value["enum"] if isinstance(item, str)]
            common = {key: item for key, item in value.items() if key not in {"type", "enum"}}
            if strings:
                alternatives.append({**deepcopy(common), "type": "string", "enum": strings})
            if None in value["enum"]:
                alternatives.append({**deepcopy(common), "type": "null"})
            value.clear()
            value["anyOf"] = alternatives
        for child in value.values():
            _adapt_anthropic_schema(child)
    elif isinstance(value, list):
        for child in value:
            _adapt_anthropic_schema(child)


def _json_shape(value: Any, *, depth: int = 0) -> dict[str, Any]:
    """Describe JSON structure without retaining scalar content."""
    if depth >= 5:
        return {"type": type(value).__name__}
    if isinstance(value, dict):
        return {
            "type": "object",
            "fields": {str(key): _json_shape(item, depth=depth + 1) for key, item in value.items()},
        }
    if isinstance(value, list):
        item_types = sorted({type(item).__name__ for item in value})
        shape: dict[str, Any] = {"type": "array", "length": len(value), "item_types": item_types}
        if value:
            shape["first_item"] = _json_shape(value[0], depth=depth + 1)
        return shape
    if isinstance(value, str):
        return {"type": "string", "length": len(value)}
    if value is None:
        return {"type": "null"}
    if isinstance(value, bool):
        return {"type": "boolean"}
    if isinstance(value, (int, float)):
        return {"type": "number"}
    return {"type": type(value).__name__}


def _response_value(response: Any, key: str) -> Any:
    if isinstance(response, dict):
        return response.get(key)
    return getattr(response, key, None)


def _choice_value(choice: Any, key: str) -> Any:
    if isinstance(choice, dict):
        return choice.get(key)
    return getattr(choice, key, None)


def _message_content(choice: Any) -> str:
    message = _choice_value(choice, "message")
    content = _response_value(message, "content")
    return content if isinstance(content, str) else str(content)


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str,
    response_format: type[BaseModel] | Mapping[str, Any] | None = None,
    timeout: float | None = None,
    prompt_name: str | None = None,
    model_options: Mapping[str, Any] | None = None,
    strict_schema: bool = False,
    system_prompt_cache_ttl: str | None = None,
) -> str:
    """Send a single-turn system+user prompt to *model* via litellm and return its text response.

    If *response_format* is given, it is forwarded to litellm as a schema-constrained output
    request; the caller is responsible for parsing the returned text (e.g. via
    ``response_format.model_validate_json(result)``) -- this function always returns plain text.
    Without *strict_schema*, OpenAI treats the schema as a hint (an ``enum`` is not enforced);
    *strict_schema* requests strict mode, which needs every field required and no ``oneOf``.
    *timeout* is forwarded to litellm as-is; `None` (the default) leaves litellm's own default
    (600 seconds) in effect. *prompt_name* is diagnostic context only and is never sent to the
    provider. Opus 5.5 uses streaming internally to keep long requests active, then assembles
    the complete response; an explicit *timeout* also bounds the full stream. *model_options*
    passes provider-specific controls such as reasoning effort through to LiteLLM.
    *system_prompt_cache_ttl* opts direct Anthropic (``5m``/``1h``) or GPT-5.6+
    (``30m``) calls into caching the system prefix only. GPT-5.6+ uses explicit-only
    mode without breakpoints when no TTL is supplied, avoiding automatic writes of
    changing user input. Older OpenAI models and Gemini keep implicit caching. The provider
    enforces model-specific minimum cache sizes; requesting caching does not guarantee a hit.
    """
    import litellm

    from ..credentials import require_credential

    if system_prompt_cache_ttl not in (None, "5m", "1h", "30m"):
        raise ValueError("System prompt cache TTL must be 5m, 1h, or 30m.")

    require_credential(model.partition("/")[0], model)

    provider, _, model_name = model.partition("/")
    openai_explicit = supports_openai_explicit_prompt_caching(model)
    if system_prompt_cache_ttl is not None:
        if provider == "anthropic" and system_prompt_cache_ttl not in ("5m", "1h"):
            raise ValueError("Anthropic system prompt cache TTL must be 5m or 1h.")
        if openai_explicit and system_prompt_cache_ttl != "30m":
            raise ValueError("OpenAI Chat Completions system prompt cache TTL must be 30m.")
    if provider == "anthropic" and model_name in _ANTHROPIC_MODEL_METADATA:
        # Older bundled LiteLLM catalogs omit this capability and fall back to forced tool use,
        # which Opus 5.5 rejects, and a tiny output budget that can be exhausted by thinking.
        # Register adaptive thinking too so explicit effort reaches output_config.effort.
        # These are published model capabilities, not task-specific generation controls.
        # Keep LiteLLM's native defaults, schema conversion, and explicit max_tokens overrides.
        metadata = _ANTHROPIC_MODEL_METADATA[model_name]
        litellm.register_model({model_name: metadata, model: metadata})

    effective_model_options: dict[str, Any] = dict(model_options) if model_options is not None else {}
    if model == _ASTRA_MODEL and "reasoning_effort" not in effective_model_options:
        effective_model_options = {**_ASTRA_MEDIUM_THINKING_OPTIONS, **effective_model_options}

    request_options: dict[str, Any] = dict(effective_model_options)
    if provider == "anthropic" and model_name in _ANTHROPIC_MODEL_METADATA:
        request_options.setdefault("stream", True)
    streaming = bool(request_options.get("stream"))
    if streaming and provider in ("openai", "gemini"):
        request_options["stream_options"] = {**(request_options.get("stream_options") or {}), "include_usage": True}

    cache_enabled = system_prompt_cache_ttl is not None and (provider == "anthropic" or openai_explicit)
    system_content: str | list[dict[str, Any]] = system_prompt
    if cache_enabled and provider == "anthropic":
        system_content = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral", "ttl": system_prompt_cache_ttl}}]
    if openai_explicit:
        # extra_body is OpenAI's supported pass-through for fields not yet present in
        # the installed LiteLLM/SDK parameter catalogs. Preserve unrelated extra fields.
        cache_options = {"mode": "explicit"}
        if cache_enabled:
            cache_options["ttl"] = system_prompt_cache_ttl
            system_content = [{"type": "text", "text": system_prompt, "prompt_cache_breakpoint": {"mode": "explicit"}}]
        request_options.pop("prompt_cache_options", None)
        request_options["extra_body"] = {**(request_options.get("extra_body") or {}), "prompt_cache_options": cache_options}
    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_prompt},
    ]
    response_schema = (
        deepcopy(dict(response_format))
        if isinstance(response_format, Mapping)
        else response_format.model_json_schema()
        if response_format is not None
        else None
    )
    schema_name = response_format.__name__ if isinstance(response_format, type) else (prompt_name or "artifact")
    if response_schema is not None:
        # Anthropic structured outputs reject this Pydantic annotation. The
        # oneOf branches and their const type fields preserve the union itself.
        _remove_schema_keyword(response_schema, "discriminator")
        if strict_schema:
            _make_strict(response_schema)
        if provider == "anthropic":
            _adapt_anthropic_schema(response_schema)
    provider_response_format = (
        {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": response_schema, **({"strict": True} if strict_schema else {})},
        }
        if response_format is not None
        else None
    )
    canonical_schema = json.dumps(response_schema, sort_keys=True, separators=(",", ":")) if response_schema else None

    with widelog.wide_event(
        op="call_llm",
        prompt_name=prompt_name,
        model=model,
        provider=model.partition("/")[0] or None,
        litellm_version=version("litellm"),
        system_prompt_chars=len(system_prompt),
        user_prompt_chars=len(user_prompt),
        response_kind="structured_json" if response_format is not None else "text",
        response_schema_name=schema_name if response_format is not None else None,
        response_schema=response_schema,
        response_schema_sha256=hashlib.sha256(canonical_schema.encode()).hexdigest() if canonical_schema else None,
        response_schema_supported=litellm.supports_response_schema(model=model) if response_format is not None else None,
        strict_schema=strict_schema if response_format is not None else None,
        model_options=effective_model_options or None,
        streaming=streaming,
        system_prompt_cache_ttl_requested=system_prompt_cache_ttl,
        system_prompt_cache_ttl_applied=system_prompt_cache_ttl if cache_enabled else None,
        prompt_caching_mode="explicit" if openai_explicit or cache_enabled else "implicit" if provider in ("openai", "gemini") else None,
    ) as log:
        async with asyncio.timeout(timeout if streaming else None):
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                response_format=provider_response_format,
                timeout=timeout,
                **request_options,
            )
            if streaming:
                chunks = []
                try:
                    async for chunk in response:
                        chunks.append(chunk)
                finally:
                    await response.aclose()
                log.set(stream_chunk_count=len(chunks))
                if not any(
                    _choice_value(choice, "finish_reason") for chunk in chunks for choice in (_response_value(chunk, "choices") or [])
                ):
                    raise ValueError("LLM stream ended without a final completion event")
                response = litellm.stream_chunk_builder(chunks, messages=messages)
        choices = _response_value(response, "choices") or []
        choice = choices[0]
        content = _message_content(choice)
        usage = _response_value(response, "usage")
        prompt_details = _response_value(usage, "prompt_tokens_details")
        if prompt_details is None:
            prompt_details = _response_value(usage, "input_tokens_details")
        cache_read_tokens = _response_value(prompt_details, "cached_tokens")
        if cache_read_tokens is None:
            cache_read_tokens = _response_value(usage, "cache_read_input_tokens")
        cache_write_tokens = _response_value(prompt_details, "cache_write_tokens")
        if cache_write_tokens is None:
            cache_write_tokens = _response_value(usage, "cache_creation_input_tokens")
        log.set(
            response_id=_response_value(response, "id"),
            response_model=_response_value(response, "model"),
            finish_reason=_choice_value(choice, "finish_reason"),
            response_content_chars=len(content),
            response_content_nonempty=bool(content.strip()),
            prompt_tokens=_response_value(usage, "prompt_tokens"),
            completion_tokens=_response_value(usage, "completion_tokens"),
            cache_read_input_tokens=cache_read_tokens,
            cache_creation_input_tokens=cache_write_tokens,
        )

        if response_format is not None:
            try:
                parsed_content = json.loads(content)
            except json.JSONDecodeError as exc:
                log.set(
                    response_json_valid=False,
                    response_json_error={"message": exc.msg, "line": exc.lineno, "column": exc.colno},
                )
            else:
                log.set(response_json_valid=True, response_json_shape=_json_shape(parsed_content))

            if isinstance(response_format, Mapping):
                return content
            try:
                response_format.model_validate_json(content)
            except ValidationError as exc:
                errors = [
                    {
                        "type": error["type"],
                        "location": list(error["loc"]),
                        "message": error["msg"],
                    }
                    for error in exc.errors(include_input=False, include_url=False)
                ]
                log.set(structured_response_valid=False, structured_response_errors=errors)
            else:
                log.set(structured_response_valid=True)

        return content
