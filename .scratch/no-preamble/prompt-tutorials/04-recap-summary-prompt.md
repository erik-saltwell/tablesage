# Tutorial: Author the Placeholder Recap Summary Prompt

## Goal and files

This prompt generates a compact, player-facing recap of the current Session from Ledger v4. It
does not reuse the recap spoken at the beginning of the recording. The application adds the
`## Recap` heading and persists the result as a standalone artifact.

This first prompt is intentionally a placeholder. It establishes only the requested one-bullet-
per-scene behavior. Final length, scene-selection policy, prose voice, and detailed Markdown
presentation remain deferred so they can be designed and optimized independently later.

Create these two new files:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_recap_summary/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_recap_summary/template.j2`

The application code is complete. The text below is ready to paste and can be reviewed one
section at a time. Because this is a new prompt, each system-prompt section is new rather than an
edit to existing prose.

## Part 1: Create `system.md`

Use these top-level headings in this exact order:

1. `# Overview`
2. `# Input Description`
3. `# Scene Rules`
4. `# Example`
5. `# Output Format`

### 1. Add `# Overview`

**What is changing:** This introduces a generator dedicated to a compact recap of the supplied
current Session.

**Why:** Recap Summary is independently reusable and independently optimizable. It must describe
the Session represented by Ledger v4, not reproduce the recording's opening recap of earlier
Sessions.

Paste:

```markdown
# Overview

Create a compact, player-facing recap of the current Session represented by the supplied Session Ledger.

Describe only what happened in this Session. Do not reproduce or reconstruct the spoken recap from the beginning of the recording, and do not recap earlier Sessions. This is an intentionally minimal placeholder prompt; do not infer additional length, selection, voice, or presentation requirements beyond the rules below.
```

### 2. Add `# Input Description`

**What is changing:** This defines the four runtime inputs in their actual order: Session
metadata, attendees and roles, glossary, and Ledger v4.

**Why:** The Ledger is the sole evidence for events. The other inputs help interpret names and
terms but must never introduce events or facts that the Ledger does not contain.

Paste:

```markdown
# Input Description

You will be provided with four inputs:

- `<session_metadata>`: the campaign name, game system when known, and Session date when known. Use this only for orientation; it cannot establish an event or fact.
- `<session_attendees>`: each human attendee followed by zero or more roles played in this Session. Use this only to interpret player and character names already present in the Session Ledger.
- `<glossary>`: campaign terms with optional descriptions. Use this only to recognize and spell terms already present in the Session Ledger. It cannot establish an event or fact.
- `<session_ledger>`: the complete canonical Ledger v4 for the current Session. This is the sole source for claims about what happened.

Do not treat Session metadata, attendee mappings, or glossary descriptions as evidence that something occurred. Do not add events, outcomes, motivations, or connections that are absent from the Session Ledger.
```

### 3. Add `# Scene Rules`

**What is changing:** This adds the complete placeholder generation policy as exactly three
bullets.

**Why:** The initial behavior requested is deliberately narrow: one compact bullet per scene,
with a scene description and a one-sentence account. More nuanced decisions remain deferred.

Paste this section exactly; do not add more bullets:

```markdown
# Scene Rules

- Produce exactly one output bullet for each scene represented in the Session Ledger.
- Give each bullet a short description of the scene.
- Follow the scene description with one sentence summarizing what happened in that scene.
```

### 4. Add `# Example`

**What is changing:** This demonstrates two scenes with exactly one output bullet for each.

**Why:** The example makes the flat one-bullet-per-scene shape concrete without deciding a final
voice, length target, or richer formatting convention.

Paste:

```markdown
# Example

For a Session Ledger containing one scene at a city gate and one scene in a council chamber, a valid response is:

- At the city gate. The party persuaded the watch captain to let them enter after presenting the recovered seal.
- In the council chamber. The council accepted the party's warning and agreed to evacuate the riverside district.
```

### 5. Add `# Output Format`

**What is changing:** This limits the model response to flat Markdown bullet content and makes
the application, rather than the model, responsible for the section heading.

**Why:** The same persisted section will be usable by itself and inserted deterministically into
the full Summary. Preventing headings and wrappers avoids duplicate `## Recap` sections and
composition cleanup.

Paste:

```markdown
# Output Format

Return only a flat sequence of Markdown bullets. Every bullet must begin with `- `.

Do not include a title, a `## Recap` heading, nested bullets, opening-preamble text, commentary, or a Markdown code fence. The application adds the `## Recap` heading deterministically.
```

Do not add final length limits, rules for selecting or combining scenes, a prescribed narrative
voice, or Markdown styling beyond the flat bullets required above. Those decisions are explicitly
deferred.

## Part 2: Create `template.j2`

**What is changing:** This template supplies full Session context followed by the complete
canonical Ledger v4. Its four tags use the same order as the full Summary template.

**Why:** Keeping the structural input format consistent reduces accidental differences between
the Recap and full Summary generators, while their independent system prompts allow their
behavior to evolve separately. Placing the Ledger in its own final tag reinforces its role as the
sole event source.

Copy the structural loops—not the prose—from
`packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/template.j2`.
The complete file should be:

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

<session_ledger>
{{ ledger }}
</session_ledger>
```

Do not add the Role Transcript, Transcript Sections, spoken Recap Range, Player Introductions, or
existing full Summary. The application passes the complete serialized Ledger v4 through
`ledger`; render it directly rather than looping over or reshaping its fields.

## Part 3: Verify

**What is changing:** Verification checks the dedicated generation contract, deterministic
heading ownership, artifact persistence, and a rendered prompt from a real Ledger v4.

**Why:** Unit tests catch empty output, wrong model/input routing, normalization, invalidation, and
atomic-write errors. Rendering catches missing resources, tag-order mistakes, and accidental
inputs that do not belong in this prompt.

After creating both files, run:

```console
uv run pytest packages/tablesage-application/tests/session_pipeline/test_generate_recap_summary.py
```

Then render a reprocessed Session that has a Ledger v4:

```console
uv run python scripts/generate_recap_summary_prompt.py "Your Campaign Name" 001
```

Inspect `temp/generate_recap_summary_prompt.txt` and verify:

- tags occur once each in this order: `<session_metadata>`, `<session_attendees>`, `<glossary>`,
  `<session_ledger>`;
- `<session_ledger>` contains the complete Ledger v4 JSON, including `starting_situation` and
  current-Session `utterances`;
- no Role Transcript, Transcript Sections, spoken Recap Range, Player Introductions, or existing
  Summary appears;
- attendee roles and glossary spellings render correctly, including empty optional values; and
- the system prompt requests bullet content but does not ask the model to emit `## Recap`.

Do not call the live LLM yet. Return control to the implementation agent for prompt review and a
prompt-loader regression test before proceeding to deterministic full Summary composition.
