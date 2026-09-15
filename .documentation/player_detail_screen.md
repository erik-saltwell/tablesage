# Player Detail

Player Detail manages one global player's name and filesystem-backed voice profile. The code is [screens/player_detail.py](../apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py); clip operations live in [voice_clips/clips.py](../packages/tablesage-application/src/tablesage_application/voice_clips/clips.py).

## Display and storage

The editable name sits above read-only centroid sample count, computed time, centroid hash and total clip duration. The table lists each WAV filename and duration. Total duration includes every clip on disk, not only clips used in the centroid.

Clips live under `players/<player-name>/` in the launch workspace. There is no VoiceSample table. Player stores `centroid_embedding`, `embedding_dimension`, `sample_count` and `computed_at`. Filename source hashes identify replaceable directory/session/audio-import contributions; cosmetic name slugs can become old after renames without breaking matching.

Renaming coordinates the database name and player directory, with rollback on rename failure. A conflicting orphan folder requires explicit confirmation before removal. Session files are not rewritten to replace speaker names; affected freshness dependencies account for identity changes.

## Actions

| Key | Behavior |
| --- | --- |
| F | Import WAV clips from a directory; see [directory import](import_player_from_filesystem.md) |
| D / Delete / Backspace | Confirm deletion of the selected clip, then recompute |
| R | Recompute the centroid from current files |
| C | Confirm recompute and permanent removal of unused duplicate/outlier clips |
| F5 | Reload metadata and the clip table without recomputing |
| Escape | Return to Players List |

There is no S session-import action here. [Players List → From Session](enhance_players_from_session.md) enhances all attendees from an existing session; [From Audio](import_players_from_audio_file.md) creates or enhances players from a new recording. Clips have no edit/open action.

## Centroid behavior

Recomputation hashes files to deduplicate identical content, embeds unique clips and applies configured outlier removal. `sample_count` counts contributing clips, not raw files. A plain recompute excludes unused files without deleting them; C additionally deletes the returned `unused_paths`. If no clips remain, centroid/dimension/computed time are cleared and sample count becomes zero.

Directory import and clip deletion recompute automatically, except an all-rejected import preserves existing clips and the stored profile without recomputation and shows a warning. The cleaning import option also removes unused files after a successful import and recomputation. R is useful after out-of-band file changes; F5 merely reloads existing state and can discard an uncommitted name edit.

Application supplies `remove_outliers.min_sample_similarity` and `min_samples` from deployed settings. Filesystem changes and database commits are not a general cross-resource transaction: do not promise recovery of deleted clips after a later embedding or database failure.
