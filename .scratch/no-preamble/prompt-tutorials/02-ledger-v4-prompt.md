# Tutorial: Convert the Ledger Prompt to v4

## Goal and files

This change makes Ledger generation consume two already-routed transcript slices and emit only the
current Session. You will edit:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/template.j2`
- `data_prompts/ledger/seed_prompt.txt`

The application schema is already Ledger v4. Its generated response has exactly three top-level
fields: `scratchpad`, required non-empty `starting_situation`, and `utterances`. There is no
Preamble, Recap, Character Introduction, or `opening_situation` field.

The text below is ready to paste. Review and apply one section at a time.

## Part 1: Edit `system.md`

### 1. Update `# Overview`

**What is changing:** The Overview moves the task from Ledger v3 over a whole transcript to Ledger
v4 over already-routed current-session material. It names `starting_situation` as a separate output
and explicitly excludes opening recap and introduction content.

**Why:** The old Overview primes the model to search the input for a Preamble. Transcript
sectioning now owns that boundary, so Ledger generation must trust its narrower inputs and avoid
reconstructing content that was intentionally routed elsewhere.

Keep the `# Overview` heading. In its first paragraph:

1. Replace `a raw session transcript` with `the supplied current-session utterances`.
2. Replace `Ledger Format v3` with `Ledger Format v4`.
3. Append this sentence to that paragraph:

```markdown
Separately derive one concise starting situation from the supplied starting context.
```

Then add this new paragraph immediately after the first paragraph:

```markdown
The Ledger must contain only the starting situation and events from the current Session. Do not reconstruct or include a recap of prior Sessions, player-character introductions, or other opening-preamble material that is absent from `<session_utterances>`.
```

Leave all other Overview text unchanged.

### 2. Update the envelope paragraph under `# Ledger Description`

**What is changing:** The Ledger envelope description replaces optional `preamble` with required
`starting_situation`, retains the six existing entry types, and clarifies which fields are supplied
by the application versus the model.

**Why:** This section establishes the model's conceptual picture of the output. If Preamble remains
in that picture, later instructions alone may not stop the model from emitting v3 fields or folding
prior-session events into regular entries.

Keep the heading, opening description, type explanations, and all six entry-type bullets exactly as
they are. Replace only the paragraph beginning `A Ledger carries a small envelope` with:

```markdown
A persisted Ledger carries a small application-supplied envelope—`version`, `session_id`, `session_name`, and an attendees roster containing `player_name` and `roles`—followed by a required `starting_situation` and `utterances`. `starting_situation` concisely states the immediate situation in which the players begin this Session. `utterances` is an ordered list of current-session entries. Array position is the only chronology; there are no timestamps, IDs, or links between entries.
```

### 3. Update `# Input Description`

**What is changing:** The single flat `<session_transcript>` input becomes two compact JSON arrays:
`<starting_context>` and `<session_utterances>`. The replacement also corrects the declared input
count, preserves roles, attendees, and glossary, and defines the different authority of each
transcript slice.

**Why:** Provenance is the central v4 invariant. Starting Context may support only
`starting_situation`; Session Utterances may support regular entries. Naming that restriction at
the input boundary prevents recap leakage and prevents the model from turning context-only evidence
into Session events.

Keep the `# Input Description` heading and the existing `<session_attendees>` and `<glossary>`
bullets unchanged.

There are currently two consecutive sentences beginning `You will be provided with`. Delete the
first one, which says there are three inputs. In the remaining sentence, replace `four` with `five`
so it reads:

```markdown
You will be provided with five inputs:
```

Replace only the existing `<known_session_roles>` bullet with the following. This corrects its
claim that the schema restricts every `source`; the implemented schema deliberately permits other
explicitly established characters and player-authored attribution.

```markdown
- `<known_session_roles>`: the canonical role and player-character names in play during this Session. Use these spellings for in-fiction `source` values when applicable. A regular `source` may still be another explicitly established character or a permitted player-authored attribution.
```

Delete the complete `<session_transcript>` bullet, including all its nested bullets. Insert these
two bullets in its former position:

