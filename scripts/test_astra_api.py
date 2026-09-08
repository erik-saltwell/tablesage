"""Verify that the configured OpenAI GPT-6 Astra route accepts a low-thinking request.

Run from the repository root:

    uv run python scripts/test_astra_api.py
"""

from __future__ import annotations

import asyncio

from tablesage_tools.llm import call_llm

ASTRA_MODEL = "openai/gpt-6-astra"


async def main() -> None:
    response = await call_llm(
        "Reply with exactly: Astra API OK",
        "Confirm that this test request completed.",
        ASTRA_MODEL,
        model_options={"reasoning_effort": "low", "allowed_openai_params": ["reasoning_effort"]},
        prompt_name="test_astra_api",
        timeout=60,
    )
    print(response.strip())


if __name__ == "__main__":
    asyncio.run(main())
