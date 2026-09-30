---
name: "Documentation guides"
status: complete
---

# Documentation guides

Replace the sparse Guides navigation with ten practical guides for common GM activities, as requested on 2026-09-30. This is a separate deliverable from the broader [public documentation](../public-documentation/item.md) site project.

The agreed scope is campaign setup, processing with new players, processing with returning players, generating/exporting outputs, next-session preparation, correcting processed sessions, campaign glossaries, voice recognition, workspace transfer, and settings. Retain existing guide paths where practical so incoming links keep working.

See [plan.md](plan.md) for implementation and verification. The user explicitly requested implementation; no rubric has been defined and quality dimensions remain unassessed.

## Completion (2026-09-30)

All ten guides are published in the repository's [Guides index](../../docs/guides/index.md). Added six pages and revised the existing four, retaining their paths and existing incoming section links. The core guides cover setup, both processing branches, generation/export, and preparation; supporting guides cover correction/recovery, glossary maintenance, voice recognition, workspace transfer, and settings. Updated README navigation and Players reference links, and linked this deliverable from the broader public-documentation record.

Checked instructions against the current screen and application code, including date-based attendance inheritance, new-player voice seeding, review controls, generation/export visibility, stale-output handling, error locations, scene-breakdown prerequisites, and exact-name requirements for campaign imports. Verified 279 local links, anchors, and image references across 32 public Markdown pages (excluding editor history), all ten distinct guide-index entries, guide titles/newlines/whitespace, and a targeted `git diff --check`; all passed. A broad whitespace check also reported pre-existing whitespace in unrelated concept pages, which was left unchanged. No unit tests or application changes were made. Existing screenshots were reused; no fresh browser verification or site build was performed because this request concerns Markdown guides and no MkDocs configuration exists yet.

The requested guide deliverable is complete. Further editorial revision can reopen it; site configuration and publication remain in the broader public-documentation item. Rubric dimensions remain unassessed.

## Editorial revision (2026-09-30)

Reopened briefly for review fixes, then completed again:

- Standardized capitalization: **Campaign** and **Session** are capitalized when they name the TableSage record (including guide titles such as "Start a Campaign"), and lowercase when used as modifiers (campaign glossary, campaign history, session outputs, session artifacts). UI labels are unchanged.
- Made the index link title match the "Prepare the next Session" page heading, including one title-style cross-link.
- Changed Player Detail's **M** description to match its **Edit Metadata** footer label (`player_detail.py`).
- The preparation guide now refers to "an LLM" instead of the High tier, per `.agent_context.md`.
- Clarified how to choose a processing guide in the index, and the restart sentence in the correction guide.
- Settings: gave it a task-oriented opening, removed a double space, and cut the duplicate explanation of deleting shell-environment keys.
- Both processing guides now describe exactly when Enter plays rather than edits in Review Transcript, verified against `speaker_review.py` `on_data_table_row_selected`, which matches the screen reference.

Verification: all ten guides are linked from `docs/guides/index.md`. 279 local links and anchors across `docs/` and `README.md` resolve, and `git diff --check` on `docs/guides` is clean. Structural decisions made by the user and applied the same day:

- `review-and-export.md`: removed the "Clean a Session" and "Extract glossary terms on demand" pointer sections (nothing linked to their anchors). Moved the failure paragraph out of "Read the Artifacts panel" into a closing "If something fails" section with a "Related tasks" line.
- `manage-players-and-voice-samples.md`: replaced both key tables with keys described in the steps and a link to the Players screen reference. The guide now runs: choose a source → remove incorrect samples → add from a Session → import from a folder → recompute/clean up → move → check. The `#add-samples-from-a-session` and `#move-players-between-workspaces` anchors are kept.
- Processing guides: both keep their own sections, but "Check new terms and spelling" and the Review Transcript steps are now word-for-word identical. Only each guide's introductory sentence, screenshot, and pause note differ. Edit both together.

Re-verified: 280 local links and anchors resolve, and `git diff --check` on `docs/guides` is clean. Rubric dimensions remain unassessed.
