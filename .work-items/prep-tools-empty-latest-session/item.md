---
name: "Preparation tools allow an empty latest Session"
status: complete
---

# Preparation tools allow an empty latest Session

Create Previously On and Generate Opportunities require every Session in the Campaign to have a current Scene Breakdown (`Application.previously_on_history`). A GM who creates the upcoming Session in advance is blocked, and Regenerate All Outputs cannot help because it silently ignores Sessions without imported audio. Found in the public-documentation quality review on 2026-09-30.

## Decision (user, 2026-09-30)

Ignore the most recent Session when it has no imported audio. Keep blocking on any earlier Session that is empty or not current, and on a latest Session that has audio but is not fully processed. If the only Session is empty, there is no history and the tools still refuse. The starting/ending situation must come from the last included Session, and Previously On's suggested file name must use the upcoming (empty) Session's number rather than one past it.

Update `docs/guides/prepare-the-next-session.md` and `docs/reference/screens/previously-on-and-opportunities.md` (and Campaign Detail's reference) to match.

No rubric has been defined; the user explicitly requested implementation.

## Completion (2026-09-30)

`Application.previously_on_history` now drops the latest Session when it has no input audio, and refuses with "This Campaign has no recorded Sessions yet" if nothing remains. Starting/ending situations and the Previously On suggested filename derive from the included Sessions, so they needed no change. Updated the preparation guide, the Previously On and Opportunities reference, and Campaign Detail's reference.

Verification: direct execution against the existing `_ready_campaign` fixture confirmed four cases — empty latest ignored (history [1, 2], filename `…-003-previously-on.md`, starting situation from Session 2); empty middle Session blocks and is named; latest Session with audio but unprocessed blocks and is named; a lone empty Session refuses. The 59 existing previously-on, opportunities, and Campaign Detail tests pass; Ruff and ty pass on `application.py`. No tests were added. Not checked in the live TUI.
