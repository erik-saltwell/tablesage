---
name: "Improve the Correct a Processed Session guide (docs/guides/correct-processed-session.md)"
status: complete
---

# Improve the Correct a Processed Session Guide

Make [Correct a Processed Session](../../docs/guides/correct-processed-session.md) more systematic by explaining restart behavior, showing an automatic step selected with **Restart from here** visible, teaching a general correction procedure, and mapping common changes to their recommended restart steps.

The user approved the restart explanation, Role correction screenshot, short general procedure, and three-column table (**Change**, **Before Restarting**, **Restart From**). Recommend the latest step that can apply the correction and explain that earlier restarts discard transcript-review edits. Finish with brief output checks and a link to full-reset instructions. The rewrite must be substantially shorter than the existing page.

## Outcome and Verification

Rewrote the guide around the approved flow and reduced it from 899 to 446 whitespace-separated words. Added the [Role restart screenshot](../../docs/images/guides/correct-session-restart.png), captured from the real app with offline authored fixtures. Retained the existing **Start the Session Over** heading so incoming links continue to work. Corrected the [Process Session](../../docs/reference/screens/process-session.md#keys) key reference, which incorrectly excluded automatic restarts.

Verified that restarting **Assign Roles To Players** after changing the fixture's Role to Captain Thorgrim updates the role transcript, completes processing, and preserves the transcript-review completion record and edits. Visually checked the screenshot's selected automatic row and **Restart from here** footer. All 25 local image/file/heading links in the changed public pages resolve; scoped `git diff --check` passes. Provider generation was stubbed in the offline fixture; no live LLM or transcription calls were made.

No approved rubric exists and no numerical assessment was performed. Against the workshop's provisional qualitative dimensions, understanding is supported by one restart explanation and screenshot, actionability by the shared procedure and three-column table, and accuracy by the code inspection, review-edit caution, and directly verified Role correction route. Reader usability has not been assessed. No implementation work remains.
