# TableSage use cases

TableSage maintains a local tabletop-campaign workspace, global player voice profiles and a reviewed audio-to-campaign-record pipeline. This document describes implemented capabilities, not a backlog. See [architecture](system_architecture.md) for storage and [screen inventory](tablesage_tui_screens.md) for controls.

## Campaigns, roster and glossary

Create a named campaign, edit its description/game system and rename its on-disk folder with its database identity. Campaigns share a workspace but keep separate session folders and glossaries. There is no active/archived campaign status or archived-only list.

Players exist independently of campaigns. A CampaignPlayer roster links an existing player and default role to a campaign. The same player can serve multiple campaigns. Removing roster membership does not delete the global player or its clips. Session attendance uses roster-scoped choices and supports multiple roles.

Maintain unique, nonblank glossary terms and optional descriptions manually, import terms from legacy settings, or extract proposals from a Role Transcript and review them before committing. A glossary change advances its input clock; generated consumers become stale without deleting old outputs. There is no general glossary search/filter control promised here.

Campaign ZIP export/import transfers campaign data; player ZIP import/export is also available separately. “Archive” in these operations means a transfer file, not hiding an inactive campaign. Entity deletion is confirmed and removes database records; orphan-directory cleanup is a separate destructive action. See the application archive/entity modules for exact payload, collision and cleanup rules.

## Players and voice profiles

Create a global player by name, even without clips/centroid. Player Detail shows the clip filenames/durations and computed profile metadata; it is not a provenance database or per-clip acceptance/playback dashboard.

Supported ways to acquire voice clips are:

- [Directory import](import_player_from_filesystem.md): import non-recursive WAVs for one player, optionally clean, replace that source's old contribution and recompute.
- [From Audio](import_players_from_audio_file.md): transcribe a standalone recording, propose speaker identities, let the user resolve/exclude whole speakers, then create/enhance players. No campaign/session is created.
- [From Session](enhance_players_from_session.md): extract clips for all attendees from an existing transcribed session. Reviewed attribution bypasses quality margin/duration bounds but still enforces the technical embedding-duration floor; machine attribution uses the configured filters.

Source hashes in generated filenames support replacement after renames. There are no VoiceSample rows or source-utterance provenance records. Extracted profile contributions are not proactively retracted when a session changes; rerunning the relevant import replaces its contribution.

Delete clips, recompute a centroid, or explicitly clean unused duplicate/outlier files. Recompute counts only contributing clips; a zero-clip profile clears its centroid. From Session prefers a current review, otherwise a current machine transcript with confidence/duration filtering, and requests retranscription if neither is current. Directory imports with every new embedding rejected preserve existing clips and the stored profile.

## Sessions and processing

Create a Session with a name and optional date. It receives a campaign-local sequence and numbered folder. Attendance is seeded from the preceding Session when available, otherwise from the roster. Names need not be unique; renaming does not change the numbered folder.

Import audio and then attempt transcription. WAV import offers a cleaning choice; other supported formats are cleaned. The managed input may be processed audio rather than an untouched original. The user retains responsibility for the original external recording.

Transcription requires attendees with computed voice centroids. It transcribes/diarizes, identifies speakers, punctuates and removes pre-review backchannels, saving machine JSON and readable Markdown. Uncertain attribution is Unassigned, not an invented identity.

[Manual Review](speaker_review_screen.md) first offers spelling suggestions when present, then permits speaker/text corrections, playback, utterance deletion and bulk replacement in a working copy. Complete saves the reviewed artifact; Cancel leaves prior saved files intact. Ordinary generated outputs require a current completed review.

## Generated record and regeneration

[Generate Outputs](session_detail_screen.md) evaluates dependencies and builds only missing or stale targets:

1. Role Transcript.
2. Transcript Sections.
3. Joint Ledger v4 and complete Scene Breakdown.
4. Player Introductions.
5. Selective Recap Summary from Scene Breakdown.
6. Detailed Summary from Ledger, with current introductions and the preceding Session's recap.

The [specs](../specs/) define exact source restrictions, schemas and failure behavior. Ledger condenses reusable current-session fiction rather than serving as a lossless transcript. Scene Breakdown supplies a compact complete scene history. The brief recap selects continuity; it is not one mandatory bullet per scene.

Input changes preserve existing files and mark affected outputs stale. Regenerate Artifact forces a selected producer and updates downstream work; Campaign Detail's Regenerate All Outputs applies the wider campaign operation. A selected Summary can require rebuilding stale prerequisites, so “summary-only” is not a promise that no upstream generator runs. No database ProcessingRun history or versioned artifact catalog is maintained.

Session Detail shows freshness and errors; generated documents are inspected externally or [exported](export_artifact.md). Export is presence-based and can copy stale files. Clean Session explicitly deletes every registered artifact including audio. Deleting the Session database record and cleaning orphan folders are separate actions on Campaign Detail.

## Prepare the next session

**Create Previously On** requires current, valid, complete Scene Breakdowns for every Session. It proposes ingredients, scouts relevant scenes, lets the GM select any scenes, then writes external Markdown. The writer sees approved scenes, the edited starting situation and glossary—not upcoming notes or private scout rationale. There is no managed artifact or resumable draft. See [the implemented design](../.scratch/campaign-aware-previously-on/proposal.md).

**Generate Opportunities** uses the complete validated Campaign Scene Recap and a required upcoming-session prompt to produce up to five reincorporation pitches. Results and their original prompt are ephemeral; saving exports the displayed set without another model call. Failure preserves the prior displayed set. See [the implemented design](../.scratch/reincorporation-assistant/proposal.md).

## Configuration and operational feedback

Settings exposes High/Medium/Low model choices and personal API keys, not every processing knob. Other deployed YAML settings remain preserved on Save. Keys use the personal user-config directory and inherited shell overrides; workspace configuration stays local. Mandatory version review blocks ordinary landing navigation until a valid Save. See [Settings](../.scratch/settings/design.md).

Long operations use modal stage/progress feedback, usually without mid-flight cancellation. Errors surface as notifications and logs; Session Detail additionally retains an in-memory error table for its import/generate/clean actions. Correct inputs and retry explicitly; the UI does not offer arbitrary concurrent navigation or automatic recovery for every failure.
