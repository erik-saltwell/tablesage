# Process a Session with Returning Players

Use this guide when every attendee already has a usable voice print. This is the usual workflow for later Sessions, but it also applies to a new Campaign whose Players are already known in the workspace. If anyone's voice still needs to be learned, use [Process a Session with New Players](process-session-new-players.md).

You need the recording and configured [keys and models](settings.md). This walkthrough takes you from the next Session's setup to generated outputs.

## Create the Session and Check Attendance

1. From the Welcome screen, press **C**, open your Campaign, and select its **Sessions** tab.
2. Press **N** (**New Session**), enter its name and optional date (`YYYY-MM-DD`), and choose **Create Session**.
3. On Session Detail, check the **Attendance** list. TableSage copies attendance and Roles from the latest dated Session before the new Session's date. If the new Session is undated, it uses the latest dated Session; if no eligible Session exists, attendance starts empty.
4. Remove anyone who was absent with **D**, add anyone missing with **N**, and edit changed character Roles with **E**. Include the GM and everyone else who spoke in the recording.

For example, if Jordan played Brother Hald last time but switched characters, edit Jordan's Role for this Session. The person's voice remains the same; the Role tells generated outputs which character they played this time.

## Import the Recording

Press **P** (**Process**), then **C** (**Continue**). Choose the recording (`.wav`, `.mp3`, `.m4a`, `.flac`, or `.ogg`). For a `.wav`, choose **Yes** at **Clean Audio?** for raw audio or **No** for audio that has already been cleaned. Other supported formats are cleaned automatically.

TableSage imports and transcribes the recording, removes brief acknowledgments that add no independent meaning, and matches voices to the attendees. Because everyone has a voice print, the new-player reviews are hidden. Uncertain matches are left for transcript review.

## Check New Terms and Spelling

In **Extract Glossary Terms**, check proposed campaign names and terms before they enter the Glossary:

- **E** or **Enter** edits a term or description.
- **D** removes a proposal you do not want.
- **N** adds a missing entry.
- **Continue** adds the remaining entries to the campaign glossary and moves on.

Next, **Spellcheck Against Glossary** proposes transcript replacements using campaign vocabulary and previously approved corrections. Check each **From** → **To** pair and its **Occurrences** count, especially before keeping a replacement that affects many lines. Edit with **E**, add with **N**, and press **D** to toggle an incorrect replacement off. Choose **Continue** when the kept corrections are right. Either review may complete automatically if there is nothing to check.

For example, a newly introduced *Tidewarden Coil* can be added to the Glossary and used immediately to correct *Tide Warden Coil* in the transcript. See [Build and Maintain Your Campaign Glossary](build-campaign-glossary.md).

## Review Speech and Speakers

**Review Transcript** is your final check of what was said and who said it. Check uncertain assignments and any lines whose wording could change the account of what happened. Known voices still need review: a confident match can be wrong.

1. Move through the lines to listen. Press **R** to replay, or **Space** to switch between Manual and Autoplay.
2. Correct the speaker using the attendee numbers (**1**–**9**) in the legend. **Edit Utterance** also offers every attendee in a dropdown, including anyone beyond the first nine.
3. Press **Enter** on a selected line to open **Edit Utterance** and change its text or speaker. The only exception is the first Enter on a freshly opened review, before you have moved to another line: it plays the first line instead, and a second Enter opens it.
4. Use **D** to mark a line for removal, or **F** to correct repeated text with **Find/Replace**.
5. Choose **Confirm** when the transcript is ready.

![Review Transcript with an utterance marked for removal](../images/screens/review-transcript-removed.png)

If you need to pause, press **Esc** and choose **Save** when offered to retain your edits as a draft. Reopen Process Session and press **C** to resume later; the review remains incomplete until you confirm it.

## Finish Generation

TableSage applies your review, replaces player names with their Roles, and generates the Session's outputs. If earlier outputs must be rebuilt first, **Prior Sessions Are Out of Date** asks for approval; choose **Regenerate Prior** to proceed.

At **Improve Player Voice Prints**, choose **Add Samples** to learn from this carefully reviewed recording, or **Not Now** to finish without adding clips. You can [add samples later](manage-players-and-voice-samples.md#add-samples-from-a-session).

When Process Session says **All steps complete**, return to Session Detail with **Esc**. The generated outputs should have current **●** indicators. Next, [Generate and Export Session Outputs](review-and-export.md) for your players, or [prepare for the next Session](prepare-the-next-session.md).

If a step fails, fix the cause shown on its row and press **Continue** to retry. To revisit a completed review, select it and press **R**; [Correct a Processed Session](correct-processed-session.md) helps you choose the right place to restart. The [Processing Review Screens](../reference/screens/processing-review-screens.md) lists every review control.
