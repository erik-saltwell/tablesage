# Spelling-correction suggestions as Manual Review's first phase

## Problem / desired outcome

ASR transcription regularly mishears campaign-specific proper nouns -- NPC names, place names,
established glossary terms, and player/character names -- because they're absent from any general
language model's vocabulary. Once a term has been established (it's in the campaign Glossary, or a
player's name is in the attendee roster), later sessions should benefit: an utterance's spelling of
a known term should converge on the campaign's canonical spelling instead of drifting per-session
ASR noise.

## History: superseded per-utterance design

The first version of this feature (implemented, then reverted) ran as an automatic sub-stage of
Transcribe, immediately after punctuation: one LLM call per utterance longer than a word-count
threshold, each constrained to replace only glossary/attendee matches, silently overwriting
`punctuated_text` with no human review. It was rejected for two reasons: (1) too LLM-call-intensive
-- one call per above-threshold utterance meant dozens to hundreds of calls per session; (2) each
call saw only one utterance in isolation, without enough surrounding context to correct confidently
or to disambiguate between similar-sounding known terms. This document replaces that design
entirely; the corresponding settings, pipeline module, prompt, and wiring are being removed.

## Accepted design

**One call, not many.** A single LLM call (`llm_model`, the default mid-tier model -- same tier
`extract_glossary` already uses for a similarly-shaped whole-transcript + glossary + attendees task)
sends the *entire* transcript alongside the campaign's glossary terms and the session's attendee
names, and gets back a list of `{from, to}` suggestions -- `from` a snippet of text found verbatim in
the transcript, `to` what it should be replaced with (a glossary term or attendee name). Whole-transcript
context lets the model disambiguate between similarly-sounding known terms in a way an isolated
single-utterance call could not.

**Placement: first phase of Manual Review, not part of Transcribe.** `ManualReviewScreen`
(`speaker_review.py`) becomes a two-phase screen: a new spelling-suggestions phase runs first,
automatically, the moment the screen mounts; only once the user completes (or the phase is skipped)
does the screen's existing speaker-review UI appear, using the same in-memory `Transcript` the
suggestions phase already modified. There is no new artifact and no early commit point -- exactly one
`Transcript` is owned by the screen for its whole lifetime, and nothing is written to disk until
Manual Review's existing Complete (`reviewed_transcript.json`, unchanged). Cancel (including Escape),
at either phase, discards the whole in-memory session and exits Manual Review entirely -- uniform
with today's single Cancel semantics, not phase-scoped.

Concretely: `on_mount` still calls `extract_review_clips` exactly as it does today (loads the
Transcript from disk, extracts per-utterance audio clips) -- clip extraction is audio-timing-based
and entirely unaffected by text corrections, so there's no need to reorder or change its signature.
Once that Transcript is loaded, the new phase's LLM call fires automatically using its text, before
the existing speaker-review table is shown.

**Automatic trigger, fail-open on both empty context and call failure.** No user action starts the
call. If the campaign has no glossary terms and the session has no attendees, or if the LLM call
itself fails (timeout/error), the suggestions phase is skipped entirely (with a brief notification)
and the screen proceeds straight to the existing speaker-review phase, unmodified -- Manual Review's
entry point must never hard-fail or dead-end just because this convenience layer broke.

**Suggestion filtering, before the table is ever shown:**
- Drop any suggestion whose `from` does not appear verbatim in the transcript (model imprecision) --
  inert noise that can never match anything.
- Drop no-op suggestions where `to == from`.
- Deduplicate by `from`: if the LLM proposes the same `from` with two different `to` values, keep an
  implementation-defined one (e.g. first-seen) and drop the rest -- rare enough not to warrant
  conflict-resolution UI; the user's existing Edit/Delete on the surviving row covers it.

Existence-checking each surviving suggestion also yields, for free, an occurrence count -- shown as a
table column so the user can judge a suggestion's impact before accepting it.

**Review table: New / Edit / Delete / Complete, mirroring `GlossaryReviewScreen`.** Each row is a
`{from, to, case_sensitive}` triple -- reusing the shape of the existing `FindReplaceDialog`
(`find`/`replace`/`case_sensitive`), but as its own dialog for a suggestion row (this feature's
default is `case_sensitive=False`, the opposite of `FindReplaceDialog`'s own default of `True` --
different context, ASR mishearings often differ only in case). New adds a manual row; Edit
pre-fills the same dialog; Delete removes a row; Complete applies every surviving row's `from`→`to`
replacement across the whole transcript, sequentially in table order (each replacement acts on the
transcript as already modified by prior replacements in the list -- the same net effect as a human
running `Find & Replace` N times in a row), matching against `punctuated_text` (never `text`, the
immutable raw ASR field) via the existing `re.escape` + `subn` pattern already used by
`transcript_review.replace_text` and `GlossaryReviewScreen.action_find_replace`. Once applied, the
screen transitions to its existing speaker-review phase, its bindings and table replacing the
suggestions phase's (same screen, same `Transcript`, phase-scoped bindings via `check_action`, the
way `SessionDetailScreen` already scopes bindings contextually -- `N`/`E`/`D`/`C` mean
new/edit/delete/complete-suggestion in phase one and are simply inactive once phase two's `D` (delete
utterance) and `F` (find/replace) take over).

## Acceptance criteria

- `ManualReviewScreen` gains a spelling-suggestions phase that runs automatically on mount, before
  its existing speaker-review UI appears, using the same `Transcript` `extract_review_clips` already
  loads.
