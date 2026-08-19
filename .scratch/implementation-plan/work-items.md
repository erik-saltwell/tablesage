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
| 8 | Session Detail screen | Designed | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | — |
| 9 | Import player from file system | Unstarted | — | — |
| 10 | Import player from audio file | Unstarted | — | — |
| 11 | Process session | Designed | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | — |
| 12 | Generate summary | Designed | [`.documentation/session_detail_screen.md`](../../.documentation/session_detail_screen.md) | — |
| 13 | Player Detail cleanup (unused samples) | Unstarted | — | — |
