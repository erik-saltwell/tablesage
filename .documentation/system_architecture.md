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

The Textual user interface. It presents data, collects input, renders progress/errors, and invokes application use cases. Persistence is delegated to Application. Most processing is also delegated there; Session Detail currently invokes the application-layer import_audio helper directly before requesting transcription.

## `tablesage-application`

The orchestration layer. It implements use cases such as campaign management, campaign roster management, player management, session processing, voice-profile seeding/enhancement, transcript review, and summary generation.

Application use cases validate inputs, own transaction boundaries, coordinate repositories and tools, emit progress, and return UI-friendly results. They use concrete SQLModel sessions and the helpers in `entities/`; Application owns the SQLite engine. There is no repository-interface or unit-of-work abstraction between these layers.

Current modules include `entities/` for database operations, `session_pipeline/` for artifact processing, `voice_clips/`, player/campaign archive helpers, `configuration`, `previously_on` and `opportunities`. Players are workspace-global; the CampaignPlayer roster links them to campaigns.

## `tablesage-model`

The concrete domain/persistence package. SQLModel tables live in `model/`:

| Model | Responsibility |
| --- | --- |
| Campaign | Campaign metadata and metadata/glossary/roster change clocks |
| Player | Global player identity and computed voice centroid metadata |
| CampaignPlayer | Campaign roster membership |
| Session | Campaign session, sequence/date/status and metadata/attendance clocks |
| SessionAttendance | A session's player attendance |
| SessionAttendanceRole | One or more roles for an attendee |
| GlossaryEntry | Campaign spelling/vocabulary guidance |

Voice clips are files, not VoiceSample rows. Transcripts, Ledger, Scene Breakdown and generated summaries are session files, not separate database tables. `setup/` applies Alembic migrations from `_migrations/` and creates a SQLite engine with foreign keys enabled. `settings/` defines AppSettings; `_paths.py` defines workspace configuration/database locations.

There are no `domain/`, `repository/` or `sqlite/` subpackages or abstract repository seam. For exact fields and constraints consult [the SQLModel declarations](../packages/tablesage-model/src/tablesage_model/model/); migrations define existing database upgrades.

## `tablesage-tools`

Independent media and provider adapters. It includes audio conversion/cleaning/clipping, transcription and diarization providers, embedding extraction, similarity calculation, centroid computation, and text post-processing.

Tools operate on generic inputs, outputs, and explicitly supplied paths. They do not know about TableSage campaigns, players, voice-sample provenance, database records, application filesystem layout, or `AppSettings`.

Tools may compute embeddings and centroids. The application/domain layers decide whether a result becomes a player voice profile, which clips are accepted, and how provenance is persisted.

## Composition and configuration

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

The executable composition root, `tablesage_tui.screens.main_app.main`, checks media tools, creates Configuration, configures logging, loads AppSettings with `ensure_settings`, validates model selections, and constructs Application with that settings snapshot. Application initializes/migrates its database and constructs the SQLite engine itself. `ensure_settings` deploys the TUI's packaged default to `.tablesage/settings.yaml` on first run. Application and session-pipeline helpers may accept settings sections; calls into tools unpack them into plain values.

The Settings screen edits a draft and delegates atomic canonical persistence to
`tablesage_application.configuration.Configuration`. After Save, `Application`
receives a replacement settings snapshot for subsequent actions. Credentials
share the explicit Save lifecycle (in a separate personal file), preserve unrelated dotenv content, and refresh managed process
variables while preserving their inherited shell overrides. An explicit
`settings_version` controls mandatory first-run and upgrade review; an unversioned
file is version zero, and a future version is rejected. Invalid files retain the
terminal-error repair path. See [the Settings design](../.scratch/settings/design.md).

## Artifact lifecycle and verification

[Artifact dependency tracking](../.scratch/artifact-dependency-tracking/design.md) describes the implemented freshness graph. Normal input changes preserve old files and make dependent outputs stale. Generate Outputs ensures dependencies and skips current work; Clean Session explicitly deletes session artifacts, including audio.

Use the [artifact specs](../specs/) for schema and routing contracts. Follow the repository's [verification policy](../.work-items/workflow.md#verification-policy); this architecture does not prescribe a new test suite or an unimplemented fake-repository seam.
