# Workspace Agent Help: Intent

## Intended Outcome

A user who is unsure how to use TableSage can start a coding agent (Claude Code, Codex, or Gemini CLI) in their workspace and get accurate help. That help covers both how to operate the app and why their own workspace is behaving the way it is.

## Scope

Fleshed out with the user on 2026-10-01 after the workshop recorded in [idea.md](idea.md). Where the two differ, this document governs.

In scope:

- Four read-only subcommands of `tablesage`.
- A TableSage-owned agent guide, thin root stubs for the three agent harnesses, and an opt-out setting.
- A Welcome screen **(H) Advanced Help** call to action that opens a dialog.
- Bundling the public docs into the installed package so the help commands serve the installed version.
- Documentation: a Troubleshooting FAQ, an Advanced Help guide, pointers from existing pages, and updated Welcome screen references and screenshots.

Out of scope for now:

- A `doctor` command (deferred; see [idea.md](idea.md#how-the-idea-evolved)).
- `llms.txt`.
- A Settings screen toggle for the opt-out.
- Error-toast pointers to Advanced Help.
- Any enforcement against agents editing files on disk; only database access is technically read-only.

## Expected Behavior

### Subcommands

`tablesage` with no arguments launches the TUI exactly as today. The four subcommands are dispatched at the very top of `main()`, before `ensure_media_tools`, `configure_logging`, `ensure_settings`, and `validate_models`, so they perform none of the app's startup writes:

- **`report-help-topics`** lists the bundled help topics, grouped by docs section (getting-started, concepts, guides, reference). Each entry has an ID, a title, and a one-line description.
- **`output-help-topic <id>`** prints one topic.
- **`run-query "<SQL>"`** runs SQL over a read-only connection.
- **`report-schema`** prints the schema.

Shared rules:

- **Workspace resolution:** the workspace is the current folder only. If there is no `.tablesage/` there, the command prints "No TableSage workspace in this folder" with the folder's path and exits non-zero. It never creates anything. This needs a non-creating way to resolve paths, because `_resolve_tablesage_dir` in `_paths.py` currently calls `mkdir`.
- **Header:** every command's output starts with a line such as `TableSage 0.1.0 · workspace /abs/path`.
- **Read-only only:** a command that finds a problem (missing settings, a database needing migration, a workspace written by a newer version) reports it instead of fixing it or crashing. `Configuration.needs_review` currently raises in the newer-version case, so these commands must handle that.
- **Staleness gate:** before doing anything else, each command checks whether the agent guide is stale. If it is, the command prints only a message asking the user to run `tablesage` once to update the help, and does no other work. The message says the app may be closed or may report an error, since the refresh happens first. The check is skipped when `install_agent_files` is false.

Per-command details:

- **Help topics:** one topic per docs page. The ID comes from the path (`guides/start-a-campaign`), the title from the page's H1, and the description from its first paragraph. No manifest is maintained. In printed output, relative links between pages become topic IDs (including anchors), and image links become absolute file paths to the bundled images; image data is never printed.
- **`run-query`:** opens SQLite with `mode=ro` and also sets `PRAGMA query_only = ON`. Output is a plain aligned table, capped at 100 rows by default, with a final line such as "100 of 4,312 rows shown; add LIMIT or narrow the query." Very long cell values (for example transcript text) are truncated to a fixed width with a "…(N more characters)" marker. `--max-rows N` lifts the row cap, and a flag lifts truncation. SQL is not parsed; the connection mode is the guarantee.
- **`report-schema`:** prints the database's own `CREATE TABLE` text from SQLite's catalog, excluding internal and migration tables, with a header line giving the migration revision the database is at and the revision this app version expects. A mismatch is reported only.

### Agent Files

- **`.tablesage/agent-guide.md`** is TableSage's own file. It contains:
  - the app version, in a regex-readable form;
  - a short map of the top-level folders (`.tablesage/`, `players/`, `campaigns/<name>/<NNN>/`, `checkpoints/`), with what to avoid in each: session folders hold audio, so do not open it; `checkpoints/` is a model download, so ignore it. It points to the `concepts/workspaces` topic for the full layout.
  - the command lines for the four subcommands, and a statement that the workspace is the folder containing `.tablesage/`, with commands run from there (no absolute path, because the header line of every command prints it);
  - the rules: never edit anything under `.tablesage/` or the Player and Campaign data, because changes go through the app; read the logs and the Troubleshooting FAQ first when diagnosing; query metadata before transcript content, because content is sent to the agent's LLM provider;
  - an instruction to tell the user to relaunch TableSage if a command's header version differs from the version in the guide.
- **Root stubs** (`CLAUDE.md`, `GEMINI.md`, `AGENTS.md`, uppercase) each carry a marker comment such as `<!-- tablesage-managed -->`. `CLAUDE.md` and `GEMINI.md` import the guide with `@.tablesage/agent-guide.md`. `AGENTS.md` tells the agent in plain words to read `.tablesage/agent-guide.md` before answering, because Codex is not known to support imports.
- **When it runs:** only when the TUI launches, at the very top of `main()` before `ensure_media_tools`, `ensure_settings`, and `validate_models`, so a launch refreshes the files even if later startup fails. Read-only subcommands never write.
- **Stale means:** the guide is missing, has no readable version, or its version differs from the installed version (newer or older). A missing or user-owned stub does not make it stale. The check is version-only.
- **Stub handling:**

  | Situation | Action |
  |---|---|
  | File missing | Create the stub |
  | File has the TableSage marker | Leave it alone (the user's additions survive; content lives in the guide) |
  | File exists without the marker (the user's own) | Never modify it; Advanced Help says so and shows the line to add |

- **Opt-out:** `install_agent_files` is a top-level boolean in `settings.yaml`, default `true`, added to `AppSettings` and the packaged `settings.yaml` following the settings convention in `.agent_context.md`. `SETTINGS_VERSION` is not bumped, because a bump would lock every existing user out of Campaigns and Players until they re-save. The early read at the top of `main()` is lenient: a missing file, a parse error, or a missing key all mean `true`, so a broken settings file never prevents help from being installed. The setting is not on the Settings screen; Advanced Help and its guide document it as a line to edit in `.tablesage/settings.yaml`.

### Welcome Screen

A new call to action in the existing style (`> type H for advanced help`) and an **H** binding. It opens a modal dialog containing:

- a short explanation that launching Claude, Codex, or Gemini from this folder (shown) gives an agent that is already set up to help with TableSage and diagnose problems;
- three or four example questions, for example "Why can't I open Campaigns?", "How do I add a new Player to a Session?", "Why did processing stop on Session 3?";
- a status line for the agent files: installed; or not installed because the user already has their own unmarked file, with the line to add; or turned off in settings;
- a note that agent help sends workspace data to the agent's LLM provider;
- Esc to close.

The launch-time install result is kept on the app, as `settings_review_required` is. The call to action and dialog are available on first launch, before settings are saved. Text must fit the dialog's one screen; the full explanation lives in the Advanced Help guide.

### Bundling

`docs/` is bundled at build time through a Hatch `force-include` into the wheel (for example under `tablesage_tui/resources/docs`), excluding `docs/.stversions`. `docs` is also added to the sdist `only-include`. When running from a source checkout, the help code falls back to the repo's `docs/`. The wheel is built from the repository for `uv tool install git+https://…`, so this must work from there too.

### Documentation Changes

Following the documentation style rules in `.agent_context.md`:

- **Troubleshooting FAQ:** a new page of questions phrased the way users experience problems, each giving the underlying facts the general docs omit. The seed has about eight to twelve entries. The top section covers scenarios where the user or the app can be blocked for implementation reasons that the user-facing docs do not address. Other candidate entries: what each Session processing state means in app terms; what soft-deleted records look like in queries (to be verified in code before writing); where logs are and which lines show a failed step; where API keys come from and how shell environment variables override them; why Campaigns and Players are locked. Symptoms already covered by `installation.md` or `review-and-export.md` get a one-line pointer, not a copy. The first paragraph says when to use it first, because that line is its description in `report-help-topics`.
- **Advanced Help guide:** a new guide explaining how to get help from an LLM agent using this feature, linked from `docs/guides/index.md`.
- **Pointers:** a sentence and link to Advanced Help at the end of **If TableSage Does Not Start** in `installation.md` and **If Something Fails** in `review-and-export.md`, plus entries in the README's documentation list and the installation page's **Next Steps**.
- **Welcome screen pages:** update `docs/reference/screens/welcome-and-settings.md` for the new binding and dialog. Retake `docs/images/getting-started/landing-screen.png` (README), `docs/images/screens/landing.png`, and `docs/images/screens/landing-settings-required.png` (used in `welcome-and-settings.md` and `installation.md`).
- **Privacy:** update `docs/reference/privacy.md` to say that agent queries and file reads send workspace content to the agent's LLM provider.

## Acceptance Conditions

Checked by behavior, with no unit tests, per `.work-items/workflow.md`.

- From an installed wheel (not the checkout), `tablesage report-help-topics` lists every docs page, `.stversions` is absent, and `tablesage output-help-topic <id>` prints the page with working topic IDs and absolute image paths.
- In a workspace, `run-query` returns rows over a read-only connection and refuses a write statement (`INSERT`, `UPDATE`, `DELETE`, `DROP`) without changing the database; rows are capped as described.
- In a folder with no `.tablesage/`, every subcommand reports there is no workspace, exits non-zero, and creates nothing.
- With the guide missing or at a different version, each subcommand prints only the "run `tablesage` once" message; after one TUI launch, even when startup then fails (for example a missing `ffmpeg`), the subcommands work.
- A fresh launch creates `.tablesage/agent-guide.md` and the three marked stubs. A pre-existing unmarked `AGENTS.md` or `CLAUDE.md` is left byte-identical, and the Advanced Help dialog reports it. With `install_agent_files: false`, nothing is created and the staleness gate never fires.
- Pressing **H** on the Welcome screen, including on first launch before settings are saved, shows the dialog; layout is verified with headless `run_test()` checks of widget regions.
- `uv build` output contains the docs and images; the new and updated screenshots are retaken; the docs pass the style rules.
- The broken-workspace test in [idea.md](idea.md#validating-the-bet) is run with Claude Code and Codex; the results decide what the Troubleshooting FAQ needs next and whether a `doctor` command is justified.

## Settled Decisions and Reasons

- **Subcommands, not flags or a second entry point:** dispatching before startup is the only way to keep these commands free of startup writes.
- **Strict current-folder workspace resolution:** this keeps the app's launch-folder rule and prevents a stray `.tablesage/` from being created by an agent in the wrong directory.
- **Read-only subcommands never write, and the guide refreshes only on TUI launch:** this keeps "read-only" literally true. The staleness gate plus a version header turns the post-upgrade gap into a clear instruction. The refresh runs first so help is not blocked when the app cannot start.
- **Output capped, enforced by the connection:** the cap protects context economy, and the connection mode is the real data-safety guarantee.
- **One topic per page, derived automatically:** no manifest to maintain, and pages are small enough to print whole (the largest is about 2,300 words).
- **`docs/` bundled by `force-include`:** one source of truth with no sync step.
- **A new setting without a version bump, read leniently:** a bump would lock existing users out, and a broken settings file is a likely reason for needing help.
- **Version-only staleness (the user's choice, over the agent's recommendation of comparing the full rendered text):** simpler and readable. The known consequences are that guide template edits reach users only when the version changes, so that must be part of the release process, and that moving a workspace does not affect the guide because it holds no absolute path.
- **A short folder map in the guide, with the full layout left to `concepts/workspaces`:** one copy of the detailed layout.
- **Raw `CREATE TABLE` text for the schema:** exact and cheap, with meanings in the FAQ.
- **A seed FAQ, not a comprehensive one:** the data-meaning gap is the main risk to the central bet, and the validation test shows what else is missing.
- **Pointers in existing troubleshooting sections:** these are where stuck users already read.

## Unresolved Questions

- How the FAQ states which settings version the app expects without hard-coding a number that drifts, and whether `report-help-topics` or the header should expose it.
- Exact output formats, exit codes, and wording of the "run `tablesage` once" message and the no-workspace message.
- The agent guide's exact text, the example questions, and the FAQ entries beyond the candidates above.
- Whether the row cap (100), the cell-width limit, and `--max-rows` belong in `settings.yaml` or as plain command defaults. The settings rule in `.agent_context.md` covers calls from the TUI into `tablesage-tools`; where this code lives (application or tools) has not been decided.
- Which package holds the new code and the bundled-docs path.
- Whether Codex and Gemini CLI load `AGENTS.md`, `GEMINI.md`, and `@` imports as assumed; verify against their current documentation.
- Whether soft-deleted records are represented in the database as assumed (verify in code before writing the FAQ entry).
- The wording of the "line to add" shown for a user's own unmarked file.

## Quality Rubric

Approved by the user on 2026-10-01. The dimensions are qualitative: they are judged in words, without scores, rating scales, anchors, weights, or thresholds.

**Subject:** the agent context files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) and supporting documentation that TableSage installs into a user's workspace.

1. **Answer fidelity:** How closely the agent's answers match what the app really does: exact screen and button names, the correct step order, and the real conditions that enable or block an action. It rewards answers a user can follow at the keyboard without having to translate. Fidelity should hold in each supported harness, not only the one used to develop the feature.
2. **Situational diagnosis:** How well the agent uses the user's actual workspace (settings, Campaign and Session state, logs) to explain why something is happening to them and what to do next, rather than repeating general documentation.
3. **Currency:** Whether the help still describes the installed version of TableSage after upgrades. This is separate from fidelity, because help can be exactly right on day one and wrong after the next release.
4. **Context economy:** How little each question costs in tokens and attention. The agent reads what it needs rather than carrying all the documentation every time.
5. **Data safety:** Whether getting help leaves Campaign, Session, and settings data intact. Changes should go through the app, and the agent should not hand-edit stored artifacts.
6. **Workspace courtesy:** How respectfully the feature treats a folder the user owns. It shouldn't overwrite the user's own agent files, should make clear what it added and why, and should be easy to decline or remove.
7. **Discoverability:** How readily a user who is stuck learns that this help exists and how to start it, whether from the app, the install docs, or the README. It rewards help that reaches the people who need it, not just help that works once someone finds it.
8. **Maintenance burden:** How little ongoing effort it takes the developer to keep the feature working and accurate. This is separate from currency, because the help could be kept current by hand at a high cost.

### Tradeoffs

- Situational diagnosis and data safety pull against each other. The more of the workspace the agent inspects, the more it will be tempted to edit.
- Context economy and answer fidelity also pull against each other. Compressing or summarizing the docs saves tokens but loses exact names and steps.

### Decisions Made While Defining the Rubric

- Situational diagnosis was added because the user wants the agent to act as a troubleshooter, not only as a guide to the docs.
- Discoverability was added because the feature's purpose is to reach users who don't know how to use the app.
- Harness parity was removed as a separate dimension at the user's direction. A note under answer fidelity covers consistency across harnesses.
