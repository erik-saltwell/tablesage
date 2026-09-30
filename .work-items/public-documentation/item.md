---
name: "Public documentation"
status: implementing
---

# Public documentation

Create and publish a GM-facing documentation experience for TableSage RPG. The current direction is recorded in [intent.md](intent.md). The planning notes once referenced here (`toc-plan.md`, `readme-toc-plan.md`, `progress.md`, `ui-behavior-findings.md`) were never committed and are not retained; the intent's information architecture and the current `docs/` tree are the record. Screenshot capture tooling and its instructions live in the git-ignored `.for-docs/session-processing/README.md`, and `scripts/README.md` describes the fixture seeder.

## Resume note

Created the public documentation directory structure at the user's request: `docs/getting-started/`, `docs/guides/`, and `docs/reference/`, plus screenshot folders under `docs/images/` for `getting-started`, `campaigns`, `session-processing`, `review-and-export`, and `session-preparation`. Empty directories contain `.gitkeep` files so Git can retain them.

Page boundaries and first-release scope remain open. The `.for-docs/` deployment now contains fictional sample campaigns and three completed Iron Pact sessions, verified through the Textual MCP using the local `.for-docs/preview.py` launcher. Public pages, selected screenshots, MkDocs configuration, and publication remain to be implemented. First drafts of `docs/getting-started/installation.md` and `docs/getting-started/first-session.md` were written and then deleted at the user's request on 2026-09-15 to restart the drafting from a clean page. `docs/getting-started/installation.md` has since been rewritten from scratch against verified application behavior. Continue from the intent's outline when drafting the rest, starting with the first-session walkthrough.

The initial `docs/concepts/` drafts were discarded as unworkable. Start the concept documentation again from a clean page, organized around three subjects:

- **Players, voice samples, voice prints, and roles.** A role is the identity or function a player takes in a session. It is often a player character, but also encompasses the game master and other non-character functions.
- **Sessions, processing, and session artifacts.** Explain the Session concept together with the processing pipeline and the artifacts it produces.
- **Campaigns and glossaries.** Explain the Campaign concept and its owned, campaign-specific glossary.

The new concept front door is `docs/concepts/index.md`. It links to empty `players.md`, `sessions.md`, and `campaigns.md` placeholders, which are ready for fresh drafts.

The concept documentation is now drafted: `docs/concepts/players.md`, `docs/concepts/sessions.md`, `docs/concepts/campaigns.md`, and `docs/concepts/delete-and-clean.md`. Together they define workspace-wide Players, session-scoped Roles, reviewed Session artifacts, Campaigns with their campaign-specific Glossaries, and the deliberate delete-then-clean-up lifecycle for directory-backed objects. The next documentation work is review and refinement of these concept pages or continuation from the broader public-documentation outline.

A session-processing concept cluster now exists (2026-09-27): `docs/concepts/session-processing.md` is its front page, explaining processing and its two workflows, and it leads to `session-processing-returning-players.md` and `session-processing-new-players.md`, which walk through each step, why it exists, and how it relates to the others. They are linked from the concepts index and `sessions.md`. Their screenshots in `docs/images/session-processing/` were captured through the Textual MCP from a scratch copy of the `.for-docs` fixture. Provider calls were stubbed with authored data, and the SVG captures were rendered with headless Chrome because the MCP's PNG converter drops the strikethrough on skipped steps. The tooling to recapture them—staging script, stubbed launcher, authored dialogue, render scripts, and the step-by-step capture sequence—lives in the git-ignored `.for-docs/session-processing/` (see its README).

The quality rubric is still missing; the user explicitly requested the outline and directory setup first. The separate repository documentation cleanup was archived locally and does not start or complete this site project.

## Current state (2026-09-29)

Public pages that exist: `docs/getting-started/installation.md`, `docs/guides/` (`index`, `settings`, `review-and-export`, `prepare-the-next-session`, `manage-players-and-voice-samples`), `docs/reference/privacy.md`, and the concepts pages (`index`, `players`, `sessions`, `campaigns`, `delete-and-clean`, and the three session-processing pages). The repository `README.md` is a short front door that links into them. On 2026-09-29 the pages were reconciled with the code after the Process Session coordinator rewrite (Continue/Restart keys, hidden new-player steps, per-row failures, model locations, Settings entry points), the guides for previously undocumented features were written from the code, and the session-processing and Session Detail screenshots were recaptured from the current UI with the `.for-docs/session-processing/` tooling.

Added `docs/concepts/workspaces.md` as the first concept-index link. It explains how a workspace relates to an installation, the verified database/settings/log paths, the Player and Campaign directories, and workspace-wide Players versus Session attendance and Roles. Checked the paths against the application and model code and verified the new page's local links. This documentation addition was explicitly requested; the missing numerical rubric remains unassessed.

The workspace page now ends with a note on API keys shared per user account, their Settings entry point, and the effect of changing shared credentials across workspaces. Verified against `Configuration` and linked to the existing key storage guidance.

