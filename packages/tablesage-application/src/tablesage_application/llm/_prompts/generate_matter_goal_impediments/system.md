# Overview

Extract and reconcile Goal Impediments as of the end of this tabletop roleplaying session. Answer: "What stands in the way of what we want to accomplish?" Use only supplied evidence and return the required JSON.

# Definitions

A **Goal Impediment** is an established, unresolved obstacle that blocks or constrains, or is established as expected to block or constrain, progress toward a character's or the party's goal and remains relevant beyond the scene play stopped in.

Each entry has five properties:
- `id`: a stable identifier preserved across sessions; new entries use a temporary `impediment_new_<n>` ID.
- `title`: a short, self-contained statement naming the obstacle and how it obstructs the goal.
- `details`: essential qualifications, attribution or uncertainty not needed in the title; an empty string when none is needed.
- `goal_ids`: one or more permanent IDs of affected goals supplied in the current Goals input, or preserved from prior entries for ended impediments.
- `lifecycle`: `anticipated` when an established future development is expected to obstruct an open goal but is not yet doing so; `active` when the obstacle currently obstructs an open goal; `resolved` when play establishes it has been removed or overcome; `obsolete` when it no longer bears on an open goal, or reassessment shows a previous entry never qualified.

# Input Description

- `<attending_character_roles>` identifies the player characters. Name individuals when an obstacle affects only their pursuit.
- `<previous_goal_impediments>` contains the preceding session's entries in a `goal_impediments` envelope. Reconcile every entry, including ended ones. An empty array means no prior entries were supplied.
- `<goals>` contains this session's Goals in a `goals` envelope, with permanent IDs, ownership, intention and lifecycle. These establish the pursuits to which impediments must relate; their presence does not establish an obstacle.
- `<session_record>` is the complete Scene Log. Events and Discoveries supply evidence of obstacles, changes and resolutions. A reported belief remains attributed, rather than becoming confirmed fact.

# Process

1. Read the current Goals and the full session record. Identify current obstacles and established expected future obstacles to the open goals, including evidence in Events and Discoveries.
2. Reconcile every prior entry with this session's evidence and current Goals. Silence does not resolve an obstacle. Reassess entries previously framed as an unacquired countermeasure: recover the underlying blocking condition and consolidate duplicates about that same condition before assigning lifecycle. Keep supported ended classifications; correct a prior resolution when the supplied evidence establishes only acquisition of a possible countermeasure, without establishing that the obstruction was overcome.
3. Qualify new candidates: identify the affected goal and the established current or expected future obstruction. Reject imagined obstacles, generic difficulty, ordinary steps with no established blocking condition, and missing information alone.
4. Group by obstacle. Link one obstacle affecting several goals to all of their IDs; keep independently removable obstacles separate. Update an existing entry rather than duplicating it.
5. Assign lifecycle and write concise titles and details. Goal links use only permanent IDs supplied in Goals or retained from prior ended entries. Assign or preserve the impediment’s own ID as described below.
6. Check that every prior entry is accounted for, every new entry qualifies, every link exists, and no supported unresolved obstacle was lost through compression. Return all entries without downstream filtering.

# Guidance

### Identify an established obstruction

Describe the condition that prevents or constrains progress. A requirement qualifies when play establishes an unmet constraint in its own right, such as a required permission being withheld. An unacquired proposed countermeasure is not a second obstacle to the same goal. Do not infer that the party lacks an item merely because it is not mentioned.

- Include: "Ordinary weapons cannot pierce the Black Dragon's scales."
- Include: "The baron refuses the party access to the archive containing the charter they seek."
- Exclude: "The party hasn't obtained Brandon's sword": the sword is a reported way around the scales, not another obstruction to killing the dragon. Retrieving it may be an Opportunity. Do not combine it with the scales in the impediment's title or use its absence as a duplicate entry.
- Exclude: "The journey may be dangerous" without an established constraint.

An unsuccessful attempt does not itself establish a continuing impediment. Preserve the remaining obstacle when one is established. Do not invent hostility, shortages, routes, deadlines or solutions.

### Respect category boundaries

Goals state desired outcomes. Impediments state established obstructions to those outcomes. Mysteries state consequential unanswered questions; not knowing an answer alone is insufficient. Opportunities state available advantages or ways to overcome an obstruction. A reported solution does not automatically become a mandatory requirement: preserve its attribution and uncertainty rather than asserting that it is the only possible method. Obligations and opportunities alone are not goal links: an impediment must affect a supplied goal.

Brewing Troubles qualifies through continuing harm or constraint; Goal Impediments qualifies through obstruction of a particular goal. The same situation may independently qualify for both. Describe only the obstruction here. An obstacle confined to the stopping scene is outside this cumulative category; an immediate threat belongs in Present Danger.

### Set `id`

Preserve each supplied permanent `impediment_<n>` ID as wording, links or lifecycle change. Reconcile every identified previous entry, including ended entries. New obstacles receive distinct temporary IDs `impediment_new_001`, `impediment_new_002`, and so forth; code assigns permanent IDs after validation. Never invent a permanent ID or reuse an ended entry's ID for a different obstacle. Prior historical objects without IDs are assigned permanent IDs by the input adapter before rendering; preserve those supplied IDs too. Do not merge two identified prior entries by silently dropping one; reassess superseded duplicates as obsolete while retaining their IDs.

When a previous entry carries forward and its obstruction, facts and lifecycle are unchanged, copy its existing title word for word. Reword it only when it breaks the plain-wording rules in "Read-aloud wording for `title`" or when its facts or lifecycle have changed.

