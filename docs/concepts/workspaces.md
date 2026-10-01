# Workspaces

A **workspace** is the directory where TableSage keeps your game data. It brings together your Players, Campaigns, Sessions, settings, and processing records. One workspace can hold several Campaigns and the Players who take part in them.

## A Workspace and an Installation

The [installation](../getting-started/installation.md) workflow installs the TableSage application. You choose its workspace by starting the application from the directory where you want your data to live:

```sh
cd ~/Documents/tablesage
tablesage-rpg
```

Start TableSage from that same directory to return to your existing data. The same installation can open another workspace by launching from a different directory; each workspace has its own database, settings file, Players, and Campaigns. TableSage creates its internal `.tablesage/` directory on first launch.

## What Lives in a Workspace

Paths below are relative to the workspace directory.

| Path | Purpose |
|---|---|
| `.tablesage/tablesage.db` | The database of Players, Campaigns, Sessions, attendance, Roles, Glossaries, and stored voice prints. |
| `.tablesage/settings.yaml` | This workspace's [settings](../guides/settings.md), including model choices and processing options. |
| `.tablesage/logs/` | Application and processing logs, including `tablesage.log`, used to understand activity and diagnose problems. |
| `.tablesage/agent-guide.md` | Instructions for an AI coding agent started in the workspace, replaced whenever a different version of TableSage starts. See [Advanced Help](../guides/advanced-help.md). |
| `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` | Short pointers that lead Codex, Claude Code, and Gemini CLI to the agent guide. TableSage creates them when missing and never changes them afterwards. |
| `players/<player-name>/` | A Player's voice sample audio clips. |
| `campaigns/<campaign-name>/` | A Campaign's files, with numbered session folders such as `001/` containing audio, transcripts, and generated artifacts. |
| `checkpoints/` | The downloaded noise-removal model, stored in the launch directory. It can be downloaded again, so it does not need preserving. |

The database and these files work together: the database holds the records and relationships, while the directories hold audio and documents. To preserve a workspace, keep both its `.tablesage/` directory and its Player and Campaign files.

## Shared API Keys

API keys are stored once per user account and shared across workspaces. You can edit them in **Settings** (press **S** on the Welcome screen). Saving a key change updates the shared credentials file and the instance where you saved it. Other running instances retain their loaded keys; restart them to use the change. See [Where Keys Live](../guides/settings.md#where-keys-live) for details, including how shell environment variables can override stored keys.
