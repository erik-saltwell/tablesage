# Tutorial: Convert the Full Summary Prompt to Marker Composition

## Goal and files

The full Summary LLM should continue generating its detailed, forward-looking Session notes from
Ledger v4 and Session context. It should no longer generate the Recap or Player Character
Introductions. Instead, it must reserve two exact locations near the top of its Markdown output:

1. `<!-- RECAP -->`
2. `<!-- PLAYER_INTRODUCTIONS -->`

After the model returns a valid template, the application loads the previous Session's completed
Recap sidecar and the current Session's Player Introductions sidecar, then replaces the markers
deterministically. For the campaign's first Session, the Recap marker is removed without adding a
Recap. This keeps all three prompts independently optimizable and prevents Recap or Introduction
text from being sent back through the full Summary model.

Edit these files:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/system.md`
- `data_prompts/summary/seed_prompt.txt`

Inspect but do not change:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/template.j2`

The instructions below change only obsolete Ledger-v3 and composition behavior. Preserve all
other Summary selection, reincorporation, tone, length, and section rules.

## Part 1: Update the runtime `system.md`

### 1. Update the Ledger field description under `# Input Description`

**What is changing:** The top-level Ledger schema changes from v3's optional `preamble` to v4's
required `starting_situation`. The description of `utterances` remains in place.

**Why:** The full Summary receives only current-Session Ledger v4. Prior-session Recap and Player
Introductions now come from independent artifacts during deterministic composition.

Under `# Input Description`, inside the `<session_ledger>` bullet, find the paragraph beginning:

> Its top-level fields are `version`, `session_id`, `session_name`...

Replace that paragraph and the complete following `preamble` bullet with:

```markdown
  Its top-level fields are `version`, `session_id`, `session_name`, `attendees` (this Session's
  roster — the same information as `<session_attendees>`, redundantly present inside the
  Ledger itself), required `starting_situation`, and `utterances`.
  - `starting_situation` is a non-empty description of the immediate situation in which the
    players begin this Session. Use it to orient the Starting Situation section without adding
    prior history that is absent from Ledger v4.
```

Leave the existing `- utterances is the ordered record...` bullet immediately after this new
`starting_situation` bullet.

### 2. Replace the Ledger JSON under `## Example Input`

**What is changing:** The example becomes Ledger v4, removes the complete `preamble` object, and
adds a current-Session `starting_situation`.

**Why:** Examples strongly steer schema interpretation. Leaving any v3 Preamble example would
encourage the model to invent prior history or generate content now owned by sidecars.

Under `## Example Input`, keep all four surrounding XML-style input tags and replace only the
complete JSON object between `<session_ledger>` and `</session_ledger>` with:

```json
{
  "version": 4,
  "session_id": "3f6a2e6e-6c1a-4b6a-9c2e-2f7b6a2e6e6c",
  "session_name": "The Gorge",
  "attendees": [
    {"player_name": "Alice", "roles": ["Game Master"]},
    {"player_name": "Bob", "roles": ["Kestrel"]},
    {"player_name": "Carol", "roles": ["Thorn"]}
  ],
  "starting_situation": "The party reaches the gorge to find the rope bridge cut from the far side.",
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
      "type": "action",
      "source": "Game Master",
      "entity": "A Warden's rider",
      "action": "Appears on the ridge behind the party."
    },
    {
      "type": "expression",
      "source": "Game Master",
      "entity": "The Warden's rider",
      "sentiment": "Hesitates at the sight of the party, visibly unsure whether to pursue."
    },
    {
      "type": "question",
      "asker": "Carol",
      "question": "How deep is the gorge — is it climbable?",
      "resolver": "Alice",
      "resolution": "Around sixty feet, with ledges enough to climb down."
    }
  ]
}
```

### 3. Update `## Example Output`

**What is changing:** The example gains both exact insertion markers immediately below its title,
and its Starting Situation contains only the immediate current-Session state.

**Why:** Marker placement is a machine-validated output contract. Removing the earlier-campaign
bullets also demonstrates that the detailed Summary cannot reconstruct the spoken opening recap.

Under `## Example Output`, inside the fenced example, find the title:

```markdown
**Ashmoor — The Gorge (2026-03-02)**
```

Immediately after the blank line following that title, add these two markers, each on its own line
and separated by a blank line:

```markdown
<!-- RECAP -->

<!-- PLAYER_INTRODUCTIONS -->
```

Then replace the complete contents of the example's `## Starting Situation` section with:

