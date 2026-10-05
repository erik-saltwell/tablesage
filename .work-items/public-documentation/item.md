---
name: "Public documentation"
status: complete
---

# Public documentation

Create and publish a GM-facing documentation experience for TableSage RPG. The current direction is recorded in [intent.md](intent.md). The planning notes once referenced here (`toc-plan.md`, `readme-toc-plan.md`, `progress.md`, `ui-behavior-findings.md`) were never committed and are not retained; the intent's information architecture and the current `docs/` tree are the record. Screenshot capture tooling and its instructions live in the git-ignored `.for-docs/session-processing/README.md`, and `scripts/README.md` describes the fixture seeder.

## Completion (2026-10-05)

Marked complete at the user's explicit direction. Public documentation is maintained in `docs/`, with the repository README as its front door. The notes below preserve earlier work and verification history; references to ongoing implementation or outstanding site publication describe the status at those earlier dates. This closure does not claim a new site deployment or publication verification.

## Historical Resume Note

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

Replaced the installation page's vague "several gigabytes" with measured figures (2026-09-30): about 10 GB to start (roughly 8 GB for the installed libraries, measured on Linux from a development environment that includes CUDA packages; macOS not measured), about 0.5 GB of downloaded models, and about 230 MB per hour of recording per Session (115 MB/hour input audio plus an equal normalized review copy). Player voice samples measured 19–457 MB per Player in a real workspace.

## Review Recommendations Applied (2026-09-30)

Applied all eight recommendations from the accuracy, conciseness, and clarity review at the user's request:

