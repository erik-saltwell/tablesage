# Sessions, Processing, and Session Artifacts

A **Session** is one occasion of tabletop play. It can hold the recording, a
transcript, and outputs such as a player-ready session summary.

## Sessions

A Session belongs to one Campaign and represents one occasion of play. It has
a name, an optional date, and a place in the Campaign's sequence of Sessions.

The first Session in a Campaign begins with no attendees. You add the Players
who were at the table and their Roles for that particular gathering. When a
new Session follows an earlier one, TableSage copies the earlier Session's
attendees and Roles as a starting point. You can adjust the new Session
without changing the historical record of the earlier one.

## Attendance and Roles

The Session attendance record captures which Players took part in that gathering.
The Roles attached to each attendee give the recording its in-fiction or
table-specific context: a character name, **Game Master**, or another
function.

This is where the Player and Role concepts meet. A Player identifies the
real-world speaker; their session-specific Roles tell TableSage how to present
that speaker in role-attributed transcripts and other artifacts. See
[Players, Voice Samples, Centroids, and Roles](players.md) for the distinction.

## Processing a Session

Processing turns a recording into material the group can read, review, and
reuse. From Session Detail, press **P** to open **Process**. Once audio exists,
the same binding is labeled **Continue Processing**. The workflow rail shows
the state of Audio, Transcript, and Outputs while you move through these steps:

1. Add the Session's input audio. TableSage imports and, when needed, cleans
   the audio; transcribes it using ElevenLabs' Scribe v2 engine; and uses the
   attendees' centroids to identify speakers.
2. Review suggested spelling corrections and the generated transcript. The
   Campaign glossary can inform spelling suggestions, but you decide which
   corrections to apply.
3. Generate the Session's artifacts.
4. Optionally extract glossary terms from the role-attributed transcript,
   review the proposed entries, and add the terms you accept to the Campaign
   glossary.

The review step is important. TableSage can make useful initial inferences
from the audio and the Players' voice profiles, but the group decides what the
record should say. Artifacts are built from the reviewed material, so a source
correction can be reflected by regenerating the affected outputs. In addition,
a well-reviewed session can be used as a source of new voice samples, improving
later quality.

You can use **Back** to revisit an earlier step without deleting completed
work, or **Exit** to return to Session Detail. If you exit after editing the
transcript, TableSage asks whether to save those edits as an unfinished draft.
Either choice resumes at Transcript next time; only **Complete** creates the
reviewed transcript used to generate outputs. Failed Audio or Outputs work
remains at that step with an error you can retry, and completed work is not
repeated. A fully processed Session opens at Outputs and reports that all
outputs are current.

## Session Artifacts

**Session artifacts** are the durable records TableSage derives from a
Session. The following artifacts are exposed in the Session UI:

- **Input audio** is the recording TableSage processes.
- A **transcript** records the initial speech-to-text result.
- A **reviewed transcript** is the corrected version the group trusts.
- A **role transcript** presents speech using the attendee Roles.
- A **ledger** captures the structured events, facts, and developments of play.
- A **recap summary** distills what happened into a short summary for use by
  later Sessions.
- A **session summary** gives the group a player-ready account of the Session.
