# Campaign UI Design Reference

This document summarizes the campaign data model and the campaign-related actions currently present or implied by the codebase. It is intended as source material for designing the campaign screen.

## Current Product Shape

The current TUI has two campaign entry surfaces:

- `NoCampaignsScreen`: empty-state welcome screen with actions for new campaign, import campaign, and help.
- `CampaignsScreen`: campaign list screen with active/archived/all filters, name search, a campaign table, row highlight, row select, new campaign, import campaign, and help.

The current campaign list uses `CampaignSummary`, a computed read model. Selecting a campaign currently only shows a notification, so the detailed campaign screen has not been implemented yet.

## Domain Glossary

| Term | Meaning | Design relevance |
| --- | --- | --- |
| Campaign | The top-level workspace for a tabletop campaign. Stores campaign metadata and glossary, and owns sessions and players through related files. | Primary object for the campaign screen. |
| Campaign slug | Filesystem-safe identifier derived from the campaign name, for example `Iron Pact` becomes `iron-pact`. | Usually hidden from users, but useful in error states and diagnostics. |
| Campaign set | Global index of available campaigns. Contains lightweight entries with `slug` and `name`. | Drives the campaign directory/list. |
| Campaign summary | Computed list-row model assembled from campaign, session set, and player set data. | Powers overview cards/tables and filters. |
| Campaign state | Active or archived. | Drives active/archived/all filtering and archive/restore actions. |
| Glossary | Campaign-level list of important proper nouns or terms. Used when generating session summaries. | Needs editable term/description management. |
| Glossary entry | One glossary item with a required non-blank term and optional description. | Simple two-field row/editor. |
| Session | A dated game session with a name, slug, raw audio filename, and attendee-role map. | Main child object under a campaign. |
| Session set | Campaign-local session index. Contains lightweight session entries with `slug`, `name`, and `session_date`. | Drives session list, date bounds, and session count. |
| Session artifacts | Derived files produced during processing: cleaned audio, discourse JSON, transcript markdown, and summary markdown. | Needs status, progress, retry, stale-data, and destructive-change UX. |
| Discourse | Structured transcript data containing utterances, words, speaker labels, embeddings, and confidence margin. | Useful for transcript review and speaker correction UI. |
| Utterance | A contiguous speech segment by one speaker. Has text, speaker, words, optional embedding, and similarity margin. | Unit for transcript display and speaker review. |
| Player | A campaign participant/speaker profile with name, slug, voice samples, and voice centroid. | Needed for attendees, speaker identification, and cast management. |
| Player set | Campaign-local player index. Contains lightweight player entries with `slug` and `name`. | Drives player/cast count and attendee pickers. |
| Role | Free-form role string for a player in a session. `Game Master` is the canonical GM role. | Session attendee editor should allow one or more roles per attendee. |
| Voice sample | Audio clip tied to a player, with embedding, source, provenance, and index. | Powers speaker identification; may need health/status indicators. |
| Voice centroid | Combined embedding representing a player's voice. | Backend detail, but useful as "speaker profile trained" status. |
| Provenance | Where a voice sample came from: imported, session enhancement, or inferred. | Useful in voice-sample management and cleanup explanations. |
| Orphan directory | Folder left behind after a campaign/session/player is removed from its index. Cleanup actions can delete these. | Deletion UX should be clear about soft removal vs cleanup. |

## Campaign Data

### Persisted Campaign Object

The `Campaign` object is stored at:

`<data_root>/campaigns/<campaign_slug>/campaign_data.yaml`

Fields:

| Field | Type | Required | Default | Notes for UI |
| --- | --- | --- | --- | --- |
| `slug` | non-blank string | Yes | None | Stable identifier; generated from name during creation. The loader rejects slug mismatches between folder and file. |
| `name` | non-blank string | Yes | None | User-facing campaign name. Creation validates this is present and that the generated slug is not already used. |
| `description` | string | No | `""` | Optional long-form campaign description. Present in model and summary, but not exposed in current TUI. |
| `default_gm` | string | No in model, required by creation dialog | `""` | Displayed as `GM` in the campaign list. Creation dialog requires a value. |
| `system` | string | No in model, required by creation dialog | `""` | Game system such as `D&D 5e` or `Blades`. Displayed in campaign list. Creation dialog requires a value. |
| `state` | enum: `active`, `archived` | No | `active` | Drives active/archived/all filters. No archive/restore action is currently exposed in the TUI. |
| `glossary` | tuple of `GlossaryEntry` | No | empty tuple | Used by summary generation to improve proper nouns and campaign-specific terms. |

### Glossary Entry

Glossary entries are embedded on the campaign object.

