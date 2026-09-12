# Canonical Ledger Format v4

## Purpose

Ledger v4 is the compact, structured record of what happened during one tabletop roleplaying
Session. It contains only the starting situation and events from the current Session. Opening
recaps of prior Sessions and player-character introductions are stored in separate artifacts and
never duplicated into the Ledger.

The Ledger is an incomplete semantic condensation rather than a transcript or fiction ontology.
It may omit table chatter, rules discussion, dice handling, repetition, and other material that
does not change campaign-relevant state. One Ledger entry may combine several transcript
utterances, and one utterance may produce several entries.

## Envelope

Every Ledger is a strict JSON object with these fields:

| Field | Type | Meaning |
| --- | --- | --- |
| `version` | literal `4` | Ledger format version |
| `session_id` | UUID | Application-supplied Session identity |
| `session_name` | non-empty text | Application-supplied Session name |
| `attendees` | ordered list of attendees | Player names and their Session roles |
| `starting_situation` | non-empty text | Immediate situation in which this Session begins |
| `utterances` | ordered list of Ledger entries | Current-session events in transcript order |

An attendee contains `player_name` and a possibly empty `roles` list. The application supplies the
version, Session identity, Session name, and attendees. The LLM supplies `starting_situation` and
`utterances`.

`starting_situation` is always required, even when `utterances` is empty. It is derived only from
the separately selected Starting Context transcript range. Prior events and character
introductions are not valid sources unless an overlapping boundary utterance also establishes the
current situation.

## Entry Types

All models reject extra fields. Persisted text is trimmed and must be non-empty. The `utterances`
array uses `type` as a lowercase discriminator:

```text
Narration: type, source, fact
Action: type, source, entity, action
Speech: type, source, entity, statement
Expression: type, source, entity, sentiment
Correction: type, source, revision
Question: type, asker, question, resolver, resolution
```

`Question.resolver` and `Question.resolution` must either both contain values or both be `null`.
Questions use human player names. The five in-fiction entry types use `source` for the role or
character making the move; accepted player-authored world facts may instead use a player name or
`players`.

## Ordering and Scope

- Array position is the only chronology. Ledger v4 has no timestamps, stable entry IDs, or source
  transcript offsets.
- Regular entries are generated only from the complete Session transcript suffix beginning at
  `session_start_index` in `transcript_sections.json`.
- Starting Context is used only to produce `starting_situation`; it cannot independently produce a
  regular Ledger entry.
- The Session suffix is not prefiltered. Ledger generation retains responsibility for semantic
  classification, inclusion, and condensation after active play begins.
- Opening recap and player-character introduction material preceding `session_start_index` cannot
  become regular entries.
- End-of-session recap speech occurs within the Session suffix and follows normal Ledger inclusion
  rules rather than opening-recap routing rules.

## Human-Readable Rendering

The deterministic `ledger.md` companion contains, in order: Session title, attendee roster,
`## Starting Situation`, `## Session` with continuously numbered entries, and a Session/version
footer. It contains no Recap or Character Introductions section and does not reinterpret content.

## Compatibility

Ledger v4 intentionally has no compatibility reader or migration for v3. Existing Sessions must
be reprocessed in order to create v4 artifacts.
