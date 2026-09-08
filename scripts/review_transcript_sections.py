"""Independently review and adjudicate a session's transcript sections.

Run from the repository root:

    uv run python scripts/review_transcript_sections.py Brandonsford "Session One" /path/to/role_transcript_prefix.json
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError
from rich.console import Console
from tablesage_application import Application
from tablesage_application.llm import PromptName, read_system_prompt
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.role_transcript import RoleTranscript
from tablesage_application.session_pipeline.transcript_sections import (
    Attendee,
    TranscriptSections,
    TranscriptSectionsGenerationResponse,
    TranscriptSectionsValidationError,
    validate_generation_response,
)
from tablesage_tools.llm import call_llm

REPO_ROOT = Path(__file__).resolve().parents[1]
FABLE_MODEL = "anthropic/claude-fable-5-1"
HIGH_THINKING = {"reasoning_effort": "high"}
ASTRA_MODEL = "openai/gpt-6-astra"
ASTRA_HIGH_THINKING = {"reasoning_effort": "high", "allowed_openai_params": ["reasoning_effort"]}
NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class _Named(Protocol):
    name: str


class EvidenceCitation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    utterance_index: int = Field(ge=0)
    excerpt: NonEmptyText


class ReviewArgument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim: NonEmptyText
    citations: list[EvidenceCitation] = Field(min_length=1)


class ValueReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: NonEmptyText
    current_value: int | None
    arguments_for: list[ReviewArgument] = Field(max_length=3)
    arguments_against: list[ReviewArgument] = Field(max_length=3)
    verdict: Literal["retain", "revise"]


class TranscriptSectionsReviewResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scratchpad: NonEmptyText
    value_reviews: list[ValueReview]
    recommended_sections: TranscriptSections


def _find_named[NamedT: _Named](items: Sequence[NamedT], name: str, *, kind: str) -> NamedT:
    matches = [item for item in items if item.name == name]
    if len(matches) == 1:
        return matches[0]
    available = ", ".join(sorted(repr(item.name) for item in items)) or "(none)"
    if not matches:
        raise ValueError(f"{kind} {name!r} was not found. Available {kind.lower()}s: {available}")
    raise ValueError(f"More than one {kind.lower()} is named {name!r}; use a unique name.")


def _expected_review_paths(sections: TranscriptSections) -> set[str]:
    paths = {"recap_range", "introduction_range", "starting_context_range", "session_start_index"}
    for name, section_range in (
        ("recap_range", sections.recap_range),
        ("introduction_range", sections.introduction_range),
        ("starting_context_range", sections.starting_context_range),
    ):
        if section_range is not None:
            paths.update({f"{name}.start_index", f"{name}.end_index"})
    return paths


def _validate_review(
    response: TranscriptSectionsReviewResponse,
    current_sections: TranscriptSections,
    transcript: RoleTranscript,
    *,
    require_complete_coverage: bool,
) -> TranscriptSectionsReviewResponse:
    recommended = response.recommended_sections
    if recommended.version != current_sections.version or recommended.role_transcript_sha256 != current_sections.role_transcript_sha256:
        raise ValueError("The recommendation must preserve the current sections version and transcript hash.")
    review_paths = [review.path for review in response.value_reviews]
    if require_complete_coverage and (
        len(review_paths) != len(set(review_paths)) or set(review_paths) != _expected_review_paths(current_sections)
    ):
        raise ValueError("The review must cover every current range-presence decision, endpoint, and session start exactly once.")
    try:
        validate_generation_response(
            TranscriptSectionsGenerationResponse(
                scratchpad="Validation only.",
                recap_range=recommended.recap_range,
                introduction_range=recommended.introduction_range,
                starting_context_range=recommended.starting_context_range,
                session_start_index=recommended.session_start_index,
            ),
            len(transcript.utterances),
        )
    except TranscriptSectionsValidationError as exc:
        raise ValueError("The recommended sections do not fit the supplied role transcript.") from exc
    return response


def _review_system_prompt(*, juror: bool) -> str:
    role = (
        "You are the final juror. Weigh both independent reviews, resolve their conflicts, and issue one coherent ruling."
        if juror
        else "You are an independent transcript-sectioning reviewer. Do not assume any other reviewer exists."
    )
    return f"""{read_system_prompt(PromptName.SECTION_TRANSCRIPT)}

# Review Task

{role}

Review the existing transcript_sections.json against the supplied indexed role transcript. The production sectioning
definitions and boundary rules above are authoritative. Audit each nullable range's current presence or absence, every
current non-null endpoint, and the current session_start_index. For each audited value provide up to three arguments for
and up to three arguments against it. Every argument must cite one or more utterance indices and short verbatim excerpts.
Do not invent unsupported opposing arguments.

