# TableSage use cases

TableSage is a local workspace for tabletop campaigns. It turns session audio into reviewable, speaker-attributed transcripts and summaries, while maintaining reusable voice profiles for campaign participants.

This document describes product behaviour. The relational data that supports it is specified separately in [TableSage data model](tablesage_data_model.md).

## Campaigns

### Create a campaign

**Description:** Start a workspace for one tabletop campaign.

**Goal:** Give the user a durable place for its people, glossary, sessions, and derived artifacts.

- The user provides a campaign name and optionally a description, game system, and default game master.
- The app creates the campaign and a stable, human-readable slug.
- The app checks that the slug is unique before creating the campaign.
- The new campaign opens with no players, sessions, or glossary entries.

### View and edit campaign metadata

**Description:** Maintain the campaign's identity and descriptive context.

**Goal:** Keep campaign information accurate without changing historical session data.

- The user opens a campaign.
- The app shows its name, description, game system, and default game master.
- The user edits one or more fields and saves.
- The app validates required values and persists the change.

### Archive, restore, and remove a campaign

**Description:** Make a campaign inactive, reactivate it, or remove it from normal use.

**Goal:** Keep the campaign list manageable without accidentally destroying useful recordings and derived work.

- The user archives a campaign when it is not currently active.
- Archived campaigns are hidden by the normal active view but remain available through an archived/all view.
- The user can restore an archived campaign.
- Removing a campaign requires confirmation and should be distinguishable from archival.
- A future maintenance action may permanently remove a campaign and its local media after explicit confirmation.

## Campaign glossary

### Maintain glossary entries

**Description:** Record campaign-specific names, places, terms, and spelling guidance.

**Goal:** Provide useful context for generated summaries and make proper nouns easier to recognize and review.

- The user opens the campaign glossary.
- The user adds, edits, or deletes a term and its optional explanation.
- The app prevents blank terms and keeps entries associated with the campaign.
- The user can search or filter entries when the glossary is large.

### Regenerate a summary after glossary changes

**Description:** Apply revised glossary context to an existing session summary.

**Goal:** Improve a summary without rerunning transcription or speaker processing.

- The user changes one or more glossary entries.
- Existing summaries remain available, but the app can mark them as generated with older context.
- The user selects a session and requests a summary-only regeneration.
- The app uses the existing reviewed transcript/discourse plus the current glossary.
- The app replaces or versions the summary while preserving the transcript and audio artifacts.

## Players and voice profiles

### Create and maintain a player

**Description:** Create a campaign participant who may later be identified in session audio.

**Goal:** Keep a stable identity for attendance, transcript attribution, and voice-profile training.

- The user adds a player with a display name.
- The app creates a campaign-local player record and stable slug/identifier.
- The user can edit the display name or deactivate/remove the player after the app explains any affected session attendance.
- A new player may initially have no voice samples and cannot yet be identified automatically by voice.

### Add voice clips from a directory

**Description:** Import reference recordings for one known player.

**Goal:** Seed or improve a player's voice profile before relying on automatic speaker identification.

- The user selects a player and a directory containing reference audio.
- The app validates that the directory exists and contains supported audio files.
- The user may choose whether clips are cleaned/normalized during import.
- The app copies or derives managed clips, computes an embedding for each, and records their import provenance.
- The app recomputes the player's voice centroid/profile from its accepted samples.
- Reimporting the same source directory replaces its earlier imported samples instead of silently duplicating them.
- The app reports rejected files or clips that cannot be embedded.

### Seed voice profiles from an unidentified session

**Description:** Bootstrap player profiles from a session when no usable reference clips exist.

**Goal:** Convert anonymous diarized voices into initial, user-confirmed player profiles without pretending that diarization knows real identities.

- The user processes a session through transcription and diarization.
- The app groups utterances by anonymous diarized speaker and presents playable candidate clips with timestamps.
- The user assigns each selected group or clip to an existing player without a profile, or creates a new player.
- The user reviews and accepts only representative, single-speaker clips; uncertain, noisy, or overlapping clips can be excluded.
- The app extracts managed clips, computes embeddings, and records that they were seeded from this session and utterance.
- The app builds initial voice centroids for the affected players.
- The user can rerun speaker identification using the new profiles and review any remaining uncertain assignments.

### Enhance profiles from an identified session

**Description:** Add high-confidence utterances from a processed session to existing player profiles.

**Goal:** Improve future automatic identification while avoiding feedback from weak or mixed segments.

- The session has cleaned audio, a transcript/discourse, attendees, and existing voice profiles for the relevant players.
- The app selects only utterances assigned to a player with enough identification margin and an acceptable duration.
- The app extracts those portions of cleaned audio and embeds them.
- The app stores them as session-enhancement samples linked to the source session and utterance.
- The app recomputes the profile and may flag or exclude embedding outliers for review.
- Rerunning enhancement for a session replaces that session's earlier generated samples, making the operation repeatable.
- If the session audio, attendee list, or transcript attribution is materially changed, its derived enhancement samples are invalidated.

