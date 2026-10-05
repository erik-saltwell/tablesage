# Troubleshooting FAQ

Answers to problems the other pages don't explain, including how TableSage's stored data relates to what its screens show. If you are an AI agent diagnosing a problem in a TableSage workspace, read this page first.

Most questions here are about things that happen behind the screens, so they mention files in the workspace and database tables you can inspect with `tablesage run-query`. See [Advanced Help](../guides/advanced-help.md) for those commands. Don't edit TableSage's files or database by hand: make changes in TableSage itself.

For problems with installing or first launching TableSage, see [If TableSage Does Not Start](../getting-started/installation.md#if-tablesage-does-not-start). For failed regeneration or export, see [If Something Fails](../guides/review-and-export.md#if-something-fails).

## When TableSage Seems Blocked

### Why Are Campaigns and Players Dimmed after I Saved Settings?

TableSage unlocks Campaigns and Players only when `settings_version` in `.tablesage/settings.yaml` matches the settings version that the installed TableSage expects. Saving on the Settings screen writes that number. If it is still lower, the last save didn't complete: open **Settings**, press **Continue**, and read any message under the form. A version update that adds settings raises the expected number, which is why an update can ask you to review settings again.

If the number is higher than the installed version expects, TableSage refuses to open the workspace with *This workspace uses a newer settings schema*. A newer TableSage has used this workspace; open it with that version.

### Why Does TableSage Stop at Launch with "Invalid settings file"?

`.tablesage/settings.yaml` isn't valid YAML, or a value in it is out of range or the wrong type. The message names the file and the setting that failed. Correct that value with a text editor. Alternatively, rename the file: TableSage creates a fresh default one at the next launch and asks you to review Settings. Your API keys aren't stored in this file, so they are kept either way.

### Why Does Creating a Campaign, Player, or Session Ask Me to Clear a Folder?

**Delete** removes an object's database record but leaves its folder on disk until you run **Clean Up**; see [Delete and Clean Up](../concepts/delete-and-clean.md). If you create a new object whose folder would have the same path, the leftover folder is in the way, and TableSage asks whether to delete it. Clearing it permanently removes the old files, so copy anything you want to keep first.

This most often happens with Sessions. A new Session is numbered one higher than the highest-numbered Session that still exists in the Campaign. After you delete the most recent Session, the next one you create gets the same number, and the deleted Session's folder is still in the way.

### Why Does Export Campaign Say the Campaign Folder Is Missing?

TableSage finds a Campaign's files by name: the Campaign named *Iron Pact* keeps its files in `campaigns/Iron Pact/`. Players work the same way under `players/`. If a folder was renamed, moved, or deleted outside TableSage, the Campaign or Player no longer finds its files. Rename the folder back to exactly the name TableSage shows. Rename Campaigns and Players in TableSage, which moves their folders for you.

### Why Is an Output Out of Date, or Why Does a Current Output Show Old Details?

Each processing step builds on the outputs of earlier steps. When a step completes, TableSage records a fingerprint of every input it used in the Session's `processing_state.json`. If one of those inputs changes later, for example after rerunning an earlier step, correcting the transcript, or changing a review decision, the outputs built from it are marked out of date (◐) on Session Detail. Rebuild them there; see [Read the Artifacts Panel](../guides/review-and-export.md#read-the-artifacts-panel).

Attendance, Roles, Session dates, Glossary entries, and model choices are not fingerprinted. After changing them, existing outputs stay marked current (●) but still reflect the old details, so regenerate the outputs that should include the change. The same page lists which changes the marks track.

An output can also be out of date when a required companion output is missing, a completion record is absent or incomplete, a required input was never recorded, or an upstream step is out of date. Existing files alone do not prove completed, current processing. See [Processing State and Freshness](processing-state-and-freshness.md) for the rules, required dependencies, metadata inspection, and recovery limits after an upgrade.

### Why Did My Unfinished Review Edits Disappear?

When you cancel a review step with unsaved work, TableSage keeps it as a draft tied to the exact transcript you were reviewing. If that transcript changes before you return, for example because an earlier step ran again, the draft no longer matches and TableSage discards it rather than apply your edits to different text.

## Finding What Went Wrong

### Can I Rerun a Completed Automatic Step?

Yes. On **Session Detail**, press **P** (**Process**), click the automatic step's row, then press **R** (**Restart from here**). Arrow keys skip automatic rows, but clicking selects them. This works even when the step is complete and its outputs are current. Processing must be idle and free of blockers. Restarting before **Review Transcript** discards its saved edits and drafts, so choose the latest step that can apply your correction. See [Correct a Processed Session](../guides/correct-processed-session.md) and [Processing State and Freshness](processing-state-and-freshness.md#restart-a-completed-step).

### Where Can I See Why a Step Failed?

Process Session shows each step's last failure beside the step. The same message is kept in the `failures` section of the Session's `processing_state.json`, in `campaigns/<Campaign name>/<Session number>/`.

The full record is in `.tablesage/logs/tablesage.log`, which has one JSON event per line. Each event names its operation in `op`, and failed operations have `"level": "error"` and an `error` field describing the problem. `.tablesage/logs/prompts/` holds the prompts TableSage sent to language models and the replies, which helps when a generated output looks wrong.

### Where Are My API Keys?

Not in the workspace. They are stored once per user account, and environment variables can override them. See [Where Keys Live](../guides/settings.md#where-keys-live) and [How Shell Environment Variables Override Keys](../guides/settings.md#how-shell-environment-variables-override-keys). A failed connection test with a key that looks right usually means an environment variable is overriding it.

## Reading Workspace Data

### Where Is a Session's Processing Progress Stored?

In the Session's folder, not the database. `campaigns/<Campaign name>/<NNN>/` holds the recording, transcripts, and generated outputs as files, plus `processing_state.json`. That file records each completed step and the fingerprints of its inputs (`records`), review decisions and suggestions (`sections`), unfinished drafts (`drafts`), and each step's last failure (`failures`). `processing_state.json.bak` is its previous version. The database's `session.status` column doesn't reflect processing progress.

### How Do Records and Folders Correspond?

- A Campaign's folder is `campaigns/<campaign.name>/`.
- A Session's folder is `campaigns/<Campaign name>/<NNN>/`, where `NNN` is `session.sequence_number` with three digits, such as `004`.
- A Player's folder is `players/<player.name>/`.

A folder with no matching database record belongs to something that was deleted. It isn't a live Campaign, Session, or Player; **Clean Up** removes it.

### How Are IDs Stored?

IDs are UUIDs stored as 32-character hexadecimal text without dashes, in `campaign.id`, `session.campaign_id`, and the other ID columns. Join on these columns rather than on names.

### Which Settings and Database Versions Does This TableSage Expect?

`tablesage report-schema` prints the database's migration revision and the one the installed TableSage expects, plus its expected settings version. Compare that version with `settings_version` in `.tablesage/settings.yaml`. If database revisions differ, launching TableSage upgrades an older database. An unrecognized revision may belong to a newer version or another database history; the report alone cannot establish which. These read-only commands do not run migrations. A missing or outdated agent guide produces a warning, not a requirement to start the app before diagnosis.
