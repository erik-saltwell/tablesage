# Players, Voice Samples, Voice Prints, and Roles

TableSage distinguishes the people at the table from the identities they use in play. That distinction lets it recognize a speaker's voice while still presenting a Session in terms of the fiction and the characters in it.

## Players

A **Player** is a persistent, workspace-wide record of a real person and their voice. Create one Player for each person whose voice you want TableSage to recognize. A Player is not tied to a particular Campaign: the same person can attend any Session in the workspace.

## Voice Samples

**Voice samples** are short recordings of a Player speaking. They give TableSage examples of that person's voice, used to identify when that Player is speaking at a Session.

You can add more samples over time. A clearer and more varied set of samples usually gives TableSage a better basis for recognizing the Player, while samples that do not fit the rest of the set are automatically excluded from that Player's voice print.

Voice samples typically come from two places:
- You can import them from a folder of audio clips if you have them.
- You can ask TableSage to add clips from a Session you have reviewed for accuracy.

If you are going to use a Session to enhance your Players' voice samples, review its transcript carefully first; otherwise, mislabeled lines can pollute a speaker's voice samples.

## Voice Prints

A **voice print** is an embedding: a compact numeric representation of a voice, derived from a single utterance or a collection of voice samples.

TableSage uses the voice print to compare a recorded utterance in a Session with the voices of the Players attending the Session. When you update a Player's voice samples, TableSage recomputes the voice print. A Player without usable samples does not yet have a voice print to match.

## New Players

A **new Player** is a Player with no voice samples yet, and therefore no usable voice print. Processing a Session with a new Player includes extra steps that learn their voice from the recording.

## Roles

A **Role** is the identity or function a Player takes in a particular Session. It is most often a character name, but it can also be **Game Master** or another table function.

When you create a new Session, TableSage copies the attendees and Roles of the latest dated Session before it as a starting point; see [Process a Session with Returning Players](../guides/process-session-returning-players.md#create-the-session-and-check-attendance).

## Managing Players

You rarely need the Players List during normal play. You can create a Player while adding them to a Session's attendance, and processing can add voice samples from a reviewed Session. Use the Players List to delete a Player, import clips from a folder, recompute or clean up voice prints, or move Players between workspaces; see [Improve Player Voice Recognition](../guides/manage-players-and-voice-samples.md).
