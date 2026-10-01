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
| `tablesage report-schema` | Prints the structure of the workspace database. |
| `tablesage run-query "<SQL>"` | Runs a database query that can only read. It shows up to 100 rows. |

None of these commands changes your workspace, and the query command can't modify the database. TableSage also tells the agent never to edit TableSage's files and to have you make changes through the app instead. That instruction is guidance, not enforcement: an agent that ignores it could still edit files in your workspace, so check what it proposes before you approve file changes.

## Your Privacy

The agent sends what it reads to its own AI provider. That can include Campaign and Session content, such as transcripts and recaps, from your workspace. TableSage asks the agent to look at names, dates, and processing records before reading content, but whatever it does read leaves your computer. See [Privacy and Data Handling](../reference/privacy.md).

## The Files TableSage Adds

TableSage adds these files to your workspace so the agents can find their instructions:

- `CLAUDE.md`, `GEMINI.md`, and `AGENTS.md` in the workspace directory. Each is a short pointer, read by Claude Code, Gemini CLI, and Codex respectively. TableSage creates a pointer only when the file is missing and never rewrites it afterwards, so you can add your own notes to it.
- `.tablesage/agent-guide.md`, the agent's instructions. TableSage replaces it whenever you start a different version of TableSage.

If you already have your own `CLAUDE.md`, `GEMINI.md`, or `AGENTS.md`, TableSage leaves it unchanged. The **Advanced Help** dialog on the Welcome screen says so and shows the line to add to your file so your agent finds TableSage's instructions.

To stop TableSage from adding these files, set `install_agent_files: false` in `.tablesage/settings.yaml`, then delete any of the files you don't want. Without that setting, TableSage recreates missing files the next time it starts.

## If the Agent Says Its Help Is Out of Date

After you update TableSage, the agent's commands may report that the help is missing or out of date. Run `tablesage` once in the workspace to refresh it. You can quit straight away, and the refresh happens even if TableSage then reports a startup problem. Then ask your question again.

## Related Pages

- [Troubleshooting FAQ](../reference/troubleshooting-faq.md) answers questions about problems the other pages don't explain. It is the first page the agent reads when diagnosing a problem.
- [Workspaces](../concepts/workspaces.md) describes what each file and folder in a workspace holds.
