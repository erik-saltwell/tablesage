# New "Question" Ledger event type

## Problem / desired outcome

The Ledger's discriminated regular-utterance union
(`packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py`)
currently has five types: Narration, Action, Speech, Expression, Correction. There's no type for
a question posed in-session (a GM asking a player something, a player asking the GM to clarify
game state, etc.) — today it would presumably get forced into Speech or dropped as
not-content-bearing. Add a sixth discriminated type, Question, so the Ledger can represent this
distinctly.

## Acceptance criteria

- A new `Question` model in `generate_ledger.py`, following the existing `_LedgerUtterance` base
  (a `source: NonEmptyText` field) plus whatever fields best capture a question (e.g. `entity`
  asking, `question` text — mirror `Speech`'s `entity`/`statement` shape unless there's a reason
  to diverge).
- Added to the `LedgerUtterance` discriminated union (`Narration | Action | Speech | Expression |
  Correction | Question`), keeping `type: Literal["question"]` lowercase per the existing
  discriminator convention.
- `canonical_ledger_format_v3.md` updated with the new type's schema and any classification
  guidance (does a rhetorical question count? a question immediately answered in the same beat?).
- The generation prompt (`_prompts/generate_ledger/`) updated to teach the model when to emit
  `Question` vs. `Speech`.
- Existing three-attempt retry / warning-count logic in `generate_ledger()` needs no change —
  `Question.source` participates in the same known-role warning check as the other types.
- Tests: schema round-trip (`Question` serializes/deserializes, rejects extra fields, participates
  in the discriminated union), and at least one generation-flow test exercising a stubbed response
  containing a `Question` entry.

## Implementation context

- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py`
  — schema definitions and `_require_meaningful_content`/`_role_warning_count`.
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/` —
  system prompt and template.
- `.documentation/canonical_ledger_format_v3.md` — the format's canonical spec; this is a v3
  addition, not a new version, unless the team decides otherwise.
- `packages/tablesage-application/tests/session_pipeline/test_generate_ledger.py`.

## Triage state

`complete` — design: [02-design.md](02-design.md), implemented in commit `6150f88`.