Revised the two Session processing workflow concept pages to explain each stage's purpose, evidence, value, and dependencies. Removed screenshots, keyboard bindings, screen/pane descriptions, buttons, and navigation directions. The new-player page explains conversational identity evidence and human review before voice-print seeding; the returning-player page explains transcription, identification, vocabulary correction, review, and artifact generation. Verified local links and section anchors and checked both pages for remaining UI instructions. The existing screenshot files remain available for task guides.

Removed fixed-width prose wrapping from the documentation and internal Markdown records, preserving paragraph boundaries and structural line breaks. The user's preference for unwrapped source paragraphs is recorded in `.agent_context.md`. Verified equivalent rendered Markdown before and after removing soft line breaks.

Concept pages now refer to an LLM without naming model tiers. This conceptual-documentation preference is recorded in `.agent_context.md`; settings guides retain the tier details needed for configuration. Checked all concept pages for remaining tier references.

Added a complete, ordered overview at the top of the new-player processing page, covering all 14 conceptual steps and identifying voice print improvement as optional.

The returning-player page now uses the same detailed overview, excluding the four new-player steps. Its ten step sections match the overview order, including optional voice print improvement. Updated the new-player page's cross-links to the corresponding step sections and verified section anchors.

Both processing overview lists now begin each description with “The user” or “The system,” matching the manual/automatic classification in `PROCESSING_STEPS`. Shared step descriptions are identical across both pages.

Added a screen reference (2026-09-29) at the user's request: `docs/reference/screens/` with an index (conventions for the footer, the Other actions menu, unavailable versus hidden keys, Esc/F5/Ctrl+Q, shared dialogs, drafts, leaving behavior, and known display issues) and pages for Welcome and Settings, Campaigns, Players, Session Detail, Process Session, the processing review screens, and Previously On and Opportunities. Each page documents every binding, secondary action, gate, and dialog, derived from the screen code. 48 screenshots in `docs/images/screens/` were captured through the Textual MCP from scratch deployments with stubbed provider calls; the tooling and capture sequence are in the git-ignored `.for-docs/screens/` (its README), which reuses `.for-docs/session-processing/`. `stage.py` there was fixed for the `voice_print_embedding` rename. The reference is linked from `docs/guides/index.md` and the README. Local links, anchors, and image paths were checked with a script. The numerical rubric remains undefined, so the pages are unassessed.

Added `docs/reference/screens/ui-patterns.md` (2026-09-30) at the user's request. It covers the shared conventions: the parts of a screen, Esc navigation, the N/E/D list pattern, secondary actions and the `?`/`/` menu (including which five screens have them and which run without confirmation), unavailable versus hidden actions, focus-dependent keys, Ctrl+Q and what it does or doesn't guard, leaving behavior, dialogs, drafts, notifications, and mouse use. The general conventions previously in the screen index moved there. The index now links to it first, and the links that pointed at the moved sections were updated. Links were rechecked with a script.

Added an opening “How to get here” section to all seven screen reference pages (2026-09-30), with concise, explicit directions. Pages covering multiple screens also give each additional screen or processing review its own navigation line. Checked the documented keys against the screen bindings and verified opening headings, one-line formatting, local links, and anchors. The screen index and shared UI-pattern reference remain overview pages.

Added the existing Players list screenshot immediately after the common list-keybindings table in `ui-patterns.md`. Visually checked that it shows a highlighted row and the New Player, Edit Player, and Delete footer actions, and verified the image path.

UI defects seen while capturing, recorded in the reference's known-issues list: the header reads *no campaign loaded* on list and processing screens; Session Detail's *Last Transcribed* label is cut off at *Last*; Campaign detail's `[S] Sessions` / `[G] Glossary` tab labels lose their key hints (probably consumed as Rich markup); Spellcheck's footer shows **D** as *Delete* although it toggles Keep/Remove; the Review Transcript footer truncates *Focus Player* at 140 columns. Also noticed: `docs/guides/review-and-export.md` links to `session-processing.md#how-a-run-behaves`, an anchor that no longer exists, and says Regenerate failures appear in Session Detail's Errors table, but only Clean Session writes there (regeneration failures go to a notification and Process Session's row).

Fixed the first three display issues from the screen reference index (2026-09-30): headers now show the screen section when no named item is loaded, Session Detail allocates enough label width for “Last Transcribed,” and Campaign detail renders `[S]`/`[G]` literally. Removed the entire public known-display-issues section and the obsolete Session Detail truncation note; retained the spellcheck keep/remove explanation without calling out its footer label. Direct headless render checks passed at 140×44 and 80×24, including named-header updates. All 60 existing base-screen, Campaign detail, and Session Detail tests passed; targeted Ruff and ty checks passed. Existing documentation screenshots have not been recaptured for these display changes.

