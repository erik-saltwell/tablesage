# Sessions, Processing, and Session Artifacts

A **Session** records one occasion of tabletop play within a Campaign. It has a name, an optional date, and a sequence number, and can hold the recording, transcript, and generated outputs.

Dates determine which Session supplies the prior recap in a session summary; see [How the Prior Recap Is Chosen](#how-the-prior-recap-is-chosen).

## Attendance and Roles

The session attendance record captures which Players took part in that Session. Each attendee record stores the real-world Player and their session-specific Roles, which tell TableSage what character or function that Player had in the game. See [Players, Voice Samples, Voice Prints, and Roles](players.md) for more on the distinction.

## Processing a Session

Processing turns a recording into material the group can read, review, and reuse. TableSage transcribes the recording, identifies who spoke each line, and asks you to review names, vocabulary, and the transcript before an LLM generates the Session's artifacts from the reviewed record. [Session Processing](session-processing.md) explains the steps and why each exists.

## Session Artifacts

**Session artifacts** are the durable records TableSage derives from a Session. The following artifacts are exposed in the Session UI:

- **Input audio** is the recording TableSage processes.
- A **transcript** records the initial speech-to-text result.
- A **reviewed transcript** is the corrected version the group trusts.
- A **role transcript** is a version of the reviewed transcript where utterances are ascribed to Roles rather than Players.
- A **ledger** is the authoritative record of what happened in your game during a Session.
- A **session summary** is a fuller account of what happened during the Session, with an opening recap from the prior Session chosen by date, when available, and any character introductions. It is designed for the GM and for players to read before they get to the table.
- A **recap summary** is a short recap of your Session, designed to be read aloud by the GM at the start of the next Session.

## How the Prior Recap Is Chosen

When generating a session summary, TableSage chooses the prior Session within the same Campaign by date:

- For a dated Session, it uses the latest Session with a strictly earlier date.
- For an undated Session, it uses the latest dated Session.
- If no eligible dated Session exists, it inserts no prior recap. This includes Campaigns where every Session is undated.

Session numbers do not determine this choice. Record dates if you want summaries to open with the preceding game's recap. If the chosen prior Session has no recap and cannot be rebuilt, the summary contains a *The prior Session recap is not available* placeholder.

Changing a Session's date does not replace the prior recap in an existing summary. Regenerate **Summary** to use the current date; see [Regenerate an Artifact](../guides/review-and-export.md#regenerate-an-artifact).
