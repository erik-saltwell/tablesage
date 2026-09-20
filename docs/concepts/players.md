# Players, Voice Samples, Centroids, and Roles

TableSage distinguishes the people at the table from the identities they use
in play. That distinction lets it recognize a speaker's voice while still
presenting a session in terms of the fiction and the characters in it.

## Players

A **Player** is a persistent, workspace-wide record for a real person. Create
one Player for each person whose voice you want TableSage to recognize. A
Player is not tied to a particular campaign: the same person can attend any
session in the workspace.

The Player record is where TableSage keeps that person's voice profile. It is
also the identity you select when adding someone to a session.

## Voice samples

**Voice samples** are short recordings of a Player speaking. They give
TableSage examples of that person's voice, which it can use when working with
a session recording.

You can add more samples over time. A clearer and more varied set of samples
usually gives TableSage a better basis for recognizing the Player, while
samples that do not fit the rest of the set are automatically excluded from
that player's voiceprint.

Voice samples typically come from two places:
- You can import them from a folder of audio clips if you have them.
- You can ask TableSage to import all the voice samples from a session after you have
reviewed a session for accuracy.  This enhances the samples of all players who
attended, so it is important that you review the generated transcript before
taking this step, as it can pollute a speaker's voice samples otherwise.

## Centroids

A **centroid** is the compact numeric representation of a Player's
voice. It is created by that player's voice samples and represents the common
characteristics of the Player's voice.

TableSage uses the centroid to compare a recorded utterance in session
with the voices of the Players attending the session. When you update a
player's voice samples, TableSage recomputes the centroid. A Player
without usable samples does not yet have a centroid to match.

## Roles

A **Role** is the identity or function a Player takes in a particular
session. It is most often a character name, but it can also be **Game Master**
or another table function. A Player may have more than one Role in the same
session, and an attendee may temporarily have none.

When you create a new session, TableSage copies the prior session's attendees
as a starting point.

## How the concepts work together

The usual flow is:

1. Create a Player for a person at the table.
2. Add voice samples so TableSage can build that Player's centroid.
3. Add the Player to a session as an attendee.
4. Record the Role or Roles they have in that session.

The Player and centroid help TableSage connect audio to a person. The
session-specific Roles give that person the useful narrative name or function
for transcripts and other session artifacts.
