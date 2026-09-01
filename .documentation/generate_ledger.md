# Generate Ledger

## Overview

Generate a version-3 `ledger.json` from the best available Session transcript. The Ledger is an incomplete semantic condensation: it may omit material, rephrase one transcript utterance, combine several utterances or speakers, or split one utterance into several entries. It preserves semantic chronology through list order rather than transcript offsets or provenance links.

The format itself is defined in [Ledger Format v3](canonical_ledger_format_v3.md). This document defines the application feature that generates and stores it.

## Key Concepts

- **Source transcript** — `role_transcript.json`, the persisted output of the Generate (`G`) action's Role Transcript step. It already has backchannels removed and player names replaced by Session roles, so Ledger generation reads it as-is.
- **Role transcript** — `role_transcript.json` itself, rendered to Markdown in memory for the generation call. Unlike before, it is a persisted, shown, exportable artifact -- not something Ledger generation builds itself.
- **Ledger** — the persisted, strict Pydantic model stored as `ledger.json`.
- **Preamble** — optional pre-session context containing a Recap, Character Introductions, or both.
- **Ledger utterance** — one of Narration, Action, Speech, Expression, or Correction.
- **Source** — the role or character associated with a regular ledger utterance, not the human player.
- **Generation candidate** — one structurally valid LLM response retained while warning-triggered retries run.

## Schema

All models reject extra fields. Every persisted content string is trimmed and must remain non-empty; generation-only `scratchpad` is an unconstrained string. Serialized type discriminators are lowercase.

```text
Recap
  events: non-empty ordered list[text]
  opening_situation: text | null

CharacterIntroduction
  character: text
  description: text

Preamble
  recap: Recap | null
  character_introductions: ordered list[CharacterIntroduction] | null

Narration
  type: "narration"
  source: text
  fact: text

Action
  type: "action"
  source: text
  entity: text
  action: text

Speech
  type: "speech"
  source: text
  entity: text
  statement: text

Expression
  type: "expression"
  source: text
  entity: text
  sentiment: text

Correction
  type: "correction"
  source: text
  revision: text

Ledger
  version: literal 3
  session_id: UUID
  session_name: text
  preamble: Preamble | null
  utterances: ordered list[Narration | Action | Speech | Expression | Correction]

LedgerGenerationResponse
  scratchpad: text
  preamble: Preamble | null
  utterances: ordered list[Narration | Action | Speech | Expression | Correction]
```

The five utterance models form a Pydantic discriminated union on `type`. The reusable format keeps `source` and `character` as strings. Known-role checks occur at the application boundary because the valid role list varies by Session.

The application, not the LLM, supplies `version`, `session_id`, and `session_name` when constructing the persisted `Ledger`. `scratchpad` exists only in the structured generation response, appears before the generated content, and is discarded after candidate selection.

## Preamble Rules

- A Preamble may contain a Recap, Character Introductions, or both. An empty Preamble is invalid.
- A Recap contains previous campaign events in the order the transcript describes them, followed by an optional opening situation.
- Character Introductions contain only `character` and `description`. Several transcript utterances about one character are consolidated into one introduction, and characters retain their first-introduction order.
- Recaps and Character Introductions are generated only when early transcript material is explicitly framed that way. Similar content is not enough to infer either section.
- When the opening situation also functions as the first in-session Narration, it appears both as `recap.opening_situation` and as the first applicable Narration entry.
- The Transcript model and transcript artifacts are unchanged; preamble recognition happens only during Ledger generation.

## Content and Ordering Rules

- A Ledger is valid when it contains at least one Recap, Character Introduction, or regular utterance. Regular `utterances` may therefore be empty when meaningful Preamble content exists.
- Regular utterances remain in the chronological order in which their content appears in the Session. The LLM's array order is authoritative.
- The Ledger has no time offsets, sequence fields, stable entry IDs, containment, or transcript-source mappings.
- A regular entry may summarize multiple transcript utterances or speakers. The LLM chooses the semantic `source`; the model does not encode input cardinality.
- Detailed classification, condensation, ordering, and Preamble examples live in the prompt. Pydantic field descriptions remain concise and describe only field/type meaning.

## Generation Flow

1. The user requests Ledger generation for a Session with a `role_transcript.json` (produced by
   Generate's (`G`) Role Transcript step, which removes backchannels and assigns Session roles).
2. The application loads the Session, its attendees and roles, and the Session folder.
3. It reads `role_transcript.json` directly and renders it to text -- speakers are already Session
   roles by this point, so no reviewed-vs-machine selection or role lookup happens here.
4. One LLM call receives the complete role transcript and requests `LedgerGenerationResponse` as structured output.
5. Pydantic performs structural validation. The application separately reports one warning for each regular `source` or introduced `character` not found in the Session's known roles.
6. A structurally invalid response or a response with role warnings triggers up to two retries. Parseable candidates are retained across attempts.
7. A warning-free candidate may be accepted immediately. After the final attempt, the application selects the candidate with the fewest warnings; the earliest candidate wins ties. Unknown names in that selected candidate are preserved rather than rejected or fuzzy-matched.
8. If no attempt produced a structurally valid candidate, generation fails without creating or replacing the Ledger.
9. The application discards `scratchpad`, injects the known version and Session metadata, and atomically replaces `ledger.json`.

Generation is whole-session and single-call per attempt. It is not batched or followed by a second semantic merge pass.

## Artifact and UI Behavior

- The artifact is called **Ledger** throughout the application and UI and is stored as `ledger.json`.
- Ledger replaces the unused Processed Session artifact concept and registry entry.
- Ledger is derived from the Transcript, shown in Session Detail, and available through artifact export.
- Session Detail's unified **Generate** (`G`) action produces the Ledger once `role_transcript.json` exists -- it is the second of Generate's three dependency-ordered steps (Role Transcript, then Ledger, then Summary).
- A successful Transcript rebuild, completed Manual Review, audio re-import, or attendance/role change invalidates the Ledger through the artifact-category rules.
- A failed generation preserves any existing Ledger. Successful replacement invalidates artifacts derived from the prior Ledger.
- Summary generation from Ledger is a separate feature; this work does not reinterpret the Summary schema or prompt.

## Implementation Boundaries

- Ledger domain and generation-response models live in `tablesage-application`, alongside the use case that owns structured generation and Session-context validation.
- The existing role-rendering function remains outside Transcription and is called by Ledger generation.
- Generation uses the shared application LLM helper and the existing configured LLM model. The two-retry policy is a feature rule, not a new `settings.yaml` knob.
- Writes use temp-file-then-rename replacement. No partial or raw LLM response is persisted.

## Acceptance Coverage

- Pydantic tests cover every discriminator, required/type-specific fields, forbidden extras, trimmed non-empty text, Preamble invariants, and the overall meaningful-content invariant.
- Prompt/generation tests cover Reviewed Transcript preference, role rendering, Session metadata injection, whole-session structured output, and scratchpad removal.
- Retry tests cover malformed responses, warning-triggered retries, fewest-warning selection, earliest tie-breaking, acceptance with remaining warnings, and all-invalid failure.
- Artifact tests cover `ledger.json`, atomic replacement, preservation on failure, invalidation, Session Detail visibility, action gating, and export.
- Prompt fixtures cover no Preamble, Recap only, Character Introductions only, both sections, consolidated introductions, and duplicated opening-situation Narration.

## Out of Scope

- Changing the Transcript schema or annotating transcript utterances as Preamble material.
- Persisting the in-memory role transcript.
- Programmatic chronology reconstruction or source-provenance tracking.
- Fuzzy correction of unknown roles or character names.
- Migrating Summary generation to consume Ledger.
