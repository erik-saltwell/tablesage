# Generate Summary — Simplification Opportunities

## Purpose

This review covers the Generate Summary use case and the adjacent role-transcript and artifact-invalidation code. Each opportunity is independent and can be approved or declined without deciding the others.

Decision states:

- [ ] Approve
- [ ] Decline

When choosing, mark exactly one state in the relevant section and optionally add a note.

## 1. Deepen the Summary Generation Module

**Decision**

- [ ] Approve
- [ ] Decline

**Files**

- `packages/tablesage-application/src/tablesage_application/application.py`
- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py`
- `packages/tablesage-application/src/tablesage_application/session_pipeline/processing.py`
- `packages/tablesage-application/tests/session_pipeline/test_generate_summary.py`
- `packages/tablesage-application/tests/session_pipeline/test_processing.py`

**Problem**

The Summary use case is spread across three modules:

- `processing.can_generate_summary` knows the prerequisite.
- `Application.generate_summary` resolves the source and target files, loads and sorts the Glossary, converts Glossary entries, runs the async implementation, and owns atomic replacement.
- `session_pipeline.generate_summary` only constructs prompt data, calls the LLM, and normalizes the response.

The `session_pipeline.generate_summary` module is shallow: its interface exposes nearly all of its implementation, while the important invariants remain in `Application`. Applying the deletion test, removing this module would eliminate little complexity; most Summary knowledge would remain scattered.

**Solution**

Make the Summary generation module own the complete file-backed use case: prerequisite checking, current role-transcript source selection, deterministic Glossary prompt preparation, LLM invocation, response validation, and atomic replacement. `Application` should retain database/session lookup and delegate the rest in one call.

This still preserves the documented future-source seam: source selection remains inside the application layer, concentrated in the Summary module rather than embedded in the `Application` facade.

**Benefits**

- **Locality:** all Summary invariants and error modes live in one module.
- **Leverage:** the TUI and future callers receive the complete behavior through one small interface.
- Tests can exercise the real use case through the same interface callers use, instead of testing an inner LLM function and then separately mocking it from `Application`.
- The standalone `processing.can_generate_summary` pass-through can be removed or moved beside generation, reducing navigation.
- The sync/async detail becomes private implementation rather than something `Application` must coordinate.

**Trade-off**

The Summary module will contain more implementation, intentionally increasing its depth. It must not query SQLite directly; `Application` should continue supplying campaign Glossary data through the repository/application layer.

**Decision note:**

> 

## 2. Give Artifact Invalidation One Owner

**Decision**

- [ ] Approve
- [ ] Decline

**Files**

- `packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py`
- `packages/tablesage-application/src/tablesage_application/session_pipeline/import_audio.py`
- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py`
- `packages/tablesage-application/src/tablesage_application/application.py`
- `packages/tablesage-application/src/tablesage_application/paths.py`

**Problem**

Artifact deletion has two implementations and two conceptual owners:

- `artifacts.invalidate_category` deletes one category.
- `import_audio.invalidate_downstream` deletes every derived artifact.

Attendance and role mutations call `import_audio.invalidate_downstream`, even though those use cases are unrelated to importing audio. Both functions iterate the same artifact registry, unlink files, and emit similar logging. The current seam leaks the historical location of invalidation into five `Application` call sites.

**Solution**

Move all registry-driven invalidation behavior into the artifacts module. Keep named operations for the two business meanings—invalidating all derived artifacts and invalidating one category—but let them share one private deletion implementation. Update audio import, transcription, attendance, and role callers to use the artifacts module directly.

**Benefits**

- **Locality:** the artifact registry and every rule that interprets its categories live together.
- **Leverage:** one deletion implementation covers current and future artifact-producing use cases.
- `import_audio` becomes focused on validating and replacing input audio.
- Call sites describe what they are doing without pretending invalidation belongs to audio import.
- Tests can verify invalidation once at the artifacts interface, leaving caller tests to verify when each operation invokes it.

**Trade-off**

This is mostly structural; it does not reduce many lines immediately. Its value is removing duplicated policy and preventing new invalidation variants from accumulating.

**Decision note:**

> 

## 3. Name the Two Transcript Renderings Explicitly

**Decision**

- [ ] Approve
- [ ] Decline

**Files**

- `packages/tablesage-application/src/tablesage_application/session_pipeline/transcribe_audio.py`
- `packages/tablesage-application/tests/session_pipeline/test_transcribe_audio.py`

**Problem**

`_render_transcript_text` and `_render_utterance` each have two output modes controlled implicitly by `role_names`:

- `role_names is None` produces the timestamped human Transcript.
- Any dictionary, including `{}`, produces the untimestamped Role Transcript.

That interface makes an optional data value also select a document format. A caller must know that `None` versus an empty dictionary changes timestamps, Markdown punctuation, and speaker labeling. The two artifacts now have distinct domain purposes, but their rendering remains coupled in one conditional implementation.

**Solution**

Use separately named human-transcript and role-transcript rendering paths, sharing only the small text-selection implementation that chooses punctuated text when available. Each path should directly express its own formatting and labeling rules.

**Benefits**

- **Locality:** each artifact's format is visible in one rendering module/function.
- The interface no longer overloads `None` as a format selector.
- Tests can assert each document contract directly and failures identify which rendering changed.
- Future changes to the LLM-facing Role Transcript cannot accidentally alter the human Transcript.

**Trade-off**

This may add a small amount of implementation duplication. That duplication is preferable if it keeps two independently evolving document formats from sharing condition-heavy code.

**Decision note:**

> 

## Suggested Order

If multiple opportunities are approved:

1. Give artifact invalidation one owner.
2. Deepen the Summary generation module using that settled artifact interface.
3. Separate the transcript renderings.

The first two touch adjacent orchestration code, so doing invalidation first avoids moving the same calls twice. The rendering change is independent.