```markdown
- `<starting_context>`: a compact JSON array of records containing exactly `speaker` and `text`. Use this input only to derive `starting_situation`. Do not generate regular Ledger entries from material that appears only in this input.
- `<session_utterances>`: a compact JSON array of records containing exactly `speaker` and `text`. This is the complete transcript suffix beginning at active play and is the only source for regular `utterances` entries.
```

Immediately after those two bullets, add these two paragraphs. They preserve the useful speaker
and transcript-quality guidance from the deleted nested bullets while applying it to both arrays:

```markdown
Speaker labels are usually roles or character names because role assignment has already occurred. A player name remains when that attendee has no assigned role. `Unassigned Speaker` identifies a real utterance whose speaker remains unknown. Text is punctuated speech-to-text and may contain disfluencies, false starts, and transcription errors.

The two transcript arrays may overlap at the transition into active play. When the same source utterance appears in both, use it for `starting_situation` and process it normally as part of `<session_utterances>`; this is intentional and does not authorize copying other Starting Context material into regular entries.
```

### 4. Replace `## Example Input`

**What is changing:** The example replaces Markdown speaker lines with the exact JSON shape sent by
the application. It demonstrates a mixed boundary utterance appearing in both inputs.

**Why:** The old example teaches the obsolete flat-transcript representation. A concrete overlap
example shows that duplication across inputs is intentional while preserving their distinct uses:
one copy supports the starting situation and the Session copy may produce a regular entry.

Replace the complete existing example-input section through the line immediately before
`# Process` with:

This is intentionally a whole-section replacement because the old example's central input no
longer exists.

````markdown
## Example Input

```text
<known_session_roles>
- Game Master
- Kestrel
- Thorn
</known_session_roles>

<session_attendees>
- Alice: Game Master
- Bob: Kestrel
- Carol: Thorn
</session_attendees>

<glossary>
- Phidipaldi: Thorn's father.
- Brandonsford: The town Kestrel was born in.
</glossary>

<starting_context>
[
  {
    "speaker": "Game Master",
    "text": "At dawn, the party reaches the gorge and finds the rope bridge cut from the far side."
  }
]
</starting_context>

<session_utterances>
[
  {
    "speaker": "Game Master",
    "text": "At dawn, the party reaches the gorge and finds the rope bridge cut from the far side."
  },
  {
    "speaker": "Kestrel",
    "text": "I scan the gorge for another way across."
  },
  {
    "speaker": "Thorn",
    "text": "How deep is it? Could we climb down?"
  }
]
</session_utterances>
```

The first source utterance appears in both transcript inputs because it establishes the starting situation and also begins active play.
````

### 5. Update `# Process`

**What is changing:** The workflow removes the “identify” and “emit” Preamble steps. It adds an
explicit Starting Situation step sourced only from Starting Context and changes the chronological
walk to name Session Utterances directly.

**Why:** The model no longer owns opening-section detection. A source-aware process makes it check
the complete routed inputs while keeping generated claims attached to the correct source, which is
especially important when the two arrays overlap.

Keep the `# Process` heading. Delete the two complete steps titled `Identify the preamble` and
`Emit the preamble, if there is one`.

Replace the step titled `Read the entire transcript before writing anything` with:

```markdown
1. **Read both transcript inputs completely before writing anything.** Read all of `<starting_context>` and `<session_utterances>` before classifying entries. Later passages may clarify names, attribution, and scene structure.
```

Immediately after that step, insert:

```markdown
2. **Derive `starting_situation`.** Write one concise statement of the immediate situation in which the players begin. Derive it only from `<starting_context>`. Include the directly supported location, objective, conditions, threats, or obstacles needed to make the opening state understandable. Do not include prior-session history or unsupported inference.
```

Replace the existing `Plan in scratchpad` step with:

```markdown
3. **Plan in `scratchpad`.** Record brief working notes about canonical spellings, scene structure, attribution, and difficult classifications. Do not restate the finished Ledger. The application discards this field.
```

Replace the existing `Walk the transcript in order and emit entries` step with:

