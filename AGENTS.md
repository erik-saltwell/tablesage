# Agent Guide

## Agent skills

### Issue tracker

Issues and PRDs use local Markdown under `.scratch/`. See [the issue-tracker guide](docs/agents/issue-tracker.md).

### Triage labels

Triage uses the default canonical state names. See [the triage-label guide](docs/agents/triage-labels.md).

### Domain docs

This repository uses a single-context domain-doc layout. See [the domain guide](docs/agents/domain.md).

## Session artifact specifications

Read the relevant specification before changing an artifact's schema, prompt contract, routing, persistence, or downstream invalidation:

- [Ledger](specs/ledger.md)
- [Player Introductions](specs/player-introductions.md)
- [Transcript Sections](specs/transcript-sections.md)

## Settings

Whenever you add code where `tablesage-tui` (directly, or via `tablesage-application`) calls into `tablesage-tools`, any tunable knob for that call must be read from the TUI's deployed `settings.yaml` (`AppSettings`, loaded by `tablesage_model.setup.ensure_settings` and injected into `Application` at `tablesage_tui.screens.main_app.main`'s composition root) rather than hardcoded.

The settings-agnostic boundary is `tablesage-tools` itself: it only ever receives plain values (`float`, `int`, etc.), never an `AppSettings` object or one of its sections; see `system_architecture.md`'s "Tools operate on generic inputs... They do not know about... `AppSettings`" rule. `tablesage-application` (including `session_pipeline`) is not bound by that rule — it may accept `AppSettings` section objects (for example, `TranscriptionAndDiarizationSettings`) directly as parameters, unpacking them into plain values only at the calls it makes into `tablesage-tools`.

The packaged default lives at `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`; add new knobs there and to `RemoveOutliersSettings`-style sections of `AppSettings` in `tablesage_model.settings`, following the `remove_outliers` precedent used by the centroid clean-up path.
