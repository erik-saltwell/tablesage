# Implementation Plan — Transcript Sectioning and Session-Scoped Outputs

## Objective

Implement the pipeline described in
[Transcript Sectioning and Session-Scoped Outputs](../../.documentation/transcript_sectioning_and_session_scoped_outputs.md):

```text
Reviewed Transcript
  → compact indexed Role Transcript
  → Transcript Sections
  → Ledger v4
  → Player Introductions
  → Recap Summary
  → marker-bearing full Summary
  → deterministically composed Summary
```

The implementation covers the codebase, schemas, orchestration, tests, prompt-development tools,
and supporting documentation. The user owns every edit to prompt text.

## Responsibility boundary

The implementation agent may:

- add or change Python code, Pydantic models, artifact definitions, tests, scripts, and domain
  documentation;
- add `PromptName` enum members and code that expects new prompt packages;
- create detailed prompt-editing tutorials; and
- verify prompt files after the user changes them.

The implementation agent must not:

- create or edit any `_prompts/<name>/system.md` file;
- create or edit any `_prompts/<name>/template.j2` file; or
- directly revise prompt seed text under `data_prompts/*/seed_prompt.txt`.

Each prompt change is therefore represented below by a tutorial work item. The tutorial must tell
the user the exact file, heading, paragraph, bullet, example, or template block to add, replace, or
delete. After writing a tutorial, the agent pauses that prompt-dependent branch until the user has
made the described edits.

## Work item 1 — Introduce the compact Role Transcript schema

**Owner:** implementation agent  
**Prompt edits:** none

1. Add application-layer `RoleTranscript` and `RoleTranscriptUtterance` models. Keep the generic
   word-level `tablesage_tools.model.Transcript` unchanged because it remains the machine and
   reviewed transcript representation.
2. Give each Role Transcript utterance exactly three persisted fields:
   - `index`: contiguous, zero-based position;
   - `speaker`: the resolved Session role, fallback player name, or `Unassigned Speaker`;
   - `text`: punctuated text when available, otherwise reconstructed raw text.
3. Make the models reject extra fields and validate contiguous indices beginning at zero.
4. Change `clean_transcript.clean_transcript()` to convert its cleaned, role-assigned generic
   Transcript into the compact Role Transcript before atomically replacing
   `role_transcript.json`.
5. Replace `render_role_transcript_text()` internals so existing glossary extraction continues to
   receive role-attributed Markdown from the compact schema.
6. Update `scripts/role_transcript_to_markdown.py` and every test or fixture that currently loads
   `role_transcript.json` through the generic `Transcript` model.
7. Do not add a compatibility reader. Re-running Generate Outputs recreates the artifact.

**Tests:** compact serialization and loading, contiguous-index rejection, punctuated/raw fallback,
role mapping, unassigned-speaker preservation, Markdown rendering, and downstream glossary input.

## Work item 2 — Implement Transcript Sections models and slicing

**Owner:** implementation agent  
**Prompt dependency:** Work item 3

1. Add `ArtifactName.TRANSCRIPT_SECTIONS` in `paths.py` as hidden
   `transcript_sections.json`, categorized as derived from the Role Transcript.
2. Add a `session_pipeline/transcript_sections.py` module containing:
   - a strict inclusive range model with `start_index` and `end_index`;
   - a structured LLM response containing `scratchpad`, nullable `recap_range`, nullable
     `introduction_range`, nullable `starting_context_range`, and `session_start_index`;
   - a persisted envelope containing `version`, a SHA-256 fingerprint of the exact source
     `role_transcript.json` bytes, and the four routing fields; and
   - compact downstream utterance records containing only `speaker` and `text`.
3. Validate every non-null range against the Role Transcript's utterance indices, with inclusive
   endpoints and `start_index <= end_index`. Permit all ranges to overlap.
4. Validate `0 <= session_start_index <= utterance_count`. The terminal value represents a
   Session with setup but no subsequent active-play utterances.
5. Treat `starting_context_range: null` as a valid model response but a generation failure: no
   downstream Ledger call may occur because a required starting situation would have no source.
