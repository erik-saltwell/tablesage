# TableSage data model

This document defines the persistent relational model needed by the TableSage use cases. It is the design input for a future SQLModel/SQLAlchemy implementation, SQLite database, and Alembic migrations.

The database stores structured metadata, relationships, processing history, transcript data, and references to managed media. Audio files and other large artifacts remain filesystem objects; the database stores their paths, provenance, and lifecycle metadata rather than their bytes.

## Modeling conventions

- Use UUID primary keys for domain records. `Campaign` and `Player` additionally require a unique, human-readable `name`, which is also the name of their on-disk folder — there is no separate slug field. `Session` folders are instead named by a campaign-scoped sequence number (see below); a session's `name` is not unique.
- Store timestamps in UTC.
- Store embeddings in a portable serialized form initially, such as a BLOB plus dimension/format metadata. Do not depend on SQLite vector search for the first version.
- Use enums for closed lifecycle/provenance values; use text fields for user-entered role names and error details.
- Preserve generated/derived records long enough to explain stale, failed, and superseded work. Do not silently overwrite history.
- Use `created_at` and `updated_at` on user-maintained root records; use immutable provenance on generated records.
- Renaming a `Campaign` or `Player` renames its on-disk folder as part of the same operation; if the filesystem rename fails, the whole rename fails and rolls back.

## Campaign

Represents one tabletop campaign. Campaigns and players are both top-level records; a campaign's participants are the players linked to it through `campaign_player` (below), not owned rows.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | Internal identity. |
| `name` | text, non-empty, unique | Display name; also the on-disk campaign folder name. |
| `description` | text, nullable | Optional campaign description. |
| `game_system` | text, nullable | Game system label. |
| `created_at`, `updated_at` | UTC datetime | Audit fields. |

There is no `default_gm_player_id`/`default_gm_name` on `Campaign` — the GM is just whichever `campaign_player` row has `default_role_name == "game-master"`.

Deleting a campaign hard-deletes its row (cascading to owned rows such as glossary entries and `campaign_player` memberships). It does not remove associated media files from disk; those become orphaned and are removed by a separate, user-invoked cleanup action, which only touches campaign folders (not player folders). There is no `status`/archive state on `Campaign` for now.

## Campaign roster

### Campaign player

Links a player to a campaign and carries the campaign-specific default used when creating new sessions.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `campaign_id` | UUID, FK to `campaign`, required | |
| `player_id` | UUID, FK to `player`, required | |
| `default_role_name` | text, non-empty | `"game-master"` marks this member as the campaign's GM; any other value is their default character name. Used only to seed `session_attendance_role` when a new session is created — a player can hold different roles in different sessions (e.g. after a character death), and this default is editable per campaign. |
| `created_at` | UTC datetime | |

Constraint: unique `(campaign_id, player_id)`. A player may belong to any number of campaigns, and the same player can have a different `default_role_name` in each.

Only players linked through `campaign_player` may be selected as attendees or attributed speakers for that campaign's sessions.

## Glossary entry

Campaign-specific terminology used as generation context.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `campaign_id` | UUID, FK to `campaign`, required, part of primary key | Owner. |
| `id` | UUID, part of primary key | |
| `term` | text, non-empty | Term or proper noun. |
| `description` | text, nullable | Meaning/spelling guidance. |
| `created_at`, `updated_at` | UTC datetime | |

Primary key: composite `(campaign_id, id)` — unlike other tables in this document, glossary entries have no independent identity outside their owning campaign. Constraint: unique `(campaign_id, term)` after an agreed normalization rule.

## Player

