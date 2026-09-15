# Transcript Sections Review Utility

## Overview

The Transcript Sections Review Utility independently audits an existing `transcript_sections.json` against a supplied role-transcript prefix, then produces a final adjudicated recommendation. It is designed for human review of section boundaries before their values become golden evaluation content.

## Key Concepts

- **Review transcript:** A hand-prepared, indexed prefix of a session's role transcript. It is supplied as a path and is never cut or rewritten by the utility.
- **Existing sections:** The session's current `transcript_sections.json`, used as the values under review.
- **Independent review:** A structured assessment produced without access to another reviewer's conclusions.
- **Juror:** The final reviewer that considers both independent reviews, the existing sections, and the review transcript to produce one coherent recommendation.
- **Recommended sections:** A complete proposed replacement for the routing values while preserving the artifact's `version` and `role_transcript_sha256`.

## Inputs

The utility accepts:

1. A campaign name.
2. A session name, resolved by exact match within that campaign.
3. A path to the hand-prepared role transcript.

It obtains all other needed session data from the resolved session, including attendee roles and the existing sections artifact.

The review transcript must preserve original utterance indices and contain the opening material required to assess all current ranges and the active-play boundary.

## Review Flow

1. Resolve the exact campaign and session; fail if the session name is missing or ambiguous.
2. Load the existing sections artifact and session attendees.
3. Run two independent reviews concurrently:
   - Astra (`openai/gpt-6-astra`) with high reasoning.
   - Fable 5.1 (`anthropic/claude-fable-5-1`) with high reasoning.
4. Print both independent review responses.
5. Send both responses, the review transcript, attendee data, and existing sections to Astra with high reasoning.
6. Print the final jury response.
7. Save only the final response in the session folder using a `_generated_` filename prefix.

## Review Response

Each reviewer returns a parseable response containing:

- A readable `scratchpad` synthesis first.
- Structured value reviews, requested for each routing decision:
  - Each nullable range's presence or absence.
  - Each non-null range's start and end index.
  - `session_start_index`.
- Up to three transcript-grounded arguments supporting the current value.
- Up to three transcript-grounded arguments opposing the current value.
- Each argument cites one or more utterance indices and short verbatim excerpts.
- A complete `recommended_sections` object.

The final juror uses the independent arguments as evidence, then issues one internally coherent recommended sections object. Current calls pass `require_complete_coverage=False`, so the validator permits omitted/consolidated value-review entries; the recommendation must still be complete and within transcript bounds. Prompt instructions to cite grounded excerpts are not an automated semantic truth check.

## Behaviors & Rules

- The production sectioning definitions and boundary rules are the authoritative review rubric.
- Arguments must remain grounded in the supplied role transcript; the reviewer does not rely on inferred campaign knowledge.
- A reviewer may provide fewer than three arguments on either side when no additional evidence-backed argument exists.
- The juror may resolve conflicts among individual reviews to ensure the final ranges and active-play boundary work together.
- `version` and `role_transcript_sha256` are copied unchanged into the recommendation.
- The utility never overwrites the existing `transcript_sections.json`.

## Implementation and invocation

Run `uv run python scripts/review_transcript_sections.py "Campaign Name" "Session Name" /path/to/role_transcript_prefix.json` from the repository root. This invokes providers and writes a generated recommendation, not the canonical sections artifact. See [the script](../../scripts/review_transcript_sections.py).

The script still prints historical “Sol review” and “Final Fable juror review” labels and uses corresponding internal result keys. Actual model selection comes from ASTRA_MODEL/FABLE_MODEL and the calls above; those labels do not identify the provider used. The generated filename includes a UTC timestamp. No model or label code was changed by the documentation cleanup.
