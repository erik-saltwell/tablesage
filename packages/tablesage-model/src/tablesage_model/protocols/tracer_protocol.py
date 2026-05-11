from __future__ import annotations

from typing import Any, Protocol


class TracerProtocol(Protocol):
    def add_context(self, name: str, value: Any) -> None: ...
    def log(self, event_name: str) -> None: ...

    def log_exception(
        self,
        exception: BaseException,
        event_name: str | None = None,
    ) -> None: ...
