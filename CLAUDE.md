## Agent skills

### Issue tracker

Issues and PRDs use local Markdown under `.scratch/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Triage uses the default canonical state names. See `docs/agents/triage-labels.md`.

### Domain docs

This repository uses a single-context domain-doc layout. See `docs/agents/domain.md`.

### Settings

Whenever you add code where `tablesage-tui` (directly, or via `tablesage-application`) calls
into `tablesage-tools`, any tunable knob for that call must be read from the TUI's deployed
`settings.yaml` (`AppSettings`, loaded by `tablesage_model.setup.ensure_settings` and injected
into `Application` at `tablesage_tui.screens.main_app.main`'s composition root) rather than
hardcoded. `tablesage-tools` itself must stay settings-agnostic — it only ever receives plain
values (`float`, `int`, etc.), never an `AppSettings` object; see `system_architecture.md`'s
"Tools operate on generic inputs... They do not know about... `AppSettings`" rule. The packaged
default lives at `apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml`; add new knobs
there and to `RemoveOutliersSettings`-style sections of `AppSettings` in
`tablesage_model.settings`, following the `remove_outliers` precedent used by the centroid
clean-up path.
