from __future__ import annotations

from pydantic import BaseModel


async def call_llm(
    system_prompt: str,
    user_prompt: str,
    model: str,
    response_format: type[BaseModel] | None = None,
) -> str:
    """Send a single-turn system+user prompt to *model* via litellm and return its text response.

    If *response_format* is given, it is forwarded to litellm as a schema-constrained output
    request; the caller is responsible for parsing the returned text (e.g. via
    ``response_format.model_validate_json(result)``) -- this function always returns plain text.
    """
    import litellm

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = await litellm.acompletion(model=model, messages=messages, response_format=response_format)
    return response["choices"][0]["message"]["content"]
