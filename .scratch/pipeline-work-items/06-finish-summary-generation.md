# Finish Summary generation

## Problem / desired outcome

Requested as "finish summary generation." The `needs-info` gap below has been resolved: the user
scoped it as "switch Summary's source from the role transcript to the Ledger" (2026-09-02),
specifically that the prompt should carry the attendees map, the glossary, and the Ledger as JSON.

## Resolution

Implemented 2026-09-02:

- `generate_summary.py`: `generate_summary(ledger, attendees, glossary, model)` replaces the old
  `(transcript, glossary, model)` signature. `ledger` is the raw `ledger.json` text (the module
  stays schema-agnostic, per `generate_summary.md`'s "generation is separated from that storage
  choice" note); `attendees` is a new `Attendee(player_name, roles)` DTO, independently defined
  here the same way `GlossaryPromptEntry` already was (not imported from `generate_ledger`).
- `summarize_session/template.j2` gained `<session_attendees>` and `<session_ledger>` sections,
  mirroring `generate_ledger`'s template shape; dropped the old bare `Transcript:` section.
- `application.py`'s `generate_summary` now reads `ledger.json`'s text and builds the attendee
  list the same way `generate_ledger` does (sorted by casefolded player name), instead of
  rendering the role transcript.
- `processing.can_generate_summary` now gates on `ArtifactName.LEDGER` instead of
  `ArtifactName.ROLE_TRANSCRIPT` — Summary reads the Ledger directly now, so the dependency chain
  is fully linear: Role Transcript → Ledger → Summary (previously Ledger and Summary were
  siblings, both depending on Role Transcript directly). No change was needed to invalidation:
  `paths.py` already categorized Summary as `FROM_LOG`, documented as "derived from the Ledger,"
  and Ledger regeneration already invalidated `FROM_LOG` — that was already anticipating this.
- Updated `.documentation/generate_summary.md` and the relevant `session_detail_screen.md`
  passages (dependency chain, Generate step description) to match.
- Of the four candidate gaps this item originally listed, only this one was in scope. Still open,
  not addressed here: no real end-to-end smoke test against a live LLM; the system prompt remains
  a placeholder (the user is writing it by hand next); glossary usage inside the prompt is
  unchanged; there is still no Session Detail UI to view a generated Summary's contents.

## Implementation context

- `.documentation/generate_summary.md`, `.documentation/session_detail_screen.md`.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py`.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/processing.py`.
- `packages/tablesage-application/src/tablesage_application/application.py` (`generate_summary`).
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/`.
- `packages/tablesage-application/tests/session_pipeline/test_generate_summary.py`,
  `test_processing.py`, `packages/tablesage-application/tests/llm/test_llm_helper.py`.

## Triage state

`ready-for-human` — code and tests are done (507 tests passing, ruff/ty clean) but uncommitted;
the user is writing `summarize_session/system.md`'s real content next, and this item shouldn't be
closed out until that lands and the change is committed.
