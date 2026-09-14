# TableSage system architecture

TableSage is organized into four layers. The structure keeps the user interface thin, makes use cases testable, and preserves reusable audio/provider capabilities.

All four layers ship in a single `tablesage-rpg` distribution built from the root
`pyproject.toml`. The existing source directories and Python import names remain
layer boundaries, not independently published distributions. Both `tablesage-rpg`
and `tablesage` console commands invoke the same composition root. The separate
`optimize-prompts` developer app is outside the runtime distribution.

Startup checks that `ffmpeg` and `ffplay` are on PATH, then loads named personal
credentials from `.env` in the OS-standard TableSage user config directory
(`platformdirs`). Inherited shell variables override stored credentials. Workspace
`.env` files are not read. Each launch directory owns its own `.tablesage`
workspace; there is no parent-directory workspace search. Only credentials are
global; workspace behavior stays in `.tablesage/settings.yaml`.

Campaign and session files live at `<workspace>/campaigns/`; player voice clips
live at `<workspace>/players/`. The database, settings, and logs stay in
`<workspace>/.tablesage/`. Application path helpers derive these locations from
the launch directory. Existing workspaces require moving their old
`.tablesage/campaigns` and `.tablesage/players` folders up one level manually.

```text
tablesage-tui → tablesage-application → tablesage-model
                                     → tablesage-tools

tablesage-model → no project packages
tablesage-tools → no project packages
```

## `tablesage-tui`

The Textual user interface. It presents data, collects input, renders progress/errors, and invokes application use cases. It does not access SQLite repositories or media/provider adapters directly.

## `tablesage-application`

The orchestration layer. It implements use cases such as campaign management, campaign roster management, player management, session processing, voice-profile seeding/enhancement, transcript review, and summary generation.

Application use cases validate inputs, own transaction boundaries, coordinate repositories and tools, emit progress, and return UI-friendly results. They depend on repository interfaces, never on a concrete SQLite implementation.

Organize this package by use case rather than technical helper type, for example `campaigns`, `players`, `sessions`, `voice_profiles`, `transcript_review`, and `summaries`. `players` is independent of `campaigns` — a player is not owned by any single campaign, so player CRUD and voice-profile management live outside the `campaigns` module, linked only through the roster (`campaign_player`).

## `tablesage-model`

The domain and persistence package. It contains domain entities such as campaigns, sessions, players, voice samples, discourse, and summaries; it also defines repository and unit-of-work interfaces.

SQLite is initially implemented here, but behind an explicit internal seam:

```text
tablesage_model/
  domain/       domain entities and invariants
  repository/   repository and unit-of-work interfaces
  sqlite/       SQLModel mappings, SQLite repositories, Alembic migrations
```

The SQLite adapter must not leak SQLAlchemy/SQLModel sessions through repository interfaces. This makes moving `sqlite/` into a separate package possible later without changing application use cases.

## `tablesage-tools`

Independent media and provider adapters. It includes audio conversion/cleaning/clipping, transcription and diarization providers, embedding extraction, similarity calculation, centroid computation, and text post-processing.

Tools operate on generic inputs, outputs, and explicitly supplied paths. They do not know about TableSage campaigns, players, voice-sample provenance, database records, application filesystem layout, or `AppSettings`.

Tools may compute embeddings and centroids. The application/domain layers decide whether a result becomes a player voice profile, which clips are accepted, and how provenance is persisted.

## Composition and testing

Generate Opportunities lives in `tablesage_application.opportunities`. Application
reloads the complete validated Campaign Scene Recap for each generation. A packaged
prompt uses `llm_model_high` and deployed `opportunities_timeout`; its structured
response contains at most five pitches. The TUI holds ephemeral results paired with
their generating prompt. Markdown export performs no further model call and does
not register artifacts, write planning history, or affect freshness.

Campaign-aware Previously On export lives in `tablesage_application.previously_on`, with
Application loading a validated Campaign snapshot through the existing artifact freshness graph.
Structured ingredients and scout responses use exact Session UUID/Scene index references.
The separate `EditorInput` boundary contains only approved Scene records, starting situation,
and glossary. All three prompts are packaged application resources; model selection uses
`llm_model_high` and timeouts come from the deployed `previously_on` settings section.
The TUI owns ephemeral selections and navigation. This external Markdown export does not register
a Session artifact or alter downstream freshness; its final LLM output is deliberately unvalidated.

The executable composition root constructs concrete SQLite repositories and tool adapters, then injects them into application use cases. This is the only place that knows all concrete implementations. It's also where `AppSettings` gets loaded (`tablesage_model.setup.ensure_settings`, deploying the TUI's packaged default `settings.yaml` to `.tablesage/settings.yaml` on first run) and injected into `Application` — settings aren't read anywhere below this point.

The Settings screen edits a draft and delegates atomic canonical persistence to
`tablesage_application.configuration.Configuration`. After Save, `Application`
receives a replacement settings snapshot for subsequent actions. Credentials
share the explicit Save lifecycle (in a separate personal file), preserve unrelated dotenv content, and refresh managed process
variables while preserving their inherited shell overrides. An explicit
`settings_version` controls mandatory first-run and upgrade review; an unversioned
file is version zero, and a future version is rejected. Invalid files retain the
terminal-error repair path. See [the Settings design](../.scratch/settings/design.md).

- Test domain invariants without SQLite or provider dependencies.
- Test application use cases with fake repositories and fake tools.
- Test tools against adapter contracts and provider/media fixtures.
- Test SQLite repositories and Alembic migrations as integration tests.
