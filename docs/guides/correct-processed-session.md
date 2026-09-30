# Correct a Processed Session

Use this guide when you notice an error after processing: a wrong speaker, a misheard name, an incorrect character Role, or an output that needs rewriting. Fix the source of the error, then bring the affected outputs up to date.

Open the Session from your Campaign's **Sessions** tab. Keep the original recording available if you intend to replace the imported audio or start over.

## Choose Where to Make the Correction

| What needs fixing? | Start here |
|---|---|
| One line's words or speaker, or speech that should be removed | Restart **Review Transcript**. |
| A repeated misheard campaign term | Check the campaign glossary, then restart **Spellcheck Against Glossary**. |
| Proposed new terms | Restart **Extract Glossary Terms**, or use Session Detail's **Extract Glossary** to obtain fresh proposals. |
| A player or character name used to identify a new speaker | Restart **Review Name Corrections** when that new-player step is present. |
| Wrong lines accepted as a new Player's voice samples | Check their voice clips as well as the Session; follow [Improve Player Voice Recognition](manage-players-and-voice-samples.md). |
| The attendee list or the character someone played | Edit **Attendance** on Session Detail, then continue processing from the first incomplete step. |
| An output needs another generation attempt, with the reviewed transcript already correct | Use [Regenerate Artifact](review-and-export.md#regenerate-an-artifact). |

Changing a Session's transcript does not remove clips already added to a Player's voice samples. If incorrect assignments were used for voice learning, remove those clips too before relying on it in another Session.

## Reopen a Transcript Review

For example, suppose a line about promising payment was assigned to Jordan but was actually spoken by Priya:

1. On Session Detail, press **P** (**Process**).
2. Highlight the completed **Review Transcript** step and press **R** (**Restart Step**).
3. Find the line, listen to its clip, and assign Priya using the legend's number key or the **Speaker** dropdown in **Edit Utterance**.
4. Correct any related text, then choose **Confirm**.
5. Complete any later prompts. TableSage applies the correction and rebuilds the dependent outputs.

The same restart pattern applies to other completed review steps. Choose the earliest review whose decision needs changing. When you confirm the restarted review, every later step that depends on it runs again, which may include further reviews before generation.

If the review is already the next incomplete step, use **C** (**Continue**) instead. To pause midway, leave with **Esc** and save a draft when offered.

## Correct Attendance or Roles

On Session Detail, focus **Attendance**. Use **E** to change an attendee's Player or Roles, **N** to add someone missing, or **D** to remove someone who did not speak in the recording. Each attendee needs at least one Role.

Then press **P** and **C** to continue. Attendance and Role edits can invalidate earlier processing decisions as well as generated outputs, so follow the first incomplete step shown. **Regenerate Artifact** is available only when the reviewed transcript is current; it cannot substitute for a review that needs completing again.

## Refresh the Campaign After a Correction

An earlier Session's changes can affect later session outputs. After completing the corrected Session's reviews, return to Campaign Detail, open **Other actions** with **?**, and choose **Regenerate All Outputs** (**O**). This refreshes missing or out-of-date outputs in session order, skipping Sessions without a current completed transcript review.

Check the completion notification for skipped Sessions and process those reviews separately. Before making a new Previously On recap or Opportunities file, [check that campaign history is current](prepare-the-next-session.md#what-you-need-first).

If you previously exported a summary, export the refreshed version again. TableSage's regeneration updates its managed files; the copy you exported earlier does not change.

## Start the Session Over

Use this when you want to replace the recording or discard all processing for this Session. Before proceeding, make sure you still have the original recording outside TableSage and export any outputs you want to keep.

1. On Session Detail, open **Other actions** (**?**) and choose **Clean Session** (**C**).
2. Read and confirm the deletion prompt. This permanently deletes every session artifact, including the imported input audio, and clears processing progress. The Session's attendance and Roles remain.
3. Press **P**, then **C**, to import the recording and process it again.

Clean Session cannot run while processing is active. It does not change any Player's voice samples or voice print. For deleting whole Sessions or cleaning up their leftover folders, see [Delete and Clean Up](../concepts/delete-and-clean.md).

## Check the Result

On Session Detail, verify that the outputs you need are current (**●**), then [export them again](review-and-export.md#export-an-artifact). Processing and regeneration failures appear in notifications and beside the affected Process Session step; fix the reported cause and use **Continue** to retry. Clean Session failures appear in Session Detail's **Errors** table.
