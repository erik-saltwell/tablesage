# Process a Session with New Players

Use this guide when you want to process a recording, and at least one attendee has no usable voice samples yet. This can be your first recording or a later Session with a new person joining the table. 

You need the session recording, configured [keys and models](settings.md), and a Session with correct attendance and Roles. If you have not created those yet, follow [Start a Campaign](start-a-campaign.md). For an existing Campaign, create a Session on its Sessions tab, check any inherited attendees, and add the new person with **N** on Session Detail.

<<# Screenshot of the New Attendee modal Dialog open, the combo box open and showing the new player option #>>
## Start Processing and Import Audio

1. Once you have selected a session, check that everyone who spoke is in **Attendance**, including the GM, and that their Roles are correct.
2. Press **P** (**Process**). The **New Players** panel names the attendees whose voices need to be learned.

   ![Process Session before processing, listing Jordan Lee under New Players](../images/screens/process-session-new-player.png)

3. Press **C** (**Continue**) and choose the recording. Supported formats are `.wav`, `.mp3`, `.m4a`, `.flac`, and `.ogg`.

<<# Screenshot of the file picker inside the 'Import Audio' step of session processing #>>

4. When the system asks if you want to clean the audio, you can usually select yes.   This option is here in case this file has already been cleaned by TableSage from prior runs.  In this case, double  cleaning the audio can create a slight degradation in audio quality.

<<# Screenshot of tablesage asking if the user want to clean the audio #>>

TableSage imports the recording, creates a transcript, and filters likely listener acknowledgments. Progress dialogs cover this automatic work.

## Check Player and Character Names

<<# Screenshot of the Review Name Corrections screen #>:>

Now that TableSage has a transcript, it is going to try to identify who is speaking by looking for times when one player refers to another by name (or their character's name).  The first step is to normalize spellings of player and character names.  An llm takes the session's transcript and attendance record and tries to identify typos and mis-spellings.  It shows them to you in the **Review Name Corrections** so you can review them.  Check each proposed **From** → **To** replacement. For example, keep a correction from *Brother Held* to *Brother Hald* if that is the character's name.

- Press **E** or **Enter** to fix a proposed replacement.
- Press **D** to delete an incorrect proposal.
- Press **N** to add a missing correction.
- Choose **Continue** when the remaining corrections look right.

The replacements apply across the transcript.
## Confirm the New Players' Voices

![Reviewing candidate utterances for a new Player's voice samples](../images/screens/new-speaker-utterances.png)

Now that name and role spellings have been corrected, TableSage passes the transcript to an LLM which uses conversational cues, like players refering to each other by name, to infer who is speaking.  The **Review New Speaker Assignments** screen allows you to review its findings.   The lines you keep will become voice samples, so listen to them and keep only speech you are sure belongs to that person.

1. Select a Player in the **Players** pane, then press or **Enter** to review that player's **Utterances**.
2. Move through the lines with your mouse or arrow keys to hear their clips.
3. Press **D** to mark a wrong or uncertain line for removal. Press **D** again on that line to restore it.
4. In the Players list, TableSage will show you a warning if a Player does not have enough audio to build a useful voice print.  In this case, select the Player and press **F** (**Find More**). TableSage will find the most similar sounding utterances in the transcript to the ones already in the list. Listen to the additions, marked **+**, and remove any that belong to someone else.  We recommend that you use **Find More** to get about one minute of audio if you can,
5. Select another Player from the Players list and repeat this process for each new person. Choose **Confirm** when you have checked the candidates.

TableSage seeds voice samples from the confirmed lines and then identifies speakers in the rest of the recording. Uncertain matches remain unassigned for review.

For playback and pane controls, see [Review New Speaker Assignments](../reference/screens/processing-review-screens.md#review-new-speaker-assignments).

## Continue Processing

The remaining steps follow [Process a Session with Returning Players](process-session-returning-players.md). Continue at [Extract Glossary Terms](process-session-returning-players.md#extract-glossary-terms) and follow that guide through transcript review, generation, and improving voice prints.
