# Pipeline work items

New work items for the transcript/Ledger/Summary generation pipeline, raised 2026-08-31 following
the Clean Transcript / Generate (`G`) rework in `session_detail_screen.md`.

| # | Item | Triage state |
| --- | --- | --- |
| 01 | [Re-add pre-review backchannel removal, batched](01-pre-review-backchannel-removal-batched.md) | `complete` — design: [01-design.md](01-design.md), commit `bc8fcf5` |
| 02 | [New "Question" Ledger event type](02-question-ledger-event.md) | `ready-for-agent` — design: [02-design.md](02-design.md) |
| 03 | [Glossary extraction](03-glossary-extraction.md) | `complete` — design: [03-design.md](03-design.md), commit `9c49dfa` |
| 04 | [Collapse Role Transcript / Ledger / Summary generation into one action](04-single-action-generate.md) | `ready-for-agent` |
| 05 | [Finish Ledger generation](05-finish-ledger-generation.md) | `needs-info` |
| 06 | [Finish Summary generation](06-finish-summary-generation.md) | `needs-info` |

01 shipped 2026-09-01 after a design brainstorm (2026-08-31, see [01-design.md](01-design.md)).
03 shipped 2026-09-01 after a design brainstorm (see [03-design.md](03-design.md)). Of the four
remaining items, 05/06 are still `needs-info`: the user needs to name the actual remaining gap
rather than the terse one-liner they were raised with.
