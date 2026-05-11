from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PhasedProgressEvent:
    source: str
    phase: str


@dataclass(frozen=True, slots=True)
class IncrementalProgressEvent:
    source: str
    completed: int
    total: int


class PhasedProgressSink(Protocol):
    async def publish(self, event: PhasedProgressEvent) -> None: ...


class NullPhasedProgressSink(PhasedProgressSink):
    async def publish(self, event: PhasedProgressEvent) -> None:
        pass


class IncrementalProgressSink(Protocol):
    async def publish(self, event: IncrementalProgressEvent) -> None: ...


class NullIncrementalProgressSink(IncrementalProgressSink):
    async def publish(self, event: IncrementalProgressEvent) -> None:
        pass
