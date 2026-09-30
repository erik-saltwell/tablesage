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
| `players/<player-name>/` | A Player's voice sample audio clips. |
| `campaigns/<campaign-name>/` | A Campaign's files, with numbered session folders such as `001/` containing audio, transcripts, and generated artifacts. |
| `checkpoints/` | The downloaded noise-removal model, stored in the launch directory. It can be downloaded again, so it does not need preserving. |

The database and these files work together: the database holds the records and relationships, while the directories hold audio and documents. To preserve a workspace, keep both its `.tablesage/` directory and its Player and Campaign files.

## Shared API Keys

API keys are the exception to workspace-specific data and settings: they are stored once per user account and shared across workspaces. You can view and edit them through **Settings** (press **S** on the Welcome screen). Changing or removing a stored key there updates the shared credentials used by all TableSage instances and workspaces for that user account. Other workspace data and settings remain separate. See [Where Keys Live](../guides/settings.md#where-keys-live) for details, including how shell environment variables can override stored keys.