6. Add pure slicing functions that:
   - select `starting_context_range` into a compact `starting_context` array;
   - select the complete suffix from `session_start_index` into `session_utterances`;
   - select `introduction_range` into the Player Introductions input; and
   - strip source indices from every downstream record.
7. Add generation orchestration using `PromptName.SECTION_TRANSCRIPT`, `llm_model_high`, and the
   attendee-to-role mapping. Attempt up to three structurally invalid or out-of-bounds responses;
   provider/configuration failures fail immediately.
8. Persist only a validated result, using temp-file replacement. Do not copy transcript text into
   the persisted artifact.

**Tests:** null ranges, valid inclusive endpoints, out-of-bounds and reversed ranges, overlapping
ranges, mixed boundary utterances, no preamble, ambiguous early Session inclusion, terminal Session
start, absent starting context, source fingerprint, retries, and atomic replacement.

## Work item 3 — Create a tutorial for authoring the Transcript Sections prompt

**Owner:** implementation agent writes the tutorial; user edits the prompt  
**Tutorial path:** `.scratch/no-preamble/prompt-tutorials/01-transcript-sections-prompt.md`

The tutorial must direct the user to create both:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/section_transcript/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/section_transcript/template.j2`

The tutorial must specify this exact `system.md` structure:

1. Create `# Overview` first. Define the task as locating opening sections and the active-play
   boundary, not summarizing, rewriting, or deciding which post-start content belongs in a Ledger.
2. Add `# Input Description` immediately after Overview. Its first bullet describes
   `<session_attendees>` and says role mappings distinguish player characters from NPCs. Its second
   bullet describes `<role_transcript>` as indexed JSON utterances with `index`, `speaker`, and
   `text`.
3. Add `# Section Definitions` after Input Description, with these subsections in order:
   - `## Recap Range`: explicitly framed prior-session recap; nullable.
   - `## Introduction Range`: only opening-preamble introductions of attendee player-character
     roles; nullable; may be the smallest enclosing range containing intervening material.
   - `## Starting Context Range`: the minimum evidence needed to state the immediate opening
     situation; nullable only when no supported starting situation exists.
   - `## Session Start Index`: the first active-play utterance, or the utterance count when setup
     exists but play never proceeds.
4. Add `# Boundary Rules` after Section Definitions. Make its first bullet say ambiguous material
   is included on the Session side. Add later bullets saying ranges may overlap, a mixed utterance
   may belong to multiple ranges, only opening structure is classified, and nothing after Session
   start is filtered for rules talk, breaks, or chatter.
5. Add `# Process` after Boundary Rules. Require reading the complete input, locating active play,
   locating the minimum starting context, then locating recap and introduction spans before
   emitting indices.
6. Add `# Output Format` last. Require one schema-conforming JSON object, no Markdown fences, and
   all four routing keys even when a range is `null`. Explain that endpoints are zero-based and
   inclusive.
7. Include at least four examples under `# Examples`, placed immediately before Output Format:
   no preamble, recap then introductions, interleaved recap/introductions, and a single utterance
   containing recap plus the transition into play.

For `template.j2`, the tutorial must tell the user to:

1. Render `<session_attendees>` first, one `- Player: role, role` line per attendee using the same
   loop and empty-role behavior as the existing Ledger template.
2. Render `<role_transcript>` second.
3. Place the already serialized compact Role Transcript JSON variable inside that tag without
   reformatting or converting it to Markdown.
4. Add no glossary or campaign-metadata tags because those inputs were explicitly excluded from
   sectioning.

The tutorial ends with verification instructions to run the Transcript Sections unit tests and a
prompt-render script added by Work item 13, then inspect the rendered prompt for exact indices and
strict tag balance.

## Work item 4 — Implement Ledger v4 code and rendering

**Owner:** implementation agent  
**Prompt dependency:** Work item 5

1. Replace `version: Literal[3]` with `Literal[4]` in the persisted Ledger.
2. Delete `Recap`, `CharacterIntroduction`, and `Preamble` from the Ledger module and remove their
   fields and validators from both persisted and generation-response models.
