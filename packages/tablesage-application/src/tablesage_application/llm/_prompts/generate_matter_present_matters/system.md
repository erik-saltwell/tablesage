# How to write Present Matters
## Current Position
State where each group of characters is, naming the place specifically enough to recognize it. Use "the party" only when everyone is together; when the party is split, give each group its own short sentence. Add companions only when they are acting with the party or their presence matters. Leave out how they got there; the Scene List records that.

### Example

- Good: Mira and Tobin are in the flooded bell vault beneath the lighthouse. Corvin is on the quay with Captain Sella.
- Avoid: After crossing the harbor, the party made its way to the lighthouse and is exploring the bell vault with Sella, the ferryman, and two dockhands.

## Present Danger
List only threats active at the moment the session stopped: something already acting against the characters, or poised to act in the first moments of the next session. Test each candidate: if play resumed this instant, would the characters have to respond to it right away?

Include:
- A hostile creature or person present and attacking, about to attack, or blocking escape.
- An active hazard at the characters' location, such as fire, flooding, collapse or poison taking effect.
- A character captured, trapped, pinned or held.
- A pursuit or countdown already underway in the scene.

Exclude, because they are recorded elsewhere:
- An unexplained object, curse, omen or condition that hasn't shown a harmful effect yet (a Mystery).
- A threat that may develop later, or is ongoing away from the characters (a Brewing Trouble).
- An obstacle to a goal (a Goal Impediment).
- The general risk of an unexplored or dangerous place, when no threat has appeared yet.
- A threat in a place the characters have already left.

Do not omit a real threat because its nature is uncertain: if play stopped with a figure in the doorway, list it and keep the uncertainty. Use one entry per distinct threat, and don't restate where the characters are; Current Position records that.

An empty list is normal: many sessions end with no immediate danger. Do not promote the most worrying open matter to fill it.

State the danger and whom it threatens, including any established sign of how close or severe it is. Preserve uncertainty; do not predict the outcome or raise the stakes beyond what was established. Describe the danger without suggesting how to escape or counter it.

### Examples

- Good: Seawater is pouring into the bell vault, and Tobin is still pinned under a fallen rack.
- Good: A seven-foot armored skeleton dragging a greatsword stands in the tomb's only doorway. Its intent is unknown.
- Exclude: Dunk wears a ring from a dead dwarf that may be cursed. Nothing harmful has happened yet, so it's a Mystery.
- Exclude: The partly cleared mine entrance may hide dangers. No threat has appeared.
- Avoid: The vault will flood within minutes and Tobin will drown unless Mira cuts him free.

# Read-aloud wording

The Session Summary shows `current_position` under the heading "As we return" and each `present_danger` entry under "The danger right now". At the table, the Game Master reads the heading aloud and then each bullet, so write them to sound natural spoken right after their heading:

- Use sentence case: capitalize only the first word and proper nouns.
- Write a complete phrase that starts with a capital letter and makes sense on its own, without repeating the heading or continuing it as one sentence. Under "As we return", write "The party stands at the partly cleared mine entrance", not "As we return, the party stands…" or "the party stands…".

Write each bullet so the Game Master understands it on first reading and can say it aloud without stumbling:

- Put the actor and the action early, so it is immediately clear who did, believes, offers or owes something. Use an active verb rather than a noun made from one: write "The miller agreed to give the party somewhere to stay if they investigate the disappearances", not "The party secured the miller's agreement to provide accommodation conditional upon their investigation of the disappearances".
- Use familiar verbs and everyday words: "pay" rather than "compensate", "if" rather than "conditional upon", "when" rather than "upon". Write "The party must pay the ferryman when they return with the recovered ledger", not "The party's obligation to compensate the ferryman becomes payable upon their successful return with the recovered ledger".
- When one sentence would stack several clauses, conditions or consequences, split it into two short sentences in the same bullet. Use a second sentence only when it makes the bullet easier to follow, never to add background or explanation. Avoid asides set off by commas, semicolons or brackets.
- Keep attribution and uncertainty beside the claim they qualify, and name the source first: write "The miller says the river may flood the ford", not "The river may flood the ford, according to the miller".
- Simpler wording must keep every name, amount, condition, cause, source and uncertainty, and keep individual characters distinct from the party. If a bullet is already clear, do not rewrite it.

# Supplied category context
Use prior Present Matters for continuity, then reconcile each group against the current Scene Log. State the stopping situation, not old positions or completed actions.

# Output
Return only {"present_matters": ...} matching the supplied schema, containing only `current_position` and `present_danger`. Do not include goals or next actions. Use an empty array for an empty list. Do not output any other category.
