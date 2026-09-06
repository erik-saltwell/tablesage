# Pipeline work items

New work items for the transcript/Ledger/Summary generation pipeline, raised 2026-08-31 following
the Clean Transcript / Generate (`G`) rework in `session_detail_screen.md`.

| # | Item | Triage state |
| --- | --- | --- |
| 01 | [Re-add pre-review backchannel removal, batched](01-pre-review-backchannel-removal-batched.md) | `complete` — design: [01-design.md](01-design.md), commit `bc8fcf5` |
| 02 | [New "Question" Ledger event type](02-question-ledger-event.md) | `complete` — design: [02-design.md](02-design.md), commit `6150f88` |
| 03 | [Glossary extraction](03-glossary-extraction.md) | `complete` — design: [03-design.md](03-design.md), commit `9c49dfa` |
| 04 | [Collapse Role Transcript / Ledger / Summary generation into one action](04-single-action-generate.md) | `complete` — superseded by the Session Detail bindings-simplification overhaul, 2026-09-02 |
| 05 | [Finish Ledger generation](05-finish-ledger-generation.md) | `complete` — closed without implementation: no remaining gap was specified |
| 06 | [Finish Summary generation](06-finish-summary-generation.md) | `complete` — commit `678fd8d` |
| 07 | [Spelling-correction suggestions as Manual Review's first phase](07-correct-spelling-post-punctuation.md) | `complete` — design: same doc, commit `f7be8f1` |

01 shipped 2026-09-01 after a design brainstorm (2026-08-31, see [01-design.md](01-design.md)).
02 and 03 shipped 2026-09-01 after design brainstorms (see [02-design.md](02-design.md) and
[03-design.md](03-design.md)). 06's scope was resolved 2026-09-02 (Summary now sources the Ledger
instead of the role transcript) and implemented and committed the same day. 04 shipped 2026-09-02
as part of a broader Session Detail bindings-simplification overhaul that also repurposed Clean
Transcript into a full-wipe Clean Session, merged Import/Transcribe into one binding, and added a
permanent Errors table -- see `.documentation/session_detail_screen.md`. 05 was closed 2026-09-05
without implementation because no remaining gap had been specified.