3. Add required, trimmed, non-empty `starting_situation` to `Ledger` and
   `LedgerGenerationResponse`. Permit an empty regular-utterance list when this field is valid.
4. Change `LedgerPromptData` to carry separately serialized `starting_context` and
   `session_utterances` arrays instead of the complete transcript.
5. Keep attendees, known roles, glossary, all six existing utterance types, attribution warnings,
   structured retries, and candidate selection behavior.
6. Remove Character Introduction warning logic from Ledger generation.
7. Change `Application.generate_ledger()` to verify the Transcript Sections fingerprint, slice the
   compact Role Transcript, and supply the two labeled inputs. Inject version, Session identity,
   and attendees after generation as today.
8. Change `Ledger.to_markdown()` to render `## Starting Situation` before `## Session`; remove the
   Recap and Characters sections.
9. Create `.documentation/canonical_ledger_format_v4.md`, update `.documentation/generate_ledger.md`,
   and redirect current pipeline references from v3 to v4. Retain the v3 document only as historical
   documentation.

**Tests:** v4 round-trip, forbidden preamble, required starting situation, empty utterances,
starting-context/session-suffix prompt data, no prior recap leakage, Markdown rendering, warnings,
retry selection, application metadata injection, stale fingerprint rejection, replacement, and
downstream invalidation.

## Work item 5 — Create a tutorial for converting the Ledger prompt to v4

**Owner:** implementation agent writes the tutorial; user edits the prompt  
**Tutorial path:** `.scratch/no-preamble/prompt-tutorials/02-ledger-v4-prompt.md`

The tutorial must cover these files:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_ledger/template.j2`
- `data_prompts/ledger/seed_prompt.txt`

For `system.md`, give the user these exact edit locations:

1. Under `# Overview`, replace “Ledger Format v3” with “Ledger Format v4”.
2. Under `# Ledger Description`, replace the paragraph beginning “A Ledger carries a small
   envelope” so it lists a required `starting_situation` followed by current-session utterances
   and contains no Preamble language.
3. Under `# Input Description`, delete both consecutive “You will be provided...” lines and add
   one correct line introducing five inputs.
4. In that same section, delete the entire `<session_transcript>` bullet and its nested bullets.
   In its position, add `<starting_context>` and `<session_utterances>` bullets. State that both are
   compact JSON arrays of `{speaker, text}` records; starting context may establish only
   `starting_situation`, while only session utterances may generate regular entries.
5. Under `## Example Input`, replace the complete `<session_transcript>` block with separate
   `<starting_context>` and `<session_utterances>` JSON examples. Include one starting-context
   utterance that describes the party's immediate state and repeat it in session utterances only
   when demonstrating an overlapping mixed boundary.
6. Under `# Process`, delete the steps named “Identify the preamble” and “Emit the preamble.” Add a
   new step immediately after “Read the entire transcript...” requiring one concise
   `starting_situation` derived only from `<starting_context>`. Change the walking step to name
   `<session_utterances>` explicitly.
7. Under `## Attribution`, find the Player-authored world facts bullet and delete its last sentence,
   “Shared party backstory is not this case; it goes to the recap (see Preamble).” Replace it with
   a sentence saying prior shared backstory is outside the supplied Session utterances.
8. Under `## Condensation and fidelity`, replace the bullet that says to prefer facts established
   “in the introductions or earlier entries”; it may refer only to the starting situation and
   earlier entries.
9. Under `## Validity`, delete the three bullets about one introduction per character, recap event
   order, and content existing in recap/introduction/entries. Add a new first bullet requiring a
   non-empty `starting_situation` supported by `<starting_context>`, and a second bullet permitting
   an empty `utterances` array.
10. Under `# Output Format` → `## Top Level Fields`, replace `preamble` with
    `starting_situation`. Under that same heading, delete the entire `### Preamble` subsection.
11. Under `## Example Response`, replace the whole example object so its top-level order is
    `scratchpad`, `starting_situation`, `utterances`; remove every recap/introduction field and the
    closing note about duplicated opening narration.
