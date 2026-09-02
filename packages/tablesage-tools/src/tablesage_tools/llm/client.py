from __future__ import annotations

import hashlib
import json
from importlib.metadata import version
from typing import Any

import widelog
from pydantic import BaseModel, ValidationError


def _remove_schema_keyword(value: Any, keyword: str) -> None:
    """Remove a provider-unsupported annotation from a generated schema in place."""
    if isinstance(value, dict):
        value.pop(keyword, None)
        for child in value.values():
            _remove_schema_keyword(child, keyword)
    elif isinstance(value, list):
        for child in value:
            _remove_schema_keyword(child, keyword)


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
    response_format: type[BaseModel] | None = None,
    timeout: float | None = None,
) -> str:
    """Send a single-turn system+user prompt to *model* via litellm and return its text response.

    If *response_format* is given, it is forwarded to litellm as a schema-constrained output
    request; the caller is responsible for parsing the returned text (e.g. via
    ``response_format.model_validate_json(result)``) -- this function always returns plain text.
    *timeout* is forwarded to litellm as-is; `None` (the default) leaves litellm's own default
    (600 seconds) in effect.
    """
    import litellm

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response_schema = response_format.model_json_schema() if response_format is not None else None
    if response_schema is not None:
        # Anthropic structured outputs reject this Pydantic annotation. The
        # oneOf branches and their const type fields preserve the union itself.
        _remove_schema_keyword(response_schema, "discriminator")
    provider_response_format = (
        {
            "type": "json_schema",
            "json_schema": {"name": response_format.__name__, "schema": response_schema},
        }
        if response_format is not None
        else None
    )
    canonical_schema = json.dumps(response_schema, sort_keys=True, separators=(",", ":")) if response_schema else None

    with widelog.wide_event(
        op="call_llm",
        model=model,
        provider=model.partition("/")[0] or None,
        litellm_version=version("litellm"),
        system_prompt_chars=len(system_prompt),
        user_prompt_chars=len(user_prompt),
        response_schema_name=response_format.__name__ if response_format is not None else None,
        response_schema=response_schema,
        response_schema_sha256=hashlib.sha256(canonical_schema.encode()).hexdigest() if canonical_schema else None,
        response_schema_supported=litellm.supports_response_schema(model=model) if response_format is not None else None,
    ) as log:
        response = await litellm.acompletion(
            model=model,
            messages=messages,
            response_format=provider_response_format,
            timeout=timeout,
        )
        choices = _response_value(response, "choices") or []
        choice = choices[0]
        content = _message_content(choice)
        log.set(
            response_id=_response_value(response, "id"),
            response_model=_response_value(response, "model"),
            finish_reason=_choice_value(choice, "finish_reason"),
            response_content_chars=len(content),
        )

        try:
            parsed_content = json.loads(content)
        except json.JSONDecodeError as exc:
            log.set(
                response_json_valid=False,
                response_json_error={"message": exc.msg, "line": exc.lineno, "column": exc.colno},
            )
        else:
            log.set(response_json_valid=True, response_json_shape=_json_shape(parsed_content))

        if response_format is not None:
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
