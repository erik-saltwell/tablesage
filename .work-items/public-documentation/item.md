---
name: "Public documentation"
status: implementing
---

# Public documentation

Create and publish a GM-facing documentation experience for TableSage RPG. The
current direction is recorded in [intent.md](intent.md).
The working table of contents is saved in [toc-plan.md](toc-plan.md).
The README outline is saved in [readme-toc-plan.md](readme-toc-plan.md).
Screenshot deployment details and verification are recorded in [progress.md](progress.md).

## Resume note

Created the public documentation directory structure at the user's request:
`docs/getting-started/`, `docs/guides/`, and `docs/reference/`, plus screenshot
folders under `docs/images/` for `getting-started`, `campaigns`,
`session-processing`, `review-and-export`, and `session-preparation`.
Empty directories contain `.gitkeep` files so Git can retain them.

The outline is saved in toc-plan.md; page boundaries and first-release scope
remain open. The `.for-docs/` deployment now contains fictional sample campaigns
and three completed Iron Pact sessions, verified through the Textual MCP using
the local `.for-docs/preview.py` launcher. See progress.md for launch instructions.
Public pages, selected screenshots, MkDocs configuration, and publication remain
to be implemented. First drafts of `docs/getting-started/installation.md` and
`docs/getting-started/first-session.md` were written and then deleted at the
user's request on 2026-09-15 to restart the drafting from a clean page.
`docs/getting-started/installation.md` has since been rewritten from scratch
against verified application behavior; it is the only public page that exists.
The verified behavior and the review that prompted the restart are recorded in
progress.md. Continue from the outline when drafting the rest, starting with the
first-session walkthrough.
[ui-behavior-findings.md](ui-behavior-findings.md) lists application behavior a
game master cannot discover from the UI, gathered by reading every screen; it is
the source list for what the guides must explain.

The initial `docs/concepts/` drafts were discarded as unworkable. Start the
concept documentation again from a clean page, organized around three subjects:

- **Players, voice samples, centroids, and roles.** A role is the identity or
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

The quality rubric is still missing; the user explicitly requested the outline
and directory setup first. The separate repository documentation cleanup was
archived locally and does not start or complete this site project.
