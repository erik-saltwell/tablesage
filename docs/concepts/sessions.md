# Sessions, Processing, and Session Artifacts

A **Session** records one occasion of tabletop play within a Campaign. It has a name, an optional date, and a sequence number. It  holds a cleaned version of the original recording, a transcript, and generated outputs.

## Session Dates

Session dates tell TableSage the chronological order of sessions, which helps it build beginning-of-session recaps; see [How the Prior Recap Is Chosen](sessions.md#how-the-prior-recap-is-chosen). 
## Attendance and Roles

TableSage keeps an attendance record which captures Players that  took part in a Session. Each attendee record stores the real-world Player and their session-specific Roles. Roles tell TableSage what character or function that Player had in the game. See [Players, Voice Samples, Voice Prints, and Roles](players.md) for more on the distinction.

## Processing a Session

Processing turns a recording into material the group can read, review, and reuse. TableSage processes a session by:
* Transcribing the recording
* Identifying who spoke each line
* Doing a find and replace mis-spelled or mis-heard glossary terms.
* Generating summaries and other human-readable artifacts.
During these steps, TableSage asks the user to approve the work it is about to do and to review crucial decisions; see [Session Processing](session-processing.md) for a more detailed explanation of the steps involved.

## Session Artifacts

**Session artifacts** are the durable records TableSage derives from a Session recording. The following artifacts are available to export from a Session: 

- The **Input audio** is the cleaned recording of a session.
- A **transcript** records the initial speech-to-text result.
- A **reviewed transcript** is the corrected version the group trusts.
- A **role transcript** is a version of the reviewed transcript where utterances are ascribed to Roles rather than Players.
- A **ledger** is the authoritative record of what happened in your game during a Session.
- A **session summary** is a fuller account of what happened during the Session, with an opening recap from the prior Session chosen by date, when available, and any character introductions. It is designed for the GM and for players to read before they get to the table.
- A **recap summary** is a short recap of your Session, designed to be read aloud by the GM at the start of the next Session.

## How the Prior Recap Is Chosen

When generating a session summary, TableSage chooses the prior Session (by date) within the same Campaign:

- For a dated Session, it uses the latest Session with a strictly earlier date.
- If no eligible dated Session exists, it inserts no prior recap.

If the chosen prior Session has no recap and cannot be rebuilt, the summary contains a *The prior Session recap is not available* placeholder.

