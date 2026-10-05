# Advanced Help

When you aren't sure how to do something in TableSage, or something isn't working, you can ask an AI coding agent such as Claude Code, Codex, or Gemini CLI. Start the agent in your workspace and TableSage has already prepared it: the agent can read TableSage's documentation for the version you have installed, look at your workspace's logs and data, and explain what to do next.

## What You Need

- One of these agents installed and signed in: [Claude Code](https://code.claude.com/docs), [Codex](https://learn.chatgpt.com/docs/codex/cli), or [Gemini CLI](https://github.com/google-gemini/gemini-cli). Each is a separate product from TableSage, with its own account and pricing.
- A workspace TableSage has opened at least once. TableSage prepares the agent the first time it starts in a workspace, and again after each update.

## Ask for Help

1. Open a terminal in your workspace, the directory you launch TableSage from.
2. Start your agent there: `claude`, `codex`, or `gemini`.
3. Ask your question in your own words.

Questions that work well include:

- *Why can't I open Campaigns?*
- *How do I add a new Player to a Session?*
- *Why did processing stop on Session 3?*
- *What does the Ledger contain, and how is it different from the Summary?*

For a problem, describe what you were doing and what you saw. The agent can check the logs and your Campaign, Session, and Player records to find the cause, then tell you which screen and action fixes it.

## Your Privacy

The agent sends what it reads to its own AI provider. That can include Campaign and Session content, such as transcripts and recaps, from your workspace. TableSage asks the agent to look at names, dates, and processing records before reading content, but whatever it does read leaves your computer. See [Privacy and Data Handling](../reference/privacy.md).

## Related Pages

- [Troubleshooting FAQ](../reference/troubleshooting-faq.md) answers questions about problems the other pages don't explain. It is the first page the agent reads when diagnosing a problem.
- [Workspaces](../concepts/workspaces.md) describes what each file and folder in a workspace holds.
- [Processing State and Freshness](../reference/processing-state-and-freshness.md) explains completion records, required outputs and inputs, and how stale processing blocks later work.
