from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

import jinja2
import widelog
from pydantic import BaseModel
from tablesage_tools.llm import call_llm

from ..observability import prompt_traces_dir
from ._prompts import PromptName, read_prompt_template, read_system_prompt

DEFAULT_LLM_MODEL = "anthropic/claude-sonnet-4-5"


@dataclass(frozen=True)
class PromptExecution:
    """Explicit experimental prompt texts and evidence hook; packaged prompts remain the default.

    The observer runs before transport and after completion/failure. Unlike diagnostic tracing,
    evidence-write failures propagate so experiments cannot silently lose their records.
    `transport` is an optional offline replay boundary, never used by normal application calls.
    """

    system: str
    template: str
    observer: Callable[[dict[str, Any]], None] | None = None
    transport: Callable[..., Awaitable[str]] | None = None


def _template_variables(template_data: object) -> dict[str, Any]:
    converter = getattr(template_data, "to_template_context", None)
    if callable(converter):
        return converter()
    if isinstance(template_data, BaseModel):
        return template_data.model_dump()
    return vars(template_data)


def render_prompt(prompt: PromptName, template_data: object, execution: PromptExecution | None = None) -> tuple[str, str]:
    """Render exactly the messages used by transport, without making a provider call."""
    system_prompt = execution.system if execution else read_system_prompt(prompt)
    template_text = execution.template if execution else read_prompt_template(prompt)
    template = jinja2.Template(
        template_text,
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=callable(getattr(template_data, "to_template_context", None)),
    )
    return system_prompt, template.render(**_template_variables(template_data))


async def call_llm_with_prompt(
    prompt: PromptName,
    template_data: object,
    model: str = DEFAULT_LLM_MODEL,
    response_model: type[BaseModel] | Mapping[str, Any] | None = None,
    timeout: float | None = None,
    model_options: Mapping[str, Any] | None = None,
    strict_schema: bool = False,
    trace_system_prompt: bool = False,
    trace_user_prompt: bool = False,
    trace_output: bool = False,
    execution: PromptExecution | None = None,
) -> str:
    """Render *prompt*'s template with *template_data* and send it to *model* alongside its system prompt.

    *template_data* is any object exposing its fields via `model_dump()` (a Pydantic model) or
    `vars()` (a dataclass or plain object); its fields become the template's top-level variables.

    *response_model* may be a Pydantic model or a bundled JSON Schema mapping.
    If *response_model* is given, it is forwarded to `tablesage_tools.call_llm` as a schema-constrained
    output request. This function always returns plain text -- coercing it into *response_model*
    (e.g. via `response_model.model_validate_json(result)`) is left to the caller. *timeout* is
    forwarded as-is; `None` leaves `tablesage_tools.call_llm`'s own default in effect.
    `model_options` passes provider-specific controls such as reasoning effort through to LiteLLM.
    `strict_schema` asks the provider to enforce *response_model* exactly (see `tablesage_tools.call_llm`).

    The `trace_*` flags save the rendered system prompt, user prompt, and/or raw output to
    `prompts/<date>_<time>_system.md`, `_user.md`, and `_output.md` in the logs directory, for
    debugging. One call's files share a timestamp. Prompts are written before the call, so they
    survive a failed one. Tracing never makes a call fail.
    """
    system_prompt, user_prompt = render_prompt(prompt, template_data, execution)
    trace_stem = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f") if trace_system_prompt or trace_user_prompt or trace_output else None
    if trace_stem is not None and trace_system_prompt:
        _write_trace(trace_stem, "system", system_prompt, prompt)
    if trace_stem is not None and trace_user_prompt:
        _write_trace(trace_stem, "user", user_prompt, prompt)
    call_kwargs: dict[str, Any] = {
        "response_format": response_model,
        "timeout": timeout,
        "prompt_name": prompt.value,
    }
    if strict_schema:
        call_kwargs["strict_schema"] = True
    if model_options is not None:
        call_kwargs["model_options"] = model_options
    observer = execution.observer if execution else None
    if observer:
        observer(
            {
                "phase": "started",
                "system": system_prompt,
                "user": user_prompt,
                "schema": dict(response_model)
                if isinstance(response_model, Mapping)
                else response_model.model_json_schema()
                if response_model
                else None,
                "strict_schema": strict_schema,
            }
        )
    started = monotonic()
    transport = execution.transport if execution and execution.transport else call_llm
    try:
        output = await transport(system_prompt, user_prompt, model, **call_kwargs)
    except Exception as exc:
        if observer:
            observer({"phase": "failed", "elapsed_seconds": monotonic() - started, "error_type": type(exc).__name__})
        raise
    if observer:
        observer({"phase": "completed", "elapsed_seconds": monotonic() - started, "raw": output})
    if trace_stem is not None and trace_output:
        _write_trace(trace_stem, "output", output, prompt)
    return output


def _write_trace(stem: str, kind: str, content: str, prompt: PromptName) -> None:
    """Write one trace file; a failure is logged rather than raised, since tracing is diagnostic only."""
    path: Path = prompt_traces_dir() / f"{stem}_{kind}.md"
    with widelog.wide_event(op="llm_prompt_trace", prompt_name=prompt.value, kind=kind, path=str(path), chars=len(content)) as log:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        except OSError as exc:
            log.error(exc)