```markdown
## Starting Situation
- The party reached the gorge to find the rope bridge cut from the far side.
```

Leave `## Scene Breakdown` and all later example sections unchanged.

### 4. Update `## Core Principle: Reincorporation`

**What is changing:** Evidence tracing refers only to Ledger v4.

**Why:** The Preamble is no longer part of the Ledger or an input to this LLM call.

Under `## Core Principle: Reincorporation`, find the sentence beginning `Every bullet must trace`.
Change only its first sentence from:

```markdown
Every bullet must trace to a specific Ledger or preamble entry.
```

to:

```markdown
Every bullet must trace to a specific Ledger field or utterance.
```

Keep the rest of that paragraph unchanged.

### 5. Update `## Player Knowledge Boundary`

**What is changing:** Player-visible evidence is defined exclusively by Ledger v4 rather than by
the Ledger plus Preamble.

**Why:** The detailed Summary model must not infer information from Recap or Player Introduction
sidecars, which it never receives.

Under `## Player Knowledge Boundary`, replace its first two sentences—from `This summary is read
by players.` through `including scenes only some characters were present for.`—with:

```markdown
This summary is read by players. Everything in Ledger v4 was seen or heard at the table during
this Session and is eligible, including scenes only some characters were present for.
```

Leave the following glossary paragraph beginning `The glossary is different` unchanged.

### 6. Delete `### The Party`

**What is changing:** The full Summary model no longer generates a Player Character section.

**Why:** The application renders `player_introductions.json` deterministically at the Player
Introductions marker. Asking the model to create the same material would duplicate it.

Under `## Output Sections`, delete the complete subsection beginning `### The Party`, including
its explanatory paragraph. After deletion, `### Starting Situation` must be the first subsection
under `## Output Sections`.

### 7. Update `### Starting Situation`

**What is changing:** The section is sourced only from Ledger v4's required
`starting_situation`.

**Why:** Prior events belong in the separately generated Recap. Falling back to early utterances
or old Preamble fields would reintroduce duplication and obsolete schema assumptions.

Under `### Starting Situation`, keep the first sentence ending `Up to 4 bullets.` Delete the
remaining sentences that mention `preamble.recap.events`, `opening_situation`, the Preamble being
absent, or the first few utterances. Immediately after the retained sentence, add:

```markdown
Render only Ledger v4's required `starting_situation`; do not add prior history from outside it.
```

The resulting subsection should read:

```markdown
### Starting Situation
Answers: where did things stand when the session opened — the team's immediate situation,
goal, and context? Up to 4 bullets. Render only Ledger v4's required `starting_situation`;
do not add prior history from outside it.
```

### 8. Replace the section-order paragraph under `# Output Format`

**What is changing:** Two mandatory markers now follow the title, and the model-generated `##`
sections begin with Starting Situation rather than The Party.

**Why:** The application requires each marker exactly once and in this order before it will load
or insert either sidecar.

Under `# Output Format`, leave the title rule unchanged. Replace the complete paragraph beginning
`Then render these ## sections` with:

```markdown
Immediately after the title and its following blank line, output these exact markers once each,
on their own lines and in this order, with a blank line between them:
<!-- RECAP -->

<!-- PLAYER_INTRODUCTIONS -->
Both markers are required even when no previous Session or no Player Introductions exist; the
application removes a marker whose insertion is empty.

Then render these `##` sections, with these exact titles, in this order, omitting any section with
nothing that qualifies: Starting Situation, Scene Breakdown, Key Decisions & Events, Ending
Situation, Open Loops, Clocks. Under Scene Breakdown each scene title is a `###`.
```

In the first sentence of `# Output Format`, replace `no preamble` with `no introductory
explanation`, so it reads:

```markdown
Output only the Markdown summary — no introductory explanation and no code fences.
```

### 9. Update `## Final Check`

**What is changing:** The checklist traces claims to Ledger v4 and explicitly verifies the marker
contract.

**Why:** The model's final self-check should mirror the validation that the application performs.

Under `## Final Check`, change the first bullet's opening from:

```markdown
- Every bullet passes the reincorporation test and traces to a Ledger or preamble entry;
```

to:

```markdown
- Every bullet passes the reincorporation test and traces to a Ledger field or utterance;
```

Keep the continuation of that bullet unchanged. Immediately before the final `Total length is at
most 700 words` bullet, add:

```markdown
- Both exact insertion markers appear once, in Recap-then-Player-Introductions order.
```