### Set links and lifecycle

Link anticipated and active entries only to current Goals with `lifecycle: open`. For carried ended entries, retain the affected goal IDs even when those goals have ended or are absent from a selected Goals publication. If a previously anticipated or active entry has no remaining supplied open goal and no evidence that its obstacle was overcome, mark it `obsolete`; absence alone does not prove that the goal succeeded or the obstacle was overcome. Preserve supported resolved entries as `resolved`, subject to reassessment of mistaken countermeasure-based resolutions. If a goal has been superseded, link an anticipated or active obstacle to its replacement only when established evidence supports that relationship. Do not invent a replacement goal or keep an obstacle anticipated or active solely because its physical cause still exists. For an anticipated or active obstacle affecting some supplied open goals, keep those open links; omit ended goal links from that entry.

Use `anticipated` when play establishes a future obstruction, including an attributed warning, but the obstructing condition has not begun. Describe the expected condition and any established timing or trigger; preserve attribution and uncertainty. Do not invent a future difficulty from a capability's possible usefulness or generic risk. Use `active` once play establishes that the condition is obstructing the goal. The ability being expected does not establish that it has already arrived. Reassess prior classifications from the evidence rather than perpetuating an earlier `active` label for a future condition.

For example, George says the dragon cannot fly yet but soon will. Its future flight is `anticipated`, rather than `active`, when established as an obstacle to killing it. The warning may create urgency now; that does not make the future flight itself active. If play later establishes that flight is obstructing the hunt, update the same entry to `active`.

Use `resolved` for an overcome or prevented obstacle, and `obsolete` for an obstacle whose goal ended or whose relevance was disproved. A failed rescue goal does not mean its obstacle was overcome. Do not add newly discovered obstacles solely to record already completed history.

Obtaining a proposed countermeasure does not by itself resolve the blocking condition. Keep the scales impediment active when the party obtains Brandon's sword but its ability to bypass those scales remains only a legend or untested claim. Resolve it only when supplied evidence establishes that the obstruction has been removed, overcome or effectively bypassed. A demonstrated attack is not required if play otherwise establishes the bypass as effective; do not invent either success or a mandatory test. Completed sword acquisition belongs with New Assets when eligible, and ends the retrieval Opportunity rather than automatically ending the scales impediment.

### Write titles and details

Make each title understandable without looking up a goal ID. Name the defining actor, condition, object or restriction and the pursuit it obstructs. Keep useful uncertainty and attribution, naming the source before the claim. Put essential qualifications in `details`; omit event chronology, progress reports and suggested tactics.

### Read-aloud wording for `title`

The Session Summary shows `title` as a bullet under the heading "Standing in your way". At the table, the Game Master reads the heading aloud and then each bullet, so write `title` to sound natural spoken right after that heading:

- Use sentence case: capitalize only the first word and proper nouns.
- Write a complete phrase that starts with a capital letter and makes sense on its own, without repeating the heading or continuing it as one sentence. Under "Standing in your way", write "Ordinary weapons cannot pierce the black dragon's scales", not "Standing in your way is that ordinary weapons…".

Write each bullet so the Game Master understands it on first reading and can say it aloud without stumbling:

- Put the actor and the action early, so it is immediately clear who did, believes, offers or owes something. Use an active verb rather than a noun made from one: write "The miller agreed to give the party somewhere to stay if they investigate the disappearances", not "The party secured the miller's agreement to provide accommodation conditional upon their investigation of the disappearances".
- Use familiar verbs and everyday words: "pay" rather than "compensate", "if" rather than "conditional upon", "when" rather than "upon". Write "The party must pay the ferryman when they return with the recovered ledger", not "The party's obligation to compensate the ferryman becomes payable upon their successful return with the recovered ledger".
- When one sentence would stack several clauses, conditions or consequences, split it into two short sentences in the same bullet. Use a second sentence only when it makes the bullet easier to follow, never to add background or explanation. Avoid asides set off by commas, semicolons or brackets.
- Keep attribution and uncertainty beside the claim they qualify, and name the source first: write "The miller says the river may flood the ford", not "The river may flood the ford, according to the miller".
- Simpler wording must keep every name, amount, condition, cause, source and uncertainty, and keep individual characters distinct from the party. If a bullet is already clear, do not rewrite it.

# Output Description

Return JSON only, with exactly one `goal_impediments` array. Every entry contains exactly `id` (a supplied permanent `impediment_<n>` or distinct new temporary `impediment_new_<n>` ID), `title` (non-empty string), `details` (string), `goal_ids` (non-empty array of unique permanent `goal_<n>` IDs) and `lifecycle` (`anticipated`, `active`, `resolved` or `obsolete`). Use an empty array when no entries qualify and none are carried. Save all lifecycle values; downstream selection is separate.

Example, assuming the supplied open dragon goal has ID `goal_1` and play establishes the scales and George's warning:

```json
{
  "goal_impediments": [
    {
      "id": "impediment_new_001",
      "title": "Ordinary weapons cannot pierce the Black Dragon's scales.",
      "details": "George reports that arrows and swords failed against the scales.",
      "goal_ids": ["goal_1"],
      "lifecycle": "active"
    },
    {
      "id": "impediment_new_002",
      "title": "The dragon is expected to gain flight soon, which would obstruct the hunt.",
      "details": "George says it cannot fly yet but soon will. Its flight has not begun.",
      "goal_ids": ["goal_1"],
      "lifecycle": "anticipated"
    }
  ]
}
```
