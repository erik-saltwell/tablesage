# Advanced Help

When you aren't sure how to do something in TableSage, or something isn't working, you can ask an AI coding agent such as Claude Code, Codex, or Gemini CLI. Start the agent in your workspace and TableSage has already prepared it: the agent can read TableSage's documentation for the version you have installed, look at your workspace's logs and data, and explain what to do next.

## What You Need

- One of these agents installed and signed in: [Claude Code](https://code.claude.com/docs), [Codex](https://learn.chatgpt.com/docs/codex/cli), or [Gemini CLI](https://github.com/google-gemini/gemini-cli). Each is a separate product from TableSage, with its own account and pricing.
- A workspace TableSage has opened at least once. TableSage prepares the agent the first time it starts in a workspace, and again after each update.

## Ask for Help

1. Open a terminal in your workspace, the directory you launch TableSage from. On the Welcome screen, press **H** (**Advanced Help**) to see that directory's path.
2. Start your agent there: `claude`, `codex`, or `gemini`.
3. Ask your question in your own words.

Questions that work well include:

- *Why can't I open Campaigns?*
- *How do I add a new Player to a Session?*
- *Why did processing stop on Session 3?*
- *What does the Ledger contain, and how is it different from the Summary?*

For a problem, describe what you were doing and what you saw. The agent can check the logs and your Campaign, Session, and Player records to find the cause, then tell you which screen and action fixes it.

## What the Agent Can See and Do

TableSage gives the agent four read-only commands, which you can also run yourself from the workspace:

| Command | What it does |
|---|---|
| `tablesage report-help-topics` | Lists every page of this documentation with a one-line description. |
| `tablesage output-help-topic <topic-id>` | Prints one page, such as `tablesage output-help-topic guides/start-a-campaign`. |
| `tablesage report-schema` | Prints the database structure, its actual and expected migration revisions, and the installed app's expected settings version. |
| `tablesage run-query "<SQL>"` | Runs a database query that can only read. It shows up to 100 rows. |

None of these commands changes your workspace, and the query command can't modify the database. TableSage also tells the agent never to edit TableSage's files and to have you make changes through the app instead. That instruction is guidance, not enforcement: an agent that ignores it could still edit files in your workspace, so check what it proposes before you approve file changes.

All four commands require the workspace folder containing `.tablesage/`. Each prints the installed version and workspace path first. Help topics are copies of the same public documentation available on GitHub, matching the installed application; an editable installation reads its checkout's `docs/`. Use these topics rather than the latest GitHub pages when versions differ. Links written `topic:<id>` refer to other help topics, and image links point to installed image files.

Queries show up to 100 rows and truncate values longer than 200 characters. Use `LIMIT`, `--max-rows N`, or `--full-values` as needed. A missing database or failed query returns an error; the commands do not initialize, migrate, or repair it. Diagnostic commands also avoid interactive startup and app-start logging. Invalid settings do not prevent access to public help.

## Boundaries for Agent Diagnosis

The workspace agent guide points here for these instructions. Application behavior is explained in these public docs; an agent should not inspect application source code or import the application to reconstruct its behavior.

- Never create, edit, move, or delete workspace files under `.tablesage/`, `players/`, or `campaigns/`, and never change the database. Recommend the documented screen and action instead.
- Use `tablesage run-query` for database access; do not open the database through tools that can write.
- Start with file listings, names, dates, completion records, and fingerprints. For processing-state questions, inspect selected metadata using [Processing State and Freshness](../reference/processing-state-and-freshness.md), rather than printing whole JSON files containing review decisions or drafts.
- Do not read Session narrative content for a freshness diagnosis. Local hashing may calculate fingerprints without printing file contents. Do not play audio, open voice samples, or inspect model checkpoints.
- Logs can contain Session text and other private data. Select only the relevant operation, timestamp, and error fields, and avoid prompt logs unless a content-specific question requires them.
- Never print or repeat API keys; report only whether one is configured.
- Use the exact screen, key, and action names documented here. Explain evidence and uncertainty; do not invent recovery actions or silently change the workspace.

## Your Privacy

The agent sends what it reads to its own AI provider. That can include Campaign and Session content, such as transcripts and recaps, from your workspace. TableSage asks the agent to look at names, dates, and processing records before reading content, but whatever it does read leaves your computer. See [Privacy and Data Handling](../reference/privacy.md).

## The Files TableSage Adds

TableSage adds these files to your workspace so the agents can find their instructions:

- `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md` in the workspace directory. Each is a short pointer, read by Claude Code, Gemini CLI, and Codex respectively. TableSage creates a pointer only when the file is missing and never rewrites it afterwards, so you can add your own notes to it.
- `.tablesage/agent-guide.md`, a pointer to the public help topics. TableSage refreshes it at startup when the installed guide template or version changes.

If you already have your own `CLAUDE.md`, `GEMINI.md`, or `AGENTS.md`, TableSage leaves it unchanged. The **Advanced Help** dialog on the Welcome screen says so and shows the line to add to your file so your agent finds TableSage's instructions.

To stop TableSage from adding these files, set `install_agent_files: false` in `.tablesage/settings.yaml`, then delete any of the files you don't want. Without that setting, TableSage recreates missing files the next time it starts.

## If the Agent Says Its Help Is Out of Date

After you update TableSage, commands may warn that `.tablesage/agent-guide.md` is missing or out of date. They continue using the installed app's commands and public help topics; you do not need to start the interactive app before diagnosis. The warning does not mean that the returned help topics are outdated. An old guide may say to stop and launch the app first; follow this page's current instructions instead. A normal launch refreshes the guide when agent files are enabled, but diagnostic commands never rewrite it.

If an old editable installation starts the TUI when you request a report, update or reinstall it so its launcher uses the current CLI. Current source also accepts the legacy `tablesage_tui.screens:main` launcher path. An installed release cannot receive that compatibility change until it is updated.

## Related Pages

- [Troubleshooting FAQ](../reference/troubleshooting-faq.md) answers questions about problems the other pages don't explain. It is the first page the agent reads when diagnosing a problem.
- [Workspaces](../concepts/workspaces.md) describes what each file and folder in a workspace holds.
- [Processing State and Freshness](../reference/processing-state-and-freshness.md) explains completion records, required outputs and inputs, and how stale processing blocks later work.
