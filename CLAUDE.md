## Agent skills

### Issue tracker

Issues and PRDs use local Markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the default canonical state names. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain-doc layout. See `docs/agents/domain.md`.

## TTRPG reincorporation

Reincorporation brings an established campaign element back into play so that it gains renewed relevance. It is strongest when the element either acquires new meaning or gains new utility:

- **New meaning:** Later context changes the nature of the element or the players' understanding of it.
- **New utility:** Players use the element as a tool or resource in a later situation.

Favor opportunities that let players discover and initiate an element's new utility themselves; this turns continuity into player agency. Support changes in meaning with established facts so they feel earned rather than like arbitrary twists, and do not force every earlier detail to return. Emotional or thematic callbacks are also valid reincorporation even when they provide neither transformation nor practical utility.

### Session artifacts

The authoritative artifact specifications are:

- [Ledger](specs/ledger.md)
- [Player Introductions](specs/player-introductions.md)
- [Transcript Sections](specs/transcript-sections.md)

### Settings

Whenever you add code where `tablesage-tui` (directly, or via `tablesage-application`) calls
into `tablesage-tools`, any tunable knob for that call must be read from the TUI's deployed
`settings.yaml` (`AppSettings`, loaded by `tablesage_model.setup.ensure_settings` and injected
into `Application` at `tablesage_tui.screens.main_app.main`'s composition root) rather than
hardcoded. The settings-agnostic boundary is `tablesage-tools` itself: it only ever receives
plain values (`float`, `int`, etc.), never an `AppSettings` object or one of its sections; see
`system_architecture.md`'s "Tools operate on generic inputs... They do not know about...
`AppSettings`" rule. `tablesage-application` (including `session_pipeline`) is not bound by that
rule — it may accept `AppSettings` section objects (e.g. `TranscriptionAndDiarizationSettings`)
directly as parameters, unpacking them into plain values only at the calls it makes into
`tablesage-tools`. The packaged default lives at
`apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`; add new knobs there and to
`RemoveOutliersSettings`-style sections of `AppSettings` in `tablesage_model.settings`, following
the `remove_outliers` precedent used by the centroid clean-up path.