### Review profile health and provenance

**Description:** Inspect the evidence behind a player's voice profile.

**Goal:** Let the user understand and correct the data that drives automatic attribution.

- The user opens a player profile.
- The app shows imported, seeded, and session-enhanced samples with their source and status.
- The user plays, removes, or excludes questionable samples.
- The app recomputes the centroid when accepted samples change.
- The app warns if too few usable samples remain for reliable matching.

## Sessions

### Create and import a session

**Description:** Add a dated game session and its raw recording.

**Goal:** Establish a durable processing unit without requiring the user to complete all setup at once.

- The user chooses a campaign and creates a session with a name and date.
- The user imports or attaches an audio recording.
- The user selects known attendees and optionally assigns their roles.
- The app preserves the original audio and records its source and storage location.
- The session is shown as ready for processing once its required inputs are present.

### Edit session inputs

**Description:** Correct session metadata, audio, or attendance.

**Goal:** Keep inputs accurate and make downstream consequences visible.

- The user changes the session name/date, replaces audio, or changes attendees/roles.
- The app identifies derived outputs affected by the change.
- The app asks for confirmation before invalidating work such as cleaned audio, transcript/discourse, summary, and enhanced voice samples.
- The original recording is retained unless the user explicitly replaces or deletes it.
- The session becomes ready to reprocess after invalidation.

### Process a session

**Description:** Produce speech artifacts from session audio.

**Goal:** Transform a recording into structured, attributable, reviewable text and a summary.

- The user starts processing a session with valid audio and attendance.
- The app validates prerequisites and reports missing/corrupt inputs before starting expensive work.
- The app cleans/normalizes audio when configured.
- The app transcribes and diarizes the recording.
- The app identifies speakers when participant profiles are available; otherwise it retains anonymous diarized speakers.
- The app stores the structured discourse, readable transcript, processing metadata, and generated summary.
- The app presents progress, failure details, and a retry action.

### Reprocess a session

**Description:** Rerun all speech-processing stages after meaningful input or configuration changes.

**Goal:** Replace stale derivatives predictably.

- The user requests a full reprocess.
- The app records why the prior results are superseded.
- The app invalidates affected derived artifacts and session-derived voice enhancements.
- The app reruns the processing pipeline and records a new processing run.
- The user can distinguish current results from failed or superseded runs.

### Remove a session

**Description:** Remove a session from active campaign use.

**Goal:** Avoid accidental loss of recordings while allowing cleanup later.

- The user requests removal from a campaign.
- The app explains whether this archives, detaches, or permanently deletes the session.
- The user confirms the action.
- A separate destructive maintenance action can permanently remove local media and derived artifacts.

## Transcript, speaker review, and summaries

### Review and correct speaker attribution

**Description:** Inspect utterances and fix automatic or anonymous speaker labels.

**Goal:** Make the transcript trustworthy enough for reading, summary generation, and future voice-profile training.

- The user opens a processed session's transcript/discourse.
- The app shows utterances with timestamps, current speaker label, diarized speaker, and confidence/margin where available.
- The user listens to a relevant clip when needed.
- The user assigns an anonymous/uncertain utterance to a player, changes an incorrect assignment, or leaves it unassigned.
- The app records whether an assignment was automatic or user-reviewed.
- The app can offer selected reviewed utterances as candidate voice clips for profile seeding/enhancement.
- The app marks summaries stale when a speaker correction materially changes their content.

### View and regenerate a summary

**Description:** Read a session summary and regenerate it from the current transcript and glossary.

**Goal:** Give users a concise campaign record without losing the source transcript.

- The user opens the latest session summary.
- The app shows its generation status and whether it is stale.
- The user requests regeneration when the transcript, speaker review, or glossary has changed.
- The app generates a replacement/versioned summary from the current discourse and glossary.
- The transcript and audio remain unchanged by a summary-only operation.

## Recovery and operational feedback

### Resolve missing or invalid inputs

**Description:** Explain why a session cannot be processed and help the user recover.

**Goal:** Prevent silent failures and expensive retries that cannot succeed.

- The app detects missing audio, unsupported media, empty/no-speech audio, missing attendees, and attendees whose player records are unavailable.
- The app reports the affected session and the action required to fix it.
- The user corrects the input and retries processing.

### Monitor background work

**Description:** Surface processing progress and failures.

**Goal:** Make long-running audio and model work understandable in a terminal UI.

- The user starts an operation such as import, processing, or profile enhancement.
- The app reports its current stage, progress where available, and recoverable errors.
- The user can return to the session/player view while work runs, or cancel/retry according to the operation's capabilities.
- The completed run records timestamps, outcome, and error details for later inspection.
