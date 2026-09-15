# Enhance Players from a Session

## Overview

Players List's `S` (**From Session**) action extracts voice clips from an already-transcribed
session for all attendees and folds them into their player voice profiles. The user chooses a
session; transcript source and filtering are then automatic.

This flow is distinct from **From Audio**: the session already has attendee identities and a
speaker-attributed transcript, so there is no proposal or per-speaker resolution step.

## Transcript source and trust rule

The artifact boundary determines how utterances are selected:

1. If `transcript_reviewed.json` is current, load it. A current completed Manual Review is treated as human
   ground truth, so every utterance whose `speaker` exactly matches an attendee name is eligible.
   Similarity margin and quality-duration bounds (`min_clip_seconds`/`max_clip_seconds`) are not
   inspected -- but duration is still checked against `enhance_voices.min_embeddable_clip_seconds`,
   a hard technical floor (the embedding model can't compute a feature window below it), not a
   quality filter. See Settings below.
2. Otherwise load `transcript.json` if current, or ask for retranscription if not. An utterance is eligible only when:
   - `speaker == attendee.player_name`;
   - `similarity_margin >= enhance_voices.min_margin_for_voice_sample`;
   - duration is at least `enhance_voices.min_clip_seconds`;
   - duration is at most `enhance_voices.max_clip_seconds`; and
   - duration is at least `enhance_voices.min_embeddable_clip_seconds` (in practice always implied
     by `min_clip_seconds`'s default, but enforced independently in case that setting is tuned low).
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

The flow uses these deployed settings:

- `enhance_voices.min_margin_for_voice_sample`
- `enhance_voices.min_clip_seconds`
- `enhance_voices.max_clip_seconds`
- `enhance_voices.min_embeddable_clip_seconds`
- `remove_outliers.min_sample_similarity`
- `remove_outliers.min_samples`

The reviewed-transcript path intentionally bypasses `min_margin_for_voice_sample`,
`min_clip_seconds`, and `max_clip_seconds` (see the trust rule above), but still applies
`min_embeddable_clip_seconds` and uses `remove_outliers` during centroid recomputation.

## Artifact lifecycle dependency

Manual Review writes `transcript_reviewed.json` only on Complete. Rebuilding the transcript or changing audio/attendance preserves the reviewed file while the artifact graph marks affected outputs stale.

From Session checks recursive artifact freshness in Application before extracting or deleting clips. It prefers a current reviewed transcript, otherwise uses a current machine transcript with the configured confidence/duration filters. If neither is current, it asks for retranscription without changing voice profiles. The picker still lists sessions by transcript existence; Application enforces freshness after selection. Recomputing attendee centroids changes an input to transcription, so another enhancement run may require retranscription first.

Previously extracted player-side clips are not proactively removed when a transcript artifact is
invalidated. They are replaced the next time From Session runs for that source session.

## Implementation map

- `players_from_session.select_enhancement_utterances`: pure machine-transcript filter.
- `players_from_session.select_assigned_utterances`: pure reviewed-transcript selection.
- `players_from_session.enhance_players_from_session`: artifact choice, extraction,
  replace-as-a-unit behavior, and centroid recomputation.
- `Application.enhance_players_from_session`: resolves database entities and player/session paths.
- `PlayersListScreen.action_enhance_from_session`: picker, progress, and result notification.

See the implementation for filter boundaries, reviewed-artifact bypass, staged progress and zero-new-clip retraction. These descriptions do not imply that a provider-backed enhancement was rerun during documentation maintenance.
