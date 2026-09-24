from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlmodel import Session
from tablesage_model.model import SessionProcessingState


def get_state(session: Session, session_id: uuid.UUID) -> SessionProcessingState | None:
    """Return a Session's workflow record without creating one."""
    return session.get(SessionProcessingState, session_id)


def get_or_create_state(session: Session, session_id: uuid.UUID) -> SessionProcessingState:
    """Return the workflow record, creating it lazily."""
    state = get_state(session, session_id)
    if state is None:
        state = SessionProcessingState(session_id=session_id)
        session.add(state)
        session.flush()
    return state


def set_draft_source(session: Session, session_id: uuid.UUID, source_artifact: str, source_modified_ns: int) -> SessionProcessingState:
    state = get_or_create_state(session, session_id)
    state.draft_source_artifact = source_artifact
    state.draft_source_modified_ns = source_modified_ns
    _touch(state)
    session.add(state)
    return state


def clear_draft_source(session: Session, session_id: uuid.UUID) -> SessionProcessingState | None:
    state = get_state(session, session_id)
    if state is None:
        return None
    state.draft_source_artifact = None
    state.draft_source_modified_ns = None
    _touch(state)
    session.add(state)
    return state


def delete_state(session: Session, session_id: uuid.UUID) -> None:
    state = get_state(session, session_id)
    if state is not None:
        session.delete(state)


def _touch(state: SessionProcessingState) -> None:
    state.updated_at = datetime.now(UTC)
