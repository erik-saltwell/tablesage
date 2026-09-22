from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import CheckConstraint
from sqlmodel import Field, SQLModel


class SessionBootstrapRun(SQLModel, table=True):
    """Immutable participant/reference snapshot for one new-speaker processing run.

    Large review payloads stay in the session folder. This record owns their fingerprints,
    current manifest revision, and the workflow state needed to resume safely.
    """

    __tablename__ = "session_bootstrap_run"
    __table_args__ = (
        CheckConstraint("schema_version >= 1", name="ck_session_bootstrap_run_schema_version"),
        CheckConstraint("manifest_revision >= 0", name="ck_session_bootstrap_run_manifest_revision"),
        CheckConstraint(
            "operation is null or operation in ('preparing', 'identifying', 'finalizing')",
            name="ck_session_bootstrap_run_operation_valid",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    session_id: uuid.UUID = Field(foreign_key="session.id", ondelete="CASCADE", index=True)
    schema_version: int = Field(default=1)
    source_sha256: str
    attendee_fingerprint: str
    settings_fingerprint: str
    prompt_fingerprint: str
    embedding_model_id: str
    targets_json: str
    attendees_json: str
    references_json: str
    manifest_sha256: str | None = Field(default=None)
    manifest_revision: int = Field(default=0)
    operation: str | None = Field(default=None)
    failure_message: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
