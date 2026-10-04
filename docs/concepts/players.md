# Players, Voice Samples, Voice Prints, and Roles

TableSage distinguishes the people at the table from the identities they use in play. That distinction lets it recognize a speaker's voice while still presenting a Session in terms of the fiction and the characters in it.

## Players

A **Player** is a persistent, workspace-wide record of a real person and their voice. Create one Player for each person whose voice you want TableSage to recognize. A Player is not tied to a particular Campaign: the same person can attend any Session in the workspace.

## Voice Samples

**Voice samples** are short recordings of a Player speaking. They give TableSage examples of that person's voice so that it can identify when that Player is speaking.

You can add more samples over time. A clearer and more varied set of samples usually gives TableSage a better basis for recognizing the Player. 

Voice samples typically come from two places:
- You can import them from a folder of audio clips if you have them.
- You can ask TableSage to add clips from a Session you have reviewed for accuracy.

If you are going to use a Session to enhance your Players' voice samples, review its transcript carefully first; otherwise, mislabeled lines can pollute a speaker's voice samples.

## Voice Prints

A **voice print** is a numeric reference built from a Player's voice samples, used to recognize their voice in a recording. A Player without usable samples does not yet have a voice print to match. TableSage recomputes a player's voice print whenever that player's voice samples change. 

When TableSage computes a voice print, it automatically looks for samples that sound like outliers, and ignores them so they don't corrupt the  voice print.

## New Players

A **New Player** is an attendee without a usable voice print, usually because they have no voice samples yet. Processing a Session with a new Player includes extra steps that learn their voice from the recording.

## Roles

A **Role** is the identity or function a Player takes in a particular Session. It is most often a character name, but it can also be **Game Master** or another table function.

When you create a new Session, TableSage copies the attendees and Roles of the prior Session (by date) as a starting point; for more see [Process a Session with Returning Players](../guides/process-session-returning-players.md#create-the-session-and-check-attendance).

## Improving Voice Recognition

As you process sessions, TableSage can use the transcript to find high confidence voice samples to add to a Player's set.  It is highly recommended that you review your first few sessions for correctness and then have TableSage enhance Players' voice samples after it generates transcripts and summaries.  Once players have a hundred or so voice samples, you do not need to keep doing this, unless audio circumstances change (like playing in a new location, or with a new microphone). See [Improve Player Voice Recognition](../guides/manage-players-and-voice-samples.md).
