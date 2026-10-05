# Improve Player Voice Recognition

[Players and their voice prints](../concepts/players.md) are shared by every Campaign in a workspace. Use this guide when recognition needs better samples, when a voice print has picked up the wrong person's voice, or when you have separate recordings you want to use as voice references. From the Welcome screen, press **P** to open the **Players** list.

## Choose a Source of Reliable Speech

For a Player without a voice print, the usual starting point is [processing a Session with new Players](process-session-new-players.md): you confirm their first samples from the recording. For a known Player, use a carefully reviewed Session or import `.wav` clips of that person speaking.

## Remove Incorrect Samples First

Before adding more samples, check whether the existing ones are correct. For example, if Jordan Lee's voice samples contain Priya Patel's speech, adding more clips can preserve the confusion.

The Players List shows how many **Samples** each Player's voice print was built from (a red **0** means no voice print yet) and whether their **Voice Print** is *ready*. To find and remove a wrong clip:

1. Select the Player and press **E** or **Enter** to open their page, which lists their **Voice Clips**, when the voice print was **Computed**, and the total **Duration** of their clips.
2. Open `players/<player-name>/` inside your workspace in a file manager and listen to its `.wav` files in an audio player.
3. On Player Detail, select an incorrect clip by its filename and press **D** (**Delete Voice Clip**). TableSage confirms, then deletes the clip and recomputes the voice print from the remaining clips.

Delete unsuitable clips rather than the Player. A Player who has attended a Session can't be deleted until they're removed from that attendance; see [Delete and Clean Up](../concepts/delete-and-clean.md).

## Add Samples from a Session

**From Session** (**S** on the Players List) learns voice samples for the Session's current attendees. It is the same action that **Improve Player Voice Prints** offers at the end of processing. Use it if you chose **Not Now** and now want to learn from that reviewed recording, or to refresh samples after correcting speaker assignments.

Only do this after checking speaker assignments carefully. A mislabeled line teaches TableSage the wrong voice for that Player.

1. Press **S** and choose a Campaign, then a Session. Sessions with no transcript are dimmed and can't be chosen.
2. TableSage cuts clips from the current transcript, replaces each attendee's earlier clips from this Session, and recomputes their voice print. A notification reports how many Players received new clips and how many clips were extracted.

For either machine transcript, it accepts only lines assigned to that Player with high confidence. Very short lines are skipped, and samples pass through the outlier check described below. If no current transcript is available, the action stops with an error.

## Import Clips from a Folder

Use a folder containing `.wav` recordings of that person speaking. The folder is read as-is: subfolders are not searched, and the folder must hold at least one `.wav`.

1. On the Player's page, press **F** (**Folder Import**) and choose the folder.
2. TableSage asks whether to **clean** the audio (remove noise and convert the format) before importing. Answer **Yes** for raw recordings and **No** for clips that are already clean, such as clips created by tablesage during session processing.
3. If you import from the same folder again, TableSage asks before replacing the clips from the earlier import.

When it finishes, it reports how many clips were imported, replaced, skipped because they couldn't be used, and removed as outliers. If no clip could be used, the voice print is left unchanged.

## Recompute and Clean Up Voice Prints

On the Player's page, open **Other actions** (**?**):

- **Recompute** rebuilds the voice print from the clips on disk without deleting anything. TableSage keeps voice prints up to date so this feature is usually only useful in the event of a bug in the application.
- **Clean Up** does the same recompute and then **permanently deletes** the duplicate and outlier clips it left out. TableSage asks first. This command is only useful for clearing up disk space, as these clips are never used in processing a player's voice print.

How different a clip must be to count as an outlier, and the minimum number of clips it will keep, are set in the workspace's `.tablesage/settings.yaml` (`remove_outliers`). Adding a clip or Session's worth of samples can change which clips count as outliers.

**Recompute All Voice Prints**, under **Other actions** on the Players List, runs a recompute for every Player. If it fails partway, it tells you which Player it stopped at and how many it finished.

For more on these screens, see [Players](../reference/screens/players.md) in the screen reference.

## Move Players Between Workspaces

For a complete campaign transfer, follow [Move a Campaign to Another Workspace](move-campaign-workspace.md), which explains why Players must be imported before the Campaign. To transfer or back up only Players and their voice samples, both actions below are under **Other actions** (**?**) on the Players List.

**Export Players** (**X**) writes every Player and their voice clips to a single `players.zip`. Choose where to save it.

**Import Players** (**I**) reads a `.zip` made by Export Players:

- **New Player names:** creates the Players.
- **Existing Player names:** adds clips they don't already have. Names are matched ignoring capitalization and surrounding spaces.
- **Clips:** skips identical clips, ignores files other than each Player's `.wav` clips, and recomputes voice prints.

When it finishes, it reports how many Players it created and matched and how many clips it imported and skipped. An archive with unsafe or unexpected contents is rejected with nothing changed, and TableSage shows what was wrong.
