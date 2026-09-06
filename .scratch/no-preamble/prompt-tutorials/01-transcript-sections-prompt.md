# Tutorial: Author the Transcript Sections Prompt

## Goal

You are adding the first prompt in the new output pipeline. Its only job is to locate the opening
recap, opening player-character introductions, the evidence for the immediate starting situation,
and the point where active play begins. It must return indices into `role_transcript.json`; it must
not summarize the transcript or decide which material after active play is Ledger-worthy.

The application code and response schema are already implemented. You will create exactly these
two prompt files:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/section_transcript/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/section_transcript/template.j2`

Do not edit `PromptName`, the Pydantic response model, or the pipeline module while following this
tutorial. Those pieces are already wired to the `section_transcript` directory.

## Part 1: Write `system.md`

Create the directory `section_transcript`, then create `system.md`. Use the following top-level
sections in exactly this order. The placement matters because the prompt should move from purpose,
to input semantics, to definitions, to decision rules, to procedure, to examples, and finally to
the response contract.

### 1. Add `# Overview` as the first section

In the opening paragraph, identify the input as the opening portion of a tabletop roleplaying
Session transcript and define the task as locating section boundaries. Explicitly state all three
negative constraints in this same section:

- do not summarize or rewrite transcript content;
- do not determine what belongs in the Ledger; and
- do not remove rules discussion, breaks, jokes, or chatter after active play starts.

End the section by saying that the returned indices route source utterances to separate downstream
generators. This gives the model a reason to preserve boundaries rather than paraphrasing content.

### 2. Add `# Input Description` immediately after Overview

Make this section a two-item bullet list in this exact order:

1. The first bullet must name `<session_attendees>`. Explain that each line maps a player name to
   zero or more Session roles, and that these mappings are authoritative for distinguishing
   player-character roles from NPCs. A role is not a player character merely because it speaks in
   the transcript.
2. The second bullet must name `<role_transcript>`. Explain that its value is JSON with an ordered
   `utterances` array and that every utterance has exactly `index`, `speaker`, and `text`. State
   that `index` is zero-based and is the value the response must reference.

Do not mention campaign metadata or a glossary. Neither is supplied to this pass.

### 3. Add `# Section Definitions` after Input Description

Add these four second-level subsections in exactly this order.

#### `## Recap Range`

Define this as an explicitly framed account of events from earlier Sessions or earlier campaign
history that is spoken at the opening. Say that ordinary reminders during active play do not count.
The value is the smallest inclusive range containing that opening recap, or `null` when no recap is
present.

#### `## Introduction Range`

Define this as explicit opening-preamble introductions of player-character roles listed in
`<session_attendees>`. Exclude NPC descriptions, Game Master self-introductions, inferred profiles,
and character facts first revealed after active play begins. Explain that when introductions are
interleaved with recap utterances, the range may be the smallest enclosing range and may therefore
contain intervening recap material. The value is `null` when no qualifying introduction is present.

#### `## Starting Context Range`

Define this as the minimum inclusive range containing enough direct transcript evidence to state
the immediate situation in which the players begin this Session. It may overlap the tail of the
recap or the transition into active play. Tell the model to return `null` only when the transcript
does not support any starting situation; the application will stop downstream generation in that
case rather than inventing one.

Be clear that this is evidence for one starting-situation statement, not a request to classify the
entire session setup or recap.

#### `## Session Start Index`

Define this as the index of the first utterance belonging to active play in the current Session.
Explain that opening recap and introductions normally precede it, while scene-setting that begins
the present action may overlap the starting context. If the recording establishes a starting
situation but contains no subsequent active play, instruct the model to return the utterance count,
which is one greater than the final utterance index.

### 4. Add `# Boundary Rules` after Section Definitions

The first bullet under this heading must say that ambiguous boundary material goes on the Session
side: choose the earlier plausible `session_start_index` so current-session content is not lost.
Then add bullets covering each of these rules:

- the three ranges may overlap;
- one mixed utterance may belong to more than one range and may also be the Session start;
- classify only the opening structure needed to find the active-play boundary;
- once active play starts, do not classify, exclude, or skip later rules talk, breaks, jokes, or
  chatter—the Session input is the complete suffix from `session_start_index`; and
- range endpoints must point at real utterances, while `session_start_index` may additionally equal
  the utterance count.

Keep the ambiguity rule first. It encodes the design's most important loss-avoidance bias.