A top-level participant identity, independent of any campaign. A player may belong to zero or more campaigns via `campaign_player`, and carries its own voice profile directly (folded onto this table rather than a separate one, since a player has at most one current profile and no profile history is tracked).

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `name` | text, non-empty, unique | Display name; also the on-disk player folder name (holding that player's wav voice clips). |
| `centroid_embedding` | serialized embedding, nullable | Null until sufficient accepted samples exist; a player may exist with no clips and no centroid. |
| `embedding_dimension` | integer, nullable | Validates compatibility. |
| `sample_count` | integer | Derived/cacheable count of accepted samples. |
| `computed_at` | UTC datetime, nullable | Last centroid computation. |
| `created_at`, `updated_at` | UTC datetime | |

Deleting a player hard-deletes its row (and its `campaign_player` memberships). It does not remove the player's on-disk clip directory; that becomes orphaned and is removed by a separate, user-invoked "cleanup players" action. There is no `status`/archive state on `Player` for now. Note: `utterance.player_id`, `diarized_speaker.player_id`, and `voice_sample.player_id` reference players — deleting a player who has transcript history needs an explicit FK on-delete decision (e.g. `SET NULL`) rather than cascading, so that history isn't silently destroyed.

The centroid is derived from accepted voice samples and must be recomputed when their acceptance changes. Processing actions that require speaker identification (e.g. processing a session's transcript) fail fast if any roster player for that session's campaign has a null centroid, rather than silently skipping identification for that player.

### Media asset

A managed or externally referenced audio file. This table does not contain the file bytes.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `storage_path` | text, required | App-managed relative path or approved external path reference. |
| `original_path` | text, nullable | Source chosen by user, retained for provenance. |
| `media_kind` | enum: `session_audio`, `voice_clip`, `cleaned_audio` | Primary purpose. |
| `format` | text, nullable | e.g. WAV, MP3. |
| `duration_seconds` | real, nullable | Extracted media metadata. |
| `checksum` | text, nullable | Supports duplicate/change detection. |
| `created_at` | UTC datetime | |

### Voice sample

One accepted or rejected clip used to train a player profile.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `player_id` | UUID, FK to `player`, required | Profile owner. |
| `media_asset_id` | UUID, FK to `media_asset`, required | Managed extracted/imported clip. |
| `provenance` | enum: `directory_import`, `session_seed`, `session_enhancement`, `manual_clip` | How it entered the profile. |
| `source_directory` | text, nullable | Required for `directory_import`; allows source replacement on reimport. |
| `source_session_id` | UUID, nullable FK to `session` | Required for session-derived samples. |
| `source_utterance_id` | UUID, nullable FK to `utterance` | Exact source when applicable. |
| `source_index` | integer, nullable | Order within a source import/session. |
| `embedding` | serialized embedding | Clip embedding. |
| `embedding_dimension` | integer | |
| `accepted` | boolean | Only accepted samples contribute to a profile. |
| `rejection_reason` | text, nullable | Manual or automatic outlier reason. |
| `created_at` | UTC datetime | |

Indexes: `player_id`; `(source_directory, provenance)`; `source_session_id`.

## Session and attendance

### Session

A dated recording and its processing lifecycle within a campaign.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | Shown in the UI. |
| `campaign_id` | UUID, FK to `campaign`, required | Owner. |
| `sequence_number` | integer, required | Campaign-scoped, assigned as `max existing + 1` at creation, never reused after a session is deleted (no gap-filling). Zero-padded to 3 digits as the on-disk session folder name (e.g. `007`). |
| `name` | text, non-empty | Session title. Not required to be unique. |
| `session_date` | date | Game-session date. |
| `raw_audio_asset_id` | UUID, nullable FK to `media_asset` | Original imported recording. |
| `status` | enum: `draft`, `ready`, `processing`, `processed`, `needs_review`, `failed` | Current user-facing state. |
| `created_at`, `updated_at` | UTC datetime | |

Constraint: unique `(campaign_id, sequence_number)`. Index `(campaign_id, session_date)` supports ordered session lists.

Deleting a session hard-deletes its row. It does not remove associated media files from disk; those become orphaned and are removed by a separate, user-invoked cleanup action.

### Session attendance

Joins campaign-roster players (see `campaign_player`) to a session. Only players who are members of the session's campaign may be added here.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `player_id` | UUID, FK to `player`, required | Must be a member of `session.campaign_id` via `campaign_player`. |
| `created_at` | UTC datetime | |

Constraint: unique `(session_id, player_id)`. When attendance is created, seed one `session_attendance_role` row from the matching `campaign_player.default_role_name`; the user may add, edit, or remove roles afterward.

### Session attendance role

Allows one attendee to have zero or more free-form roles in a session (e.g. a player who takes over an NPC alongside their main character).

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `attendance_id` | UUID, FK to `session_attendance`, required | |
| `name` | text, non-empty | e.g. `Game Master`. |

Constraint: unique `(attendance_id, name)` after normalization.

## Processing and generated artifacts

### Processing run

An attempt to process a session. This gives long-running work durable status and error history.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `run_kind` | enum: `full`, `transcription`, `speaker_identification`, `summary` | Requested scope. |
| `status` | enum: `queued`, `running`, `succeeded`, `failed`, `cancelled`, `superseded` | Outcome/lifecycle. |
| `started_at`, `finished_at` | UTC datetime, nullable | |
| `stage` | text, nullable | Current/last stage for UI progress. |
| `error_code`, `error_message` | text, nullable | Recoverable failure detail. |
| `configuration_snapshot` | JSON text, nullable | Settings/model versions used by this run. |
| `supersedes_run_id` | UUID, nullable FK to `processing_run` | Run lineage. |

Indexes: `session_id`; `(session_id, status)`.

### Session artifact

Metadata for a derived file associated with a processing run.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `processing_run_id` | UUID, nullable FK to `processing_run` | Producer. |
| `media_asset_id` | UUID, nullable FK to `media_asset` | Used for cleaned audio. |
| `artifact_type` | enum: `cleaned_audio`, `discourse_export`, `transcript_export`, `summary_export` | |
| `storage_path` | text, required | Export path when no media asset applies. |
| `status` | enum: `current`, `stale`, `superseded`, `deleted` | Lifecycle without destroying provenance. |
| `created_at` | UTC datetime | |

At most one `current` artifact of each type should exist per session.

### Summary

A generated or user-maintained summary for one session.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `processing_run_id` | UUID, nullable FK to `processing_run` | Generation run. |
| `content_markdown` | text, required | Summary body. |
| `status` | enum: `current`, `stale`, `superseded` | |
| `generated_at` | UTC datetime | |

## Diarization, attribution, and transcript

### Diarized speaker

An anonymous voice cluster produced for one session. It is intentionally separate from a real player.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `diarization_label` | text, required | Provider label such as `speaker_0`. |
| `player_id` | UUID, nullable FK to `player` | User-confirmed cluster-level mapping when appropriate. |
| `assignment_source` | enum: `unassigned`, `automatic`, `user_reviewed` | Never infer identity solely from label text. |
| `created_at`, `updated_at` | UTC datetime | |

Constraint: unique `(session_id, diarization_label)`.

### Utterance

A contiguous transcript segment. It is the primary review and voice-sample selection unit.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `processing_run_id` | UUID, nullable FK to `processing_run` | Producer. |
| `diarized_speaker_id` | UUID, nullable FK to `diarized_speaker` | Anonymous cluster. |
| `player_id` | UUID, nullable FK to `player` | Current real-person attribution. |
| `attribution_source` | enum: `unassigned`, `diarization`, `automatic_profile_match`, `user_reviewed` | Attribution provenance. |
| `text` | text, required | Spoken text. |
| `start_seconds`, `end_seconds` | real, required | Session-audio time range. |
| `embedding` | serialized embedding, nullable | Embedding used for profile matching. |
| `similarity_margin` | real, nullable | Confidence-like difference from competing profile matches. |
| `review_status` | enum: `unreviewed`, `accepted`, `corrected`, `excluded` | Human review state. |
| `created_at`, `updated_at` | UTC datetime | |

Indexes: `(session_id, start_seconds)`; `player_id`; `diarized_speaker_id`; `review_status`.

### Word

Word-level timing within an utterance.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `utterance_id` | UUID, FK to `utterance`, required | |
| `position` | integer, required | Preserves order, including spacing/audio events if retained. |
| `text` | text, required | Token text. |
| `start_seconds`, `end_seconds` | real, required | Word timing. |
| `kind` | enum: `word`, `spacing`, `audio_event` | Provider classification. |

Constraint: unique `(utterance_id, position)`.

## Required relationship rules

- Campaign and Player are both top-level; a campaign's participants are the players linked via `campaign_player`, not owned rows. A player may belong to any number of campaigns (or none).
- A campaign owns its sessions and glossary entries directly (unlike players).
- A session can reference only players who are members of its campaign (via `campaign_player`) as attendees or attributed speakers.
- A player can have many voice samples but carries at most one current centroid/profile, stored directly on the `player` row.
- A session-derived voice sample must reference its source session; when available, it should reference its utterance.
- An imported directory source is replaceable as a unit: a new import supersedes/retires previous `directory_import` samples for the same player and normalized source directory.
- An enhancement run is replaceable as a unit: rerunning it supersedes/retires prior `session_enhancement` samples for that player/session pair.
- Diarized speakers are session-local anonymous clusters. They may map to a player, but the original cluster label must remain available for audit and re-review.
- User-reviewed utterance attribution takes precedence over automatic matching until the user explicitly changes it.
- Changing raw audio, attendance, or transcript attribution marks affected artifacts and session-derived voice samples stale; it does not delete raw audio automatically.
- Processing actions requiring speaker identification fail fast if any campaign-roster player lacks a computed centroid, rather than silently proceeding without identifying that player.

## Initial migration sequence

1. Create campaign, player, campaign-player, glossary, session, session-attendance, session-attendance-role, and media-asset tables.
2. Create voice-sample table (centroid fields already live on `player`).
3. Create processing-run, artifact, and summary tables.
4. Create diarized-speaker, utterance, and word tables.
5. Add indexes and uniqueness constraints after the basic relationships are established.

The first SQLModel implementation should keep database operations behind a repository/store interface so the TUI does not depend on SQLAlchemy session mechanics.
