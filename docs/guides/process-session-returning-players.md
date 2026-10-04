# Process a Session with Returning Players

Use this guide when you want to process a recording and every attendee already has a usable voice print. This is the usual workflow for later Sessions, but it also applies to a new Campaign whose Players already have voice samples. If anyone's voice still needs to be learned, use [Process a Session with New Players](process-session-new-players.md).

You need the recording and configured [keys and models](settings.md). 

## Create the Session and Check Attendance

<<# Screenshot of the welcome screen #>>

1. From the Welcome screen, press **C**, open your Campaign, and press **S (Sessions)** to select the sessions tab

<<# Screenshot of the campaign detail screen with the sessions tab open #>>

2. Press **N** (**New Session**), enter its name and optional date (`YYYY-MM-DD`), and choose **Create Session**.
3. On the Session Detail screen, check the **Attendance** list. TableSage copies attendance and Roles from the latest dated Session before the new Session's date. If the new Session is undated, it uses the latest dated Session; if no eligible Session exists, attendance starts empty.  
4. Update the attendees - Remove anyone who was absent with **D**, add anyone missing with **N**, and edit changed character Roles with **E**. Include the GM and everyone else who spoke in the recording.

For example, if Jordan Lee played Brother Hald last time but switched characters, edit Jordan's Role for this Session. The person's voice samples remain the same; the Role tells generated outputs which character they played this time.

## Start Processing and Import Audio

1. Once you have selected a session, check that everyone who spoke is in **Attendance**, including the GM, and that their Roles are correct.
2. Press **P** (**Process**). The **New Players** panel names the attendees whose voices need to be learned.

<<# Screenshot of the Session Processing screen without new player steps (so the returning players flow) #>>

3. Press **C** (**Continue**) and choose the recording. Supported formats are `.wav`, `.mp3`, `.m4a`, `.flac`, and `.ogg`.

<<# Screenshot of the file picker inside the 'Import Audio' step of session processing #>>

4. When the system asks if you want to clean the audio, you can usually select yes.   This option is here in case this file has already been cleaned by TableSage from prior runs.  In this case, double  cleaning the audio can create a slight degradation in audio quality.

<<# Screenshot of tablesage asking if the user want to clean the audio #>>

TableSage imports the recording, creates a transcript, and filters likely listener acknowledgments. Progress dialogs cover this automatic work.

## Extract Glossary Terms

<<# Screenshot of the Extract Glossary Terms Screen with filled in values #>>

TableSage will now review your transcript and look for terms that look like campaign specific jargon, including NPC names, places, and organizations.   The  **Extract Glossary Terms** screen allows you to review these suggestions.  Use **E** to edit, **D** to remove a proposal, or **N** to add a term. **Continue** adds the remaining entries to the Campaign Glossary.

This review may complete automatically if there is nothing to check. See [Extract Glossary Terms](../reference/screens/processing-review-screens.md#extract-glossary-terms)  for a fuller reference to this screen,  [Build and Maintain Your Campaign Glossary](build-campaign-glossary.md) for vocabulary guidance and how corrections are reused across Sessions.

## Spellcheck Against Glossary

<<# Screenshot of the Spellcheck Against Glossary screen with replacement options filled in #>>

Within a transcript, the same term may show up under multiple spellings.  For example, **Deathwarden Drake** may show up as **Deathwarden Drake** one time, and **Death Warden Drake** another.   TableSage asks an LLM to review the transcript and look for such cases, and proposes replacements that will consolidate spellings to what is in your Campaign Glossary. Edit with **E** or toggle an incorrect replacement off with **D**, then choose **Continue**.

This review may complete automatically if there is nothing to check. See [Spellcheck Against Glossary](../reference/screens/processing-review-screens.md#spellcheck-against-glossary) for a complete reference to this screen., and [Build and Maintain Your Campaign Glossary](build-campaign-glossary.md) for vocabulary guidance and how corrections are reused across Sessions.

## Review Speech and Speakers

![Review Transcript with an utterance marked for removal](../images/screens/review-transcript-removed.png)

**Review Transcript** is your final check of what was said and who said it. Check uncertain assignments and any lines whose wording could change the account of what happened. Known voices still need review: a confident match can be wrong.

1. Move through the lines to listen and compare them with the text.  Use the arrow keys to quickly navigate between utterances.   The space bar toggles auto mode where utterances play automatically one after another.
2. Correct speakers with the legend's number keys. After moving to a line, press **Enter** for **Edit Utterance** to fix the text or its attendee. Use **D** to mark unwanted speech for removal.
3. Choose **Confirm** when the transcript is ready.

See [Review Transcript](../reference/screens/processing-review-screens.md#review-transcript) for playback, editing, and **Find/Replace** controls.

If you leave this screen, you will have a chance to save your progress and come back to finish later. 

## Finish Generation

TableSage applies your edits, replaces player names with their Roles, and generates the Session's outputs. If an earlier session needs to be rebuilt in order to generate the pre-session recap,  **Prior Sessions Are Out of Date** asks for approval; choose **Regenerate Prior** to proceed.

At **Improve Player Voice Prints**, choose **Add Samples** to extract voice samples from this session and enhance player voice prints; see [learn from the Session later](manage-players-and-voice-samples.md#add-samples-from-a-session).

When Process Session says **All steps complete**, return to Session Detail with **Esc**. 

<<# Screenshot of session with all artifacts generated #>>

The generated outputs should have current **●** indicators. Next, [Generate and Export Session Outputs](review-and-export.md) for your players, or [prepare for the next Session](prepare-the-next-session.md).

If a step fails, fix the cause shown on its row and press **Continue** to retry. To revisit a completed review, select it and press **R**; [Correct a Processed Session](correct-processed-session.md) helps you choose the right place to restart. See [Processing Review Screens](../reference/screens/processing-review-screens.md) for a complete reference to the session processing screens.
