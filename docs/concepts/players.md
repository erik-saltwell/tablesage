# Players, Voice Samples, Voice Prints, and Roles

TableSage distinguishes the people at the table from the identities they use
in play. That distinction lets it recognize a speaker's voice while still
presenting a session in terms of the fiction and the characters in it.

## Players

A **Player** is a persistent, workspace-wide record of a real person and their voice.
Create one Player for each person whose voice you want TableSage to recognize. A
Player is not tied to a particular campaign: the same person can attend any
session in the workspace.

## Voice samples

**Voice samples** are short recordings of a Player speaking. They give
TableSage examples of that person's voice, used to identify when that
player is speaking at a session.

You can add more samples over time. A clearer and more varied set of samples
usually gives TableSage a better basis for recognizing the Player, while
samples that do not fit the rest of the set are automatically excluded from
that player's voice print.

Voice samples typically come from two places:
- You can import them from a folder of audio clips if you have them.
- You can ask TableSage to import all the voice samples from a session after you have
reviewed a session for accuracy.  This enhances the samples of all players who
attended, so it is important that you review the generated transcript before
taking this step, as it can pollute a speaker's voice samples otherwise.

## Voice Prints

A **voice print** is an embedding: a compact numeric representation of a
voice, derived from a single utterance or a collection of voice samples.
A Player's stored voice print combines their usable samples to represent
the common characteristics of their voice.

TableSage uses the voice print to compare a recorded utterance in session
with the voices of the Players attending the session. When you update a
player's voice samples, TableSage recomputes the voice print. A Player
without usable samples does not yet have a voice print to match.

## Roles

A **Role** is the identity or function a Player takes in a particular
session. It is most often a character name, but it can also be **Game Master**
or another table function. A Player may have more than one Role in the same
session, and an attendee may temporarily have none.

When you create a new session, TableSage copies the prior session's attendees
and their Roles as a starting point.

## How the concepts work together

The usual flow is:

1. Create a Player for a person at the table.
2. Add voice samples so TableSage can build that Player's voice print.
3. Add the Player to a session as an attendee.
4. Record the Role or Roles they have in that session.

The Player and voice print help TableSage connect audio to a person. The
session-specific Roles give that person the useful narrative name or function
for transcripts and other session artifacts.

## Related guide

[Manage players and voice samples](../guides/manage-players-and-voice-samples.md)
covers adding samples from a Session or a folder, cleaning up a voice profile, and
moving players between workspaces.
