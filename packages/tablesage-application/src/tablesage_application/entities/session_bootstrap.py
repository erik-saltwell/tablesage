from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import text
from sqlmodel import Session, select
from tablesage_model.model import BootstrapProfileContribution, SessionBootstrapRun


def create_run(
    session: Session,
    *,
    session_id: uuid.UUID,
    source_sha256: str,
    attendee_fingerprint: str,
    settings_fingerprint: str,
    prompt_fingerprint: str,
    embedding_model_id: str,
    targets_json: str,
    attendees_json: str,
    references_json: str,
) -> SessionBootstrapRun:
    run = SessionBootstrapRun(
        session_id=session_id,
        source_sha256=source_sha256,
        attendee_fingerprint=attendee_fingerprint,
        settings_fingerprint=settings_fingerprint,
        prompt_fingerprint=prompt_fingerprint,
        embedding_model_id=embedding_model_id,
        targets_json=targets_json,
        attendees_json=attendees_json,
        references_json=references_json,
    )
    session.add(run)
    session.flush()
    return run


def get_run(session: Session, run_id: uuid.UUID) -> SessionBootstrapRun | None:
    return session.get(SessionBootstrapRun, run_id)


def latest_run(session: Session, session_id: uuid.UUID) -> SessionBootstrapRun | None:
    statement = select(SessionBootstrapRun).where(SessionBootstrapRun.session_id == session_id).order_by(text("created_at DESC"))
    return session.exec(statement).first()


def publish_manifest(session: Session, run: SessionBootstrapRun, manifest_sha256: str, revision: int) -> SessionBootstrapRun:
    if revision < run.manifest_revision:
        raise ValueError("Bootstrap manifest revision cannot move backward.")
    run.manifest_sha256 = manifest_sha256
    run.manifest_revision = revision
    run.updated_at = datetime.now(UTC)
    session.add(run)
    return run


def begin_operation(session: Session, run: SessionBootstrapRun, operation: str) -> SessionBootstrapRun:
    if run.operation is not None:
        raise RuntimeError(f"Bootstrap run is already {run.operation}.")
    run.operation = operation
    run.failure_message = None
    run.updated_at = datetime.now(UTC)
    session.add(run)
    return run


def finish_operation(session: Session, run: SessionBootstrapRun, failure_message: str | None = None) -> SessionBootstrapRun:
    run.operation = None
    run.failure_message = failure_message
    run.updated_at = datetime.now(UTC)
    session.add(run)
    return run


def get_contribution(session: Session, session_id: uuid.UUID, player_id: uuid.UUID) -> BootstrapProfileContribution | None:
    statement = select(BootstrapProfileContribution).where(
        BootstrapProfileContribution.session_id == session_id,
        BootstrapProfileContribution.player_id == player_id,
    )
    return session.exec(statement).first()


def get_or_create_contribution(
    session: Session, *, session_id: uuid.UUID, player_id: uuid.UUID, run_id: uuid.UUID
) -> BootstrapProfileContribution:
    contribution = get_contribution(session, session_id, player_id)
    if contribution is not None:
        return contribution
    contribution = BootstrapProfileContribution(session_id=session_id, player_id=player_id, run_id=run_id)
    session.add(contribution)
    session.flush()
    return contribution


def update_contribution(
    session: Session,
    contribution: BootstrapProfileContribution,
    *,
    state: str,
    clip_count: int,
    reviewed_transcript_sha256: str | None,
    failure_message: str | None = None,
) -> BootstrapProfileContribution:
    contribution.state = state
    contribution.clip_count = clip_count
    contribution.reviewed_transcript_sha256 = reviewed_transcript_sha256
    contribution.failure_message = failure_message
    contribution.updated_at = datetime.now(UTC)
    session.add(contribution)
    return contribution
