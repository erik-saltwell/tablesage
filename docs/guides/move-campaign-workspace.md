# Move a Campaign to Another Workspace

Transfer a Campaign's Sessions, Glossary, and files together with the Players needed to open it in another workspace. Exporting creates archives; it leaves the source workspace intact.

You need access to both workspaces, space for the archives and imported recordings, and TableSage installed on the destination computer if it is a different machine. A workspace is the directory from which you launch TableSage; see [Workspaces](../concepts/workspaces.md).

## Export from the Source Workspace

Finish or stop any active processing before exporting the Campaign.

1. From the Welcome screen, press **P** to open **Players**.
2. Open **Other actions** (**?**) and choose **Export Players** (**X**). Save `players.zip` somewhere you can access from the destination. This exports every workspace Player and their voice clips.
3. Return to the Welcome screen, press **C**, and highlight the Campaign you want to transfer.
4. Open **Other actions** and choose **Export Campaign** (**X**). Save `campaign.zip` alongside the player archive.

The campaign archive includes its session records, attendance and Roles, Glossary, and campaign files. Players are shared across the workspace, so they and their voice samples travel in the separate player archive. Keep both files together for the transfer.

## Open the Destination Workspace

Exit TableSage, create or choose the destination directory, and launch TableSage from it. For example, on a system where TableSage is already installed:

```sh
mkdir -p ~/Documents/tablesage-new
cd ~/Documents/tablesage-new
tablesage-rpg
```

In every new workspace, press **S** on the Welcome screen, check your keys and model choices, and choose **Continue** to save and check Settings before importing. Players and Campaigns remain unavailable until settings are saved. See [Update Your Settings](settings.md).

On the same computer and user account, your existing API keys are shared with the new workspace. On a different computer or user account, configure them again; the archives do not include keys. Model choices are workspace-specific, so check them in either case.

## Import Players First

1. From the destination Welcome screen, press **P**.
2. Open **Other actions** (**?**) and choose **Import Players** (**I**).
3. Select `players.zip` and wait for voice prints to be recomputed.
4. Read the completion notification and check the Players List.

Existing Players are matched by name, ignoring capitalization and surrounding spaces, and their clips are merged. Identical clips are skipped. If the destination already has Players, make sure matching names refer to the same people before importing.

Campaign import requires every attendee to exist with the exact archived player name. A destination Player whose name differs in capitalization may be matched by player import but still fail the Campaign's exact-name check. For example, if the destination already has a Player named *priya* and the archive's attendee is *Priya*, player import merges Priya's clips into *priya*, but campaign import reports *Missing player: Priya*. Check the reported missing name and use **Edit Metadata** on Player Detail to make the name match before retrying campaign import.

## Import the Campaign

1. Return to the Welcome screen and press **C**.
2. Open **Other actions** and choose **Import Campaign** (**I**).
3. Select `campaign.zip`.
4. Open the imported Campaign and check its Sessions and Glossary tabs. Open a processed Session to inspect attendance, Roles, and available artifacts.

If import reports **Missing player**, return to Players and import the player archive or correct the destination Player's name, then retry. If a Campaign of the same name already exists, import into a different workspace or resolve that name conflict before retrying; importing is not a merge into an existing Campaign.

Use TableSage-generated archives. If an archive is rejected, read the listed problems and re-export from the source rather than editing the ZIP by hand.

## Confirm You Can Continue

The transfer is ready when the Campaign and its Sessions open, attendees refer to the intended Players, and those Players' voice prints are available. Outputs may need refreshing under the destination's configuration or TableSage version; use [Regenerate All Outputs](review-and-export.md#regenerate-every-session-in-a-campaign), completing any required reviews separately.

The source Campaign remains available. Keep it until you have checked the destination and retained whatever backups you need. To continue play, follow [Process a Session with Returning Players](process-session-returning-players.md) or [Prepare the Next Session](prepare-the-next-session.md).
