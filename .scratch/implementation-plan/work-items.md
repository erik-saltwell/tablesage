# Implementation plan — work items

Tracks status for each phase of `.documentation/tablesage_implementation_plan.md`
(the campaign/player re-architecture). This table is the source of truth for
status; the plan doc itself holds the narrative/scope for each phase.

Status is one of:

- **Unstarted** — no dedicated design work done yet.
- **Designed** — has a dedicated design doc beyond plan-bullet detail.
- **Implemented** — built and merged.

"Design doc" is populated once a phase reaches Designed or later. "Commit" is
populated once a phase reaches Implemented — the commit that completed it.

| ID | Name | Status | Design doc | Commit |
| --- | --- | --- | --- | --- |
| 0 | Data model & migrations | Implemented | — | `b73ed3c` |
| 1 | Filesystem + application layer | Implemented | — | `b73ed3c` |
| 2 | Landing screen rework | Implemented | — | `b73ed3c` |
| 3 | Campaigns List screen | Implemented | — | `bc7323c` |
| 4 | Campaign Detail screen | Implemented | — | `511131b` |
| 5 | Players List screen | Implemented | — | `9c6270d` |
| 6 | Player Detail screen | Implemented | [`.documentation/player_detail_screen.md`](../../.documentation/player_detail_screen.md) | `8741da2` |
| 7 | Tests | Implemented | — | `8741da2` |
| 8 | Session Detail screen | Implemented | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | `0f4284a` |
| 9 | Import player from file system | Implemented | [`.documentation/import_player_from_filesystem.md`](../../.documentation/import_player_from_filesystem.md) | `6842595` |
| 11 | Process session | Implemented | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | `15f52b8` |
| 12 | Generate summary | Designed | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | — |
| 13 | Player Detail cleanup (unused samples) | Implemented | [`.documentation/player_detail_screen.md`](../../.documentation/player_detail_screen.md) | `36d6d05` |
| 14 | Import players from audio file | Designed | [`.documentation/import_players_from_audio_file.md`](../../.documentation/import_players_from_audio_file.md) | — |
| 15 | Enhance players from session | Designed | [`.documentation/enhance_players_from_session.md`](../../.documentation/enhance_players_from_session.md) | — |
| 16 | Punctuated transcript as its own artifact | Unstarted | — | — |
| 17 | Export artifact command | Unstarted | — | — |
| 18 | Move to textual-fspicker for file/directory picking | Implemented | — | `c741008` |
