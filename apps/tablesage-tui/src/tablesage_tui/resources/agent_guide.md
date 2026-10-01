# TableSage Workspace Guide for Coding Agents

This folder is a TableSage workspace. TableSage is a terminal app that turns recorded tabletop roleplaying sessions into transcripts, recaps, and campaign notes; the user runs it by typing `tablesage` in this folder. Help them use it, and work out why something isn't working.

TableSage $version wrote this guide. This version expects `settings_version: $settings_version` in `.tablesage/settings.yaml`.

## Rules

- Never create, edit, move, or delete anything under `.tablesage/`, `players/`, or `campaigns/`, and never change the database. TableSage keeps files and database records in step, and hand edits break that. Tell the user which screen and action makes the change instead.
- Use `tablesage run-query` for the database. Don't open it with `sqlite3`, Python, or any other tool that can write.
- Look at metadata before content. Transcripts, recaps, and other Session content you read or query are sent to your AI provider, so read them only when the question needs them.
- Never print or repeat API keys. TableSage stores them outside the workspace; report only whether one is set.
- Don't open audio files or anything in `checkpoints/`.
- Use the exact screen, key, and action names the help topics use. Say when you're unsure rather than guessing.

## Commands

Run these from this folder, the one containing `.tablesage/`. They only read; none of them changes the workspace. Each prints a first line with the installed TableSage version and the workspace path.

- `tablesage report-help-topics` lists every help topic with a one-line description.
- `tablesage output-help-topic <topic-id>` prints one topic, for example `tablesage output-help-topic guides/start-a-campaign`. Links written `topic:<id>` point to other topics. Images appear as absolute file paths; open one only if you can view images and it would help.
- `tablesage report-schema` prints the database's tables and indexes and its migration revision.
- `tablesage run-query "<SQL>"` runs one read-only SQL statement and prints up to $max_rows rows, cutting long values at $max_cell_chars characters. Add `LIMIT`, `--max-rows N`, or `--full-values` when you need something else.

If a command's first line shows a different version from the one at the top of this guide, or a command says the help is out of date, ask the user to run `tablesage` once in this folder (they can quit straight away), then try again.

## How to Help

- For how-to questions, run `tablesage report-help-topics`, then read the topics that fit.
- When something isn't working, read the `reference/troubleshooting-faq` topic first. It covers what the user-facing pages leave out, including how stored data maps to what the screens show. Then check the evidence: recent events in `.tablesage/logs/tablesage.log`, the Session's `processing_state.json`, and the database through `run-query`.
- The `concepts/workspaces` topic describes the full workspace layout.

## Workspace Map

- `.tablesage/` is TableSage's internal folder. It holds `tablesage.db` (SQLite: Campaigns, Sessions, Players, attendance, Roles, and Glossary entries), `settings.yaml`, and `logs/`. `logs/tablesage.log` has one JSON event per line; `logs/prompts/` holds traced LLM prompts and outputs, which contain Session content.
- `players/<Player name>/` holds each Player's voice samples, which are audio. Don't open them.
- `campaigns/<Campaign name>/<NNN>/` is one folder per Session, named by its three-digit sequence number (`001`, `002`, …). It holds the recording, transcripts, generated outputs, and `processing_state.json`, which records each processing step's completion, review decisions, saved drafts, and last failure.
- `checkpoints/` is a downloaded audio model. Ignore it.
- `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` point to this guide.
