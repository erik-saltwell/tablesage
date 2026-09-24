# Resumable session processing flow

> **Status note (2026-09-24):** this three-phase direction (Audio → Transcript → Outputs, with a workflow rail) was implemented, then superseded by the Process Session step list. That list is a numbered, artifact-driven sequence of manual and automatic steps with a New Players list and an error list. Its settled design is recorded in [item.md](item.md) and [intent.md](intent.md). The text below is kept as the original idea.

## Intended effect

Make the normal path from session audio to generated artifacts feel like one coherent process rather than three separate actions, while retaining safe checkpoints when a user stops partway through.

## Working direction

Session Detail will offer one `P` binding that starts the multi-screen processing flow:

| Session state | Binding label |
| --- | --- |
| No audio artifact | `P` — Process |
| An audio artifact exists | `P` — Continue Processing |

The flow covers the existing conceptual phases in order:

1. Add or replace audio and transcribe it.
2. Review the transcript.
3. Generate session outputs.

Completing a phase moves the user forward and saves its intermediate state. Each screen has a Back control for returning to an earlier screen. The feature is intentionally resumable rather than a one-sitting modal wizard.

## Transcript-review exit behavior

When leaving while transcript edits are present, the app asks whether to save those changes. A return to the processing flow after leaving transcript review always opens the transcript screen, whether the edits were saved or discarded. Saved unfinished review work must be distinguishable from a completed review so incomplete edits do not become generation input.

## Workflow rail

Every processing screen has a compact, non-interactive workflow rail immediately above the existing keyboard-shortcut footer, for example:

`Audio ●  ─  Transcript ◐  ─  Outputs ○`

The rail reflects persisted workflow state rather than only the current screen. It may use `!` when a phase needs attention after an error, such as:

`Audio ●  ─  Transcript ●  ─  Outputs !`

The existing shortcut footer remains separate: the rail explains processing state, while the footer explains available actions. Navigation remains through Back and forward controls rather than clickable rail stages.

## Rationale

The existing pipeline already has meaningful checkpoints: importing audio triggers transcription, human review can be lengthy, and output generation follows a completed review. A unified entry point improves discoverability, while persisted phase state and an always-visible rail prevent the flow from hiding those checkpoints or making cancellation feel destructive.

## Open details

- The concrete storage and invalidation rules for unfinished transcript-review edits, particularly after audio replacement or retranscription.
- The behavior of Back after a completed phase, including whether it is navigation only and how later artifacts become stale after edits.
- How the flow presents a fully current session after `P` is invoked.
- Exact screen layout, forward controls, and behavior while a long-running transcription or generation operation is active.
- Which existing specialist actions remain available outside the primary processing flow.
