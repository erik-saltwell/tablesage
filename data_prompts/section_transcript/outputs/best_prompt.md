# Overview

Identify the opening sections of a tabletop roleplaying Session transcript and locate the boundary where active play begins. Return transcript indices that route the relevant source utterances to separate downstream generators.

Do not summarize or rewrite the transcript. Do not decide which material belongs in the Ledger. Do not remove rules discussion, breaks, jokes, or other chatter that occurs after active play begins.

# Input Description

- `<session_attendees>` lists each player and their zero or more roles in this Session. Treat these role mappings as authoritative when distinguishing player characters from NPCs. A role is not a player character merely because it speaks in the transcript.
- `<role_transcript>` contains JSON with an ordered `utterances` array. Each utterance has exactly three fields: `index`, `speaker`, and `text`. The `index` is zero-based and is the value referenced by every range and boundary in the response.

# Section Definitions

## Recap Range

Some sessions begin by recapitulating what has happened in the fiction in prior sessions, or earlier in the fictional game world, before active play begins.  It often leads up to describing the situation the characters find themselves in at the start of the session.  The Recap Range is the smallest inclusive range containing an explicitly framed opening account of events from previous Sessions or earlier campaign history. Ordinary reminders during active play are not part of the Recap Range. Return `null` when no opening recap is present. Do not extend the Recap Range solely to include a separate description of the current starting situation. When one utterance contains both recap and starting-situation material, it may belong to both the Recap Range and the Starting Context Range.

::: examples
If the recap's first substantive line recounting past events occurs at utterance 40 (even if utterance 41 continues the same recap), the Recap Range must start at 40, not 41 — starting one index too late incorrectly excludes real recap content.
:::

::: guidance
When locating the start of the Recap Range, choose the smallest start_index whose utterance already begins narrating or referencing prior-session events — do not skip past a short lead-in, acknowledgment, or transitional line if it is the first utterance carrying recap content. Shifting the start index later than the true first recap utterance is a common error to avoid.
:::

## Introduction Range

If this is the first session, or a new player character is joining the party, the start of the session may include an introduction of new player characters. The Introduction Range is the smallest inclusive range containing explicit opening-preamble introductions of player-character roles listed in `<session_attendees>`. Exclude NPC descriptions, Game Master self-introductions, inferred character profiles, and character facts first revealed after active play begins.

::: guidance
The Introduction Range must end before any Recap Range content begins — the two ranges must never overlap. If utterances shift from player/character naming into narrating earlier in-fiction events (a recap), stop the Introduction Range at the last utterance before that shift, even if the recap content occurs later in the same block of dialogue.
:::

When introductions are interleaved with recap utterances, use the smallest range enclosing all qualifying introductions. The range may therefore contain intervening recap material. Return `null` when no qualifying introduction is present.

::: examples
If utterances 1–36 are attendees introducing their characters, and utterances 41–59 recount earlier campaign events (a recap), the Introduction Range is 1–36, not 1–59 — the recap content must be excluded even though it appears before the true start of play.
:::

## Starting Context Range

The minimum inclusive range containing enough direct transcript evidence to state the immediate situation in which the players begin this Session. It may overlap the end of the recap or the transition into active play.

::: guidance
- The Starting Context Range must begin at or before the session_start_index and extend far enough to fully establish the immediate starting situation. Do not truncate the range to only the last utterance(s) before active play begins — if the recap transitions into mixed or transitional content, that content belongs inside the Starting Context Range, not excluded from it.
- The Starting Context Range must span enough utterances to fully establish the immediate present-scene situation (who is present, where they are, what is about to happen) — do not stop at the first utterance after the recap/introduction transition if the starting situation is not yet fully established. Likewise, the range should begin only once genuine present-scene narration starts, not at the last recap/introduction utterance.
- Keep the Starting Context Range as narrow as possible: it should cover only the utterance(s) strictly necessary to establish the immediate starting situation, not every utterance that continues or elaborates on that situation. If a single utterance establishes the starting context, set start_index equal to end_index rather than extending the range forward.
:::

This range provides evidence for a single starting-situation statement; it does not classify the entire setup, recap, or the string of events leading to the starting situation.  Relevant evidence may include the characters’ location, current objective, immediate conditions, threats, or obstacles, but only when explicitly supported by the transcript. Return `null` only when the transcript does not support any starting situation. The application will stop downstream generation rather than inventing one.

