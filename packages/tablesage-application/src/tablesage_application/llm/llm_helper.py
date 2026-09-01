from __future__ import annotations

from typing import Any

import jinja2
from pydantic import BaseModel
from tablesage_tools.llm import call_llm

from ._prompts import PromptName, read_prompt_template, read_system_prompt

DEFAULT_LLM_MODEL = "anthropic/claude-sonnet-4-5"


def _template_variables(template_data: object) -> dict[str, Any]:
    if isinstance(template_data, BaseModel):
        return template_data.model_dump()
    return vars(template_data)


async def call_llm_with_prompt(
    prompt: PromptName,
    template_data: object,
    model: str = DEFAULT_LLM_MODEL,
    response_model: type[BaseModel] | None = None,
    timeout: float | None = None,
) -> str:
    """Render *prompt*'s template with *template_data* and send it to *model* alongside its system prompt.

    *template_data* is any object exposing its fields via `model_dump()` (a Pydantic model) or
    `vars()` (a dataclass or plain object); its fields become the template's top-level variables.

    If *response_model* is given, it is forwarded to `tablesage_tools.call_llm` as a schema-constrained
    output request. This function always returns plain text -- coercing it into *response_model*
    (e.g. via `response_model.model_validate_json(result)`) is left to the caller. *timeout* is
    forwarded as-is; `None` leaves `tablesage_tools.call_llm`'s own default in effect.
    """
    system_prompt = read_system_prompt(prompt)
    template = jinja2.Template(read_prompt_template(prompt), undefined=jinja2.StrictUndefined)
    user_prompt = template.render(**_template_variables(template_data))
    return await call_llm(system_prompt, user_prompt, model, response_format=response_model, timeout=timeout)
