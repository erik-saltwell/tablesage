# Enhance Players from a Session

## Overview

Players List's `S` (**From Session**) action extracts voice clips from an already-transcribed
session for all attendees and folds them into their player voice profiles. The user chooses a
session; transcript source and filtering are then automatic.

This flow is distinct from **From Audio**: the session already has attendee identities and a
speaker-attributed transcript, so there is no proposal or per-speaker resolution step.

## Transcript source and trust rule

The artifact boundary determines how utterances are selected:

1. If `transcript_reviewed.json` exists, load it. A completed Manual Review is treated as human
   ground truth, so every utterance whose `speaker` exactly matches an attendee name is eligible.
   Similarity margin and duration are not inspected.
2. Otherwise load `transcript.json`. An utterance is eligible only when:
   - `speaker == attendee.player_name`;
   - `similarity_margin >= enhance_voices.min_margin_for_voice_sample`;
   - duration is at least `enhance_voices.min_clip_seconds`; and
   - duration is at most `enhance_voices.max_clip_seconds`.
3. `Unassigned Speaker` never matches an attendee name and is silently skipped in either path.

A missing `similarity_margin` fails the machine-transcript filter. No new similarity calculation
is performed here: the machine path consumes the value recorded during speaker identification,
while the reviewed path deliberately trusts the human decision.

## Flow

1. `S` opens `SessionFromCampaignPickerDialog` from Players List.
2. The campaign selector scopes a session table. Sessions without `transcript.json` remain
   visible but dimmed and cannot be selected.
3. Selecting a transcribed session starts a progress dialog immediately. There is no separate
   filtering prompt or per-utterance review.
4. For each attendee, the application determines eligible utterances using the source rule
   above and extracts their ranges from `input_audio.wav`.
5. New files use a deterministic source-session hash segment plus a UUID:
   `session-{player}-{campaign}-{session}-{hash8(session_id)}-{uuid}.wav`.
6. The run captures that attendee's prior clips from the same source session. Only after all new
   clips for that attendee are extracted successfully are those prior files deleted. This
   extract-then-retract ordering preserves the old contribution on failure.
7. The prior contribution is retracted even when the new eligible set is empty.
8. Every attendee's centroid is recomputed afterward, including attendees whose run produced no
   clips, because old clips may have been removed.
9. The UI reports enhanced-player count and total new clip count.

## Progress

- `Stage.EXTRACTING` reports one running count across all eligible utterances.
- `Stage.RECOMPUTING_CENTROIDS` reports once per attendee.

## Settings

No new settings are needed. When the machine transcript is used, the flow reuses:

- `enhance_voices.min_margin_for_voice_sample`
- `enhance_voices.min_clip_seconds`
- `enhance_voices.max_clip_seconds`
- `remove_outliers.min_sample_similarity`
- `remove_outliers.min_samples`

The reviewed-transcript path intentionally bypasses the three `enhance_voices` selection values,
but still uses `remove_outliers` during centroid recomputation.

## Artifact lifecycle dependency

Manual Review writes `transcript_reviewed.json` only on Complete. A transcript rebuild, successful
audio re-import, or attendance mutation deletes that reviewed artifact. The next From Session run
therefore falls back automatically to the filtered machine transcript instead of trusting stale
human assignments.

Previously extracted player-side clips are not proactively removed when a transcript artifact is
invalidated. They are replaced the next time From Session runs for that source session.

## Implementation map

- `players_from_session.select_enhancement_utterances`: pure machine-transcript filter.
- `players_from_session.select_assigned_utterances`: pure reviewed-transcript selection.
- `players_from_session.enhance_players_from_session`: artifact choice, extraction,
  replace-as-a-unit behavior, and centroid recomputation.
- `Application.enhance_players_from_session`: resolves database entities and player/session paths.
- `PlayersListScreen.action_enhance_from_session`: picker, progress, and result notification.

Tests cover filter boundaries, reviewed-artifact bypass, unassigned exclusion, staged progress,
rerun replacement, and zero-new-clip retraction.