| Field | Type | Required | Default | Notes for UI |
| --- | --- | --- | --- | --- |
| `term` | non-blank string | Yes | None | The proper noun or campaign-specific term. |
| `description` | string | Yes by model construction | None | May be empty. Used as context when generating summaries. |

Suggested glossary UI needs:

- Add term.
- Edit term and description.
- Delete term.
- Search/filter terms for large campaigns.
- Show that glossary changes affect future summary generation, and existing summaries likely need rerun to reflect changes.

### Campaign Summary Read Model

`CampaignSummary` is computed for list views and is not persisted. It is assembled by loading:

- The campaign set index.
- Each campaign object.
- Each campaign's session set.
- Each campaign's player set.

Fields:

| Field | Source | Notes for UI |
| --- | --- | --- |
| `slug` | Campaign | Hidden identifier. |
| `name` | Campaign set entry | Preserves campaign-set order. |
| `state` | Campaign | Used by filters. |
| `description` | Campaign | Available for richer list/detail previews. |
| `default_gm` | Campaign | Current list column: `GM`. |
| `system` | Campaign | Current list column: `SYSTEM`. |
| `first_session_date` | Min date from session set | `None` when there are no sessions; current UI displays a dash placeholder. |
| `last_session_date` | Max date from session set | `None` when there are no sessions; current UI displays a dash placeholder. |
| `session_count` | Count of session set entries | Current list column: `SESSIONS`. |
| `player_count` | Count of player set entries | Current list column: `PLAYERS`. |

### Campaign Set Index

Global campaign index stored at:

`<data_root>/campaigns.yaml`

Fields:

| Field | Type | Notes for UI |
| --- | --- | --- |
| `campaigns` | tuple of `CampaignName` | List order is preserved in summaries. |

`CampaignName` fields:

| Field | Type | Notes for UI |
| --- | --- | --- |
| `slug` | non-blank string | Links index entry to campaign folder. |
| `name` | non-blank string | Lightweight display name. Comment says this is intentionally separate so display name can be updated independently of full campaign data. |

## Session Data In A Campaign

Sessions are child records under a campaign.

Session index path:

`<data_root>/campaigns/<campaign_slug>/sessions.yaml`

Full session path:

`<data_root>/campaigns/<campaign_slug>/sessions/<session_slug>/session.yaml`

### Session Set Entry

| Field | Type | Required | Notes for UI |
| --- | --- | --- | --- |
| `slug` | non-blank string | Yes | Session identifier and folder name. |
| `name` | non-blank string | Yes | Display name. |
| `session_date` | date | Yes | Stable list-level fact used to compute first/last session dates without opening every session file. |

### Full Session

| Field | Type | Required | Notes for UI |
| --- | --- | --- | --- |
| `session_date` | date | Yes | Primary timeline/sorting field. |
| `name` | non-blank string | Yes | Session title. |
| `slug` | non-blank string | Yes | Hidden identifier; loader rejects folder/file slug mismatch. |
| `audio_filename` | string | Yes | Filename of imported raw audio relative to the session directory. Extension is preserved from the source file. |
| `attendees` | map of player slug to tuple of roles | Yes | Session attendee roster. A player can have multiple roles. Speaker processing fails if any attendee slug is not in the campaign player set. |

### Session Artifacts

Derived files live in the session directory.

| Artifact | File | Produced by | Notes for UI |
| --- | --- | --- | --- |
| Cleaned audio | app setting value, relative to session directory | `clean_audio` | Deleted when audio/attendees change or session processing reruns. |
| Discourse | `discourse.json` | `process_session` after speaker identification | Structured transcript data for review/correction. |
| Transcript | `transcript.md` | `process_session` | Human-readable transcript markdown. |
| Summary | `summary.md` | `generate_summary` | Markdown summary generated with the campaign glossary. |

### Discourse And Transcript Detail

`Discourse` contains a non-empty tuple of utterances. Each utterance includes:

| Field | Type | Notes for UI |
| --- | --- | --- |
| `text` | non-blank string | Segment transcript text. |
| `speaker` | non-blank string | Initially from diarization, then replaced by identified player name when confidence passes threshold. Can be an unassigned speaker sentinel. |
| `words` | non-empty tuple of words | Word-level timing and speaker labels. |
| `embedding` | embedding | Present after speaker identification. |
| `similarity_margin` | float | Confidence-like margin used to decide whether to assign or leave unassigned. |
| `start` | computed from words | First word start time. |
| `end` | computed from words | Last word end time. |

Each word includes text, start time, end time, and speaker.

## Player Data In A Campaign

Player index path:

`<data_root>/campaigns/<campaign_slug>/players/players.yaml`

Full player path:

`<data_root>/campaigns/<campaign_slug>/players/<player_slug>/player.yaml`

### Player Set Entry