Return only the structured review response. Its scratchpad is a readable synthesis. Its recommended_sections must be a
complete replacement object, preserve version and role_transcript_sha256 exactly, and contain only a coherent final ruling.
"""


def _review_input(
    *,
    attendees: tuple[Attendee, ...],
    transcript: RoleTranscript,
    current_sections: TranscriptSections,
    sol_review: TranscriptSectionsReviewResponse | None = None,
    fable_review: TranscriptSectionsReviewResponse | None = None,
) -> str:
    base = {
        "session_attendees": [attendee.model_dump() for attendee in attendees],
        "role_transcript": transcript.model_dump(),
        "current_transcript_sections": current_sections.model_dump(),
    }
    if sol_review is not None and fable_review is not None:
        base["independent_reviews"] = {"sol": sol_review.model_dump(), "fable": fable_review.model_dump()}
    return json.dumps(base, indent=2)


async def _call_reviewer(
    *,
    model: str,
    thinking: dict[str, str],
    system_prompt: str,
    user_prompt: str,
    current_sections: TranscriptSections,
    transcript: RoleTranscript,
    require_complete_coverage: bool,
) -> tuple[str, TranscriptSectionsReviewResponse]:
    raw = await call_llm(
        system_prompt,
        user_prompt,
        model,
        response_format=TranscriptSectionsReviewResponse,
        prompt_name="review_transcript_sections",
        model_options=thinking,
    )
    try:
        response = TranscriptSectionsReviewResponse.model_validate_json(raw)
    except ValidationError as exc:
        raise ValueError(f"{model} returned an invalid review response.") from exc
    return raw, _validate_review(
        response,
        current_sections,
        transcript,
        require_complete_coverage=require_complete_coverage,
    )


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("campaign_name")
    parser.add_argument("session_name")
    parser.add_argument("role_transcript_path", type=Path)
    return parser.parse_args()


async def _run(arguments: argparse.Namespace) -> Path:
    console = Console()
    application = Application(REPO_ROOT)
    campaign = _find_named(application.list_campaigns(), arguments.campaign_name, kind="Campaign")
    game_session = _find_named(application.list_sessions(campaign.id), arguments.session_name, kind="Session")
    transcript_path: Path = arguments.role_transcript_path
    if not transcript_path.is_file():
        raise ValueError(f"Role transcript not found at {transcript_path}.")
    transcript = RoleTranscript.load(transcript_path)
    session_folder = application.session_folder(game_session.id)
    current_sections = TranscriptSections.load(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT_SECTIONS].filename)
    attendees = tuple(
        Attendee(player_name=attendee.player_name, roles=attendee.roles) for attendee in application.list_attendance(game_session.id)
    )
    user_prompt = _review_input(attendees=attendees, transcript=transcript, current_sections=current_sections)
    sol_task = _call_reviewer(
        model=ASTRA_MODEL,
        thinking=ASTRA_HIGH_THINKING,
        system_prompt=_review_system_prompt(juror=False),
        user_prompt=user_prompt,
        current_sections=current_sections,
        transcript=transcript,
        require_complete_coverage=False,
    )
    fable_task = _call_reviewer(
        model=FABLE_MODEL,
        thinking=HIGH_THINKING,
        system_prompt=_review_system_prompt(juror=False),
        user_prompt=user_prompt,
        current_sections=current_sections,
        transcript=transcript,
        require_complete_coverage=False,
    )
    (sol_raw, sol_review), (fable_raw, fable_review) = await asyncio.gather(sol_task, fable_task)
    console.print("[bold]Sol review[/bold]")
    console.print_json(sol_raw)
    console.print("[bold]Fable review[/bold]")
    console.print_json(fable_raw)
    jury_raw, jury_review = await _call_reviewer(
        model=ASTRA_MODEL,
        thinking=ASTRA_HIGH_THINKING,
        system_prompt=_review_system_prompt(juror=True),
        user_prompt=_review_input(
            attendees=attendees,
            transcript=transcript,
            current_sections=current_sections,
            sol_review=sol_review,
            fable_review=fable_review,
        ),
        current_sections=current_sections,
        transcript=transcript,
        # Value reviews are explanatory scratch work.  A juror may consolidate
        # or omit a no-change item without affecting its validated recommendation.
        require_complete_coverage=False,
    )
    console.print("[bold]Final Fable juror review[/bold]")
    console.print_json(jury_raw)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    target = session_folder / f"_generated_transcript_sections_review_{timestamp}.json"
    temporary = target.with_name(f".{target.name}.tmp")
    temporary.write_text(jury_review.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)
    return target


def main() -> None:
    try:
        target = asyncio.run(_run(_arguments()))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Saved final review to {target.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
