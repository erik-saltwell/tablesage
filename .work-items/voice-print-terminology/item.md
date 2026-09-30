---
name: "Use voice print terminology everywhere"
status: complete
---

# Use voice print terminology everywhere

Use “voice print” for the embedding representing a voice from one utterance or a collection of samples. Apply the terminology consistently across code identifiers, UI, public documentation, internal records, benchmarks, and existing tests. Preserve existing database contents through a schema migration; historical migration inputs retain their original column name.

The user explicitly requested implementation. No numerical rubric was defined or scored.

Completed and verified: 738 existing project tests and 16 benchmark tests passed, along with lint, type checks, and fresh/populated database migration checks. See [progress.md](progress.md) for scope, compatibility details, and verification.

## Reopened (2026-09-30): remove "voice profile"

The user directed that "voice profile" is the same thing as a voice print and must not be used anywhere: UI (including the **Improve Player Voice Profiles** step), documentation, and code. The rule is recorded in `.agent_context.md` under Documentation style. Found in the public-documentation quality review. Saved processing progress, drafts, and step identifiers must keep working after the rename.

### Completion (2026-09-30)

Renamed across the UI, code, packaged settings comments, scripts, public docs, README, and existing tests: the step is now **Improve Player Voice Prints** (automatic follow-on **Enhance Voice Prints**), with `StepID.IMPROVE_VOICE_PRINTS` / `ENHANCE_VOICE_PRINTS`, `ArtifactName.VOICE_PRINT_DECISION` / `VOICE_PRINT_ENHANCEMENT`, and `save_voice_print_decision` / `enhance_voice_prints`. Loose prose that meant a Player's clips now says "voice samples"; prose that meant the embedding says "voice print".

Compatibility: `ProcessingState` translates the old keys when it reads `processing_state.json` (records, sections, `artifact:` input names, and step-id-keyed drafts and failures), so existing Sessions keep their completed step. Verified by loading state files written by the previous code: both processed Sessions still report `voice_print_decision` and `voice_print_enhancement` as current.

Verification: 738 existing tests pass; Ruff and ty pass. Recaptured the five screenshots showing the step (`process-session-new-player`, `process-session-midway`, `progress-dialog`, `process-session-complete`, and `improve-voice-prints`, renamed from `improve-voice-profiles`) through the Textual MCP and checked them visually. Historical records in completed work items were left unchanged.