### 5. Add `# Process` after Boundary Rules

Use an ordered list. Tell the model to perform these steps in order:

1. Read the complete attendees mapping and complete transcript before choosing any boundary.
2. Locate the earliest defensible beginning of current-session active play.
3. Locate the minimum evidence for the immediate starting situation.
4. Locate any opening recap span.
5. Locate any qualifying player-character introduction span, using attendee roles as the
   eligibility test.
6. Check every endpoint against the transcript and emit the indices.

Do not add a content-selection or summarization step.

### 6. Add `# Examples` immediately before Output Format

Include at least four compact examples. Each example should show a short indexed input and the four
routing values. Keep prose outside the JSON response so the examples do not imply extra output
fields. Cover these cases:

1. **No preamble:** active play begins at index `0`; recap and introduction ranges are `null`;
   starting context points to the scene-setting evidence at or after index `0`.
2. **Recap followed by introductions:** recap and introduction ranges are separate, starting
   context selects the immediate scene setup, and Session start follows the preamble.
3. **Interleaved recap and introductions:** Introduction Range encloses qualifying introduction
   utterances even though recap material appears between them; overlapping ranges are acceptable.
4. **Mixed transition utterance:** one utterance finishes recap material and begins present action;
   show it as the recap endpoint, part of Starting Context, and the Session Start Index.

Every example response must contain `scratchpad`, `recap_range`, `introduction_range`,
`starting_context_range`, and `session_start_index`. Use objects shaped like
`{"start_index": 2, "end_index": 4}` for non-null ranges. Do not add confidence scores, labels,
extracted text, summaries, or arrays of disjoint ranges—the code will reject extra fields.

### 7. Add `# Output Format` as the final section

Require exactly one JSON object conforming to the supplied structured-output schema, with no
Markdown fence and no prose before or after it. Explain each response field:

- `scratchpad`: brief reasoning used to check boundaries; this is not persisted;
- `recap_range`: an inclusive range object or `null`;
- `introduction_range`: an inclusive range object or `null`;
- `starting_context_range`: an inclusive range object or `null`; and
- `session_start_index`: one zero-based index, or the utterance count for setup-only input.

State explicitly that all four routing keys must always be present even when a range is `null`, and
that all range endpoints are zero-based and inclusive. There are four routing keys because
`scratchpad` is diagnostic reasoning, not routing metadata.

## Part 2: Write `template.j2`

Create `template.j2` beside `system.md`. It must contain exactly two XML-style blocks in this order.

First, add the attendee block. Copy the attendee loop behavior from the existing Ledger template,
but use only this block—do not copy the Ledger's known-role or glossary blocks:

```jinja2
<session_attendees>
{% for attendee in attendees %}- {{ attendee.player_name }}{% if attendee.roles %}: {{ attendee.roles | join(", ") }}{% endif %}
{% endfor %}</session_attendees>
```

This renders an attendee with no roles as `- Player Name` and an attendee with roles as
`- Player Name: Role One, Role Two`.

Immediately after it, add the Role Transcript block:

```jinja2
<role_transcript>
{{ role_transcript }}
</role_transcript>
```

The application has already serialized `role_transcript` as compact JSON. Insert it directly; do
not loop over utterances, renumber them, reformat them as Markdown, or apply a JSON filter.

The finished template must not contain `<known_session_roles>`, `<glossary>`, campaign name, game
system, Session date, or any other metadata.

## Part 3: Verify your prompt

From the repository root, first run the Transcript Sections tests:

```console
uv run pytest packages/tablesage-application/tests/session_pipeline/test_transcript_sections.py
```

Then render the prompt against a reprocessed Session that already has the new compact
`role_transcript.json`:

```console
uv run python scripts/generate_transcript_sections_prompt.py "Your Campaign Name" 001
```

Open `temp/generate_transcript_sections_prompt.txt` and verify:

- the system prompt headings appear in the required order;
- there is exactly one opening and closing tag for each of `<session_attendees>` and
  `<role_transcript>`;
- the transcript is valid JSON and its indices are unchanged, zero-based, and contiguous;
- attendee roles are readable and attendees without roles do not show `None` or empty brackets;
- no glossary or campaign metadata appears; and
- the examples agree with the inclusive-range and Session-side ambiguity rules.

Do not call the live LLM yet. Once these checks pass, return control to the implementation agent so
the prompt can be reviewed and the next code slice—Ledger v4—can begin.
