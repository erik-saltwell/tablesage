from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


@dataclass(frozen=True)
class PromptCachingPolicy:
    """Exact model/system pairs eligible during one campaign regeneration operation."""

    prefixes: frozenset[tuple[str, str]]
    ttl: str


_policy: ContextVar[PromptCachingPolicy | None] = ContextVar("regeneration_prompt_caching", default=None)


@contextmanager
def prompt_caching_scope(prefixes: frozenset[tuple[str, str]], ttl: str) -> Iterator[None]:
    """Propagate into asyncio.run without leaking to other workers or subsequent operations."""
    token = _policy.set(PromptCachingPolicy(prefixes, ttl))
    try:
        yield
    finally:
        _policy.reset(token)


def system_prompt_cache_ttl(model: str, system_prompt: str) -> str | None:
    policy = _policy.get()
    return policy.ttl if policy is not None and (model, system_prompt) in policy.prefixes else None
