from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel
from tablesage_tools.model import Transcript

REVIEW_DRAFT_FILENAME = "transcript_review_draft.json"
SPELLING_REVIEW_FILENAME = "spelling_review.json"


class SpellingReview(BaseModel, frozen=True):
    """A resumable, noncanonical spelling checkpoint tied to a canonical source file."""

    source_artifact: str
    source_modified_ns: int
    transcript: Transcript


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


def spelling_review_path(session_folder: Path) -> Path:
    return session_folder / SPELLING_REVIEW_FILENAME


def save_spelling_review(session_folder: Path, review: SpellingReview) -> None:
    """Atomically persist spelling work without creating a reviewed transcript artifact."""
    target = spelling_review_path(session_folder)
    temporary = target.with_name(f".{target.stem}.tmp{target.suffix}")
    try:
        temporary.write_text(review.model_dump_json(indent=2), encoding="utf-8")
        temporary.replace(target)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def load_spelling_review(session_folder: Path) -> SpellingReview | None:
    path = spelling_review_path(session_folder)
    return SpellingReview.model_validate_json(path.read_text(encoding="utf-8")) if path.is_file() else None


def discard_spelling_review(session_folder: Path) -> None:
    spelling_review_path(session_folder).unlink(missing_ok=True)
