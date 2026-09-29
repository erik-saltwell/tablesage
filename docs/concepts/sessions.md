# Sessions, Processing, and Session Artifacts

A **Session** is one occasion of tabletop play. It can hold the recording, a
transcript, and outputs like a session summary.

## Sessions

A Session belongs to one Campaign and represents one occasion of play. It has
a name, an optional date, and a place in the Campaign's sequence of Sessions.


## Attendance and Roles

The Session attendance record captures which Players took part in that session.
Each attendee tracks the name of the player who attended, and their role in the
game. A Player identifies the real-world speaker; their session-specific Roles
tell TableSage what charater or role that Player played. See
[Players, Voice Samples, Voice Prints, and Roles](players.md) for more on
the distinction.

## Processing a Session

Processing turns a recording into material the group can read, review, and
reuse. [Session processing](session-processing.md) explains every step in
detail. From Session Detail, press **P** to open **Process Session**. It lists
the processing steps in order, marks each one done once its output is
current, and shows the Session's **New Players** (attendees with no voice
profile yet) when there are any. Press **C** to continue from the first
unfinished step. Steps in bold need you; the others run automatically, and
finishing a step continues processing to the next one:

1. **Import Audio**. TableSage imports and, when needed, cleans the
   audio, transcribes it using ElevenLabs' Scribe v2 engine, and removes
   backchannels and other bad utterances.
2. **Review Name Corrections**. Correct misheard player and character
   names. New players' utterances are then isolated automatically.
3. **Review New Speaker Assignments**. Keep only the utterances each new
   player really said. They become that player's voice samples, and every
   speaker is then identified from the attendees' voice profiles.
4. **Extract Glossary Terms**. Review proposed new glossary entries —
   add, edit, or delete them — before they join the Campaign glossary. When
   nothing new is found, processing simply moves on.
5. **Spellcheck Against Glossary**. Review suggested corrections to
   glossary terms and names, including the terms just added; you decide which
   to apply.
6. **Review Transcript**. Check speaker labels and text. If you leave
   with unsaved edits, TableSage asks whether to save them as a draft to resume
   later; only **Complete** creates the reviewed transcript. Player names are
   then replaced with character names for generation.
7. **Generate Artifacts**. Runs on its own once you complete the review.
   It builds every missing or out-of-date output. If an earlier Session's
   outputs are out of date, a **Rebuild Prior Sessions** step asks before
   rebuilding them first. If the previous Session can't be rebuilt (it was
   never processed or reviewed), its existing recap is used as-is, or the
   Summary notes that the recap is not available.
8. **Improve Player Voice Profiles**. Optionally add voice samples from the
   reviewed transcript to the attendees' voice profiles.

Steps 2 and 3 only matter for new players; with none, they don't appear in
the list and complete on their own. You can also extract glossary terms from the
role-attributed transcript on Session Detail at any time, review the proposed
entries, and add the terms you accept to the Campaign glossary; that never marks
any of the Session's outputs out of date.

The review steps are important. TableSage can make useful initial inferences
from the audio and the Players' voice profiles, but the group decides what the
record should say. Artifacts are built from the reviewed material, so a source
correction can be reflected by regenerating the affected outputs, and changing
an earlier step makes every later step's output out of date.

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

## Related guide

[Review, regenerate, and export a Session](../guides/review-and-export.md) explains
the Artifacts panel and how to regenerate, export, or clean a Session's artifacts.