12. Search the full file case-insensitively for `preamble`, `recap`, `introduction`,
    `opening_situation`, and `v3`; inspect every remaining match and remove any obsolete reference.
    Preserve `## End of session recaps`, which concerns recap speech occurring after active play
    begins.

For `template.j2`, instruct the user to leave the roles, attendees, and glossary blocks in place;
delete the entire `<session_transcript>` block; then add `<starting_context>` followed immediately
by `<session_utterances>`, each containing its matching pre-serialized JSON variable.

Finally, instruct the user to apply the same `system.md` semantic changes to
`data_prompts/ledger/seed_prompt.txt`. Do not say “keep it in sync”; enumerate the same affected
headings in the tutorial and verify that the seed prompt has no obsolete v3 Preamble language.

## Work item 6 — Implement Player Introductions generation

**Owner:** implementation agent  
**Prompt dependency:** Work item 7

1. Add `ArtifactName.PLAYER_INTRODUCTIONS` as hidden `player_introductions.json`, derived from the
   Role Transcript.
2. Add `session_pipeline/generate_player_introductions.py` with strict models for:
   - generated `{character, description}` entries;
   - a response containing `scratchpad` and an ordered introductions list; and
   - a persisted envelope containing `version: 1`, application-supplied `session_id`, and the list.
3. Supply only the selected `introduction_range` utterances, but also supply full Session context:
   campaign name, game system, Session date, attendees/roles, and glossary.
4. Treat a null Introduction Range as a successful empty result without calling the LLM.
5. Reject duplicate characters and every character not exactly equal to a non-GM attendee role.
   Unlike Ledger name warnings, these are invalid candidates. Attempt up to three candidates.
6. Preserve first-introduction order and write the envelope atomically.
7. Add a deterministic renderer returning either an empty string or:
   `## Player Characters` plus one `- **Character** — description` bullet per entry.

**Tests:** null range without an LLM call, full-context inputs, range-only transcript input,
strict names, GM/NPC rejection, duplicates, empty list, retries, envelope metadata, order,
rendering, and atomic preservation.

## Work item 7 — Create a tutorial for authoring the Player Introductions prompt

**Owner:** implementation agent writes the tutorial; user edits the prompt  
**Tutorial path:** `.scratch/no-preamble/prompt-tutorials/03-player-introductions-prompt.md`

Direct the user to create:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_player_introductions/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_player_introductions/template.j2`

The tutorial must prescribe these `system.md` headings and locations:

1. `# Overview`: extract only explicitly framed Player Character introductions from the supplied
   opening-preamble slice.
2. `# Input Description`: document `<session_metadata>`, `<session_attendees>`, `<glossary>`, and
   `<introduction_transcript>` in that order. State that the selected transcript may include
   intervening recap material because its range is the smallest enclosing span.
3. `# Inclusion Rules`: make the first bullet require an exact non-GM role from attendees; the
   second require explicit opening introduction; later bullets require consolidation and
   first-introduction order.
4. `# Exclusion Rules`: explicitly exclude NPCs, Game Master, player names, incidental in-session
   revelations, mechanics/build inspiration, glossary-only facts, and invented filler.
5. `# Output Format`: require one schema-conforming JSON object with `scratchpad` first and
   `introductions` second. State that an empty list is correct when nothing qualifies.
6. `# Examples`, immediately before Output Format: include an ordinary roll-call, interleaved
   recap material, no introductions, and an NPC introduction that must be excluded.

For `template.j2`, require tags in this exact order: `<session_metadata>`,
`<session_attendees>`, `<glossary>`, `<introduction_transcript>`. Use the same metadata, attendee,
and glossary rendering conventions as `summarize_session/template.j2`; put the pre-serialized
compact `{speaker, text}` JSON array in the last tag.

## Work item 8 — Implement Recap Summary generation and artifact behavior

**Owner:** implementation agent  
**Prompt dependency:** Work item 9  
**Companion scope:** [Implement Recap Summary](01-implement-recap-summary.md)

1. Add `ArtifactName.RECAP_SUMMARY` as visible/exportable `recap_summary.md`, derived from Ledger.
2. Add `session_pipeline/generate_recap_summary.py` with prompt data for Ledger v4 and full Session
   context.
