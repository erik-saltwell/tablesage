# Players

[Screen Reference](index.md) › Players

## How to Get Here

To get to the Players List screen, press **P** on the Welcome screen.

Players belong to the whole workspace, not to one Campaign. Each Player has a voice print, built from voice clips, that lets TableSage recognize who is speaking. See [Players, Voice Samples, Voice Prints, and Roles](../../concepts/players.md) for the concepts, and [Improve Player Voice Recognition](../../guides/manage-players-and-voice-samples.md) for common tasks.

## Players List

![The Players List](../../images/screens/players-list.png)

| Column | Meaning |
|---|---|
| **Samples** | How many voice samples the Player's voice print was built from. A red **0** means none yet; hovering over it says so. |
| **Player** | The Player's name. |
| **Voice Print** | *ready* when the Player has a voice print, *no samples* when they don't. |

| Key | Action | Available |
|---|---|---|
| **S** | **From Session.** Refreshes attendees' voice samples from a transcribed Session and recomputes their voice prints; see [From Session](#from-session). | Always |
| **N** | **New Player.** Asks for a name. The name becomes the Player's folder name on disk, so it can't contain `/` or `\`, and it can't be `.` or `..`. Names that differ only in capitalization count as the same name. Problems are shown inside the dialog. | Always |
| **E**, **Enter** | **Edit Player.** Opens the highlighted Player in [Player Detail](#player-detail). | When a Player is highlighted |
| **D**, **Delete**, **Backspace** | **Delete Player.** Deletes the highlighted Player, after you confirm. A Player who has attended any Session can't be deleted, and TableSage explains this before asking. Remove their attendance first. The Player's folder stays on disk until you run **Clean Up**. | When a Player is highlighted |
| **Esc** | Back to the Welcome screen. | Always |

### Other Actions

![Other actions on the Players List](../../images/screens/players-list-other-actions.png)

| Key | Action |
|---|---|
| **R** | **Recompute All Voice Prints.** Starts at once, without asking. Rebuilds every Player's voice print from the clips in their folder, one Player at a time, with progress. If one Player fails, it stops there and reports how many it finished. |
| **I** | **Import Players.** Imports Players and their voice clips from a ZIP archive, then computes their voice prints. Players whose names already exist are matched rather than duplicated, and identical clips are skipped. A notification summarizes what was created, matched, imported, and skipped. If the archive can't be imported, an **Import Players Failed** window lists the problems. |
| **X** | **Export Players.** Writes every Player and their voice clips to a ZIP archive (default name `players.zip`). |
| **C** | **Clean Up.** After you confirm, removes player folders on disk that no longer have a Player in the database. |

Import and export move Players between workspaces; see [Move a Campaign to Another Workspace](../../guides/move-campaign-workspace.md) for the complete transfer workflow, or [Move Players Between Workspaces](../../guides/manage-players-and-voice-samples.md#move-players-between-workspaces) for Players alone.

### From Session

**S** opens a picker. Choose a Campaign from the drop-down, then choose one of its Sessions and press **Enter** or **Select**.

![The From Session picker](../../images/screens/from-session-picker.png)

Sessions that haven't been transcribed are listed but dimmed, with the status *No transcript*. Selecting one is refused with *This session hasn't been transcribed yet.* For a *Ready* Session, TableSage cuts voice clips for its current attendees and recomputes their voice prints, behind a progress dialog. A notification reports how many Players received new clips and how many clips were extracted.

For each attendee, this replaces their earlier clips from the same Session, even if no new clips qualify. TableSage trusts human assignments only when the completed transcript review is current; otherwise it uses high-confidence machine assignments. See [Add Samples from a Session](../../guides/manage-players-and-voice-samples.md#add-samples-from-a-session) for source selection and replacement details.

Only use this on a Session whose speaker assignments you have reviewed carefully. A mislabeled line teaches TableSage the wrong voice for a Player. Process Session offers the same thing at the end of processing; see [Improve Player Voice Prints](processing-review-screens.md#improve-player-voice-prints).

## Player Detail

### How to Get Here

To get to the Player Detail screen, select a Player from the Players List screen and press **E** or **Enter**.

The header shows the Player's name.

![Player Detail for Priya Patel](../../images/screens/player-detail.png)

The top of the screen shows:

| Field | Meaning |
|---|---|
| **Name** | The Player's name. |
| **Voice Print Samples** | How many clips the current voice print was built from. |
| **Computed At** | When the voice print was last computed, or *Never*. |
| **Voice Print** | A short fingerprint of the current voice print, or *None*. It isn't meaningful by itself, but it changes whenever the voice print changes, so you can see whether a recompute did anything. |
| **Duration** | The total length of every clip in the Player's folder, including clips the voice print doesn't currently use. |

The **Voice Clips** table lists every clip file in the Player's folder and its length. Clips added from a Session are named after the Campaign and Session they came from.

| Key | Action | Available |
|---|---|---|
| **F** | **Folder Import.** Imports clips from a folder. See [Import Clips from a Folder](#import-clips-from-a-folder). | Always |
| **M** | **Edit Metadata.** Renames the Player, which also renames their folder. If a leftover folder already has the new name, TableSage asks whether to delete it and continue. | Always |
| **D**, **Delete**, **Backspace** | **Delete Voice Clip.** Deletes the highlighted clip, after you confirm. The clip file is deleted, and the voice print is recomputed from the remaining clips. | When a clip is highlighted |
| **Esc** | Back to the Players List. | Always |

![Confirming deletion of a voice clip](../../images/screens/delete-clip-confirm.png)

### Other Actions

![Other actions on Player Detail](../../images/screens/player-detail-other-actions.png)

| Key | Action |
|---|---|
| **R** | **Recompute.** Starts at once, without asking. Rebuilds this Player's voice print from every clip in their folder. If the folder has no clips, the voice print is cleared. |
| **C** | **Clean Up.** After you confirm, recomputes the voice print and **permanently deletes** any clip files it finds to be duplicates or outliers, meaning clips that don't sound like the rest. A notification reports how many were removed. |

### Import Clips from a Folder

**F** imports every `.wav` clip at the top level of a folder you choose:

1. Choose the folder in the directory picker. TableSage checks that it contains clips it can import; if not, it says why and stops.
2. **Clean Audio** asks whether to denoise and reformat the files first. Choose **Yes** for raw recordings and **No** for audio that is already clean. **Cancel** stops the import.
3. If you have imported from this folder before, **Replace Prior Import** says how many earlier clips will be replaced. Confirm to continue.
4. TableSage imports the clips and recomputes the voice print. A notification reports how many clips it imported and replaced. It also reports any clips it skipped because they couldn't be used, and any it removed as outliers. If no clip could be used, the voice print is left unchanged, and a warning says so.