1. Added Git to the README prerequisites and added installation guidance, a `git --version` check, and missing-Git troubleshooting to [Install TableSage](../../docs/getting-started/installation.md).
2. Corrected [Improve Player Voice Recognition](../../docs/guides/manage-players-and-voice-samples.md) to direct users to their workspace's Player folder and an external audio player before selecting an incorrect clip by filename on Player Detail.
3. Added [How the Prior Recap Is Chosen](../../docs/concepts/sessions.md#how-the-prior-recap-is-chosen), explaining date-based selection, undated Sessions, the absence of a recap when no eligible dated Session exists, and explicit regeneration after date changes. Updated the Campaign concepts, returning-player processing concepts, creation guides, and Session dialog reference to agree.
4. Added the required first-launch Settings save before imports in [Move a Campaign to Another Workspace](../../docs/guides/move-campaign-workspace.md), including shared keys on the same computer and account versus destination-specific model choices.
5. Clarified [Privacy and Data Handling](../../docs/reference/privacy.md) to distinguish provider processing uploads, local storage, and Hugging Face downloads of locally used models.
6. Corrected the Python isolation explanation: Python can serve other uv-managed applications, while TableSage's dependencies are isolated in its tool environment.
7. Shortened both processing guides' glossary, spellcheck, and transcript-review instructions while retaining essential controls and decisions. Detailed playback and editing controls now link to [Processing Review Screens](../../docs/reference/screens/processing-review-screens.md).
8. Simplified the Campaign concept opening, moved missing-recording guidance to [Sessions without Recordings](../../docs/guides/start-a-campaign.md#sessions-without-recordings), and replaced installation's duplicate model-default table with a link to Settings.

Verification: checked the behavior against Session date selection and summary composition, Player Detail bindings, Welcome navigation gates, Settings saving, preparation-history validation, and local-model download code. Checked Git and uv guidance against their official documentation. All 310 local links, anchors, and image references across the README, 31 public pages, and four tool READMEs resolve; `git diff --check` passes. Fresh installations and screenshots were not exercised, and no site build was run because MkDocs configuration is absent.

This review pass is finished. The broader public-documentation item remains `implementing`, consistent with `WORK-ITEMS.md`, with site configuration and publication still outstanding. The numerical rubric remains undefined and unassessed; the user explicitly authorized applying these recommendations.

## Recovery and Clarity Fixes (2026-09-30)

Applied all eight findings from the subsequent documentation review at the user's request:

1. Corrected [Correct a Processed Session](../../docs/guides/correct-processed-session.md#correct-attendance-or-roles): attendance and Role edits leave completed processing current. The guide now directs users to explicitly reopen transcript review for speaker corrections and regenerate Role Transcript to apply the current attendees and Roles. Newly added attendees require manual speaker assignments in an already processed Session.
2. Corrected [Build and Maintain Your Campaign Glossary](../../docs/guides/build-campaign-glossary.md#correct-an-existing-entry) and the spellcheck reference: restarting spellcheck reopens saved corrections rather than generating new suggestions from the edited Glossary. The documented recovery uses Review Transcript's Find/Replace, including when an empty spellcheck review completes automatically.
3. Documented the multiple-Role limitation in the Player concepts, campaign-start guide, correction guide, and attendee-dialog reference: all a Player's speech is attributed to their alphabetically first Role.
4. Reconciled the correction guide, output guide, and Process Session reference: changed accepted content rebuilds affected work; confirming the same review decision leaves later work current.
5. Standardized the New Player definition on an attendee without a usable voice print, including the Settings guide's description of name correction.
6. Clarified shared credential changes in the workspace concepts and Settings guide: saving updates the shared file and the current instance; other running instances must restart to load the change, and shell environment variables retain precedence.
7. Removed the unsupported reassurance about LLM resilience to typos and misattributions from the returning-player processing concepts.
8. Shortened the workflow-selection concepts and removed duplicated opening navigation from the Previously On and Opportunities reference, preserving its How to Get Here sections.

Verification: isolated execution in a temporary workspace confirmed that Role and attendee edits leave artifact states unchanged, explicit Role Transcript regeneration applies the alphabetically first Role and schedules dependent outputs, transcript review accepts a newly added attendee's speaker assignment, spellcheck restart retains saved corrections without a new suggestion call, unchanged spelling decisions preserve completed downstream work, and Find/Replace applies an updated glossary spelling. External processing services and expensive audio operations were stubbed using existing fixture helpers; no unit tests were created or changed. Checked credential loading and review-opening behavior against the code. All 306 local links, anchors, and image references across the README and 31 public pages resolve; `git diff --check` passes. Fresh installations, screenshots, and a site build were not exercised.

This requested documentation pass is complete. The broader item remains `implementing`, with site configuration and publication outstanding. The numerical rubric remains undefined and unassessed; the user explicitly authorized these updates.

## Accuracy, Clarity, and Conciseness Fixes (2026-09-30)

Applied the findings of a further accuracy, conciseness, and clarity review at the user's request:

- **Accuracy (checked against the code):** folder import takes only top-level `.wav` files (`voice_clips/clips.py`); the **Samples** column counts clips used in the voice print, and a red 0 means no voice print yet (Start a Campaign, Session Detail reference, Improve Player Voice Recognition); voice samples take tens to a few hundred megabytes per Player; Create Previously On uses the High model for ingredients, scene recommendations, and the recap (`settings.yaml`); installation now suggests `uv python install 3.12`, the version the development environment runs (3.14 is untested, although `uv.lock` has cp314 wheels).
- **Newly documented behavior:** ElevenLabs omits filler words, false starts, and stutters (`no_verbatim`), and Assign Roles To Players drops brief acknowledgments still unassigned after review (`clean_transcript.py`).
- **Clarity:** removed the unexplained "samples without a usable voice print" sentence, "shared" Glossary, the tangled preparation-exception sentence, the ambiguous list-keys reference and shortened step names in `ui-patterns.md`, installation's tier wording (now High/Medium/Low), and the mismatched Extract Glossary link text.
- **Conciseness:** replaced the new-player concept page's repeated step list with a pointer to the overview; trimmed the repeated date advice in the returning-player guide and Session Dialog reference.
- Not changed: the repeated "How to Get Here" lines and duplicated review sections in the processing guides, which were earlier user choices.

Verification: all 306 local links and anchors across the README and 31 public pages resolve; `git diff --check` passes. No site build, fresh installation, or Python 3.14 install was exercised. The numerical rubric remains undefined and unassessed.

## Privacy, Freshness, and Readability Fixes (2026-09-30)

Applied all six findings from the latest public-documentation review at the user's request:

1. Expanded [Privacy and Data Handling](../../docs/reference/privacy.md) to include Player names, Roles, Glossary entries, campaign metadata, generated records, and preparation notes sent to LLM providers. Corrected the audio-upload trigger to **Create Transcript**, including the corresponding Settings guide wording.
2. Narrowed the current-artifact indicator's meaning in [Generate and Export Session Outputs](../../docs/guides/review-and-export.md#read-the-artifacts-panel). Documented that attendance, Role, date, Glossary, and model changes can leave outputs marked current, with guidance on source corrections and explicit regeneration.
3. Corrected [Import Audio](../../docs/reference/screens/processing-review-screens.md#import-audio): **No** skips noise removal, while every import converts to 16 kHz mono and creates normalized review audio. Reconciled the returning-player processing concept page and preserved the distinction between imported audio and the original file.
4. Clarified Session-number ordering, the single highest-numbered unrecorded Session exception, and the starting-situation source in [Prepare the Next Session](../../docs/guides/prepare-the-next-session.md). Reconciled the campaign-start guide and the Campaigns and preparation-tool screen references, distinguishing this order from date-based summary recap selection.
5. Narrowed the shared UI guidance to the six screens where **F5** reloads data, renamed its section **Shared Keys**, and documented the attendee dialog's explicit **Save** action as an exception to Enter submission.
6. Combined the repeated Campaign and Session concept openings and simplified the voice-print definition to a numeric reference built from a Player's voice samples.

Verification: checked the wording against the audio-import pipeline, artifact dependency declarations, preparation-history ordering, LLM preparation inputs, screen refresh implementations, and attendee dialog submission code. The preceding review also directly confirmed WAV conversion and normalized review audio in a temporary directory. All 310 local links, anchors, and image references across the README and 31 public pages resolve; `git diff --check` passes. Existing edits were preserved. No site build, fresh installation, or screenshot recapture was performed; MkDocs configuration is still absent.

This requested pass is complete. The broader item remains `implementing`, consistent with `WORK-ITEMS.md`, with site configuration and publication outstanding. The numerical rubric remains undefined and unassessed; the user explicitly authorized these updates.

## Voice Learning and Readability Fixes (2026-09-30)

Applied all eight proposed changes from the public-documentation review at the user's request:

1. Explained **From Session** replacement of each current attendee's earlier clips from that Session, including when no new lines qualify, and its preference for a current completed transcript review. Reconciled the voice-recognition guide, processing guides and concepts, and Player and processing-review references, including replacement of initial seed clips.
2. Replaced the guarantee that meaningful short replies survive automatic cleanup with the actual question-check rule and its limitation. The processing concepts explain that the initial transcript preserves the pre-cleanup text; the Settings guide links to that explanation.
3. Narrowed **Find More** rejection guidance to removed Find More additions, matching the screen's negative-example selection.
4. Replaced the installation page's normal Welcome screenshot with the existing first-launch capture showing Campaigns and Players disabled.
5. Replaced “oldest Session first” with explicit Session number ordering in the output guide.
6. Shortened the shared UI's quitting guidance, retained the screen comparison table, and consolidated draft details without removing save/discard behavior or the special quit guards.
7. Condensed model uses into the Settings table and replaced the repeated task lists with short model-choice guidance, preserving High-model use across all Previously On stages.
8. Made advance Python download explicitly optional, shortened terminal guidance, and moved installation storage estimates into a table.

Verification: rechecked transcript source selection, session-clip replacement, Find More rejection handling, and the backchannel question-check rule against the implementation. Markdown parsing confirms all 314 local links, heading anchors, and image references across the README and 31 public pages resolve. `git diff --check` passes. The replacement screenshot was visually inspected during the review; no new screenshot, site build, fresh installation, or live provider workflow was run. Existing edits were preserved.

This requested pass is complete. The broader item remains `implementing`, matching its master-list row, with site configuration and publication outstanding. The numerical rubric remains undefined and unassessed; the user explicitly authorized these changes.

## Readability Review Loop (2026-09-30)

Completed three fresh sub-agent reviews limited to worthwhile readability improvements, with independent approval of each proposal and preservation of technical meaning. Twelve proposals were approved and applied across eight public documentation files. The third full pass produced no worthwhile proposals, satisfying the user's stopping condition. Decisions and verification are recorded in [Public Documentation Readability Review](readability-review.md); all 326 public local references resolve and `git diff --check` passes. This completed pass does not change the broader item's `implementing` status or address site publication. The numerical rubric remains undefined and unassessed; the explicit readability criteria governed this requested pass.

At the user's renewed request, a fourth fresh sub-agent completed another full review and submitted no worthwhile proposals. The renewed loop therefore stopped after one iteration, with no additional public edits and all twelve approved changes preserved. All 326 public local references resolve and `git diff --check` passes; see the review record for the renewed-loop outcome. The broader item remains `implementing`.

At the user's third request, a fifth fresh sub-agent independently reviewed all 32 public files and returned no proposals. The parent agreed, ending this requested loop after one full iteration without new public edits. All twelve approved changes remain applied; all 326 local references resolve and `git diff --check` passes. The review record includes the outcome; the broader item remains `implementing`.
