# Import player voice clips from a directory

Player Detail's **F — Folder Imp** action imports reference WAVs for one existing player. It is implemented in [Player Detail](../apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py), Application and [voice_clips/clips.py](../packages/tablesage-application/src/tablesage_application/voice_clips/clips.py).

## Flow

1. Open the shared `SelectDirectory` picker at the user's home directory.
2. Validate that the selection is a directory containing at least one non-recursive `*.wav` match. Other files are ignored.
3. Ask whether to clean the recordings. No means import without cleaning; cancel aborts.
4. Find previous clips from this same resolved source path. If any exist, confirm replacing that contribution.
5. Copy each WAV to a new generated filename, optionally after denoising/formatting. With cleaning enabled, loudness normalization follows `audio_cleaning.normalize_volume`.
6. Attempt an embedding for each new clip. An embedding failure deletes that new target, records the source filename as rejected and continues. Progress reports source files processed.
7. If at least one embedding succeeded, remove the prior source-matched clips, then recompute the player's centroid over all current clips. If every embedding was rejected, stop without changing existing clips or the stored centroid (including its timestamp).
8. When cleaning was selected, delete all unused duplicate/outlier files returned by recomputation, including older files from other contributions. Otherwise leave unused files on disk.
9. Refresh the profile/table and report imported, replaced, rejected and removed-unused counts. An all-rejected import warns that no usable clips were imported and the voice profile is unchanged; its replaced count is zero.

## Provenance and replacement

Generated names are:

```text
import-<player-slug>-<sourcehash8>-<uuid4hex>.wav
```

`sourcehash8` is the first eight SHA-256 hex characters of the resolved absolute source-directory path. Matching uses the prefix and hash, not the player's cosmetic slug. Renaming the player therefore does not break replacement, but moving the source directory changes its identity.

Session-derived and diarized-audio imports use separate `session-` and `diarized-` prefixes and their own hash inputs; see [session enhancement](enhance_players_from_session.md) and [audio import](import_players_from_audio_file.md). There is no provenance database table.

## Failure and settings boundaries

Picker cancellation and declining replacement make no changes. An all-rejected embedding pass preserves the previous contribution and profile, including when cleaning was requested. A partially successful import still replaces the old source contribution. This is not a general atomic import: cleaning/copy failures propagate rather than being treated as individual embedding rejections, and already copied new files can remain. Failures during recomputation do not roll back filesystem replacement.

Outlier thresholds come from deployed `remove_outliers` settings. Cleaning is a per-invocation choice, while normalization and outlier thresholds are configured values. No new picker abstraction or import-phase stub remains to implement.
