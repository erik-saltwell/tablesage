# Ledger Artifact Specification

The Ledger is TableSage's canonical, structured record of one session's current play. It condenses campaign-relevant fiction into an ordered, machine-readable account; it is not a transcript, a campaign encyclopedia, or a summary of the opening recap.

## Purpose and position in the pipeline

Transcript Sections routes the role-attributed transcript into a starting-context view and a current-session view. Ledger generation consumes those two views, attendee roles, and glossary spellings. It runs after the Role Transcript and Transcript Sections artifacts exist.

One structured LLM call generates only `ledger: {utterances}`, plus `starting_situation` for the first recorded Session when opening context is supplied. Scene Log is generated separately from Ledger and the prior Endcap. See [Narrative Artifact Contracts](../port-latest-artifact-generation/specification.md) for the current pipeline; the old Scene Breakdown specification is retained for legacy files.

The persisted artifact is `ledger.json`; its deterministic human-readable companion is `ledger.md`. Both live in the session folder. Ledger and Scene Log are independent producer steps. Replacing Ledger makes Scene Log and its downstream consumers stale through content fingerprints; it does not delete their files.

The packaged Ledger system prompt, template, schemas, input/assembly code and generation controls are build dependencies. Roster, Glossary, Session name and bootstrap mode are also fingerprinted. Changes propagate through Scene Log to Summary and Table Recap.

## Source boundaries

| Output content | Permitted source |
| --- | --- |
| `starting_situation` | `starting_context_range` selected by Transcript Sections |
| Regular Ledger entries | The complete Role Transcript suffix beginning at `session_start_index` |
| Canonical spellings | Glossary, but only for names already established by the current-session transcript |
| Attribution mapping | Session attendees and known roles |

The starting-context and current-session slices can overlap at the transition into active play. A mixed boundary utterance may therefore support both the starting situation and a regular entry, but recap or introduction content in that utterance must not be reconstructed. Excluded material must not be used indirectly to infer antecedents, names, terms, prices, relationships, or other facts.

## Persisted schema

`ledger.json` is a strict JSON object: unknown fields are rejected, utterance text is trimmed and non-empty, and new generation persists `version: 5`. Legacy version 4 remains loadable.

```text
Ledger
├── version: 5
├── session_id: UUID
├── session_name: non-empty string
├── attendees: [{ player_name, roles[] }]
├── starting_situation: non-empty bootstrap string or null
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

## Generation and Validation

The generator makes at most three structured-output attempts. Structural failures retry with validation feedback. Question attendees are checked against the roster; after warning-only retries, the valid candidate with fewest warnings wins, with earlier attempts breaking ties.

Generation requires current Role Transcript and Transcript Sections; routing checks the Role Transcript digest. First-session bootstrap requires usable starting context; later Sessions may route current play without an opening-context slice. The model never receives prior Endcaps or recaps. The application supplies Session metadata and persists Ledger JSON/Markdown as one recoverable pair.

Current implementation is [narrative.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/narrative.py). Utterance types, legacy loading and Markdown rendering remain in [generate_ledger.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py). See [Narrative Artifact Contracts](../port-latest-artifact-generation/specification.md) for continuity, persistence and freshness.
