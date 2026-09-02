# Generate Session Summary

## Overview

Generate a Markdown summary of a session from its Ledger, the session's attendees, and the campaign glossary. Generation is separated from the Ledger's storage choice so a future source can replace it.

## Key Concepts

- **Ledger** — `ledger.json`, the session's canonical structured record (see `generate_ledger.md`, `canonical_ledger_format_v3.md`). Summary generation reads its raw JSON text and treats it as an opaque string; it does not depend on the Ledger's Pydantic schema.
- **Attendees** — the session's human roster (player name and session roles), sourced the same way Ledger generation sources it, and included as its own prompt section alongside the Ledger.
- **Glossary** — the campaign's terms and optional descriptions, always included as a prompt section.
- **Summary** — unstructured Markdown returned by the LLM and stored as `summary.md`.
- **Log-derived artifact** — Summary's `FROM_LOG` category: it is derived from the Ledger, and generating a new Ledger invalidates any existing Summary.

## Generate Summary Flow

1. Generation is available when the Ledger exists.
2. The application reads `ledger.json`'s raw text, the session's attendees, and the campaign glossary.
3. Glossary entries are ordered alphabetically; attendees are ordered alphabetically by player name. All three are combined as prompt data.
4. The application renders the summary prompt and makes one LLM call through its standard prompting boundary.
5. An empty or whitespace-only response fails generation.
6. A successful response atomically replaces `summary.md`; a failure preserves the previous summary.

## Behaviors & Rules

- Render glossary entries as `- Term: description`, or `- Term` when no description exists.
- Include the glossary section even when the campaign has no glossary entries.
- Render attendees as `- player_name: role, role`, or `- player_name` when they have no session roles.
- Save non-empty Markdown without interpreting its structure, except to normalize surrounding whitespace and ensure one final newline.
- The summary call returns plain Markdown and does not use structured output.
- The system prompt is a placeholder to be supplied separately.
- Generating a new Ledger invalidates any existing Summary (Summary's `FROM_LOG` category is defined as "derived from the Ledger"); regenerating the role transcript invalidates both, since Ledger is itself derived from it.
- Glossary changes do not invalidate existing summaries. Regeneration is an explicit user action.

## Current Integration Constraints

- The application use case owns reading `ledger.json` and the session's attendees; the summary prompt layer receives a plain Ledger JSON string, an attendee list, and glossary data without knowing their storage location.
- Summary generation uses `tablesage_application.llm.call_llm_with_prompt` with no response model.
- Session Detail no longer exposes Summary as its own binding -- it's produced by the unified Generate (`G`) action once Role Transcript and Ledger both exist, in that order (Role Transcript → Ledger → Summary is now a strict chain, since Summary reads the Ledger directly). See `session_detail_screen.md`.