```markdown
4. **Walk `<session_utterances>` in order and emit entries.** For each passage, decide whether it carries campaign-relevant fiction. Omit it if it does not. If it does, classify its move and condense it, merging adjacent utterances that make one move and splitting one utterance that makes several. Preserve the order in which the content occurs.
```

Replace the existing `Check before finishing` step with:

```markdown
5. **Check before finishing.** Confirm that `starting_situation` is non-empty and supported by `<starting_context>`; every regular entry is supported by `<session_utterances>`; entries remain chronological; every applicable field is non-empty; fiction-bearing material was not accidentally dropped; and non-fiction material was not retained.
```

### 6. Update one bullet under `## Attribution`

**What is changing:** Player-authored world facts remain regular narration when established during
the Session, but the obsolete instruction to move shared party backstory into a Ledger Recap is
removed. The replacement states that prior shared backstory is outside the supplied Session input.

**Why:** Ledger v4 has no Recap destination. Retaining the old sentence would direct the model
toward a nonexistent field and could encourage it to reconstruct prior history from Starting
Context.

Find the bullet beginning `- **Player-authored world facts.**` Replace that entire bullet with:

```markdown
- **Player-authored world facts.** When a player, out of character, states something about the world that is not their character acting—“let's say the town has a river,” “the mule is named Seamus”—and the Game Master or table accepts it, record it as narration. Its `source` is the player's name from `<session_attendees>` when the speaker is known, or `players` when the fact was built jointly or the speaker is unknown. Prior shared party backstory belongs outside the supplied Session utterances; never reconstruct it from `<starting_context>`.
```

Leave the other Attribution bullets in place.

### 7. Update one bullet under `## Condensation and fidelity`

**What is changing:** The model now resolves incidental misstatements against
`starting_situation` or earlier Ledger entries, rather than against character introductions.

**Why:** Introductions no longer exist in the Ledger input or output. Starting Situation is the
only pre-entry canonical state available to this generation pass.

Find the bullet beginning `- When a speaker misstates an established fact in passing`. Replace it
with:

```markdown
- When a speaker misstates an established fact in passing and the table does not treat it as a revision, prefer the fact as established in `starting_situation` or earlier Ledger entries. Only a revision the table notices and accepts is a `correction`.
```

### 8. Update `## Validity`

**What is changing:** Preamble-specific validity rules are replaced with v4 invariants: a sourced,
non-empty Starting Situation; permission for an empty regular-entry list; and strict separation of
Starting Context from Session-entry evidence.

**Why:** These rules mirror the implemented Pydantic schema while also stating the semantic
constraint that a structural schema cannot enforce—regular entries must not come from context-only
material.

Keep the `## Validity` heading and these existing bullets unchanged:

- the bullet beginning `Every text field must be non-empty`; and
- the bullet beginning `On a question`.

Delete these three obsolete bullets:

- the bullet beginning `At most one introduction per character`;
- the bullet beginning `Recap events stay in the order`; and
- the bullet beginning `The Ledger must carry real content somewhere`.

Insert these three new bullets as the first three bullets under `## Validity`, before the retained
`Every text field` bullet:

```markdown
- `starting_situation` must be non-empty and supported only by `<starting_context>`.
- `utterances` may be an empty array when a starting situation is established but active play contains no campaign-relevant moves.
- Every regular Ledger entry must trace to `<session_utterances>`. Material found only in `<starting_context>`, the glossary, or attendee metadata cannot produce a regular entry.
```

### 9. Preserve `## End of session recaps`

**What is changing:** This section remains, but its wording explicitly distinguishes recap speech
inside active play from the removed opening Recap field.

**Why:** “No recap in the Ledger” must not cause the model to mishandle an end-of-session review
that establishes a new fact. The rule concerns inclusion and condensation within Session
Utterances, not preamble routing.

Keep this subsection and its existing sentence unchanged. It concerns recap speech after active
play begins and therefore remains part of `<session_utterances>`. Append this sentence to the
existing paragraph:

```markdown
This rule applies to recap speech inside `<session_utterances>` and does not create an opening Recap or Preamble field.
```

