# Finish Ledger generation

## Problem / desired outcome

Requested as "finish ledger extraction." Ledger generation is implemented and working
end-to-end (`generate_ledger.md`, `canonical_ledger_format_v3.md`, wired to Generate's Ledger
step) — this item was raised alongside "finish summary generation" as a pair, implying there's
known remaining work, but the specific gap wasn't stated.

## Open question (why this is `needs-info`)

What's left? Candidates that came up in adjacent conversation but aren't confirmed as this item's
scope:

- Item 02 (Question ledger event type) landing changes what "complete" classification coverage
  means for the discriminated union — is this item waiting on that, or separate?
- Quality/accuracy of extraction on real sessions (e.g. does it currently under/over-classify;
  is there a benchmark or eval harness for Ledger quality the way `benchmarks/speaker_id` exists
  for speaker identification)?
- Multi-session continuity (does a new session's Ledger generation have any awareness of prior
  sessions' Ledgers, e.g. for Preamble/Recap accuracy)?
- Something UI-facing (viewing/browsing a generated Ledger's contents from Session Detail —
  `.documentation/session_detail_screen.md`'s Out of Scope section explicitly defers "Viewing/
  reading generated file contents from this screen").

Needs the user to say which of these (or something else) is meant before this can be scoped into
acceptance criteria.

## Implementation context

- `.documentation/generate_ledger.md`, `.documentation/canonical_ledger_format_v3.md`.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py`.
- `packages/tablesage-application/tests/session_pipeline/test_generate_ledger.py`.

## Triage state

`needs-info` — get the specific gap(s) from the user before further scoping.
