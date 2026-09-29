---
name: "Public documentation"
status: implementing
---

# Public documentation

Create and publish a GM-facing documentation experience for TableSage RPG. The
current direction is recorded in [intent.md](intent.md).
The planning notes once referenced here (`toc-plan.md`, `readme-toc-plan.md`,
`progress.md`, `ui-behavior-findings.md`) were never committed and are not
retained; the intent's information architecture and the current `docs/` tree are
the record. Screenshot capture tooling and its instructions live in the
git-ignored `.for-docs/session-processing/README.md`, and `scripts/README.md`
describes the fixture seeder.

## Resume note

Created the public documentation directory structure at the user's request:
`docs/getting-started/`, `docs/guides/`, and `docs/reference/`, plus screenshot
folders under `docs/images/` for `getting-started`, `campaigns`,
`session-processing`, `review-and-export`, and `session-preparation`.
Empty directories contain `.gitkeep` files so Git can retain them.

Page boundaries and first-release scope remain open. The `.for-docs/` deployment now contains fictional sample campaigns
and three completed Iron Pact sessions, verified through the Textual MCP using
the local `.for-docs/preview.py` launcher.
Public pages, selected screenshots, MkDocs configuration, and publication remain
to be implemented. First drafts of `docs/getting-started/installation.md` and
`docs/getting-started/first-session.md` were written and then deleted at the
user's request on 2026-09-15 to restart the drafting from a clean page.
`docs/getting-started/installation.md` has since been rewritten from scratch
against verified application behavior. Continue from the intent's outline when
drafting the rest, starting with the first-session walkthrough.

The initial `docs/concepts/` drafts were discarded as unworkable. Start the
concept documentation again from a clean page, organized around three subjects:

- **Players, voice samples, voice prints, and roles.** A role is the identity or
  function a player takes in a session. It is often a player character, but
  also encompasses the game master and other non-character functions.
- **Sessions, processing, and session artifacts.** Explain the Session concept
  together with the processing pipeline and the artifacts it produces.
- **Campaigns and glossaries.** Explain the Campaign concept and its owned,
  campaign-specific glossary.

The new concept front door is `docs/concepts/index.md`. It links to empty
`players.md`, `sessions.md`, and `campaigns.md` placeholders, which are ready
for fresh drafts.

The concept documentation is now drafted: `docs/concepts/players.md`,
`docs/concepts/sessions.md`, `docs/concepts/campaigns.md`, and
`docs/concepts/delete-and-clean.md`. Together they define workspace-wide
Players, session-scoped Roles, reviewed Session artifacts, Campaigns with their
campaign-specific Glossaries, and the deliberate delete-then-clean-up lifecycle
for directory-backed objects. The next documentation work is review and
refinement of these concept pages or continuation from the broader
public-documentation outline.

A session-processing concept cluster now exists (2026-09-27):
`docs/concepts/session-processing.md` is its front page, explaining processing
and its two workflows, and it leads to
`session-processing-returning-players.md` and
`session-processing-new-players.md`, which walk through each step, why it
exists, and how it relates to the others. They are linked from the concepts
index and `sessions.md`. Their screenshots in `docs/images/session-processing/`
were captured through the Textual MCP from a scratch copy of the `.for-docs`
fixture. Provider calls were stubbed with authored data, and
the SVG captures were rendered with headless Chrome because the MCP's PNG
converter drops the strikethrough on skipped steps. The tooling to
recapture them—staging script, stubbed launcher, authored dialogue, render
scripts, and the step-by-step capture sequence—lives in the git-ignored
`.for-docs/session-processing/` (see its README).

The quality rubric is still missing; the user explicitly requested the outline
and directory setup first. The separate repository documentation cleanup was
archived locally and does not start or complete this site project.

## Current state (2026-09-29)

Public pages that exist: `docs/getting-started/installation.md`,
`docs/guides/` (`index`, `settings`, `review-and-export`, `prepare-the-next-session`,
`manage-players-and-voice-samples`), `docs/reference/privacy.md`, and the concepts
pages (`index`, `players`, `sessions`, `campaigns`, `delete-and-clean`, and the
three session-processing pages). The repository `README.md` is a short front door
that links into them. On 2026-09-29 the pages were reconciled with the code after
the Process Session coordinator rewrite (Continue/Restart keys, hidden new-player
steps, per-row failures, model locations, Settings entry points), the guides for
previously undocumented features were written from the code, and the
session-processing and Session Detail screenshots were recaptured from the
current UI with the `.for-docs/session-processing/` tooling.

Known gaps: there is no `docs/index.md` or MkDocs configuration yet; the
first-session walkthrough and the "start a campaign" task guide from the intent are
not written; the review-screen screenshots (glossary, spellcheck, name corrections,
new-speaker review) were compared against the current UI and left unchanged, but
`review-transcript*.png` were not re-verified; and Session Detail's "Last
Transcribed" label renders truncated ("Last") in screenshots, an application UI
defect rather than a documentation one.