::: examples
- If session_start_index is 114 and the recap winds down through utterance 117 with mixed transitional dialogue before active play resumes at 118, the correct starting_context_range is {"start_index": 114, "end_index": 118} — not {"start_index": 117, "end_index": 118}, which omits the material that actually establishes the starting scene.
- If the recap-to-play transition occurs around utterance 187 but the present-scene situation (location, who's present, immediate action) isn't fully established until utterance 189, and continues being established through utterance 193, the correct Starting Context Range is 189–193, not 187–189 — the range should not start at the bare transition point nor end before the situation is fully clear.
- If present-scene narration begins at utterance 61 and establishes the immediate starting situation right there, with utterances 62–73 merely continuing that same scene, the Starting Context Range is {"start_index": 61, "end_index": 61} — not 61–73.
:::

## Session Start Index

The index of the first utterance belonging to active play in the current Session. Opening recap and introductions normally precede it, while scene-setting that begins the present action may also be included in the Starting Context Range.  Active play often begins when the Game Master presents the immediate situation or asks, “What do you do?” When such an utterance marks the transition into active play, use its index as `session_start_index`.

If the recording establishes a starting situation but contains no subsequent active play, return the utterance count—one greater than the final utterance index.

# Boundary Rules

- When a boundary is ambiguous, include the material on the Session side by choosing the earlier plausible `session_start_index`. This prevents current-session content from being lost.
- `recap_range`, `introduction_range`, and `starting_context_range` may overlap.
- A mixed utterance may belong to multiple ranges and may also be the `session_start_index`.
- Classify only the opening structure needed to locate the active-play boundary.
- After active play begins, do not classify, exclude, or skip rules discussion, breaks, jokes, or other chatter. The Session input is the complete transcript suffix beginning at `session_start_index`.
- Every range endpoint must reference an existing utterance index.
- `session_start_index` must reference an existing utterance or equal the utterance count when the recording establishes a starting situation but contains no subsequent active play.

# Process

1. Read the complete `<session_attendees>` mapping and the complete `<role_transcript>` before choosing any boundary.
2. Locate the earliest defensible beginning of active play in the current Session.
3. Locate the minimum transcript evidence needed to establish the immediate starting situation.
4. Locate any explicitly framed opening recap of prior events.
5. Locate any qualifying opening player-character introductions, using the attendee role mappings as the authoritative eligibility test.
6. Verify that every range endpoint references an existing utterance and that `session_start_index` references an existing utterance or equals the utterance count.
7. Emit the selected indices without summarizing, rewriting, or filtering the transcript.

# Examples

## Example 1: No Preamble

`<session_attendees>`:

- Alice: Zaria
- Morgan: Game Master

`<role_transcript>`:

```json
{
  "utterances": [
    {
      "index": 0,
      "speaker": "Game Master",
      "text": "Rain lashes the riverbank as you wake beside the wrecked boat."
    },
    {
      "index": 1,
      "speaker": "Zaria",
      "text": "I check whether our supplies survived."
    }
  ]
}
```

The opening scene-setting is already part of active play. There is no recap or player-character introduction.

```json
{
  "scratchpad": "Active play begins with the opening scene at index 0, which also establishes the immediate starting situation.",
  "recap_range": null,
  "introduction_range": null,
  "starting_context_range": {
    "start_index": 0,
    "end_index": 0
  },
  "session_start_index": 0
}
```

## Example 2: Recap Followed by Introductions

`<session_attendees>`:

- Alice: Zaria
- Ben: Corin
- Morgan: Game Master

`<role_transcript>`:

```json
{
  "utterances": [
    {
      "index": 0,
      "speaker": "Game Master",
      "text": "Last time, the party escaped from the flooded mine."
    },
    {
      "index": 1,
      "speaker": "Game Master",
      "text": "You recovered the stolen map, but the bandit captain escaped."
    },
    {
      "index": 2,
      "speaker": "Zaria",
      "text": "Zaria is an elven wizard searching for her missing sister."
    },
    {
      "index": 3,
      "speaker": "Corin",
      "text": "Corin is a former royal guard who now protects the group."
    },
    {
      "index": 4,
      "speaker": "Game Master",
      "text": "At dawn, you are camped beside the river while riders approach from the east."
    },
    {
      "index": 5,
      "speaker": "Zaria",
      "text": "I extinguish the fire and wake Corin."
    }
  ]
}
```

The recap and introductions occupy separate ranges. Index `4` both establishes the starting situation and begins active play.

```json
{
  "scratchpad": "Indices 0–1 are prior-session recap, indices 2–3 are explicit introductions of attendee player-character roles, and current-session play begins with the scene at index 4.",
  "recap_range": {
    "start_index": 0,
    "end_index": 1
  },
  "introduction_range": {
    "start_index": 2,
    "end_index": 3
  },
  "starting_context_range": {
    "start_index": 4,
    "end_index": 4
  },
  "session_start_index": 4
}
```

## Example 3: Interleaved Recap and Introductions

`<session_attendees>`:

- Alice: Zaria
- Ben: Corin
- Morgan: Game Master

`<role_transcript>`:

```json
{
  "utterances": [
    {
      "index": 0,
      "speaker": "Game Master",
      "text": "Previously, the party entered the ruins beneath Ashmoor."
    },
    {
      "index": 1,
      "speaker": "Zaria",
      "text": "Zaria is an elven wizard who carries a silver staff."
    },
    {
      "index": 2,
      "speaker": "Game Master",
      "text": "There, you discovered that the sealed gate had been opened."
    },
    {
      "index": 3,
      "speaker": "Corin",
      "text": "Corin is a former royal guard haunted by the fall of the capital."
    },
    {
      "index": 4,
      "speaker": "Game Master",
      "text": "Now you stand inside the gatehouse as something pounds against the outer doors."
    },
    {
      "index": 5,
      "speaker": "Corin",
      "text": "I draw my sword and brace the doors."
    }
  ]
}
```

The Introduction Range encloses both qualifying introductions, including the recap utterance between them. This overlap is valid.

```json
{
  "scratchpad": "The recap spans indices 0–2. The qualifying introductions at indices 1 and 3 require an enclosing Introduction Range of 1–3. Active play begins with the immediate threat at index 4.",
  "recap_range": {
    "start_index": 0,
    "end_index": 2
  },
  "introduction_range": {
    "start_index": 1,
    "end_index": 3
  },
  "starting_context_range": {
    "start_index": 4,
    "end_index": 4
  },
  "session_start_index": 4
}
```

## Example 4: One Utterance Contains the Recap-to-Play Transition

`<session_attendees>`:

- Alice: Zaria
- Morgan: Game Master

`<role_transcript>`:

```json
{
  "utterances": [
    {
      "index": 0,
      "speaker": "Game Master",
      "text": "Last time, Zaria pursued the thief through the old city."
    },
    {
      "index": 1,
      "speaker": "Game Master",
      "text": "The thief escaped with the crown, and now Zaria sees him boarding a ship at the crowded harbor."
    },
    {
      "index": 2,
      "speaker": "Zaria",
      "text": "I run toward the ship and call for the harbor guards."
    }
  ]
}
```

Index `1` finishes the recap and transitions directly into the current scene. It belongs to the Recap Range and Starting Context Range and is also the Session Start Index.

```json
{
  "scratchpad": "Index 1 is a mixed boundary utterance: it concludes the prior event and establishes the present actionable situation. Including it on the Session side prevents current-session context from being lost.",
  "recap_range": {
    "start_index": 0,
    "end_index": 1
  },
  "introduction_range": null,
  "starting_context_range": {
    "start_index": 1,
    "end_index": 1
  },
  "session_start_index": 1
}
```

# Output Format

Return exactly one JSON object conforming to the supplied structured-output schema. Do not wrap the object in a Markdown code fence, and do not include prose before or after it.

The object must contain these fields:

- `scratchpad`: Brief reasoning used to identify and verify the section boundaries. This field is diagnostic and is not persisted as routing metadata.
- `recap_range`: An inclusive range object containing `start_index` and `end_index`, or `null` when no qualifying opening recap is present.
- `introduction_range`: An inclusive range object containing `start_index` and `end_index`, or `null` when no qualifying opening player-character introduction is present.
- `starting_context_range`: An inclusive range object containing `start_index` and `end_index`, or `null` only when the transcript provides no supported starting situation.
- `session_start_index`: The zero-based index of the first active-play utterance. When the transcript establishes a starting situation but contains no subsequent active play, this may equal the utterance count.

Always include all four routing keys: `recap_range`, `introduction_range`, `starting_context_range`, and `session_start_index`. Include a range key even when its value is `null`.

All range endpoints are zero-based and inclusive. Every non-null range must satisfy `start_index <= end_index`, and both endpoints must reference existing utterances. `session_start_index` must reference an existing utterance or equal the utterance count in the setup-only case.

Do not add confidence scores, labels, extracted transcript text, summaries, arrays of disjoint ranges, or any fields not defined by the supplied schema.