- The phase is skipped (with a notification, straight to speaker review) when the campaign has no
  glossary terms and the session has no attendees, and also on LLM call failure.
- The LLM call uses `llm_model`, given the full transcript text, campaign glossary terms, and
  session attendee names, and returns `{from, to}` suggestions via a structured response schema.
- Suggestions are filtered (verbatim match required, `to != from`, deduped by `from`) before display;
  each surviving suggestion's table row shows an occurrence count.
- The suggestions table supports New, Edit (pre-filled dialog: from/to/case-sensitive, default
  insensitive), Delete, and Complete, mirroring `GlossaryReviewScreen`'s existing table-review
  pattern.
- Complete applies every surviving suggestion's find/replace sequentially against `punctuated_text`
  across the whole transcript, then transitions to the existing speaker-review phase with the
  corrected `Transcript`.
- Cancel/Escape at either phase discards the entire in-memory session and exits Manual Review, same
  as today -- no phase-scoped cancel.
- Nothing is written to disk by this feature independent of Manual Review's own existing Complete
  (`reviewed_transcript.json`).
- The prior per-utterance design is fully removed: `CorrectSpellingSettings` and the
  `correct_spelling` section of `AppSettings`/`settings.yaml`, the `correct_spelling` pipeline module
  and its `_prompts/correct_spelling/` template, `PromptName.CORRECT_SPELLING`, the
  `CORRECTING_SPELLING` stage of `transcribe_audio.Stage`, and its wiring in
  `transcribe_audio.transcribe_audio` and `session_detail.py`'s Import Audio action.

## Implementation context

- `apps/tablesage-tui/src/tablesage_tui/screens/speaker_review.py` (`ManualReviewScreen`) -- add the
  new phase. `on_mount` (line ~153) already fetches attendees (`list_attendance`) and calls
  `extract_review_clips`; add a `list_glossary_entries(campaign_id)` fetch (campaign_id via
  `application.get_session(session_id).campaign_id`, same pattern used elsewhere) and the new LLM
  call once the Transcript is loaded. `BINDINGS` (line 90) needs phase-scoped entries; `check_action`
  (not yet present on this screen -- `SessionDetailScreen.check_action` is the precedent) gates which
  bindings are active per phase.
- `apps/tablesage-tui/src/tablesage_tui/screens/glossary_review.py` (`GlossaryReviewScreen`) --
  closest precedent for the whole review-table UX: `_DraftEntry`-style in-memory rows with a
  synthetic uuid key, `_reload_table` full-rebuild-not-patch, New/Edit/Delete bindings, `Complete`
  validation-then-commit shape. The suggestions table's `_DraftEntry` equivalent needs `from`, `to`,
  `case_sensitive`, and a derived (recomputed on each reload) occurrence count.
- `apps/tablesage-tui/src/tablesage_tui/dialogs/find_replace.py` (`FindReplaceDialog`,
  `FindReplaceResult`) -- shape to mirror for the suggestion row New/Edit dialog (`find`/`replace`/
  `case_sensitive` fields); note its own default (`case_sensitive=True`) is the opposite of what this
  feature wants for new suggestion rows.
- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcript_review.py`
  (`replace_text`, lines ~147-173) -- existing single find/replace-across-transcript implementation;
  the new Complete action's sequential N-suggestion apply is N calls of this same shape (or a
  factored-out shared helper, since `GlossaryReviewScreen.action_find_replace` reimplements the same
  `re.escape`+`subn` loop independently today -- worth consolidating into one shared utility while
  touching this).
- `packages/tablesage-application/src/tablesage_application/session_pipeline/extract_glossary.py` --
  precedent for the new module's shape: whole-transcript + attendees + glossary in one `call_llm_with_prompt`
  call, `_StrictModel` response schema, `PromptName` entry, `_prompts/<name>/{system.md,template.j2}`.
  A new `session_pipeline/suggest_spelling_corrections.py` (name TBD) replaces
  `session_pipeline/correct_spelling.py` entirely.
- `packages/tablesage-application/src/tablesage_application/application.py` -- new facade method
  (e.g. `suggest_spelling_corrections(session_id) -> list[SpellingSuggestion]`), following
  `extract_glossary`'s shape (lines 283-313): fetch transcript text + attendees + glossary inside one
  `Session`, then the LLM call outside it.
- **Removal:** `packages/tablesage-model/src/tablesage_model/settings/app_settings.py`
  (`CorrectSpellingSettings`, and its field on `AppSettings`) and `settings/__init__.py`'s export;
  `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`'s `correct_spelling:` section;
  `packages/tablesage-application/.../session_pipeline/correct_spelling.py` and its test
  `tests/session_pipeline/test_correct_spelling.py`; `_prompts/correct_spelling/` and its
  `PromptName.CORRECT_SPELLING` entry; `transcribe_audio.py`'s `CORRECTING_SPELLING` stage, its
  `correct_spelling` import/call, and its `correct_spelling_settings`/`glossary_terms`/
  `attendee_names` parameters (reverting `transcribe_audio()`'s signature to what it was before);
  `session_detail.py`'s glossary/attendee fetch in `do_import_and_transcribe` and the
  `CORRECTING_SPELLING` stage label; the corresponding call-site updates in
  `tests/session_pipeline/test_transcribe_audio.py`.

## Triage state

`complete` — implemented in commit `f7be8f1`.