Known gaps: there is no `docs/index.md` or MkDocs configuration yet; the first-session walkthrough and the "start a campaign" task guide from the intent are not written; the review-screen screenshots (glossary, spellcheck, name corrections, new-speaker review) were compared against the current UI and left unchanged, but `review-transcript*.png` were not re-verified; and Session Detail's "Last Transcribed" label renders truncated ("Last") in screenshots, an application UI defect rather than a documentation one.

Fixed the identified issues in `docs/guides/review-and-export.md` (2026-09-30): replaced the two removed processing-anchor links with regeneration guidance and the Process Session controls reference; corrected error reporting for regeneration, glossary extraction, export, campaign-wide regeneration, and Clean Session; and fixed an additional removed glossary anchor. Checked behavior against the coordinator and screen code and verified all 8 local links and anchors. Public documentation remains `implementing`; the numerical rubric remains undefined and unassessed. Guide restructuring is still a recommendation, pending further direction.

The user authorized all ten recommended task guides on 2026-09-30. That deliverable is tracked separately in [Documentation guides](../documentation-guides/item.md). Its guide index is `docs/guides/index.md`; the existing output, preparation, voice-sample, and settings paths are preserved. The broader site project remains `implementing`, including outstanding site configuration and publication work.

## Site-wide review and style pass (2026-09-30)

A full review of the 26 public pages (excluding the git-ignored `docs/.stversions/`) led to the style standard now recorded in `.agent_context.md` under "Documentation style". The user chose each convention. All of `docs/` and the README's documentation links were brought into line with it:

- **Record nouns:** capitalized Campaign, Session, Player, Role, and Glossary when they mean the record. Where "players" means the people at the table (for example "send players an account"), quoted app messages, and modifier phrases ("campaign glossary", "session outputs") were left lowercase.
- **Headings and page titles:** converted about 150 headings to Title Case. Exceptions: "uv" stays lowercase, "Previously On" is a feature name, and "Assign Roles To Players" matches the app's step label.
- **Screen names:** now written in Title Case: Campaign Detail, Player Detail, Players List, Campaigns List, Welcome screen.
- **Link text:** index and "See" links now use exact page or section titles. Links inside sentences keep natural wording.
- **Factual fixes, checked against the code:**
  - Process Session now lists six new-player steps, including Seed Player Voice Samples (`processing_steps.py`).
  - The new-players concept page no longer describes Identify Speakers as a user review; Find More is attributed to Review New Speaker Assignments.
  - The installation page's stale "walkthrough is forthcoming" line now points to Start a Campaign.
  - The Players concept page gives the date-based attendance-copy rule (`entities/sessions.py`).
- **Typos and formatting:** fixed typos, double spaces, trailing whitespace, and extra blank lines in the installation and concept pages, and removed the padded table in `ui-patterns.md`.

Verification: 282 local links and anchors resolve, and `git diff --check` is clean. All noun and link changes were reviewed as listed proposals before being applied. No site build was run, because no MkDocs configuration exists yet.

## Quality review and fixes (2026-09-30)

A qualitative review of all 32 public pages (no rubric exists, so nothing was scored) checked the riskiest claims against the code. Fixes applied at the user's direction:

- **Claims the code contradicted:** Player Introductions are opening character introductions, not "new Players"; the session summary embeds the previous Session's Recap Summary, which the concept pages now explain as the reason prior Sessions must be current; Import Audio also needs the Low model's provider key; Previously On and Opportunities save only to `.md` files outside `campaigns/`; Regenerate All refuses (not waits) while processing; `workspaces.md` lists `checkpoints/`.
- **Pages that disagreed:** the two processing concept overviews now share identical Import Audio, Spellcheck, and Review Transcript lines.
- **Structure:** the guide index nests the two processing guides as alternatives under one step; `sessions.md`'s processing section explains the flow; Settings links Remove Bad Utterances to its concept section; every screen-reference breadcrumb now sits directly under the title; `players.md`'s New Players and Managing Players sections were rewritten.
- **Style:** index-tree and breadcrumb casing, record-noun casing, "behavior", Welcome casing, `privacy.md` key-file and workspace wording, and installation's opening and Windows terminal advice.
- **Related items:** [Preparation tools allow an empty latest Session](../prep-tools-empty-latest-session/item.md) (app change plus guide/reference updates) and the reopened [voice print terminology](../voice-print-terminology/item.md) rename, both completed the same day.
- **Screenshots:** added three current guide captures (New Campaign dialog and attendance in Start a Campaign, Export in Generate and Export) and the recaptured Process Session screen in the new-player guide. Deleted 58 unreferenced images (44 in `images/guides/`, all 14 in `images/session-processing/`) and the empty `campaigns/`, `review-and-export/`, `session-preparation/`, and `session-processing/` image folders.

Verification: 288 local links, anchors, and image paths resolve; `git diff --check` on `docs` and `README.md` is clean. Not verified: the "several gigabytes" disk-space figure.
