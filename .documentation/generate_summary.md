# Generate Session Summary

## Overview

Generate and compose a Markdown summary from the current Session's Ledger and Player Introductions
plus the previous Session's Recap. The LLM sees only the current Ledger, attendees, and campaign
context; sidecars are inserted afterward in code.

## Key Concepts

- **Ledger** — `ledger.json`, the session's canonical structured record (see `generate_ledger.md`, `canonical_ledger_format_v4.md`). Summary generation reads its raw JSON text and treats it as an opaque string; it does not depend on the Ledger's Pydantic schema.
- **Attendees** — the session's human roster (player name and session roles), sourced the same way Ledger generation sources it, and included as its own prompt section alongside the Ledger.
- **Glossary** — the campaign's terms and optional descriptions, always included as a prompt section.
- **Recap Summary** — `recap_summary.md` generated from one Session's Ledger and inserted into the
  following Session's Summary.
- **Player Introductions** — the current Session's structured `player_introductions.json`, rendered
  deterministically when composed.
- **Summary template** — Markdown returned by the LLM with one `<!-- RECAP -->` marker followed by
  one `<!-- PLAYER_INTRODUCTIONS -->` marker.
- **Summary** — the deterministically composed Markdown stored as `summary.md`.
- **Log-derived artifact** — Summary's `FROM_LOG` category: it is derived from the Ledger, and generating a new Ledger invalidates any existing Summary.

## Generate Summary Flow

1. Order Sessions within the campaign by date and then sequence number. Undated Sessions follow
   dated Sessions and use sequence number among themselves.
2. Require the current Session's Ledger and Player Introductions. When a previous Session exists,
   also require its Recap Summary; the first Session does not require one.
3. Read the current `ledger.json`, attendees, and campaign glossary as LLM prompt inputs.
4. Ask the LLM for a Summary template. Reject empty, missing, duplicate, or reversed markers and
   retry up to three times. Provider errors fail immediately.
5. Only after marker validation, load the previous Session's Recap when one exists and the current
   Session's Player Introductions. Validate the Introduction sidecar's Session ID and character
   eligibility.
6. Replace the Recap marker with the previous Recap, or remove it for the first Session. Replace
   the Introductions marker with the current rendered section, or remove it when empty.
7. Normalize blank lines and the final newline, then atomically replace `summary.md`. Any failure
   preserves the previous Summary.

## Behaviors & Rules

- Render glossary entries as `- Term: description`, or `- Term` when no description exists.
- Include the glossary section even when the campaign has no glossary entries.
- Render attendees as `- player_name: role, role`, or `- player_name` when they have no session roles.
- Require both exact insertion markers once and in Recap-then-Player-Introductions order.
- Never send either sidecar to the full Summary LLM.
- A missing previous Recap is an error; absence of a previous Session is valid and emits no Recap
  section.
- Always use Player Introductions from the current Session, never the previous Session.
- Save composed Markdown without otherwise rewriting LLM content, except to normalize blank lines
  and ensure one final newline.
- The summary call returns plain Markdown and does not use structured output.
- Generating a new Ledger invalidates any existing Summary (Summary's `FROM_LOG` category is defined as "derived from the Ledger"); regenerating the role transcript invalidates both, since Ledger is itself derived from it.
- Regenerating a Session's Recap does not automatically invalidate the following Session's
  existing Summary. The user owns that regeneration for now.
- Glossary changes do not invalidate existing summaries. Regeneration is an explicit user action.

## Current Integration Constraints

- The application use case owns Session ordering and reading all artifacts; the Summary prompt
  layer receives a plain current-Session Ledger JSON string, attendee list, and glossary data
  without knowing their storage locations.
- Summary generation uses `tablesage_application.llm.call_llm_with_prompt` with no response model.
- Session Detail does not expose Summary as its own binding; it is produced by the unified
  Generate (`G`) workflow. See `session_detail_screen.md`.
