"""Manual-step drafts: unfinished work a step's screen offers to save when it is cancelled.

Every manual step's screen leaves the same way: with no changes it just closes; with changes it asks Save / Don't
Save / Cancel. Save keeps the work as a draft in the Session's processing state, tied to what the step reviews, and
the step reopens from it next time. A draft never completes a step.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from ..dialogs.generic import ConfirmationDialog

if TYPE_CHECKING:
    from tablesage_application import Application
    from tablesage_application.paths import ArtifactName
    from textual.screen import Screen


@dataclass(frozen=True)
class DraftSlot:
    application: Application
    session_id: uuid.UUID
    step_id: str
    # What the step reviews; a draft made against an earlier version of it is not offered.
    basis: ArtifactName

    def load(self) -> Any:
        return self.application.load_step_draft(self.session_id, self.step_id)

    def save(self, value: object) -> None:
        self.application.save_step_draft(self.session_id, self.step_id, self.basis, value)

    def discard(self) -> None:
        self.application.discard_step_draft(self.session_id, self.step_id)


def leave_with_draft(
    screen: Screen[Any], *, changed: bool, slot: DraftSlot | None, value: Callable[[], object], leave: Callable[[], object]
) -> None:
    """Close a manual step's screen as cancelled, first offering to keep changed work as a draft."""
    if not changed or slot is None:
        leave()
        return

    def on_choice(choice: bool | None) -> None:
        if choice is None:
            return
        if choice:
            try:
                slot.save(value())
            except (OSError, ValueError) as exc:
                screen.notify(f"Could not save your changes: {exc}", severity="error")
                return
        leave()

    screen.app.push_screen(
        ConfirmationDialog(
            title="Save Your Changes?",
            prompt="Save your changes so you can pick up where you left off?",
            no_label="Don't Save",
            yes_label="Save",
        ),
        on_choice,
    )
