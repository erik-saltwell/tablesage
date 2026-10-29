# Sessions, Processing, and Session Artifacts

A **Session** records one occasion of tabletop play within a Campaign. It has a name, an optional date, and a sequence number. It  holds a cleaned version of the original recording, a transcript, and generated outputs.

## Session Dates

Session dates describe when play happened. Narrative continuity follows recorded Session sequence numbers; see [How Continuity Is Carried Forward](#how-continuity-is-carried-forward).
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
- A **Scene Log** organizes the Ledger into scenes with participants, events, discoveries, outcomes and memorable cues. It is available as structured JSON or readable Markdown.
- **Post-Session Matters** combines this Session’s Developments, Revelations, New Assets, Present Matters and six Open Matters categories into one JSON export. It copies the existing filtered records without another LLM call.
- **Summary** turns Post-Session Matters into structured Markdown a Game Master can read aloud at the table, using titles and primary text and omitting descriptions and evaluation metadata. It includes the current position and present danger. Its headings are meant to be spoken, and the LLM that writes each Matters category already words its entries to follow their heading: in sentence case, as phrases that sound natural read aloud. Rendering the Summary itself uses deterministic code and makes no LLM call.
- **Table Recap** uses an LLM to present all Summary content in the second person. It keeps the bullet sections and ends with one prose passage combining the current position and any immediate danger under **As we return**. It exports as Markdown.

TableSage also stores ten internal Matters artifacts: Present Matters, Goals, Obligations, Brewing Troubles, Goal Impediments, Opportunities, Mysteries, New Assets, Revelations and Developments. They have independent dependencies and completion records, but no selectable artifact rows or exports.

## How Continuity Is Carried Forward

The first recorded Session derives its opening Situation from its transcript’s starting context. Every later Scene Log uses the previous recorded Session’s Present Matters as context. Each cumulative Matters category reconciles its own filtered prior state against the current Scene Log. The predecessor is the highest earlier recorded Session number, including undated Sessions. An unrecorded upcoming Session supplies no continuity.

Missing or out-of-date prior Matters must be rebuilt before their consumers can run. TableSage does not substitute a recap placeholder or treat a later Session as the first one. Merely opening a workspace never generates these artifacts.

## Existing Workspaces

Old Scene Breakdown and Recap Summary files remain available as legacy artifacts. Regenerate outputs from current reviewed transcripts to produce the new Scene Logs and internal Matters. An old Scene Breakdown cannot supply the new contract by changing its filename. Reviewed transcripts are preserved by narrative regeneration. When a legacy Ledger or Summary is first replaced, its original bytes are kept under the Session’s `legacy/narrative/` folder.
