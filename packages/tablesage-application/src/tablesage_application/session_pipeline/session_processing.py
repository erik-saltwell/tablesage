from __future__ import annotations

from pathlib import Path

from tablesage_tools.model import Transcript

REVIEW_DRAFT_FILENAME = "transcript_review_draft.json"


def review_draft_path(session_folder: Path) -> Path:
    """Return the noncanonical, resumable transcript-review working-copy path."""
    return session_folder / REVIEW_DRAFT_FILENAME


def save_review_draft(session_folder: Path, transcript: Transcript) -> None:
    """Atomically save review work without creating a reviewed-transcript artifact."""
    target = review_draft_path(session_folder)
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        transcript.save(temporary)
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def load_review_draft(session_folder: Path) -> Transcript | None:
    """Load the persisted working copy when present; callers validate its source fingerprint."""
    path = review_draft_path(session_folder)
    return Transcript.load(path) if path.is_file() else None


def discard_review_draft(session_folder: Path) -> None:
    """Remove the noncanonical working copy; completed review is never affected."""
    review_draft_path(session_folder).unlink(missing_ok=True)
