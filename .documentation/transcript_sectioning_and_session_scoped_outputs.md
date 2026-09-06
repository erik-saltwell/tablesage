# Transcript Sectioning and Session-Scoped Outputs

## Overview

Generation begins by identifying the opening recap, player-character introductions, starting
context, and active-session boundary within the Role Transcript. Each downstream generator
receives only the material relevant to its output. Ledger v4 contains the starting situation and
events from the current session only; prior-session recap and character introductions live outside
the Ledger.

## Key Concepts

### Role Transcript

The Role Transcript is the canonical source for generated session outputs. It contains an ordered
sequence of compact utterances with:

- `index`
- `speaker`
- `text`

Indices are zero-based and stable for the lifetime of that Role Transcript.

### Transcript Sections

`transcript_sections.json` records how the Role Transcript is divided for downstream generation.
It contains:

- an optional `recap_range`;
- an optional `introduction_range`;
- an optional `starting_context_range`; and
- a required `session_start_index`.

Ranges use zero-based, inclusive endpoints. They may overlap because one utterance can contain
more than one kind of material.

The artifact records references to the Role Transcript rather than duplicating its text.

### Ledger v4

Ledger v4 represents only the current session. It has:

- a required, non-empty `starting_situation`;
- the Session metadata and attendee roster; and
- chronological session utterances.

It has no Preamble, prior-events Recap, or Character Introductions.

Existing Ledgers do not require migration or backward-compatible reading. Sessions will be
reprocessed to produce Ledger v4.

### Player Introductions

`player_introductions.json` contains:

- `version`;
- `session_id`; and
- `introductions`.

Each introduction contains `character` and `description`.

Only player-character roles explicitly introduced during the opening preamble qualify. NPCs, the
Game Master role, inferred character details, and introductions after active play begins are
excluded. An empty introductions list is valid.

### Recap Summary

`recap_summary.md` is a compact, player-facing account of the current session, generated from
Ledger v4 and Session context. It does not reproduce the spoken recap from the beginning of the
recording.

It is a reusable Markdown section beginning with `## Recap` and is available independently as a
Session artifact. A Session's Recap is inserted into the following Session's composed Summary,
not its own.

### Composed Summary

The full Summary remains independently generated from Ledger v4 and Session context. Its output
contains two required insertion markers in a fixed position near the top:

1. `<!-- RECAP -->`
2. `<!-- PLAYER_INTRODUCTIONS -->`

The markers are replaced deterministically with the previous Session's Recap Summary and the
current Session's rendered Player Characters section. Sessions are ordered within a campaign by
date, with sequence number breaking same-day ties; undated Sessions follow dated Sessions and use
sequence number among themselves. The first Session has no Recap section. If a previous Session
exists but has no Recap artifact, Summary generation fails.

## Generation Flow

1. Generate the compact, indexed Role Transcript.
2. Section the Role Transcript using Session attendees and their role mappings.
3. Persist the resulting section ranges in `transcript_sections.json`.
4. Generate Ledger v4 from two labeled inputs:
   - `starting_context`, selected from `starting_context_range`;
   - `session_utterances`, containing the entire transcript suffix beginning at
     `session_start_index`.
5. Generate Player Introductions from `introduction_range` plus full Session context.
6. Generate the Recap Summary from Ledger v4 plus full Session context.
7. Generate the full Summary from Ledger v4 plus full Session context.
8. Replace the Summary's required markers with:
   - the preceding Session's complete `## Recap` section, or nothing for the first Session;
   - the current Session's `## Player Characters` section followed by one
     `- **Character** — description` bullet per introduction.

When there are no introductions, the Player Characters marker is removed without emitting an
empty section.

Generate Outputs always regenerates every phase in this order. A failure stops later phases while
preserving artifacts successfully completed earlier in the run. The composed Summary is replaced
only after every required phase succeeds.

## Sectioning Rules

- The sectioning pass identifies opening structure only. It does not filter rules discussion,
  breaks, or other chatter after active play begins.
- Ambiguous boundaries favor inclusion in the Session input.
- `session_start_index` identifies the first active-session utterance.
- `starting_context_range` identifies the minimum evidence needed to establish the immediate
  opening state.
- Starting context may include the tail of a spoken recap, but Ledger generation may use it only
  for `starting_situation`.
- `recap_range` is retained for inspection and evaluation; it is not an input to Recap Summary
  generation.
- `introduction_range` may contain intervening recap material when introductions and recap are
  interleaved.
- A mixed boundary utterance may appear in multiple downstream inputs.
- If no preamble is identifiable, the optional recap and introduction ranges are `null`.
- If no usable starting situation can be identified, generation fails rather than inventing one.
- A transcript containing an opening situation but no subsequent events may still produce a valid
  Ledger with no regular utterances.

## Output Rules

- Downstream transcript slices contain only `speaker` and `text`; source indices remain in the
  Role Transcript and Transcript Sections artifacts.
- Ledger, Player Introductions, sectioning, Recap Summary, and full Summary use the existing
  high-effort model setting while retaining independent prompts.
- Player Introduction names must exactly match non-GM Session roles. Unknown or duplicate
  characters are invalid.
- The full Summary must contain each insertion marker exactly once. Missing or duplicate markers
  are invalid.
- Regenerating a Recap does not automatically invalidate a later Session's already-composed
  Summary; keeping those cross-Session dependents current is the user's responsibility for now.
- Structurally invalid Sectioning, Ledger, Player Introductions, or Summary-marker responses may
  be attempted up to three times.
- Recap Summary receives one generation attempt because its remaining quality criteria are
  subjective rather than structural.

## Open Questions

- What final length, voice, inclusion rules, and Markdown format should Recap Summary use?

The initial placeholder behavior is one short bullet per scene, containing a short scene
description and a one-sentence account of what happened.
