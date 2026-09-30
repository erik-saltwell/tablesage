# Process a Session with New Players

Use this guide when at least one attendee has no usable voice print. This can be your first recording or a later Session with a new person joining the table. TableSage learns their voice from lines in this recording that you confirm, then uses it alongside the other attendees' voice prints.

You need the session recording, configured [keys and models](settings.md), and a Session with correct attendance and Roles. If you have not created those yet, follow [Start a Campaign](start-a-campaign.md). For an existing Campaign, create a Session on its Sessions tab, check any inherited attendees, and add the new person with **N** on Session Detail.

## Start Processing and Import Audio

1. On Session Detail, check that everyone who spoke is in **Attendance**, including the GM, and that their Roles are correct.
2. Press **P** (**Process**). The **New Players** panel names the attendees whose voices need to be learned.

   ![Process Session before processing, listing Jordan under New Players](../images/screens/process-session-new-player.png)

3. Press **C** (**Continue**) and choose the recording. Supported formats are `.wav`, `.mp3`, `.m4a`, `.flac`, and `.ogg`.
4. For a `.wav`, answer **Clean Audio?**: choose **Yes** for a raw recording or **No** if it has already been cleaned. Other supported formats are cleaned automatically.

TableSage imports the recording, creates a transcript, and removes short acknowledgments that add no independent meaning. Progress dialogs cover this automatic work. The run then opens each review in order; confirm a review to continue. A review with nothing to check may be skipped automatically.

## Check Player and Character Names

In **Review Name Corrections**, check each proposed **From** → **To** replacement. For example, keep a correction from *Brother Held* to *Brother Hald* if that is the character's name.

- Press **E** or **Enter** to fix a proposed replacement.
- Press **D** to delete an incorrect proposal.
- Press **N** to add a missing correction.
- Choose **Continue** when the remaining corrections are right.

The replacements apply across the transcript. Correct names help TableSage interpret introductions and conversations when it looks for each new person's speech.

## Confirm the New Players' Voices

**Review New Speaker Assignments** proposes lines for each new Player. The lines you keep will become voice samples, so listen to them and keep only speech you are sure belongs to that person.

1. Select a Player in the **Players** pane, then press **→** or **Enter** to enter their **Utterances**.
2. Move through the lines to hear their clips. Press **R** to replay a clip, or **Space** for Autoplay.
3. Press **D** to mark a wrong or uncertain line for removal. Press **D** again on that line to restore it.
4. If there is too little speech, keep at least one certain line and press **F** (**Find More**). Listen to the additions, marked **+**, and remove any that belong to someone else.
5. Press **←** to return to Players and repeat for each new person. Choose **Confirm** when you have checked the candidates.

![Reviewing candidate utterances for a new Player's voice samples](../images/screens/new-speaker-utterances.png)

A character name mentioned in a line is not enough to identify its speaker. If Priya says “Hald, what do you think?”, that is Priya's voice, even though Hald is Jordan's character. A few certain clips are more useful than a collection containing mixed voices. If little usable speech remains, do not keep incorrect samples to increase the count; speaker assignments will need particular attention in transcript review.

TableSage seeds voice samples from the confirmed lines and then identifies speakers in the rest of the recording. Uncertain matches remain unassigned.

## Check New Terms and Spelling

In **Extract Glossary Terms**, check proposed campaign names and terms before they enter the Glossary:

- **E** or **Enter** edits a term or description.
- **D** removes a proposal you do not want.
- **N** adds a missing entry.
- **Continue** adds the remaining entries to the campaign glossary and moves on.

Next, **Spellcheck Against Glossary** proposes transcript replacements using campaign vocabulary and previously approved corrections. Check each **From** → **To** pair and its **Occurrences** count, especially before keeping a replacement that affects many lines. Edit with **E**, add with **N**, and press **D** to toggle an incorrect replacement off. Choose **Continue** when the kept corrections are right. Either review may complete automatically if there is nothing to check.

For example, a newly introduced *Tidewarden Coil* can be added to the Glossary and used immediately to correct *Tide Warden Coil* in the transcript. See [Build and Maintain Your Campaign Glossary](build-campaign-glossary.md).

## Review Speech and Speakers

**Review Transcript** is your final check of what was said and who said it. Give new Players' lines and unassigned speech particular attention.

1. Move through the lines to listen. Press **R** to replay, or **Space** to switch between Manual and Autoplay.
2. Correct the speaker using the attendee numbers (**1**–**9**) in the legend. **Edit Utterance** also offers every attendee in a dropdown, including anyone beyond the first nine.
3. Press **Enter** on a selected line to open **Edit Utterance** and change its text or speaker. The only exception is the first Enter on a freshly opened review, before you have moved to another line: it plays the first line instead, and a second Enter opens it.
4. Use **D** to mark a line for removal, or **F** to correct repeated text with **Find/Replace**.
5. Choose **Confirm** when the transcript is ready.

![Review Transcript, where you check speech against its audio](../images/screens/review-transcript.png)

## Generate Outputs and Improve Recognition

After confirmation, TableSage applies your review, assigns character Roles, and generates the Session's artifacts. If **Prior Sessions Are Out of Date** appears, choose **Regenerate Prior** to rebuild the required earlier outputs before this Session's outputs are generated.

At **Improve Player Voice Prints**, choose **Add Samples** if you have carefully checked speaker assignments. This adds further clips from the reviewed Session to attendees' voice samples and recomputes their voice prints. Choose **Not Now** if you want to finish without adding samples; you can [add them later](manage-players-and-voice-samples.md#add-samples-from-a-session).

Processing is finished when Process Session says **All steps complete**. Press **Esc** to return to Session Detail and check its artifact indicators. You can now [export a summary or other outputs](review-and-export.md), or [prepare for the next Session](prepare-the-next-session.md).

## Pause or Recover

If you need to stop during a review, use **Esc** and save a draft when offered. Later, reopen Process Session and press **C** to continue. A saved draft does not complete the review.

If a step fails, its row shows the cause. Fix it, then press **Continue** to retry. To change a review you already completed, select it and press **R** (**Restart Step**); see [Correct a Processed Session](correct-processed-session.md). For every review control, see [Processing Review Screens](../reference/screens/processing-review-screens.md).