3. Make one free-form `PromptName.GENERATE_RECAP_SUMMARY` call with `llm_model_high` and reject an
   empty response.
4. Normalize the model result as bullet content and add `## Recap` deterministically in code; the
   model must not own that heading.
5. Atomically replace the artifact and preserve any previous copy on failure.
6. Extend standard artifact indicators and export behavior through the existing artifact registry,
   without adding Recap-specific UI branches.

**Tests:** prompt inputs, model choice, empty output, heading ownership, newline normalization,
atomic replacement, Ledger invalidation, indicator visibility, export listing, and file export.

## Work item 9 — Create a tutorial for authoring the placeholder Recap Summary prompt

**Owner:** implementation agent writes the tutorial; user edits the prompt  
**Tutorial path:** `.scratch/no-preamble/prompt-tutorials/04-recap-summary-prompt.md`

Direct the user to create:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_recap_summary/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_recap_summary/template.j2`

The tutorial must state that this is intentionally a placeholder prompt and prescribe:

1. `# Overview`: describe a compact recap of the supplied current Session, not the recording's
   opening recap and not a recap of earlier sessions.
2. `# Input Description`: document `<session_metadata>`, `<session_attendees>`, `<glossary>`, and
   `<session_ledger>` in that order. State that Ledger v4 is the sole source for claims about what
   happened; other context supplies orientation and spelling only.
3. `# Scene Rules`: add exactly three bullets. The first requests one output bullet per scene; the
   second requests a short description of the scene; the third requests one sentence summarizing
   what happened in that scene.
4. `# Output Format`: require Markdown bullets only, each beginning `- `; prohibit a title,
   `## Recap`, nested bullets, preamble text, commentary, and code fences because the application
   adds the section heading.
5. `# Example`, immediately before Output Format: show at least two scenes and exactly one bullet
   for each.

For `template.j2`, require the same four tags and ordering as the Summary template. The tutorial
must explicitly say to copy the structural loops, not the prose, from
`summarize_session/template.j2` and to render the Ledger v4 JSON inside `<session_ledger>`.

Record the final length, selection policy, and voice as deferred; do not make the placeholder
tutorial silently decide them.

## Work item 10 — Implement validated Summary composition

**Owner:** implementation agent  
**Prompt dependency:** Work item 11

1. Define exact marker constants `<!-- RECAP -->` and `<!-- PLAYER_INTRODUCTIONS -->`.
2. Change full Summary generation to validate that each marker occurs exactly once and that Recap
   precedes Player Introductions. Retry malformed model outputs up to three times; reject empty
   responses and provider failures as today.
3. Keep the LLM inputs limited to Ledger v4 plus full Session context. Do not send Recap Summary or
   Player Introductions into the full Summary prompt.
4. Load the previous Session's completed `recap_summary.md` and the current Session's
   `player_introductions.json` only after a marker-valid response is available. Select the
   previous Session within the campaign by date, then sequence number; sort undated Sessions after
   dated Sessions.
5. Replace the Recap marker verbatim with the previous Session's persisted Recap section, or with
   an empty string when there is no previous Session. If a previous Session exists without a Recap,
   fail. Replace the introductions marker with the current Session's deterministic Markdown
   section or with an empty string when the list is empty.
6. Normalize blank lines and the final newline without otherwise rewriting LLM Markdown.
7. Require the current Ledger and Player Introductions plus the previous Session's Recap when a
   previous Session exists. Keep `summary.md` unchanged unless generation, validation, loading,
   and composition all succeed. Do not automatically invalidate later Sessions when a Recap is
   regenerated.

**Tests:** missing, duplicate, reversed, and valid markers; three-attempt selection; empty
introductions; exact Recap insertion; rendered introductions; whitespace normalization;
eligibility; and old-Summary preservation for every failure point.

## Work item 11 — Create a tutorial for converting the full Summary prompt to marker composition

**Owner:** implementation agent writes the tutorial; user edits the prompt  
**Tutorial path:** `.scratch/no-preamble/prompt-tutorials/05-summary-composition-prompt.md`

