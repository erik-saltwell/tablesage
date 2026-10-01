# Workspace Agent Help: Progress

Implementation started 2026-10-01 at the user's request, directly after fleshing-out; no `plan.md` was written. This file is the handoff.

## Done: Code

- **Subcommands:** `apps/tablesage-tui/src/tablesage_tui/cli.py` is the new entry point for `tablesage` and `tablesage-rpg` (`pyproject.toml` scripts and `tablesage_tui/main.py`). With no arguments it calls `screens.main_app.main()` unchanged in role. The four read-only commands are handled before any startup work.
- **Application layer:** `tablesage_application.agent_help` contains:
  - `agent_files.py`: the guide, stubs, staleness check, and lenient opt-out read;
  - `help_topics.py`: topics derived from docs pages, with link rewriting;
  - `database.py`: the `mode=ro` + `query_only` connection, query cap, table formatting, schema, and revision.
- **Paths and model:** non-creating `workspace_state_dir`, `database_path`, and `settings_path` in `tablesage_application.paths`, and `expected_database_revision()` in `tablesage_model.setup`.
- **Guide template:** `tablesage_tui/resources/agent_guide.md`. The guide records the version and the expected `settings_version` (`SETTINGS_VERSION`), which resolves the intent's open question about how the expected settings version is exposed. `tablesage_tui/agent_help.py` renders it and holds the `run-query` defaults (100 rows, 200 characters).
- **Setting:** `install_agent_files: bool = True` in `AppSettings` and the packaged `settings.yaml`, with no `SETTINGS_VERSION` bump. It is not on the Settings screen, which only shows keys and models.
- **Welcome screen:** an **H** binding and `> type H for advanced help` call to action open `dialogs/advanced_help.py`. The launch status is stored on `TableSageApp.agent_files`.
- **Bundling:** `pyproject.toml` spells out the wheel's `packages` as `only-include` plus `sources`, adding `docs` mapped to `tablesage_tui/resources/docs`, with `exclude = ["docs/.stversions"]`. The sdist also includes `docs`. `tablesage_tui.resources.docs_directory()` falls back to the checkout's `docs/`.

## Deviations From the Intent

- **Refresh timing:** the agent-file refresh runs at the top of `main()` only when `.tablesage/` already exists. A new workspace gets its files just after `ensure_media_tools()`. The reason is that the existing test `test_main_stops_before_creating_workspace_when_media_tools_missing` protects a deliberate rule: a folder TableSage can't run in must never become a workspace. The upgrade case the intent cared about (an existing workspace whose startup then fails) is still refreshed first.
- **Separate entry point:** the subcommands live in a new `cli.main` rather than inside `main_app.main()`, because tests call `main_app.main()` directly under pytest's own `sys.argv`.
- **Defaults are not settings:** `run-query`'s row and width limits are command defaults with `--max-rows` and `--full-values`. They are not in `settings.yaml`, because the code calls no `tablesage-tools` function and the read-only commands must not depend on loading settings.
- **Welcome layout:** to fit the fourth call to action, the panel grew from 31 to 32 rows and the space above the actions shrank from 2 rows to 1.
- **Stub wording:** "delete this file" alone is not an opt-out, because a deleted stub is recreated. The stub says to set the setting first.
- **Bundling mechanism:** the intent named Hatch `force-include`, but a wheel built directly from this working tree then carried 39 `docs/.stversions` files, because `force-include` ignores `exclude`. `only-include` plus `sources` honors it. Apart from the new files, the package files match a wheel built from `HEAD`.
- **FAQ correction:** the intent assumed soft-deleted records. In fact, Delete removes the database record and leaves the folder on disk until Clean Up (`docs/concepts/delete-and-clean.md`).
- **Staleness entry:** the FAQ's staleness entry follows `review-and-export.md`. Changes to attendance, Roles, dates, the Glossary, and models are not fingerprinted, so outputs stay marked current after them.
- **Extra screenshot:** a new `docs/images/screens/advanced-help.png` illustrates the dialog on the Welcome reference page. The dialog's last paragraph has no bottom margin, so the button row's own margin is the only gap.

## Verification So Far

