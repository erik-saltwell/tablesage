# Session Processing

**Session processing** turns the recording of one Session into a reviewed, speaker-attributed transcript and the artifacts built from it: the ledger, the recap summary, and the player-ready session summary. It is a fixed sequence of steps. TableSage runs some of them automatically; at others it stops and asks you to check its work before anything is built on top of it.

## Before You Process

Processing works from the Session's attendance, so set it up first:

- **Attendees.** Add every Player who was at the table. A Session with no attendees can't be processed.
- **Roles.** Give each attendee their Role for this Session—a character name, **Game Master**, or another table function. Processing replaces player names with these Roles before it generates artifacts.

Processing also calls outside services, so you need an ElevenLabs key for transcription and keys for the providers of your LLMs. See [Update Your Settings](../guides/settings.md).

## Two Workflows

TableSage recognizes speakers by comparing utterances with attendees' **voice prints**, built from their voice samples (see [Players, Voice Samples, Voice Prints, and Roles](players.md)). The workflow depends on whether every attendee already has a usable voice print.

A **new Player** is an attendee without a usable voice print—usually someone attending their first Session who has no voice samples yet.

TableSage chooses the workflow from the attendees:

- **[Processing with Returning Players](session-processing-returning-players.md)** uses existing voice prints when every attendee has a usable one.
- **[Processing with New Players](session-processing-new-players.md)** establishes voice prints for attendees who need them, using speech you confirm from the recording before identifying speakers.

## Exporting Artifacts

After processing, you can export copies of the Session's artifacts to use or share. See [Sessions, Processing, and Session Artifacts](sessions.md) for what each artifact is.
