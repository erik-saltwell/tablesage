# Ledger Artifact Specification

The Ledger is TableSage's canonical, structured record of one session's current play. It condenses campaign-relevant fiction into an ordered, machine-readable account; it is not a transcript, a campaign encyclopedia, or a summary of the opening recap.

## Purpose and position in the pipeline

Transcript Sections routes the role-attributed transcript into a starting-context view and a current-session view. Ledger generation consumes those two views, attendee roles, and glossary spellings. It runs after the Role Transcript and Transcript Sections artifacts exist.

One structured LLM call generates the shared `starting_situation`, `ledger: {utterances}`, and `scene_breakdown: {ending_situation, scenes}` directly from the routed transcript. The response has exactly those three top-level fields; no scratchpad is returned. See [Scene Breakdown](scene-breakdown.md) for the paired schema and reference rules.

The persisted artifact is `ledger.json`; its deterministic human-readable companion is `ledger.md`. Both live in the session folder. Ledger and Scene Breakdown are sibling outputs of one generation step. Replacing Ledger makes its actual consumers stale through modification-time comparison; it does not delete them or make its Scene Breakdown sibling stale.

The packaged Generate Ledger `system.md` is an input to the shared build step. A newer prompt makes
both Ledger and Scene Breakdown stale.

## Source boundaries

| Output content | Permitted source |
| --- | --- |
| `starting_situation` | `starting_context_range` selected by Transcript Sections |
| Regular Ledger entries | The complete Role Transcript suffix beginning at `session_start_index` |
| Canonical spellings | Glossary, but only for names already established by the current-session transcript |
| Attribution mapping | Session attendees and known roles |

The starting-context and current-session slices can overlap at the transition into active play. A mixed boundary utterance may therefore support both the starting situation and a regular entry, but recap or introduction content in that utterance must not be reconstructed. Excluded material must not be used indirectly to infer antecedents, names, terms, prices, relationships, or other facts.

## Persisted schema

`ledger.json` is a strict JSON object: unknown fields are rejected, all text fields are trimmed and non-empty, and `version` is always `4`.

```text
Ledger
├── version: 4
├── session_id: UUID
├── session_name: non-empty string
├── attendees: [{ player_name, roles[] }]
├── starting_situation: non-empty string
└── utterances: ordered array of Ledger utterances
```

Each utterance has exactly one of these shapes:

| Type | Fields | Meaning |
| --- | --- | --- |
| `narration` | `source`, `fact` | A fact established about the game state. |
| `action` | `source`, `entity`, `action` | An entity does something in the fiction. |
| `speech` | `source`, `entity`, `statement` | An entity speaks in the fiction. |
| `expression` | `source`, `entity`, `sentiment` | An entity's feeling or realization. |
| `correction` | `source`, `revision` | An accepted revision to previously established state. |
| `question` | `asker`, `question`, `resolver`, `resolution` | An out-of-character question that changes or establishes fiction. |

For a `question`, `asker` and `resolver` are human attendee names, not role names. `resolver` and `resolution` are either both non-empty or both `null`. Other utterance types use `source`, normally a role/character; it remains a non-empty free-text field so explicitly established NPCs and accepted player-authored world facts can be attributed correctly.

Array order is the Ledger's only chronology. The Markdown companion is a faithful rendering of the same content and is not an independent source of truth.

## Content rules

Include reusable, current-session fiction: state changes, actions, in-fiction speech with durable facts or commitments, character states, corrections, meaningful out-of-character question/answer exchanges, discoveries, routes, hazards, negotiations, named NPC details, and independently supported components of salient compound facts. Retain uncertainty rather than resolving it by inference.

Omit opening recap, player-character introductions, table logistics, rules and dice procedure, repetition, and momentary banter or color without reusable fiction. End-of-session recap is also omitted unless it first establishes a fact; such a fact is narration.

Condense by merging only material that the source supports as one move. Split an utterance that contains multiple moves. Do not merge separate characters' proposals or plans in a way that changes attribution or implies collaboration. Preserve transcript order rather than reconstructing the fiction's chronology.

Classify by the move made at the table, not by grammatical form. For example, an in-character question is `speech`; an out-of-character question is `question` only when its exchange adds fiction. A normal roll outcome is narration, not a correction. A correction requires the table to recognize a retcon, reversal, or walk-back.

Every claim must be directly traceable to the permitted transcript slice. Rephrasing and removal of disfluencies are allowed; genre-conventional details, assumed motives, customary dialogue, responses, and outcomes are not.

## Generation and validation

The generator makes at most three structured-output attempts. Structurally invalid results, including incomplete or overlapping scene coverage, are discarded as a pair. Validation errors are included in the next attempt. A structurally valid candidate whose question attendees do not match the current attendee roster is retried; after the final attempt, the candidate with the fewest such warnings wins, with earlier attempts breaking ties.

Generation requires a current `role_transcript.json` and `transcript_sections.json`. The sections artifact is bound to the exact Role Transcript bytes with SHA-256; a stale sections artifact prevents generation instead of silently routing changed text.

The application builds both persisted artifacts with the same starting situation. Handled replacement failures roll back the pair and Ledger Markdown. Interrupted replacements leave a marker that blocks use until regeneration. Existing downstream files remain on disk and become stale when their inputs are newer. Existing Ledgers retain version 4; generating a recap requires generating the shared step when Scene Breakdown is absent.

## Authoritative implementation references

- Schema, rendering, validation, and generation: [`generate_ledger.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py)
- Prompt contract: [`generate_ledger/system.md`](../packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/system.md)
- Session orchestration and recursive freshness: [`application.py`](../packages/tablesage-application/src/tablesage_application/application.py) and [`artifact_graph.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py)
- Artifact filenames and categories: [`paths.py`](../packages/tablesage-application/src/tablesage_application/paths.py)