The tutorial must cover:

- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/system.md`
- `packages/tablesage-application/src/tablesage_application/llm/_prompts/summarize_session/template.j2`
- `data_prompts/summary/seed_prompt.txt`

Give these exact `system.md` instructions:

1. Under `# Input Description`, find the `<session_ledger>` description. Replace the top-level
   field paragraph so it names Ledger v4's `version`, `session_id`, `session_name`, `attendees`,
   required `starting_situation`, and `utterances`. Delete the following Preamble bullet entirely
   and add a bullet explaining `starting_situation` immediately before the existing utterances
   bullet.
2. Under `## Example Input`, replace the complete Ledger JSON example: change version 3 to 4,
   delete `preamble`, and add a non-empty `starting_situation` immediately before `utterances`.
3. Under `## Example Output`, insert `<!-- RECAP -->` on its own line immediately after the title
   and blank line. Insert `<!-- PLAYER_INTRODUCTIONS -->` on its own line immediately after the
   Recap marker and blank line. Delete the example's old `## Starting Situation` bullets if they
   contain prior-session recap events; retain a current-session Starting Situation example derived
   from Ledger v4.
4. Under `## Core Principle: Reincorporation`, replace “Ledger or preamble entry” with “Ledger
   field or utterance.”
5. Under `## Player Knowledge Boundary`, replace the first two sentences that refer to “the Ledger
   and preamble” with language referring only to Ledger v4.
6. Under `## Output Sections`, delete the complete `### The Party` subsection, including its
   explanatory paragraph. Player Characters are inserted by the application.
7. Under `### Starting Situation`, delete the sentences directing the model to use
   `preamble.recap.events`, `opening_situation`, or the first few utterances. Replace them with one
   instruction to render only Ledger v4's `starting_situation`, without adding prior history.
8. Under `# Output Format`, keep the title rule. Replace the paragraph beginning “Then render these
   `##` sections” with an exact sequence: title, Recap marker, Player Introductions marker, then the
   existing detailed `##` sections beginning with Starting Situation. State that both markers are
   required exactly once even when no introductions exist.
9. Under `## Final Check`, replace “Ledger or preamble entry” with “Ledger field or utterance”; add
   a new penultimate bullet requiring both exact markers once and in Recap-then-Introductions
   order; remove The Party from any section-title validation.
10. Search the entire file case-insensitively for `preamble`, `character_introductions`,
    `opening_situation`, and `The Party`; resolve every obsolete match, including examples.

Tell the user that `summarize_session/template.j2` requires no semantic change: inspect it and
leave its four existing input tags and ordering intact. This explicit no-change check prevents an
unnecessary attempt to pass Recap or Introductions into the LLM.

Apply the same heading-specific edits to `data_prompts/summary/seed_prompt.txt`, then verify the
runtime and seed prompts both contain the two literal marker strings and no Preamble schema.

## Work item 12 — Wire artifacts, invalidation, Application orchestration, and TUI progress

**Owner:** implementation agent  
**Prompt edits:** none beyond completed tutorial gates

1. Register artifacts in pipeline order:
   Role Transcript, Transcript Sections (hidden), Ledger, Player Introductions (hidden), Recap
   Summary (visible), Summary (visible).
2. Update Role Transcript regeneration, audio re-import, completed review, attendance/role edits,
   and Clean Session so every new downstream artifact is invalidated or deleted consistently.
3. Keep Ledger replacement invalidating all Ledger-derived artifacts, including Recap Summary and
   the composed Summary, without deleting newly generated Player Introductions.
4. Add Application methods for sectioning, Player Introductions, and Recap Summary. Each method
   owns its database/context lookup and delegates plain values to its pipeline module.
5. Change Session Detail's Generate Outputs worker to run and label:
   - Role Transcript;
   - Transcript Sections;
   - Ledger;
   - Player Introductions;
   - Recap Summary;
   - Summary.
6. Preserve fail-fast error wrapping so the Errors table names the exact failed phase.
7. Keep one final “Outputs generated.” notification and refresh artifact indicators only after the
   worker completes.
