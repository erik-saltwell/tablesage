# Overview

Extract only explicitly framed Player Character introductions from the supplied opening-preamble transcript slice. Produce one concise, structured introduction for each qualifying character.

Do not summarize the Session, reconstruct its opening recap, describe NPCs, or infer character profiles from incidental details. The supplied transcript slice has already been selected for this task and is the only source for introduction content.

# Input Description

You will be provided with four inputs:

- `<session_metadata>`: the campaign name, game system when known, and Session date when known. Use this only for orientation; it cannot establish an introduction or character fact.
- `<session_attendees>`: each human attendee followed by zero or more roles played in this Session. These role mappings are authoritative for deciding which names are eligible Player Characters.
- `<glossary>`: campaign terms with optional descriptions. Use it only to recognize and spell terms that are explicitly present in the Introduction Transcript. It cannot establish a character or add facts absent from that transcript.
- `<introduction_transcript>`: a compact JSON array of records containing exactly `speaker` and `text`, selected from the opening Introduction Range. This is the only source for introduction content.

The Introduction Transcript is the smallest single range enclosing all candidate opening introductions. It may therefore contain intervening recap material or other non-introduction utterances. Classify individual content within the range; do not treat every record as an introduction.

# Inclusion Rules

- Every `character` must exactly match a non-Game-Master role listed in `<session_attendees>`, including capitalization and spelling.
- Include a character only when the Introduction Transcript explicitly presents that character as part of an opening introduction or roll-call.
- An introduction may be spoken by the character's player, another attendee, or the Game Master; eligibility depends on the introduced character and explicit framing, not the speaker label.
- Include only in-fiction details explicitly stated as part of the introduction, such as appearance, ancestry, occupation, class, personality, background, relationships, or immediate motivation.
- Consolidate all qualifying statements about one character into one `introductions` entry.
- Preserve first-introduction order: order entries by where each qualifying character is first introduced in the Introduction Transcript.

# Exclusion Rules

- Exclude NPCs and every Game Master role, even when they receive a detailed introduction.
- Exclude human player names. The `character` field must contain an eligible role name, never the attendee's name.
- Exclude recap events, prior-session history, and other intervening material that does not explicitly describe a qualifying Player Character.
- Exclude character facts revealed incidentally during active play or merely suggested by dialogue, actions, abilities, equipment, or later events.
- Exclude rules, statistics, build choices, mechanical explanations, and real-world inspiration unless the same statement also explicitly establishes an in-fiction character detail; retain only the in-fiction detail.
- Exclude glossary-only and metadata-only facts, even when they seem applicable to an introduced character.
- Do not add connective prose, inferred motivations, genre assumptions, or other filler not directly supported by the Introduction Transcript.

# Examples

## Example 1: Ordinary Roll-Call

Attendee roles include `Zaria` and `Corin`. The Introduction Transcript says:

```json
[
  {
    "speaker": "Zaria",
    "text": "Zaria is an elven wizard searching for her missing sister."
  },
  {
    "speaker": "Corin",
    "text": "Corin is a former royal guard who now protects the group."
  }
]
```

Output both introductions in that order.

## Example 2: Interleaved Recap Material

Attendee roles include `Zaria` and `Corin`. The Introduction Transcript says:

```json
[
  {
    "speaker": "Zaria",
    "text": "Zaria is an elven wizard who carries a silver staff."
  },
  {
    "speaker": "Game Master",
    "text": "Last time, the party escaped from the flooded mine."
  },
  {
    "speaker": "Corin",
    "text": "Corin is a former royal guard haunted by the fall of the capital."
  }
]
```

Output introductions for `Zaria` and `Corin`. Do not include the flooded-mine event in either description.

## Example 3: No Explicit Introductions

Attendee roles include `Zaria`. The Introduction Transcript says:

```json
[
  {
    "speaker": "Game Master",
    "text": "Everyone ready to begin?"
  },
  {
    "speaker": "Zaria",
    "text": "Yes, let's go."
  }
]
```

Return an empty `introductions` list. Do not infer an introduction from the attendee mapping or speaker label.

## Example 4: NPC Introduction

Attendee roles include `Zaria` and `Game Master`, but not `Veyra`. The Introduction Transcript says:

```json
[
  {
    "speaker": "Game Master",
    "text": "Veyra is a silver-eyed envoy from the northern court who carries the queen's seal."
  }
]
```

Return an empty `introductions` list. `Veyra` is not an eligible attendee role, so this is an NPC introduction.

# Output Format

Return exactly one JSON object conforming to the supplied structured-output schema. Do not wrap it in a Markdown code fence, and do not include prose before or after it.

The object has exactly two top-level fields in this order:

- `scratchpad`: brief reasoning identifying candidate names, their attendee-role eligibility, excluded material, consolidation, and final order. The application discards this field.
- `introductions`: an ordered JSON array of qualifying Player Character introductions. Return an empty array when nothing qualifies.

Every introduction contains exactly:

- `character`: the exact eligible non-Game-Master role name from `<session_attendees>`; and
- `description`: one concise, non-empty description containing only explicitly introduced in-fiction facts.

Emit at most one entry per character and preserve first-introduction order. Do not emit version, Session identity, player name, source indices, confidence, citations, or any field not defined by the schema.

Example response:

```json
{
  "scratchpad": "Zaria and Corin are attendee roles explicitly introduced in that order. The intervening flooded-mine sentence is recap material and is excluded.",
  "introductions": [
    {
      "character": "Zaria",
      "description": "An elven wizard who carries a silver staff."
    },
    {
      "character": "Corin",
      "description": "A former royal guard haunted by the fall of the capital."
    }
  ]
}
```
