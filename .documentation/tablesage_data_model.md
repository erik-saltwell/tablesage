# TableSage data model

This document defines the persistent relational model needed by the TableSage use cases. It is the design input for a future SQLModel/SQLAlchemy implementation, SQLite database, and Alembic migrations.

The database stores structured metadata, relationships, processing history, transcript data, and references to managed media. Audio files and other large artifacts remain filesystem objects; the database stores their paths, provenance, and lifecycle metadata rather than their bytes.

## Modeling conventions

- Use UUID primary keys for domain records. Human-readable slugs are stable secondary identifiers, not foreign keys.
- Store timestamps in UTC.
- Store embeddings in a portable serialized form initially, such as a BLOB plus dimension/format metadata. Do not depend on SQLite vector search for the first version.
- Use enums for closed lifecycle/provenance values; use text fields for user-entered role names and error details.
- Preserve generated/derived records long enough to explain stale, failed, and superseded work. Do not silently overwrite history.
- Use `created_at` and `updated_at` on user-maintained root records; use immutable provenance on generated records.

## Campaign

Represents one tabletop campaign and owns its player, glossary, and session records.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | Internal identity. |
| `name` | text, non-empty | Display name. |
| `description` | text, nullable | Optional campaign description. |
| `game_system` | text, nullable | Game system label. |
| `default_gm_player_id` | UUID, nullable FK to `player` | Preferred GM when that person is a campaign player. |
| `default_gm_name` | text, nullable | Transitional/display fallback for a GM not yet modeled as a player. |
| `created_at`, `updated_at` | UTC datetime | Audit fields. |

Deleting a campaign hard-deletes its row (cascading to owned rows such as glossary entries). It does not remove associated media files from disk; those become orphaned and are removed by a separate, user-invoked cleanup action. There is no `status`/archive state on `Campaign` for now.

## Glossary entry

Campaign-specific terminology used as generation context.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `campaign_id` | UUID, FK to `campaign`, required | Owner. |
| `term` | text, non-empty | Term or proper noun. |
| `description` | text, nullable | Meaning/spelling guidance. |
| `created_at`, `updated_at` | UTC datetime | |

Constraint: unique `(campaign_id, term)` after an agreed normalization rule.

## Player and voice profile

### Player

A campaign participant who can attend sessions and receive transcript attribution.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `campaign_id` | UUID, FK to `campaign`, required | Campaign-local identity. |
| `slug` | text, required | Human-readable stable identifier within a campaign. |
| `name` | text, non-empty | Display name. |
| `created_at`, `updated_at` | UTC datetime | |

Constraint: unique `(campaign_id, slug)`.

Deleting a player hard-deletes its row. It does not remove associated media files from disk; those become orphaned and are removed by a separate, user-invoked cleanup action. There is no `status`/archive state on `Player` for now. Note: `utterance.player_id`, `diarized_speaker.player_id`, and `voice_sample.player_id` reference players — deleting a player who has transcript history needs an explicit FK on-delete decision (e.g. `SET NULL`) rather than cascading, so that history isn't silently destroyed.

### Voice profile

The current derived representation used for speaker matching. One active profile belongs to one player.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `player_id` | UUID, unique FK to `player` | One current profile per player. |
| `centroid_embedding` | serialized embedding, nullable | Null until sufficient accepted samples exist. |
| `embedding_dimension` | integer, nullable | Validates compatibility. |
| `sample_count` | integer | Derived/cacheable count of accepted samples. |
| `computed_at` | UTC datetime, nullable | Last profile computation. |
| `status` | enum: `untrained`, `ready`, `needs_review` | Profile health. |

The centroid is derived from accepted voice samples and must be recomputed when their acceptance changes.

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
| `id` | UUID, primary key | |
| `campaign_id` | UUID, FK to `campaign`, required | Owner. |
| `slug` | text, required | Stable campaign-local identifier. |
| `name` | text, non-empty | Session title. |
| `session_date` | date | Game-session date. |
| `raw_audio_asset_id` | UUID, nullable FK to `media_asset` | Original imported recording. |
| `status` | enum: `draft`, `ready`, `processing`, `processed`, `needs_review`, `failed` | Current user-facing state. |
| `created_at`, `updated_at` | UTC datetime | |

Constraint: unique `(campaign_id, slug)`. Index `(campaign_id, session_date)` supports ordered session lists.

Deleting a session hard-deletes its row. It does not remove associated media files from disk; those become orphaned and are removed by a separate, user-invoked cleanup action.

### Session attendance

Joins known campaign players to a session.

| Field | Type / constraint | Notes |
| --- | --- | --- |
| `id` | UUID, primary key | |
| `session_id` | UUID, FK to `session`, required | |
| `player_id` | UUID, FK to `player`, required | |
| `created_at` | UTC datetime | |

Constraint: unique `(session_id, player_id)`.

### Attendance role

Allows one attendee to have zero or more free-form roles in a session.

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

- A campaign owns players, sessions, and glossary entries.
- A session can reference only players from its campaign as attendees or attributed speakers.
- A player can have many voice samples but one current voice profile.
- A session-derived voice sample must reference its source session; when available, it should reference its utterance.
- An imported directory source is replaceable as a unit: a new import supersedes/retires previous `directory_import` samples for the same player and normalized source directory.
- An enhancement run is replaceable as a unit: rerunning it supersedes/retires prior `session_enhancement` samples for that player/session pair.
- Diarized speakers are session-local anonymous clusters. They may map to a player, but the original cluster label must remain available for audit and re-review.
- User-reviewed utterance attribution takes precedence over automatic matching until the user explicitly changes it.
- Changing raw audio, attendance, or transcript attribution marks affected artifacts and session-derived voice samples stale; it does not delete raw audio automatically.

## Initial migration sequence

1. Create campaign, glossary, player, session, attendance, and media-asset tables.
2. Create voice-profile and voice-sample tables.
3. Create processing-run, artifact, and summary tables.
4. Create diarized-speaker, utterance, and word tables.
5. Add indexes and uniqueness constraints after the basic relationships are established.

The first SQLModel implementation should keep database operations behind a repository/store interface so the TUI does not depend on SQLAlchemy session mechanics.
