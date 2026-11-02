# Still Unanswered

Examples for the questions heading (formerly Mysteries). Conventions are in the [README](../README.md#conventions). The rules are [PREF-003](../preferences.md#pref-003), [PREF-054](../preferences.md#pref-054), [PREF-013](../preferences.md#pref-013) and [PREF-043](../preferences.md#pref-043).

The best calibration set is the user's 54-case testbed of fictional excerpts (`mystery_testbed.md`, under `~/.t3/userdata/attachments/`, with the user's definition file `mystery_definition_and_scoring.md`; see [sources.md](../sources.md) R-06). The user judged its graded evaluation "more or less perfect". Consult it before inventing new cases.

## Good Form

### EX-062 Session 001's Mysteries under the unified pipeline
- Verdict: good (the Session 001 target) · Session 001, unified pass 5, 2026-10-30 · SRC-55
- Rule: [PREF-003](../preferences.md#pref-003). Allowance: [ALW-002](../allowances.md#alw-002)

**The text** (verbatim):
> - What empties Quinn's stock every night?
> - What happened to the shipments that stopped reaching Brandonsford?
> - Where did the black dragon come from?

Hidden in the same run, uncommented: the treasure-map question (depth and payoff low), the Clurichen's nightly visits, the dragon's lair, and Warwick's charms.

**User's words:**
> Mysteries: this is good

**Later judgments:**
- Pass 11 published, in Session 001 (complete list):
  > Why has nothing come into Brandonsford for months?
  > Who or what empties Quinn's good stock every night?

  and in Session 002:
  > Why has nothing come into Brandonsford for months?
  > Why are fairies that once stayed hidden now coming out more often?

  Session 001 lacked the dragon-origin question: "this is actually fine for me for now" (ALW-002). Session 002 lost it: "agreed this is worth fixing".
- Pass 12 Session 002 lacked the earlier "Why are the once-hidden fairies coming out more often?" The agent recommended keeping it as an unexplained change in the world; the user: "Yes".

**Spot it:** one bare question about an underlying truth; no clue, source or background. Reassess eligibility as evidence changes rather than freezing an earlier rating.

---

### EX-019 Golden Mysteries: bare questions about underlying truths
- Verdict: good (style); the Gill's sons line is no longer required · Session 002 golden, user-authored · SRC-01, SRC-60
- Rule: [PREF-003](../preferences.md#pref-003). Allowance: [ALW-007](../allowances.md#alw-007)

**The text** (verbatim):
> - Where and what is the treasure?
> - How is this dragon related to the one Sir Brandon was supposed to have killed?
> - What is going on with the fairies?
> - What happened to Gill's sons?
> - Why does Warwick fill his smithy with lucky charms?
> - Why have supply shipments stopped?

**Why:** one short question each, with no clues attached; doubt sits on what the plot rests on ("supposed to have killed"); situations that went quiet are included.

**Gill's sons** (2026-11-01): the agent recommended allowing the omission because the known expedition establishes no mysterious disappearance; the user: "Agreed" (ALW-007). New evidence of an unexplained disappearance would justify reassessment. A question does not need danger.

**Spot it:** one bare question, about ten words, about an underlying truth.

---

### EX-020 Testbed calibration: include vs exclude
- Verdict: good (graded judgments the user approved) · SRC-34; R-06
- Rule: [PREF-003](../preferences.md#pref-003); [APP-011](../approaches.md#app-011)

**Include** (verbatim, case B01):
> Session evidence: Three villagers were murdered in locked rooms. Each held the same black flower, which does not grow locally. The killer remains unknown.
> Candidate: Who is murdering the villagers, and what connects the victims?

Graded "include — Repeated murders and a shared anomalous clue establish a hidden connection."

**Exclude** (verbatim, case D02):
> Session evidence: The party enters an abandoned temple, defeats a giant spider, and collects coins. The temple's abandonment is not discussed.
> Candidate: What terrible secret caused the temple's abandonment?

Graded "exclude — Abandonment alone does not establish a terrible secret." Payoff `trivial`: "The proposed significance comes entirely from the wording."

**User's words:**
> ok, your judgement on those was more or less perfect

**Spot it:** an evocative wording must not raise the ratings. Grade the evidence.

## Not a Question

### EX-002 Incidental unknowns treated as Mysteries
- Verdict: bad · Session 003, 2026-10-25 · SRC-33
- Rule: [PREF-003](../preferences.md#pref-003)

**The text** (verbatim):
> `mystery_8`: "Who is the huge undead swordsman stalking the Barrow Mound?"
> `mystery_10`: "What powers does Sir Brandon's sword have?"

**User's words:**
> I don't like either of these mysteries. Neither feel to me like investigative targets. Yes they are unknowns, but they are not questions the party is existed to find out for its own sake. Like, they could care less who the undead is, at long as they get the sword.

**Spot it:** would a different answer change anything the party wants or does, or reveal a hidden story? Testbed cases A01 and A02 are these two failures in generic form. Adding "and why is he undead" does not by itself make it a question.

---

### EX-014 Undisclosed information is not a Mystery
- Verdict: bad · Session 001, 2026-10-25 · SRC-32
- Rules: [PREF-003](../preferences.md#pref-003), [PREF-012](../preferences.md#pref-012)

**The text** (verbatim): "What are the other problems Eric the Reeve faces besides the dragon?" Its relevance claimed his further problems "could become paid work for the party."

**User's words:**
> OK there is one here I don't like. The'what other problems does the reeve have? ' this is a hypothetical that could be asked of every npc in the game?

**Spot it:** could the same question be asked of any character who mentioned having more to say?

**Outcome:** the prompt rule's first example (a guildmaster with "plenty of other problems") was rejected as too close to the Session and replaced with an archivist (PREF-012). The candidate is still generated but rated low.

---

### EX-016 Knowing who holds a secret is not knowing what it is about
- Verdict: bad · Session 002, 2026-10-25 · SRC-32
- Rule: [PREF-003](../preferences.md#pref-003)

**The text** (verbatim): "What secret does Naggeneen the Clurichen claim to know?"

**User's words:** after asking for the same diagnosis as EX-014, and seeing it recommend exclusion:
> Make the change

**Spot it:** can you say what the answer would be *about*? If the only known facts are who holds it and its price, exclude. (A later run rated it medium on three dimensions; only low investigative potential kept it out.)

---

### EX-015 An unexplained refusal is an obstacle, not a Mystery
- Verdict: bad · Session 001, 2026-10-25 · SRC-32
- Rules: [PREF-003](../preferences.md#pref-003), [PREF-034](../preferences.md#pref-034)

**The text** (verbatim): "Why does Warwick refuse to sell his mithril chain shirt?" Its basis invented a tension ("even though he has almost nothing else of value to sell").

**User's words:**
> It seems to me that while I can see a case for this, the player's just want the armor, and why is not yet an investigation target

> Yes if anything this is an impediment.

**Spot it:** does the evidence make the "why" itself strange (a contradiction, a lie, a pattern), or would knowing it only help overcome an obstacle? The fictional pair used in prompts: a ferryman refusing evening passengers is excluded; the same ferryman seen secretly carrying hooded passengers at midnight is included. The obstacle form is EX-060.

## The Underlying Question

### EX-017 The treasure: central to the adventure, yet framed as its clues
- Verdict: contested until 2026-11-01; now the question must be published (PREF-054), and clue framing is a minor wording issue · Session 001 from 2026-10-19 on; unified passes 11–12 · SRC-12, SRC-32, SRC-59, SRC-60
- Rules: [PREF-003](../preferences.md#pref-003), [PREF-054](../preferences.md#pref-054)

**The golden** (verbatim, Sessions 001 and 002): "Where and what is the treasure?"

**Generated** (verbatim): "Which of the locations marked on the party's treasure map holds the treasure?" (filtered as closed-ended); "Where is the treasure marked on the party's map?" (depth and payoff low, filtered); pass 11 "Where does the treasure lie?" (hidden for low depth and payoff); pass 12 "Where are the treasure map's marked locations, and which holds the treasure?" (shown).

**User's words:**
> why do you think we are having such problem with the treasure?  It seems to be central to the adventure

> this is more bothersome for me, because adventrure level goals should be excluded from the low impact filter

On pass 12, after the agent recommended "Where and what is the treasure?":
> Your recommendation is certainly my preference, but again, another minor issue.

**Spot it:** is a question that defines a shown adventure goal missing? Is the question the underlying unknown, or one clue that bears on it?

## Lifecycle and Resolution

### EX-018 Local mysteries should end when the episode ends
- Verdict: bad · Session 004, 2026-10-25 · SRC-34
- Rules: [PREF-013](../preferences.md#pref-013), [PREF-051](../preferences.md#pref-051)

**The text** (verbatim):
> Who does the noblewoman statue guarding Sir Brandon's tomb depict?
> Who is the giant undead swordsman stalking the Barrow Mound, and why does he still walk?

The party had finished the tomb expedition and left.

**User's words:**
> I was expecting these to be marked obsolete one they left the barrow mound

**Spot it:** has the episode that made this question matter ended, with the party gone and no evidence carrying it forward?

**Outcome:** an episode-ending rule fixed it in all three following runs.

---

### EX-068 An intentional table revelation can settle an unknown
- Verdict: good (unified approach); bad (requiring a separate in-character discovery) · hypothetical input, reviewed 2026-10-31 · SRC-57
- Rule: [PREF-043](../preferences.md#pref-043)

**Illustrative input** (verbatim; not generated output):
> The characters are investigating who poisoned the mayor. In a cutaway narrated only to the players, the GM reveals that the mayor’s steward prepared the poison. None of the characters witnesses this or receives the information.

**User's words** (numbered response 4):
> I prefer the unified approach - information revealed at the table, if not an accidental slip, is established fact in the fiction and can be included.  (not your recomendation)

**Spot it:** is a resolved unknown kept open only because no character witnessed an intentional table revelation? Was the disclosure intentional and authoritative, or an accidental slip or an attributed claim?
