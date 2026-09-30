# Improve Player Voice Recognition

[Players and their voice prints](../concepts/players.md) are shared by every Campaign in a workspace. Use this guide when recognition needs better samples, when a voice print has picked up the wrong person's voice, or when you have separate recordings you want to use as voice references. From the Welcome screen, press **P** to open the **Players** list.

## Choose a Source of Reliable Speech

For a Player without a voice print, the usual starting point is [processing a Session with new Players](process-session-new-players.md): you confirm their first samples from the recording. For a known Player, use a carefully reviewed Session or import `.wav` clips of that person speaking.

## Remove Incorrect Samples First

The Players List shows each Player's number of **Samples** (a red **0** means none) and whether their **Voice Print** is *ready*. Select a Player and press **E** or **Enter** to open their page, which lists their **Voice Clips**, when the voice print was **Computed**, and the total **Duration** of their clips.

Before adding more samples, check whether the existing ones are correct. For example, if Jordan's voice samples contain Priya's speech, adding more clips without removing those mistakes can preserve the confusion. On Jordan's page, listen to the clips, select a known wrong one, and press **D** (**Delete Voice Clip**). TableSage confirms, then recomputes the voice print from the remaining clips.

Delete unsuitable clips rather than the Player. A Player who has attended a Session can't be deleted until they're removed from that attendance; see [Delete and Clean Up](../concepts/delete-and-clean.md).

## Add Samples from a Session

**From Session** (**S** on the Players List) adds clips from a Session to the voice samples of everyone who attended it. It is the same action that **Improve Player Voice Prints** offers at the end of processing, available whenever you decide to do it. Use this if you chose **Not Now** during processing and now want to learn from that reviewed recording.

1. Press **S** and choose a Campaign, then a Session. Sessions with no transcript are dimmed and can't be chosen.
2. TableSage cuts clips from that Session's transcript and recomputes each attendee's voice print. A toast reports how many Players and clips were affected.

Which lines become samples depends on how far the Session got. If you completed [Review Transcript](../concepts/session-processing-returning-players.md#review-transcript), TableSage trusts your speaker assignments and uses those lines. Otherwise it uses only lines it identified with high confidence. In both cases very short lines are skipped, and the results still pass through the outlier check described below.

Only do this after checking speaker assignments carefully. A mislabeled line teaches TableSage the wrong voice for that Player.

## Import Clips from a Folder

On the Player's page, press **F** (**Folder Import**) and choose a folder containing `.wav` recordings of that person speaking. The folder is read as-is: subfolders are not searched, and the folder must hold at least one `.wav`.

TableSage asks whether to **clean** the audio (remove noise and convert the format) before importing. Answer **Yes** for raw recordings and **No** for clips that are already clean. If you import from the same folder again, TableSage asks before replacing the clips from the earlier import. When it finishes, it reports how many clips were imported, replaced, skipped because they couldn't be used, and removed as outliers. If no clip could be used, the voice print is left unchanged.

## Recompute and Clean Up Voice Prints

On the Player's page, open **Other actions** (**?**):

- **Recompute** rebuilds the voice print from the clips on disk without deleting anything. Duplicate clips and clips that don't sound like the rest are left out of the voice print but stay on disk.
- **Clean Up** does the same recompute and then **permanently deletes** the duplicate and outlier clips it left out. TableSage asks first.

How different a clip must be to count as an outlier, and the minimum number of clips it will keep, are set in the workspace's `.tablesage/settings.yaml` (`remove_outliers`). Adding a clip or Session's worth of samples can change which clips count as outliers.

**Recompute All Voice Prints**, under **Other actions** on the Players List, runs a recompute for every Player. If it fails partway, it tells you which Player it stopped at and how many it finished.

For every key on these screens, see [Players](../reference/screens/players.md) in the screen reference.

## Move Players Between Workspaces

For a complete campaign transfer, follow [Move a Campaign to Another Workspace](move-campaign-workspace.md), which explains why Players must be imported before the Campaign. To transfer or back up only Players and their voice samples, both actions below are under **Other actions** (**?**) on the Players List.

**Export Players** (**X**) writes every Player and their voice clips to a single `players.zip`. Choose where to save it.

**Import Players** (**I**) reads a `.zip` made by Export Players. For each Player in the archive, TableSage creates them if they don't exist or, if a Player with that name already exists (ignoring capitalization and surrounding spaces), adds any clips they don't already have. Identical clips are skipped, files other than each Player's `.wav` clips are ignored, and voice prints are recomputed. When it finishes it reports how many Players it created and matched and how many clips it imported and skipped. An archive with unsafe or unexpected contents is rejected with nothing changed, and TableSage shows what was wrong.

**Clean Up** (**C**) deletes player folders on disk that no longer belong to any Player, the leftovers of deleted Players.

## Check the Result in the Next Session

After adding samples or recomputing, check that the Players List shows a ready voice print and that Player Detail shows its sample count and computation time. Those indicators confirm a voice print exists; they do not measure recognition accuracy.

Process the next recording and check the Player's assignments in **Review Transcript**, comparing them with the audio. If misassignments persist, inspect the source samples again and correct the current Session before using it for further voice learning. Updating a voice print does not rewrite already generated session outputs; follow [Correct a Processed Session](correct-processed-session.md) when an existing record needs repair.