- `ruff check`, `ruff format --check`, and `ty check` pass.
- Existing tests (`apps/tablesage-tui`, `packages/tablesage-application`, `packages/tablesage-model`): 689 pass and 3 fail. The failures are `test_campaign_detail.py::test_new_session_*`. They were reproduced on a clean `HEAD` worktree with only the user's uncommitted `session_editor.py` and `campaign_detail.py` edits applied (the new required Session date), so they are unrelated to this work.
- Direct checks in scratch workspaces under `/tmp`:
  - no workspace: exit 2, nothing created;
  - fresh launch: guide and three stubs created;
  - stale or missing guide: exit 3 with the message;
  - launch with `ffplay` missing on an existing workspace: the guide is refreshed before the failure;
  - the user's own `CLAUDE.md` and `AGENTS.md` are byte-identical after launch, and additions to a managed stub survive;
  - `install_agent_files: false`: nothing created and no gate;
  - broken `settings.yaml`: files are still installed;
  - `run-query`: 100-row cap with an "N of M" line, truncation marker, `--full-values`, and `DELETE`, `DROP`, `INSERT`, and multiple statements all refused with an unchanged database checksum;
  - `report-schema`: prints the revision and `CREATE` text;
  - help topics: 31 listed, `topic:` links, absolute image paths, unknown topic gives exit 2.
- Headless `run_test()` regions: all four calls to action, the Welcome panel, and the dialog fit at 140×44 and 100×36; Esc closes the dialog.

## Done: Documentation and Screenshots

- **New pages:**
  - `docs/guides/advanced-help.md`, titled "Advanced Help" as the user named it.
  - `docs/reference/troubleshooting-faq.md`. Its top section covers blocked scenarios: the settings-version lock, an invalid settings file, leftover-folder prompts and Session number reuse, folders renamed by hand, out-of-date outputs and the changes that aren't tracked, and discarded drafts. Further sections cover failures and logs, keys, and how to read workspace data.
- **Pointers:** `guides/index.md`, `installation.md` (troubleshooting and Next Steps), `review-and-export.md` (If Something Fails), and the README's Learn More list and image alt text.
- **Updated pages:** `reference/screens/welcome-and-settings.md` (four calls to action, **H** in the key table, and an Advanced Help section), `concepts/workspaces.md` (rows for the agent files), and `reference/privacy.md` (what agents send; files on disk). The user's uncommitted edits to `installation.md` and `guides/index.md` were kept; entries were only added.
- **Screenshots:** `landing.png`, `landing-settings-required.png`, `getting-started/landing-screen.png` (a copy of `landing.png`), and the new `advanced-help.png`, all 1726×1124. They were captured at 140×44 with the Textual MCP and rendered by `.for-docs/screens/save.sh`. The capture steps are recorded in `.for-docs/screens/README.md` (git-ignored), along with its new `advanced_help_app` factory.
- **Link check:** every link and image in the 34 docs and README pages resolves, including anchors.

## Packaging Verification

- `uv build` from the sdist and `uv build --wheel` from the working tree list identical files: 33 doc pages, 55 images, and no `.stversions`.
- The wheel was installed with `--no-deps` into a fresh venv outside the checkout. `docs_directory()` resolved inside the installed package. `report-help-topics` listed the new pages, `output-help-topic` produced `topic:` links with anchors and absolute image paths that exist inside the installed package, and `run-query` and `report-schema` worked.

## Review Follow-Ups

- **Command speed:** each command took about 2.3 s because `tablesage_application/__init__.py` eagerly imported `Application` and the audio/ML stack. Its exports are now loaded on first use (PEP 562 `__getattr__`), and every subcommand takes about 0.26 s. An agent may call these many times per question.
- **FAQ entry removed:** the export-blocked entry depended on a `session.status = 'processing'` value that `git log -S` shows no version of the app ever wrote (only tests set it), so it was removed rather than published as a guess.
- **Links and types:** the external agent links point at their current addresses (Claude Code docs moved to code.claude.com; Codex CLI docs to learn.chatgpt.com). `mypy` on the changed modules reports only the missing PyYAML stubs, which existing modules hit as well.
- **Open question for the user:** launching TableSage in the home folder, or in repo subfolders during development, now creates `CLAUDE.md` and `GEMINI.md` there too. Claude Code and Gemini CLI read context files from parent folders, so in the home folder the guide would load into every coding session below it. A guard (for example, skip the root stubs when the workspace is the home folder) has not been implemented; it awaits the user's decision.

## Final Checks

`ruff check`, `ruff format --check`, and `ty check` pass. The existing suites give 689 passed and 3 failed; the three are the same `test_campaign_detail.py::test_new_session_*` failures caused by the user's uncommitted required-date change, as above. No tests were added.

## Remaining (Carried Over at Completion)

The item was marked complete on 2026-10-01 at the user's request with the following not done:

- **Not run: the broken-workspace validation of the central bet.** Set up four or five deliberately broken workspaces and ask Claude Code and Codex to diagnose them, then refine the Troubleshooting FAQ and decide whether `doctor` is needed. This needs those agents run by the user. Gemini CLI's handling of `@` imports and Codex's handling of `AGENTS.md` are also confirmed only by this run.
- No rubric evaluation has been recorded. Every dimension in [intent.md](intent.md#quality-rubric) is unassessed.
- Nothing is committed.
