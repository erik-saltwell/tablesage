from __future__ import annotations


async def call_llm(prompt: str, model: str) -> str:
    """Send a single-turn prompt to *model* via litellm and return its text response."""
    import litellm

    response = await litellm.acompletion(model=model, messages=[{"role": "user", "content": prompt}])
    return response["choices"][0]["message"]["content"]
