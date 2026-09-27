# Session Processing

**Session processing** turns the recording of one Session into a reviewed,
speaker-attributed transcript and the artifacts built from it: the ledger,
the recap summary, and the player-ready session summary. It is a fixed
sequence of steps. TableSage runs some of them automatically; at others it
stops and asks you to check its work before anything is built on top of it.

Open processing from Session Detail by pressing **P**. The **Process
Session** screen lists every step in order, marks each one with a check once
its output is current, and shows the Session's **New Players** and any
errors.

![Process Session for a Session whose attendees all have voice profiles](../images/session-processing/process-session-returning-players.png)

## Before you process

Processing works from the Session's attendance, so set it up first on Session
Detail:

- **Attendees.** Add every Player who was at the table. A Session with no
  attendees can't be processed.
- **Roles.** Give each attendee their Role for this Session—a character
  name, **Game Master**, or another table function. Processing replaces
  player names with these Roles before it generates artifacts.

Processing also calls outside services, so you need an ElevenLabs key for
transcription and keys for the providers of your High, Medium, and Low
models. See [Update your settings](../guides/settings.md).

## Two workflows

TableSage recognizes speakers by comparing their voices with each attendee's
**voice profile**: the centroid built from that Player's voice samples (see
[Players, Voice Samples, Centroids, and Roles](players.md)). Everything else
in processing depends on knowing who said what, so the workflow depends on
whether every attendee already has a voice profile.

A **new player** is an attendee without a usable voice profile—usually
someone attending their first Session who has no voice samples yet. Session
Detail's **Samples** column shows how many samples each attendee has; a
new player's count is shown in red as **0**.

![Session Detail with a new player, Jordan, who has no voice samples](../images/session-processing/session-detail-new-player.png)

You never choose a workflow. Process Session looks at the attendees and
follows the right one:

- **[Processing with returning players](session-processing-returning-players.md)**
  applies when every attendee already has a voice profile. The **New
  Players** panel reads *All attendees have voice profiles*, and the four
  steps that serve new players are struck through. They complete on their
  own without doing anything, so you move straight from the transcript to
  speaker identification.
- **[Processing with new players](session-processing-new-players.md)**
  applies when at least one attendee is a new player. Those players are
  listed in the **New Players** panel, and the four steps that are skipped for returning players run
  for real. Together they find lines each new player spoke in this
  recording, let you confirm them, and turn them into that player's first
  voice samples—so that speaker identification can recognize them along
  with everyone else.

![Process Session for a Session with a new player](../images/session-processing/process-session-new-player.png)

The simpler workflow is the foundation of the more complex one. Every step
in the returning-player workflow also runs, and means the same thing, when
there are new players.

## The steps at a glance

Numbered steps are the ones you can start with that number key. Most of them
are review steps where you check TableSage's proposals. The others run
automatically.

| Step | Key | Returning players | New players |
|---|---|---|---|
| Import Audio | `1` | You choose the recording | You choose the recording |
| Create Transcript | | Automatic | Automatic |
| Remove Bad Utterances | | Automatic | Automatic |
| Review Name Corrections | `2` | Skipped | You review |
| Isolate New Speakers | | Skipped | Automatic |
| Review New Speaker Assignments | `3` | Skipped | You review |
| Seed Player Voice Samples | | Skipped | Automatic |
| Identify Speakers | | Automatic | Automatic |
| Extract Glossary Terms | `4` | You review | You review |
| Spellcheck Against Glossary | `5` | You review | You review |
| Review Transcript | `6` | You review | You review |
| Assign Roles To Players | | Automatic | Automatic |
| Generate Artifacts | `7` | Automatic | Automatic |

## How a run behaves

The same rules apply in both workflows:

- **One guided run.** Press **1** and choose the recording. From then on,
  finishing a step continues to the next one. Automatic steps run behind a
  progress dialog, and each review screen opens when processing reaches it.
- **Reviews only when there is something to review.** If a review step has
  nothing to propose—no misspellings or new glossary terms, for
  example—it completes on its own and processing moves on.
- **You can stop and resume.** Cancel a review screen, or leave Process
  Session with **Esc**, and your finished steps stay finished. Later,
  press the number of the next step to continue from there. Step keys are
  active only once every earlier step is done.
- **Order matters.** Each step works from the output of the step before it.
  If you redo an earlier step—for example, importing different audio or
  changing the corrections you accepted—every later step's output becomes
  out of date and loses its check, and you work forward from there again.
- **Errors stop the run.** If a key a step needs is missing, TableSage
  asks for it before the step starts. If a step fails while running, the
  message appears in the **Errors** panel and processing stops at that
  step. Fix the cause and press the step's number to try again.

![Process Session after a completed run](../images/session-processing/process-session-complete.png)

When every step is checked, the Session's artifacts are ready on Session
Detail. See [Sessions, Processing, and Session Artifacts](sessions.md) for
what each artifact is.
