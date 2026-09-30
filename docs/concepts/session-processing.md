# Session Processing

**Session processing** turns the recording of one Session into a reviewed, speaker-attributed transcript and the artifacts built from it: the ledger, the recap summary, and the player-ready session summary. It is a fixed sequence of steps. TableSage runs some of them automatically; at others it stops and asks you to check its work before anything is built on top of it.

## Before You Process

Processing works from the Session's attendance, so set it up first:

- **Attendees.** Add every Player who was at the table. A Session with no attendees can't be processed.
- **Roles.** Give each attendee their Role for this Session—a character name, **Game Master**, or another table function. Processing replaces player names with these Roles before it generates artifacts.

Processing also calls outside services, so you need an ElevenLabs key for transcription and keys for the providers of your LLMs. See [Update Your Settings](../guides/settings.md).

## Two Workflows

TableSage recognizes speakers by comparing their voices with each attendee's **voice print**: the voice print built from that Player's voice samples (see [Players, Voice Samples, Voice Prints, and Roles](players.md)). Everything else in processing depends on knowing who said what, so the workflow depends on whether every attendee already has a voice print.

A **new player** is an attendee without a usable voice print—usually someone attending their first Session who has no voice samples yet.

You never choose a workflow. Process Session looks at the attendees and follows the right one:

- **[Processing with Returning Players](session-processing-returning-players.md)** applies when every attendee already has a voice print. The **New Players** panel is hidden, and the steps that serve new Players do not appear in the list. They still run behind the scenes without asking anything of you, so you move straight from the transcript to speaker identification.
- **[Processing with New Players](session-processing-new-players.md)** applies when at least one attendee is a new Player. Those Players are listed in the **New Players** panel. The extra steps for **New Players** find lines each new Player spoke in this recording, let you confirm them, and turn them into that Player's first voice samples—so that speaker identification can recognize them along with everyone else.

## Exporting Artifacts

Once you are done processing a Session, you can export its artifacts to somewhere else on disk, where you can use them as you see fit. See [Sessions, Processing, and Session Artifacts](sessions.md) for what each artifact is.
