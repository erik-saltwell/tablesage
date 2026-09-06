# Tutorial: Author the Player Introductions Prompt

## Goal and files

This prompt extracts structured descriptions of player characters who are explicitly introduced
in the opening preamble. Transcript Sections has already selected the smallest enclosing
Introduction Range. This generator must not search the rest of the Session or infer character
profiles from unrelated context.

Create these two new files:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_player_introductions/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_player_introductions/template.j2`

The application code and strict response schema are complete. The text below is ready to paste and
can be reviewed one section at a time. Because this is a new prompt, each system-prompt section is
new rather than an edit to existing prose.

## Part 1: Create `system.md`

Use these top-level headings in this exact order:

1. `# Overview`
2. `# Input Description`
3. `# Inclusion Rules`
4. `# Exclusion Rules`
5. `# Examples`
6. `# Output Format`

### 1. Add `# Overview`

**What is changing:** This introduces a generator dedicated to Player Character introductions,
separate from Ledger generation. Its transcript has already been restricted to the opening
Introduction Range.

**Why:** Ledger v4 contains only the current Session. Extracting introductions independently keeps
them reusable without duplicating information across Session Ledgers.

Paste:

```markdown
# Overview

Extract only explicitly framed Player Character introductions from the supplied opening-preamble transcript slice. Produce one concise, structured introduction for each qualifying character.

Do not summarize the Session, reconstruct its opening recap, describe NPCs, or infer character profiles from incidental details. The supplied transcript slice has already been selected for this task and is the only source for introduction content.
```

### 2. Add `# Input Description`

**What is changing:** This defines four inputs in their runtime order: Session metadata, attendees
and role mappings, glossary, and the selected Introduction Transcript.

**Why:** Attendee roles determine eligibility, while metadata and glossary provide orientation and
spelling only. The Introduction Range can contain recap lines between introductions, so the prompt
must not assume every supplied utterance describes a character.

Paste:

```markdown
# Input Description

You will be provided with four inputs:

- `<session_metadata>`: the campaign name, game system when known, and Session date when known. Use this only for orientation; it cannot establish an introduction or character fact.
- `<session_attendees>`: each human attendee followed by zero or more roles played in this Session. These role mappings are authoritative for deciding which names are eligible Player Characters.
- `<glossary>`: campaign terms with optional descriptions. Use it only to recognize and spell terms that are explicitly present in the Introduction Transcript. It cannot establish a character or add facts absent from that transcript.
- `<introduction_transcript>`: a compact JSON array of records containing exactly `speaker` and `text`, selected from the opening Introduction Range. This is the only source for introduction content.

The Introduction Transcript is the smallest single range enclosing all candidate opening introductions. It may therefore contain intervening recap material or other non-introduction utterances. Classify individual content within the range; do not treat every record as an introduction.
```

### 3. Add `# Inclusion Rules`

**What is changing:** This defines the positive requirements for an introduction to qualify and
the deterministic ordering and consolidation rules.

**Why:** The application rejects unknown and duplicate character names. Stating the same rules in
the prompt reduces retries and makes the output stable when one character is described across
several utterances.

Paste:

```markdown
# Inclusion Rules

- Every `character` must exactly match a non-Game-Master role listed in `<session_attendees>`, including capitalization and spelling.
- Include a character only when the Introduction Transcript explicitly presents that character as part of an opening introduction or roll-call.
- An introduction may be spoken by the character's player, another attendee, or the Game Master; eligibility depends on the introduced character and explicit framing, not the speaker label.
- Include only in-fiction details explicitly stated as part of the introduction, such as appearance, ancestry, occupation, class, personality, background, relationships, or immediate motivation.
- Consolidate all qualifying statements about one character into one `introductions` entry.
- Preserve first-introduction order: order entries by where each qualifying character is first introduced in the Introduction Transcript.
```

### 4. Add `# Exclusion Rules`

**What is changing:** This lists superficially similar material that must not become a Player
Introduction.

**Why:** The enclosing transcript range can contain recap material, NPC descriptions, and table
conversation. Explicit exclusions prevent those nearby details and contextual metadata from being
silently folded into character profiles.

Paste:

```markdown
# Exclusion Rules

- Exclude NPCs and every Game Master role, even when they receive a detailed introduction.
- Exclude human player names. The `character` field must contain an eligible role name, never the attendee's name.
- Exclude recap events, prior-session history, and other intervening material that does not explicitly describe a qualifying Player Character.
- Exclude character facts revealed incidentally during active play or merely suggested by dialogue, actions, abilities, equipment, or later events.
- Exclude rules, statistics, build choices, mechanical explanations, and real-world inspiration unless the same statement also explicitly establishes an in-fiction character detail; retain only the in-fiction detail.
- Exclude glossary-only and metadata-only facts, even when they seem applicable to an introduced character.
- Do not add connective prose, inferred motivations, genre assumptions, or other filler not directly supported by the Introduction Transcript.
```

### 5. Add `# Examples`

**What is changing:** These examples cover an ordinary roll-call, an enclosing range containing
interleaved recap, an absence of introductions, and a detailed NPC introduction that must be
excluded.

**Why:** The most likely errors are treating every utterance in the selected range as introduction
content or confusing a named NPC with an eligible attendee role. Contrasting examples make those
boundaries concrete.

Paste:

````markdown
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
````

### 6. Add `# Output Format`

**What is changing:** This defines the exact structured response expected by
`PlayerIntroductionsGenerationResponse`, with diagnostic reasoning followed by an ordered array.

**Why:** The application validates exact eligible names and uniqueness, then supplies version and
Session ID itself. An explicitly valid empty array lets the pipeline succeed when the selected
range contains no qualifying introduction.

Paste:

````markdown
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
````

## Part 2: Create `template.j2`

**What is changing:** This template supplies full Session context followed by the already-selected
Introduction Transcript. Its tag order matches the application's prompt-data model.

**Why:** Metadata, attendee roles, and glossary improve interpretation and spelling, but placing the
selected transcript in its own final tag reinforces that it alone can establish introduction
content.

Paste the complete file:

```jinja2
<session_metadata>
Campaign: {{ campaign_name }}
Game system: {{ game_system if game_system else "unspecified" }}
Session date: {{ session_date if session_date else "unknown" }}
</session_metadata>

<session_attendees>
{% for attendee in attendees %}- {{ attendee.player_name }}{% if attendee.roles %}: {{ attendee.roles | join(", ") }}{% endif %}
{% endfor %}</session_attendees>

<glossary>
{% for entry in glossary %}- {{ entry.term }}{% if entry.description %}: {{ entry.description }}{% endif %}
{% endfor %}</glossary>

<introduction_transcript>
{{ introduction_transcript }}
</introduction_transcript>
```

This copies only the structural rendering conventions from `summarize_session/template.j2`; it
does not copy Summary prompt prose. Do not add Ledger, Recap, full Role Transcript, or Transcript
Sections tags. The application has already serialized `introduction_transcript` as a compact
`{speaker, text}` JSON array, so do not loop over or reformat it.

## Part 3: Verify

**What is changing:** Verification checks both the strict generation contract and a fully rendered
prompt using a real selected Introduction Range.

**Why:** Unit tests catch invalid names, duplicates, retries, and metadata errors. Rendering catches
template mistakes such as reordered tags, leaked indices, or accidentally including the complete
Role Transcript.

After creating both files, run:

```console
uv run pytest packages/tablesage-application/tests/session_pipeline/test_generate_player_introductions.py
```

Then render a reprocessed Session with a non-null Introduction Range:

```console
uv run python scripts/generate_player_introductions_prompt.py "Your Campaign Name" 001
```

Inspect `temp/generate_player_introductions_prompt.txt` and verify:

- tags occur once each in this order: `<session_metadata>`, `<session_attendees>`, `<glossary>`,
  `<introduction_transcript>`;
- Introduction Transcript is a JSON array whose records contain only `speaker` and `text`;
- no source indices or out-of-range transcript utterances appear;
- attendee roles and glossary spellings render correctly, including empty optional values; and
- the output contract has only `scratchpad` and `introductions`.

Do not call the live LLM yet. Return control to the implementation agent for prompt review before
proceeding to Recap Summary.