8. Add Recap Summary to the standard export table through `should_show_in_ui=True`; do not add
   export special cases.

**Tests:** artifact ordering/existence, all invalidation sources, Clean Session, six-phase TUI call
order, each mid-chain failure boundary, error text, indicator refresh, Recap export, and hidden
artifact exclusion.

## Work item 13 — Update prompt inspection and optimization support

**Owner:** implementation agent  
**Prompt edits:** none

1. Add prompt-render scripts for Transcript Sections, Player Introductions, and Recap Summary.
   Each script loads a real Session, constructs the exact production prompt data, and writes system
   plus user prompt to `temp/` without making an LLM call.
2. Update `scripts/generate_ledger_prompt.py` for Transcript Sections slicing and Ledger v4's two
   transcript inputs.
3. Update `scripts/generate_summary_prompt.py` for Ledger v4 and add an optional composition check
   that reports missing/duplicate markers without altering prompt text.
4. Update Ledger optimizer imports and target response schema to Ledger v4.
5. Regenerate or mechanically migrate Ledger and Summary optimizer input fixtures to the new input
   envelopes after the user's prompt edits. The implementation agent may change input fixtures and
   metrics code; only seed-prompt prose remains user-owned.
6. Do not add Recap optimization metrics or a dataset yet; its final quality contract remains an
   open question. Prompt rendering and runtime tests are sufficient for the placeholder.
7. Update `apps/optimize-prompts/README.md` and `scripts/README.md` with the new inspection flow and
   the boundary between runtime prompts, seed prompts, and generated evaluation inputs.

## Work item 14 — Finish documentation and end-to-end verification

**Owner:** implementation agent

1. Update `generate_ledger.md`, `generate_summary.md`, `session_detail_screen.md`,
   `export_artifact.md`, `system_architecture.md`, and relevant use-case/implementation-plan text.
2. Remove current-state claims that Role Transcript is word-level, Ledger is v3, Ledger owns a
   Preamble, or Generate Outputs has three phases.
3. Cross-link the canonical Ledger v4 document, the feature design, and both implementation work
   items.
4. Run focused tests after each work item, then run the complete repository checks:

```text
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest
```

5. Render all five production prompts with representative Session data and verify:
   - Transcript Sections references valid persisted indices;
   - Ledger receives no opening recap except labeled starting context;
   - Player Introductions receives only its selected range;
   - Recap receives Ledger v4 rather than opening recap text;
   - Summary contains both markers exactly once before composition; and
   - composed Summary contains the persisted Recap and deterministic Player Characters section.

## Execution order and user gates

1. Agent completes Work items 1–2 and writes the tutorial in Work item 3.
2. User authors the Transcript Sections prompt; agent verifies it.
3. Agent completes Work item 4 and writes Work item 5's tutorial.
4. User converts the Ledger runtime and seed prompts; agent verifies them.
5. Agent completes Work item 6 and writes Work item 7's tutorial.
6. User authors the Player Introductions prompt; agent verifies it.
7. Agent completes Work item 8 and writes Work item 9's tutorial.
8. User authors the placeholder Recap prompt; agent verifies it.
9. Agent completes Work item 10 and writes Work item 11's tutorial.
10. User converts the Summary runtime and seed prompts; agent verifies them.
11. Agent completes Work items 12–14 and the full verification pass.

The prompt gates are intentional stopping points. The agent must not fill missing prompt files or
repair prompt prose on the user's behalf; it reports exact verification failures and points back to
the relevant tutorial.

## Definition of done

- All code and non-prompt documentation in the linked design and implementation work items is
  implemented.
- All five prompt tutorials exist and have been followed by the user.
- Runtime prompt packages load successfully and their templates render with strict undefined
  variables.
- Ledger v4 and all new artifacts obey their schemas, dependencies, visibility, and failure rules.
- Generate Outputs completes the six-phase pipeline and produces a correctly composed Summary.
- Prompt inspection tooling reflects production inputs without making LLM calls.
- Formatting, lint, type checking, and the full test suite pass.
