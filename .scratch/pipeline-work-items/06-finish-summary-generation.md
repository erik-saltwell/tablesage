# Finish Summary generation

## Problem / desired outcome

Requested as "finish summary generation." Summary generation is implemented and, as of the most
recent session, actually functional end-to-end for the first time in a while — it was silently
unreachable before that (`can_generate_summary` gated on `transcript_roles.md`, a file nothing
had written since role-rendering moved into the Clean Transcript step; it's now gated on, and
reads, `role_transcript.json` instead). Beyond that plumbing fix, the specific remaining gap
wasn't stated.

## Open question (why this is `needs-info`)

What's left? Candidates, none confirmed as this item's actual scope:

- No real (non-mocked) end-to-end test has run Summary generation against a real session since
  the `role_transcript.json` fix — worth a manual smoke pass at minimum.
- The system prompt is a documented placeholder (`generate_summary.md`: "The system prompt is a
  placeholder to be supplied separately") — is writing the real prompt part of "finishing" this?
- Glossary integration: Summary already includes glossary entries as prompt context, but if item
  03 (glossary extraction) lands, does Summary's glossary usage change at all?
- UI-facing gap similar to Ledger's: no way to view a generated Summary's contents from Session
  Detail today.

Needs the user to say which of these (or something else) is meant before this can be scoped into
acceptance criteria.

## Implementation context

- `.documentation/generate_summary.md`.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py`.
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/`.
- `packages/tablesage-application/tests/session_pipeline/test_generate_summary.py`.

## Triage state

`needs-info` — get the specific gap(s) from the user before further scoping.
