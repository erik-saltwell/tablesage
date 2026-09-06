# Implement Transcript Sectioning and Session-Scoped Outputs

## Problem / desired outcome

Implement the generation pipeline defined in
[Transcript Sectioning and Session-Scoped Outputs](../../.documentation/transcript_sectioning_and_session_scoped_outputs.md).
Follow the ordered code/prompt handoff in the
[implementation plan](implementation-plan.md).

The generation pipeline currently asks multiple prompts to independently interpret the complete
Role Transcript and persists prior-session recap and Player Character introductions inside Ledger
v3. Replace that behavior with one shared transcript-sectioning phase, a current-session-only
Ledger v4, and independently generated sidecar outputs.

Recap Summary's initial placeholder prompt and artifact behavior are tracked in
[Implement Recap Summary](01-implement-recap-summary.md).

## Scope

### Compact Role Transcript

- Replace the generic word-level `role_transcript.json` representation with a dedicated compact
  schema.
- Store each utterance as zero-based `index`, `speaker`, and final displayed `text`.
- Update its renderers, consumers, prompt-development scripts, tests, and documentation.

### Transcript sectioning

- Add a dedicated high-effort structured-output prompt that receives the indexed Role Transcript
  plus Session attendees and their role mappings.
- Return nullable, inclusive `recap_range`, `introduction_range`, and
  `starting_context_range` values plus a required `session_start_index`.
- Permit ranges to overlap and permit mixed boundary utterances to feed multiple downstream
  inputs.
- Bias ambiguous boundaries toward the Session; do not classify or filter content after active
  play begins.
- Persist a versioned `transcript_sections.json` containing the validated routing fields and a
  fingerprint of its source Role Transcript. Do not duplicate transcript text in it.
- Keep Transcript Sections internal rather than presenting it as a user-facing artifact.

### Ledger v4

- Replace Ledger v3 with v4 without a compatibility reader or migration.
- Remove Preamble, Recap, and Character Introduction models and fields from the Ledger.
- Add a required non-empty top-level `starting_situation` string.
- Pass the Ledger prompt two compact `{speaker, text}` arrays:
  - `starting_context`, taken from `starting_context_range` and usable only to establish
    `starting_situation`;
  - `session_utterances`, containing the complete suffix from `session_start_index` onward.
- Keep all existing in-session Ledger classification and condensation behavior. The sectioning
  phase does not replace Ledger relevance filtering.
- Update deterministic Ledger Markdown rendering for the new envelope.

### Player Introductions

- Add a separate structured-output prompt that receives `introduction_range`'s compact
  `{speaker, text}` records plus full Session context.
- Generate only explicit opening-preamble introductions for non-GM attendee roles. Do not infer a
  profile from in-session details.
- Validate that every character exactly matches an eligible Session role and that characters are
  unique. Allow an empty list.
- Persist `player_introductions.json` with `version: 1`, application-supplied `session_id`, and
  ordered `{character, description}` entries. Keep the JSON artifact internal.
- Render introductions deterministically as `## Player Characters` with one
  `- **Character** — description` bullet per entry. Emit no section for an empty list.

### Summary composition

- Keep full Summary and Recap Summary as separate high-effort LLM calls based on Ledger v4 and
  full Session context.
- Require the full Summary response to emit exactly one `<!-- RECAP -->` marker followed by
  exactly one `<!-- PLAYER_INTRODUCTIONS -->` marker near the top of the document, before its
  detailed sections.
- Replace the markers deterministically with the previous Session's complete Recap section and
  the current Session's rendered Player Characters section. Remove the Recap marker for the first
  Session; fail when a previous Session exists without a Recap artifact.
- Do not replace `summary.md` unless all required generation and marker validation succeeds.

### Generate Outputs lifecycle

- Always rerun the phases in this order: Role Transcript, Transcript Sections, Ledger, Player
  Introductions, Recap Summary, then full Summary and composition.
- Use the existing `llm_model_high` setting for every LLM phase while keeping a separate prompt
  identity for each generator.
- Fail fast. Atomically preserve each earlier artifact that completed successfully, and do not run
  later phases after a failure.
- Retry structurally invalid Transcript Sections, Ledger, Player Introductions, and Summary-marker
  responses up to three times. Recap Summary receives one application-level attempt.
- Update invalidation so every derived artifact is removed when its source becomes stale.

## Acceptance criteria

- `role_transcript.json` uses the compact indexed schema and every existing consumer works with
  it.
- A successful sectioning call writes a source-bound `transcript_sections.json` satisfying all
  bounds, nullability, and overlap rules in the design.
- Invalid or out-of-bounds section responses are retried and cannot reach downstream generators.
- Ledger v4 contains `starting_situation` and current-session utterances but no preamble content.
- Ledger generation fails rather than inventing a starting situation when
  `starting_context_range` is `null`.
- Player Introductions are extracted only from the selected opening range, strictly validated,
  and persisted independently from the Ledger.
- Recap Summary is visible and exportable; Transcript Sections and Player Introductions remain
  internal artifacts.
- The composed Summary contains the previous Session's Recap when one exists and the current
  Session's Player Characters when present, at the validated marker positions.
- Generate Outputs regenerates all phases in dependency order and retains fail-fast,
  per-artifact atomic replacement behavior.
- Tests cover schema validation, absent and interleaved preamble sections, ambiguous and mixed
  boundaries, a setup-only Session, no usable starting context, strict Player Character
  membership, prompt inputs, retries, invalidation, failure preservation, composition, artifact
  visibility/export, and TUI progress ordering.
- The Ledger, Summary, Session Detail, canonical format, artifact/export, and prompt-development
  documentation reflects the new pipeline and Ledger v4.

## Triage state

`ready-for-agent`
