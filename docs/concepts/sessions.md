# Sessions, Processing, and Session Artifacts

A **Session** is one occasion of tabletop play. It can hold the recording, a transcript, and outputs like a session summary.

## Sessions

A Session belongs to one Campaign and represents one occasion of play. It has a name, an optional date, and a place in the Campaign's sequence of Sessions.

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
- A **session summary** is a fuller account of what happened during the Session, opening with the previous Session's recap summary and any character introductions. It is designed for the GM and for players to read before they get to the table.
- A **recap summary** is a short recap of your Session, designed to be read aloud by the GM at the start of the next Session.
