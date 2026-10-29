# Session Summary Transition

- [x] Move the deterministic renderer and unchanged Jinja layout to Summary; enable its producer, dependencies, processing completion and regeneration/export integration.
- [x] Pause Table Recap generation while retaining saved files, UI entry points and an explanatory CLI response.
- [x] Add `regenerate-session-summary`, archive prior summaries on replacement, and update current contracts/help.
- [x] Verify output parity, direct producer/CLI behavior, freshness and file preservation in a disposable fixture, then run lint/type/build checks. No new unit tests or shared artifact regeneration.

The following completed plan is historical and is superseded by the transition above.

# Implementation Plan

- [x] Add a pure Markdown renderer using primary fields and brief deterministic transitions, with source validation and rollback-safe persistence.
- [x] Connect the existing Table Recap producer to Post-Session Matters; add it to generation order and completion, remove it from deferred/model-generated sets, and keep Summary paused. Preserve existing artifact UI/export/cleanup behavior.
- [x] Verify rendering against all four real publications and direct edge cases, dependency propagation, failures, input races, and credential-free regeneration. Do not add unit tests.
- [x] Audit the source-producer code and pre/post dependencies; perform the guarded application-file fingerprint migration only if all other source inputs and output bytes are unchanged. Generate four recaps without model calls.
- [x] Verify the TUI's current indicators, regeneration and Markdown export, plus lint, type checks, packaging and synchronization. Record evidence and complete tracking.

## Jinja Template Revision

- [x] Move wording and layout into a packaged Jinja template; keep validation and text preparation in Python.
- [x] Track template edits as recap dependencies and verify output parity, editing/failure behavior and packaged rendering.
- [x] Preserve all shared recap files, verify regeneration in a disposable copy without model calls, and document the template editing path.

## Campaign Name in Template

- [x] Pass the owning Campaign name into Jinja and use “Previously on <Campaign name>:”.
- [x] Track the Campaign name in recap dependencies, verify all four renderings and preserve existing saved Markdown.

## Standalone Regeneration Command

- [x] Add `tablesage regenerate-table-recap --campaign NAME --session NUMBER` using the existing direct producer.
- [x] Verify successful regeneration, failure exits, source preservation and no model/credential/TUI use in a disposable workspace.
- [x] Document the standalone command and complete validation.

## Session Metadata in the Header

- [x] Pass the recorded Session date and existing Scene Log Session cue into Jinja and display them in the title.
- [x] Track both inputs, verify metadata edits and failure behavior, and preserve existing saved Markdown.
