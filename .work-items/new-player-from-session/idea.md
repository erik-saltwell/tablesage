# New player from session

## Intended effect

Let someone setting up a session create a missing player without leaving the attendee flow. Make every player's available voice clips immediately scannable in the player list and the session's attendee display, while treating an empty clip set as a warning rather than a prerequisite.

## Accepted design

### Create a player while adding attendees

The attendee picker ends with a visually distinct action option labeled `<New player…>`. The ellipsis indicates that it opens another step rather than naming an existing player.

Choosing the action opens the existing input-message dialog and asks for the player's name. Confirming the name creates the player with zero clips and automatically adds that new player to the session's attendees. The user therefore remains in the session setup flow and does not need to visit the player screen or select the new player a second time.

### Display clip counts

The player list and the session attendee display each gain a leading table column headed **Clips**. It shows the player's clip count:

- A positive count uses the ordinary text color.
- A zero count tints only the numeral in a warning red that fits the existing UI color scheme.

Hovering a zero explains that the player has no clips yet. In the session-attendee context, the explanation should also make clear that processing will add clips. Exact tooltip wording remains to be chosen during detailed design or implementation.

## Rationale and boundaries

Creating and immediately adding the player makes the new-player action a continuation of attendee setup, rather than a detour to player management. The leading **Clips** column supports fast comparison across both contexts. Keeping the warning treatment to the zero numeral avoids error styling or any implication that the user must add clips before continuing.

The workshop considered but did not adopt additional accessible count labels beyond the visible count and hover behavior.

## Workshop outcome

The workshop phase is complete. This is an agreed feature concept, not an implementation plan; detailed behavior and implementation choices remain for a later stage.