The existing section-title validation should refer only to the section titles listed in the newly
updated Output Format. Do not add The Party to it.

### 10. Remove all obsolete terminology

**What is changing:** This catches stale schema or model-owned composition rules missed by the
targeted edits.

**Why:** Even one contradictory instruction or example can steer the model back toward Ledger v3.

Search the entire runtime `system.md`, case-insensitively, for each of these strings:

- `preamble`
- `character_introductions`
- `opening_situation`
- `The Party`

There should be no matches after the edits. Do not remove `starting_situation`, `## Starting
Situation`, or ordinary prose that refers to the player characters individually.

## Part 2: Update `data_prompts/summary/seed_prompt.txt`

**What is changing:** The optimization seed receives the same Ledger-v4 and marker-composition
contract as the runtime prompt.

**Why:** Optimizing an obsolete v3 prompt could later overwrite or regress the correct runtime
behavior.

Repeat runtime Steps 1–7 and Step 10 in `data_prompts/summary/seed_prompt.txt`, using the same exact
anchors and replacement text. The Seed prompt currently differs in two nearby places, so apply
Steps 8 and 9 as follows.

### Seed-specific Output Format edit

Under `# Output Format`, leave the title rule unchanged. Replace the complete paragraph beginning
`Then render all of these ## sections` with:

```markdown
Immediately after the title and its following blank line, output these exact markers once each,
on their own lines and in this order, with a blank line between them:
<!-- RECAP -->

<!-- PLAYER_INTRODUCTIONS -->
Both markers are required even when no previous Session or no Player Introductions exist; the
application removes a marker whose insertion is empty.

Then render all of these `##` sections, with these exact titles, in this order: Starting Situation,
Scene Breakdown, Key Decisions & Events, Ending Situation, Open Loops, Clocks. Under Scene
Breakdown each scene title is a `###`. When a section has no qualifying content, render exactly one
bullet: `- None.`
```

Also replace the first sentence of Seed `# Output Format` with:

```markdown
Output only the Markdown summary — no introductory explanation and no code fences.
```

### Seed-specific Final Check edit

Apply the same two exact Final Check changes from runtime Step 9:

1. Change `traces to a Ledger or preamble entry` to `traces to a Ledger field or utterance` in the
   first bullet.
2. Immediately before the final `Total length is at most 700 words` bullet, add:

```markdown
- Both exact insertion markers appear once, in Recap-then-Player-Introductions order.
```

Do not otherwise make the runtime and Seed prompts identical as part of this tutorial. Preserve
their existing unrelated difference about omitting empty detailed sections versus rendering
`- None.`.

## Part 3: Inspect `template.j2` without changing it

**What is changing:** Nothing in this file.

**Why:** The existing template already passes exactly the four permitted inputs in the correct
order: Session metadata, attendees, glossary, and Ledger. Passing Recap Summary or Player
Introductions into this template would defeat independent generation and deterministic
composition.

Open
`packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/template.j2`
and confirm it still contains exactly these top-level tags in order:

1. `<session_metadata>`
2. `<session_attendees>`
3. `<glossary>`
4. `<session_ledger>`

Do not add Recap, Player Introductions, Role Transcript, or Transcript Sections tags.

## Part 4: Verify

**What is changing:** Verification checks both prompt copies, the unchanged input boundary, marker
validation, sidecar loading order, composition, and atomic preservation.

**Why:** The Summary is replaced only after every LLM, sidecar, and composition check succeeds.
The previous Session's Recap is required when a previous Session exists, while the first Session
validly omits it. The checks below catch obsolete schema language and accidental sidecar input
before a live call.

First run these searches; each command should produce no output:

```console
rg -ni 'preamble|character_introductions|opening_situation|The Party' packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/system.md
rg -ni 'preamble|character_introductions|opening_situation|The Party' data_prompts/summary/seed_prompt.txt
```

Confirm both prompts contain each marker literally:

```console
rg -n '<!-- RECAP -->|<!-- PLAYER_INTRODUCTIONS -->' packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/system.md data_prompts/summary/seed_prompt.txt
```

Each file should have two matches in `## Example Output`, two in `# Output Format`, and marker
language in `## Final Check`.

Run the focused tests:

```console
uv run pytest packages/tablesage-application/tests/session_pipeline/test_generate_summary.py
```

Do not call the live LLM yet. Return control to the implementation agent for prompt review and
prompt-loader assertions before proceeding to six-phase Generate Outputs orchestration.