### 10. Replace `# Output Format`

**What is changing:** The top-level response changes from `scratchpad`, `preamble`, and
`utterances` to `scratchpad`, `starting_situation`, and `utterances`. The complete Preamble schema
and v3 example are removed and replaced with a valid v4 response example.

**Why:** This is the model's final output contract and must exactly match
`LedgerGenerationResponse`. Explicitly allowing an empty `utterances` array supports setup-only
Sessions, while requiring Starting Situation ensures every valid Ledger still contains meaningful
opening state.

Replace the complete section from `# Output Format` through the end of the file with:

This is intentionally a whole-section replacement: one of three top-level fields disappears, a
different required field takes its place, an entire nested schema is removed, and the example
response must be rebuilt. Surgical edits here would be more difficult to validate than the final
replacement.

````markdown
# Output Format

Return one JSON object conforming to the JSON schema supplied through structured output. Do not include prose, an explanation, or Markdown fences. The response is parsed directly.

## Top Level Fields

The object has exactly three top-level fields in this order:

- `scratchpad` — brief planning notes from the Process section; discarded after generation.
- `starting_situation` — one concise, non-empty statement derived only from `<starting_context>`.
- `utterances` — the ordered list of entries derived only from `<session_utterances>`; this array may be empty.

### Envelope

Do not generate the persisted Ledger envelope. The application supplies `version`, `session_id`, `session_name`, and `attendees`. Your response begins with `scratchpad`.

### Utterances

Each entry in `utterances` carries a lowercase `type` discriminator and exactly that type's fields:

- `narration` — `source`, `fact`
- `action` — `source`, `entity`, `action`
- `speech` — `source`, `entity`, `statement`
- `expression` — `source`, `entity`, `sentiment`
- `correction` — `source`, `revision`
- `question` — `asker`, `question`, `resolver`, `resolution`; it has no `source`

`source` is the role or character making the move; `entity` is who acts, speaks, or feels within the fiction. They often match for a player character and differ when the Game Master voices an NPC. Questions instead use human player names for `asker` and `resolver`.

Every field listed for a chosen type is required, including nullable question fields. Write `null` explicitly for both `resolver` and `resolution` when a question is unresolved. Never add fields the schema does not define, and never emit an empty string.

## Example Response

```json
{
  "scratchpad": "The bridge state is the opening situation. Kestrel searches for a crossing. Thorn's out-of-character question establishes the gorge depth and is resolved by Alice.",
  "starting_situation": "At dawn, the party reaches a gorge where the rope bridge has been cut from the far side.",
  "utterances": [
    {
      "type": "narration",
      "source": "Game Master",
      "fact": "The rope bridge over the gorge has been cut from the far side."
    },
    {
      "type": "action",
      "source": "Kestrel",
      "entity": "Kestrel",
      "action": "Searches the gorge rim for another crossing."
    },
    {
      "type": "question",
      "asker": "Carol",
      "question": "How deep is the gorge, and is it climbable?",
      "resolver": "Alice",
      "resolution": "It is around sixty feet deep, with enough ledges to climb down."
    }
  ]
}
```
````

### 11. Search for obsolete language

**What is changing:** This is a semantic cleanup pass for v3 terms that may survive outside the
large replaced sections.

**Why:** The prompt is long, and one stale instruction can contradict the new source boundaries.
Some words such as “recap” still have legitimate uses, so every match must be reviewed in context
instead of deleted mechanically.

Search the entire file case-insensitively for these terms:

```text
preamble
recap
introduction
opening_situation
v3
session_transcript
```

After the replacements above:

- `v3`, `opening_situation`, and `session_transcript` should have no matches.
- `introduction` should appear only in the Overview prohibition, if retained.
- `preamble` should appear only in the Overview prohibition and the end-of-session clarification,
  if retained.
- `recap` may remain in the Overview prohibition, returning-scene rule, and
  `## End of session recaps`. None of those creates or consumes an opening Recap field.

Inspect every match rather than deleting blindly.

## Part 2: Update `template.j2`

