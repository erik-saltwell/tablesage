# Manage players and voice samples

[Players and their voice profiles](../concepts/players.md) are shared by every
Campaign in a workspace. From the welcome screen, press **P** to open the
**Players** list. This page covers keeping those profiles healthy, and moving
players between workspaces.

## The Players list

The list shows every player with the number of **Samples** behind their voice
profile (a red **0** means none) and whether their **Voice Print** is *ready* or
they have *no samples*.

| Key | Action |
|---|---|
| **N** | Create a new player. |
| **E** or **Enter** | Open the selected player. |
| **D** | Delete the selected player. |
| **S** | Add voice samples from a Session (**From Session**). |
| **?** | Open **Other actions**: Recompute All Voice Prints, Import Players, Export Players, Clean Up. |

A player who has attended a Session can't be deleted until they're removed from
that attendance. Deleting a player leaves their files on disk until a Clean Up;
see [Delete and clean up](../concepts/delete-and-clean.md).

## Add samples from a Session

**From Session** (**S**) adds clips from a Session you have already processed to
the profiles of everyone who attended it. It is the same action that
[Improve Player Voice Profiles](../concepts/session-processing-returning-players.md#improve-player-voice-profiles)
offers at the end of processing, available whenever you decide to do it.

1. Press **S** and choose a Campaign, then a Session. Sessions with no transcript
   are dimmed and can't be chosen.
2. TableSage cuts clips from that Session's transcript and recomputes each
   attendee's voice profile. A toast reports how many players and clips were
   affected.

Which lines become samples depends on how far the Session got. If you completed
[Review Transcript](../concepts/session-processing-returning-players.md#review-transcript),
TableSage trusts your speaker assignments and uses those lines. Otherwise it uses
only lines it identified with high confidence. In both cases very short lines are
skipped, and the results still pass through the outlier check described below.

Only do this after checking speaker assignments carefully. A mislabeled line
teaches TableSage the wrong voice for that player.

## The player's page

Open a player to see their **Voice Print Samples**, when the voice print was **Computed**,
a short hash that changes whenever the voice print does, and the total **Duration**
of their clips. Below that is the list of **Voice Clips**.

| Key | Action |
|---|---|
| **M** | Rename the player. |
| **D** | Delete the selected clip. TableSage confirms, then recomputes the voice print from the remaining clips. |
| **F** | Import clips from a folder of `.wav` files (**Folder Imp**). |
| **?** | **Other actions**: Recompute, Clean Up. |

### Import clips from a folder

Press **F** and choose a folder containing `.wav` recordings of that person
speaking. The folder is read as-is: subfolders are not searched, and the folder
must hold at least one `.wav`.

TableSage asks whether to **clean** the audio (remove noise and convert the
format) before importing. Answer **Yes** for raw recordings and **No** for clips
that are already clean. If you import from the same folder again, TableSage asks
before replacing the clips from the earlier import. When it finishes, it reports
how many clips were imported, replaced, and skipped because they couldn't be used.

### Recompute and Clean Up

- **Recompute** rebuilds the voice print from the clips on disk without deleting
  anything. Duplicate clips and clips that don't sound like the rest are left
  out of the voice print but stay on disk.
- **Clean Up** does the same recompute and then **permanently deletes** the
  duplicate and outlier clips it left out. TableSage asks first.

How different a clip must be to count as an outlier, and the minimum number of
clips it will keep, are set in the workspace's `.tablesage/settings.yaml`
(`remove_outliers`). Adding a clip or Session's worth of samples can change
which clips count as outliers.

**Recompute All Voice Prints** on the Players list runs a recompute for every player.
If it fails partway, it tells you which player it stopped at and how many it
finished.

## Move players between workspaces

Use these when you set up a new workspace or want a backup of voice profiles.
Both are under **Other actions** (**?**) on the Players list.

**Export Players** (**X**) writes every player and their voice clips to a single
`players.zip`. Choose where to save it.

**Import Players** (**I**) reads a `.zip` made by Export Players. For each player
in the archive, TableSage creates them if they don't exist or, if a player with
that name already exists (ignoring capitalization and surrounding spaces), adds
any clips they don't already have. Identical clips are skipped, files other than
each player's `.wav` clips are ignored, and voice prints are recomputed. When it
finishes it reports how many players it created and matched and how many clips it
imported and skipped. An archive with unsafe or unexpected contents is rejected
with nothing changed, and TableSage shows what was wrong.

**Clean Up** (**C**) deletes player folders on disk that no longer belong to any
player, the leftovers of deleted players.