| Field | Type | Notes for UI |
| --- | --- | --- |
| `slug` | non-blank string | Links index entry to player folder and session attendees. |
| `name` | non-blank string | Player/speaker display name. |

### Full Player

| Field | Type | Notes for UI |
| --- | --- | --- |
| `slug` | non-blank string | Hidden identifier. |
| `name` | non-blank string | Display name used in identified transcript speakers. |
| `voice_samples` | tuple of `VoiceSample` | Audio evidence for speaker identification. |
| `centroid` | embedding | Aggregate voice embedding. |

### Voice Sample

| Field | Type | Notes for UI |
| --- | --- | --- |
| `filepath` | path | Relative path under the player directory. |
| `embedding` | embedding | Backend matching data. |
| `provenance_type` | enum | `import`, `session_enhancement`, or `inferred`. |
| `source` | string | Import directory path or source session slug. |
| `index` | int | Source-local ordering/index. |

## Campaign Actions

### Implemented In Current TUI

| Action | Where | Behavior | UX notes |
| --- | --- | --- | --- |
| View campaign list | `CampaignsScreen` | Displays campaign name, system, GM, first session, last session, session count, and player count. | Current layout is table-first and keyboard-oriented. |
| Filter campaigns | `CampaignsScreen` | Toggle `active`, `archived`, or `all`. Counts are shown per filter. | Search resets when changing filters. |
| Search campaigns | `CampaignsScreen` | Filters by case-insensitive substring match on campaign name. | Current placeholder is `/search campaigns...`; only name is searched. |
| Highlight campaign | `CampaignsScreen` | Updates footer with highlighted campaign name. | Footer is hidden when no campaign is highlighted. |
| Select campaign | `CampaignsScreen` | Currently calls `_open_campaign`, which only notifies `Selected <name>`. | Detail navigation is still future work. |
| Create campaign | `NoCampaignsScreen`, `NewCampaignDialog`, model store | Requires campaign name, system, and default GM. Generates slug, rejects slug collision, creates campaign data, empty session set, empty player set, then appends to global campaign set. | Success should land in campaign list or new campaign detail. Validation errors are inline. |
| Import campaign | `NoCampaignsScreen`, `CampaignsScreen` | Currently only shows `Import campaign` notification. | UI exists as a command, backend import workflow is not present in inspected code. |
| Help | home/list screens | Shows keybindings and notes that campaign workflows are coming next. | Help content will need expansion as campaign detail actions are added. |

### Supported By Model/IO, Not Yet Exposed In TUI

| Action | Backend support | Behavior | UX notes |
| --- | --- | --- | --- |
| Load campaign detail | `load_campaign` | Opens full campaign data by slug and validates slug consistency. | Use for detail screen load. |
| Save campaign detail | `save_campaign` | Writes full campaign data. | Needed for editing name, description, GM, system, state, glossary. If renaming affects slug, extra work is required; existing save does not move folders. |
| Delete campaign from index | `delete_campaign` | Removes campaign entry from global campaign set. The campaign directory remains until cleanup. | This is a soft removal from the app index, not immediate file deletion. Confirmation copy should be precise. |
| Cleanup orphan campaign folders | `cleanup_orphan_campaign_dirs` | Deletes campaign directories not present in the campaign set. | Destructive cleanup action; likely admin/settings or advanced recovery UX. |
| Load/save session | `load_session`, `save_session` | Reads/writes full session file. | Needed for session detail/editor. |
| Delete session from index | `delete_session` | Removes session entry from session set. Session directory remains until cleanup. | Same soft-delete pattern as campaigns. |
| Cleanup orphan session folders | `cleanup_orphan_session_dirs` | Deletes session directories not present in the session set. | Destructive cleanup action. |
| Load/save player | `load_player`, `save_player` | Reads/writes full player file. | Needed for cast/speaker profile editor. |
| Delete player from index | `delete_player` | Removes player entry from player set. Player directory remains until cleanup. | Can create orphan attendee references in sessions if not handled by UI. |
| Cleanup orphan player folders | `cleanup_orphan_player_dirs` | Deletes player directories not present in the player set. | Destructive cleanup action. |
| Save/load summary | `save_summary`, `load_summary` | Summary markdown is stored literally. | Summary viewer/editor can preserve markdown. |
| Save/load discourse | `save_discourse`, `load_discourse` | Structured transcript data stored as JSON. | Transcript correction UI can work at utterance level. |

### Campaign Detail Actions To Design For

These actions are implied by model support and processing workflows, even if not all are wired into the TUI.

#### Campaign Metadata

- Open campaign.
- Edit campaign name.
- Edit description.
- Edit game system.
- Edit default GM.
- Archive campaign.
- Restore archived campaign.
- Remove campaign from index.
- Cleanup removed/orphaned campaign files.

Design cautions:

- Archive is distinct from delete/remove. `state` exists for active/archived filtering.
- Delete currently means "remove from index"; files remain.
- Slug changes are not currently handled by a rename helper. Renaming display name is straightforward; changing slug/folder identity is not.

#### Glossary

- Add glossary entry.
- Edit glossary term.
- Edit glossary description.
- Delete glossary entry.
- Search/filter glossary.
- Regenerate affected summaries after glossary changes.

Design cautions:

- Glossary improves generated summaries. It is not automatically applied to already-written summary files unless summary generation is rerun.
- Empty descriptions are allowed.

#### Sessions

- Add/import a session with date, name, raw audio file, and attendees.
- Edit session date/name.
- Replace session audio.
- Edit attendees and roles.
- Remove session from index.
- Cleanup removed/orphaned session files.
- Process session.
- Rerun session processing.
- Rerun summary only.
- View transcript.
- View summary.
- View structured speaker/utterance review.

Design cautions:

- A full session requires `audio_filename`; session creation needs an audio import step or a staged draft state outside the current model.
- Speaker identification requires at least two attendees and fails if an attendee slug is not in the campaign player set.
- Raw audio is preserved when downstream artifacts are invalidated.
- Replacing audio, editing attendees, or rerunning processing deletes stale cleaned audio, discourse, transcript, summary, and retracts voice samples learned from that session.
- Rerunning summary only deletes the summary and preserves transcript, discourse, cleaned audio, and raw audio.

#### Session Processing

Processing pipeline:

1. Invalidate stale derived artifacts.
2. Load campaign, session, player set, and attendees.
3. Clean audio.
4. Transcribe and diarize.
5. Identify speakers against attendee voice profiles.
6. Save discourse JSON.
7. Save transcript markdown.
8. Generate summary markdown using the campaign glossary.

Progress phases surfaced by code include:

- `cleaning audio`
- `transcribing and diarizing`
- `transcribing and diarizing with elevenlabs`
- `building transcript`
- `identifying speakers`
- `generating summary`

Design states to consider:

- Not processed.
- Processing queued/running.
- Processing failed with recoverable error.
- Transcript ready.
- Summary ready.
- Summary stale.
- Transcript/discourse stale due to destructive input changes.
- Speaker assignment needs review or has unassigned speakers.

#### Players And Speaker Profiles

- Add player.
- Edit player name.
- Delete player from index.
- Add/import voice clips for a player.
- Optionally clean imported voice clips.
- Recompute player voice centroid.
- Remove outlier voice samples.
- Enhance voice profiles from processed sessions.
- Review voice sample provenance.

Design cautions:

- Attendees reference player slugs. Deleting a player can leave sessions with attendee references that fail processing.
- Imported voice clips are replaced per source directory: adding clips from the same source retracts previous imported samples from that source.
- Session enhancement can add voice samples from confident utterances after a session is processed.
- Destructive session changes retract voice samples that came from that session's enhancement.

## Current Campaign List Columns

| Column | Data | Empty value |
| --- | --- | --- |
| `Campaign` | `CampaignSummary.name` | Not applicable |
| `SYSTEM` | `CampaignSummary.system` | Dash placeholder |
| `GM` | `CampaignSummary.default_gm` | Dash placeholder |
| `FIRST SESSION` | `CampaignSummary.first_session_date` | Dash placeholder |
| `LAST SESSION` | `CampaignSummary.last_session_date` | Dash placeholder |
| `SESSIONS` | `CampaignSummary.session_count` | `0` |
| `PLAYERS` | `CampaignSummary.player_count` | `0` |

## Empty And Error States

States visible or implied by code:

- No campaigns exist.
- Campaign list has campaigns, but active filter returns no campaigns.
- Search returns no campaigns.
- Campaign listed in index has missing/corrupt detail files; summary loading fails fast.
- New campaign name is empty.
- New campaign slug already exists.
- New campaign system is empty.
- New campaign default GM is empty.
- Session processing fails because attendee slug is missing from player set.
- Session processing fails because raw audio file is missing.
- Session processing fails because audio has no speech.
- Speaker identification fails with fewer than two attendees.

## Designer Questions

- Should campaign detail open into overview, sessions, glossary, players, or last active workflow?
- Should archive be the default non-destructive removal action instead of delete?
- Should "delete" be exposed while it only removes index entries and leaves files behind?
- Should cleanup of orphan folders be user-facing, hidden maintenance, or settings/admin only?
- Should glossary edits mark summaries as stale, or should users manually choose summary reruns?
- How should the UI represent transcript/speaker confidence and unassigned speakers?
- Should players be called players, speakers, cast, participants, or a combination depending on context?
- Do sessions need a draft state before audio is available, or is audio required at creation time?
- Should campaign search include system, GM, and description, or remain name-only?