**What is changing:** The runtime template keeps roles, attendees, and glossary, removes the flat
Session Transcript block, and renders separately serialized Starting Context and Session
Utterances arrays.

**Why:** The application now routes and serializes these arrays before rendering the prompt. The
template must preserve their JSON exactly so the model sees the provenance boundary established by
Transcript Sections.

Keep the existing `<known_session_roles>`, `<session_attendees>`, and `<glossary>` blocks unchanged.
Delete the entire `<session_transcript>` block and replace it, in the same position, with:

```jinja2
<starting_context>
{{ starting_context }}
</starting_context>

<session_utterances>
{{ session_utterances }}
</session_utterances>
```

The application has already serialized both values as JSON arrays. Do not loop over them, apply a
JSON filter, convert them to Markdown, or add an indices field.

## Part 3: Edit `data_prompts/ledger/seed_prompt.txt`

**What is changing:** The prompt-development seed receives the same v4 task, input, process,
validity, and output semantics as the runtime system prompt.

**Why:** This seed is used to evolve or optimize the Ledger prompt. Leaving v3 Preamble rules here
would cause future prompt work to regenerate obsolete behavior even if the runtime prompt is
currently correct.

This file is the prompt-development seed corresponding to `system.md`. Apply the same semantic
changes explicitly:

1. Under `# Overview`, make the same two phrase replacements, append the Starting Context sentence,
   and add the new Session-only paragraph described in Part 1, step 1. Leave the heading and all
   other text unchanged.
2. Under `# Ledger Description`, replace only the paragraph beginning
   `A Ledger carries a small envelope` with the exact replacement from Part 1, step 2. Preserve the
   opening description and all entry-type definitions.
3. Under `# Input Description`, remove the duplicate input-count sentence, change the remaining
   count to five, replace only the Known Session Roles bullet, preserve the Attendees and Glossary
   bullets, and replace only the Session Transcript bullet with the two new input bullets and
   shared explanatory paragraphs from Part 1, step 3.
4. Replace `## Example Input` with the Starting Context and Session Utterances example above.
5. Under `# Process`, delete the two Preamble steps and individually replace or insert the five
   numbered steps exactly as described in Part 1, step 5.
6. Replace the Player-authored world facts and misstatement bullets with the exact replacements
   above.
7. Under `## Validity`, preserve the two unchanged bullets, delete the three obsolete bullets, and
   insert the three new bullets exactly as described in Part 1, step 8.
8. Under `## End of session recaps`, retain the existing sentence and append the clarification from
   Part 1, step 9.
9. Replace `# Output Format` through end-of-file with the exact v4 output section above.
10. Run the same obsolete-language search and inspect every remaining match.

Do not add the Jinja template tags to the seed prompt unless its existing format requires literal
example tags; it is prompt-development source text, not the runtime template.

## Part 4: Verify

**What is changing:** Verification now checks the v4 schema tests and inspects an exact rendered
prompt built from source-bound transcript slices.

**Why:** Unit tests prove the application contract, while rendering catches prompt-only mistakes
such as stale tags, accidental index exposure, invalid JSON placement, or recap utterances leaking
into Session Utterances.

Run:

```console
uv run pytest packages/tablesage-application/tests/session_pipeline/test_generate_ledger.py
uv run pytest packages/tablesage-application/tests/llm/test_llm_helper.py
```

Then render a real reprocessed Session whose `transcript_sections.json` matches its Role Transcript:

```console
uv run python scripts/generate_ledger_prompt.py
```

The current Ledger render script uses its configured campaign and Session constants. Inspect
`temp/generate_ledger_prompt.txt` and verify:

- `<starting_context>` and `<session_utterances>` each appear exactly once and contain JSON arrays;
- records contain only `speaker` and `text`;
- `<session_transcript>` is absent;
- recap and introduction utterances preceding `session_start_index` do not appear in Session
  Utterances;
- the overlapping boundary utterance appears in both arrays only when the section ranges require
  it; and
- the output contract contains `starting_situation` and no Preamble fields.

Return control to the implementation agent for prompt review before proceeding to Player
Introductions.
