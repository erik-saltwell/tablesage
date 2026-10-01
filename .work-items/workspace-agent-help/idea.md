# Workspace Agent Help: Idea

## Intended Effect

A user who is unsure how to use TableSage, or is stuck, can launch a coding agent (Claude Code, Codex, or Gemini CLI) from their TableSage workspace and get accurate help. The agent explains how to operate the app, and it acts as a troubleshooter that diagnoses the user's own workspace state. It is not only a guide to the docs.

Quality is judged against the approved rubric in [intent.md](intent.md#quality-rubric).

## Promising Core

The help is delivered inside the user's real workspace, using agents many users already have. The agent can see the logs, settings, and data, which a docs website cannot. TableSage is a terminal app driven by LLM API keys, so its users are likely to have a coding agent installed.

## Working Direction

The user agreed to everything in this section during the workshop on 2026-10-01. It was refined afterwards in the flesh-out session recorded in [intent.md](intent.md); where the two differ, `intent.md` governs. The main refinements: the read-only commands refuse to run when the guide is stale, the agent-file refresh runs at the top of `main()` and only when the TUI launches, the guide holds no absolute workspace path, `install_agent_files` is read leniently without bumping `SETTINGS_VERSION`, and the Welcome screen **H** key opens a dialog.

### New `tablesage` Commands

Command names are as the user proposed them:

- **`report-schema`** reads the schema directly from the live workspace database and prints it.
- **`run-query`** opens a read-only SQLite connection (for example `mode=ro`) and prints the result of the provided SQL.
- **`report-help-topics`** lists the help topics bundled with the installed version, each with a one-line description.
- **`output-help-topic`** prints one topic. Where the topic has screenshots, it prints the file path of each bundled image in place, so agents that can view images can open them. Image data itself is not written to the output.

These commands must not perform the app's normal startup writes. Today, startup creates a default `settings.yaml` through `ensure_settings` and runs migrations through `ensure_database`. A read-only command should report a problem, such as missing settings, a database that needs migration, or a workspace written by a newer version, rather than fix it or crash. Currently `Configuration.needs_review` raises an error in the newer-version case.

The help topics are the public `docs/` pages, bundled into the installed package. `docs/` is not in the wheel today. `docs/.stversions/` (Syncthing version history) must be excluded from the bundle so old copies don't appear as duplicate topics.

### Agent Context Files

- **`.tablesage/agent-guide.md`** is owned by TableSage and holds all of the real content:
  - the app version it applies to, in a form a regex can extract
  - the on-disk layout of Players, Campaigns, logs, and settings
  - the command lines for calling `tablesage`
  - the rules: never edit anything under `.tablesage/` or the Campaign and Player data, because changes go through the app; read the logs and the Troubleshooting FAQ first when diagnosing; query metadata before transcript content, because content is sent to the agent's LLM provider

  On launch, the app rewrites this file whenever its version differs from the installed version (newer or older), or when the version text can't be found.
- **Root stubs**, each carrying a marker comment such as `<!-- tablesage-managed -->`:
  - `CLAUDE.md` and `GEMINI.md` import the guide with `@.tablesage/agent-guide.md`.
  - `AGENTS.md` tells the agent in plain words to read `.tablesage/agent-guide.md` before answering, because Codex is not known to support imports.
  - File names must be uppercase, because harnesses look for them by exact name on case-sensitive filesystems.
- **Stub handling on launch:**

  | Situation | Action |
  |---|---|
  | File missing | Create the stub |
  | File has the TableSage marker | Leave it alone; content changes go to the guide, so a stub never needs rewriting and the user's additions survive |
  | File exists without the marker (the user's own) | Never modify it; Advanced Help notes this and shows the line to add |

- **Opt-out:** an `install_agent_files` setting (default on) in `settings.yaml`. Without it, stubs the user deleted would be recreated on every launch. Follow the settings conventions in `.agent_context.md`.

### Welcome Screen

Add a call to action and binding, **(H) Advanced Help**, in the style of the existing keyed calls to action in `landing.py`. It explains that launching Claude, Codex, or Gemini from the folder where TableSage was launched gives an agent that is already set up to provide advanced help and diagnostic support, and it shows example questions. When the user's own unmarked agent files prevented installation, it says so and shows the line to add. Help should be available on first launch, before settings are saved, because that is where users first get stuck.

### Documentation

- **Troubleshooting FAQ:** a new help page of questions phrased the way users experience problems, each giving the underlying facts the general docs don't state. For example: "Why are Campaigns and Players disabled?", answered with the comparison between the settings version in `settings.yaml` and the version the app expects. The guide directs the agent to it first when diagnosing, and it is listed with a clear description in `report-help-topics`, so its name can be chosen for people. It follows the documentation style rules in `.agent_context.md`.
- **Advanced Help guide:** a new guide explaining how to get help from an LLM agent with this feature, linked from `docs/guides/index.md`.
- **Welcome screen updates:** update `docs/reference/screens/welcome-and-settings.md` to describe the new binding, and retake every Welcome screenshot:
  - `docs/images/getting-started/landing-screen.png`, used in the README
  - `docs/images/screens/landing.png`, used in `welcome-and-settings.md`
  - `docs/images/screens/landing-settings-required.png`, used in `welcome-and-settings.md` and `getting-started/installation.md`

### Validating the Bet

Before relying on the feature, create four or five deliberately broken workspaces and check whether Claude Code and Codex diagnose each correctly:

- settings not saved
- a missing API key
- a Session stopped partway through processing
- a Player without a voice print
- a failed transcription recorded in the logs

Failures show which facts the Troubleshooting FAQ is missing, or which checks a future `doctor` would need. This is a behavior-level check, not an automated test suite.

## How the Idea Evolved

1. **Original idea:** write one compressed, single-file copy of the docs into `CLAUDE.md` and `AGENTS.md` at setup. This was rejected because about 26,700 words (roughly 35k tokens) would load into every conversation (an earlier estimate of 61,000 words was wrong because it counted the `docs/.stversions/` history copies), compression loses exact button names and steps, and the copy goes stale after upgrades.
2. **Docs come from the installed app:** help commands read the installed version's docs, which removes staleness and loads only the pages needed.
3. **Read-only database queries were added** for diagnosis. Read-only is enforced by the connection rather than requested by instruction, and a sanctioned route reduces the temptation to use writable tools such as `sqlite3` or Python scripts.
4. **An in-app help panel with consent to install was rejected.** The user chose a Welcome screen call to action with automatic installation instead.
5. **A `doctor` command was considered and deferred.** It would have reported workspace state and run blocked-state checks, ideally by calling the app's own rules. The user bet that a flexible LLM with the docs, files, logs, schema, and read-only queries will diagnose better than fixed checks, while avoiding a refactor and a second copy of the rules. The agent's caution, which the user accepted: docs describe rules in user terms, not storage terms. The Troubleshooting FAQ and the validation test address this. `doctor` remains an option if testing shows gaps.
6. **"Workspace facts" became the Troubleshooting FAQ:** questions in user language help both people and the agent.
7. **Root files became stubs** pointing to a TableSage-owned guide, so version changes never touch files the user can see or edit.

## Assumptions and Known Risks

- An LLM can reliably connect documentation-level rules to raw data and logs. This is the central bet, and it is unverified until the validation test.
- Codex follows the plain-language "read this file first" instruction. It is slightly less dependable than the import used by Claude Code and Gemini CLI.
- Session files and other data on disk are protected from agent edits only by the instruction; only database access is technically read-only.
- Querying transcript content sends it to the agent's LLM provider. The guide and `docs/reference/privacy.md` should say so.
- Exact Codex and Gemini CLI context-file behavior should be checked against their current documentation when designing the feature.

## Set Aside

- **`llms.txt`:** the docs are hosted only in the GitHub repo, not on a docs site. Reconsider if a docs site is published.
- **`doctor`:** deferred, as described above.
