# Mysteries Examples

Concrete good, bad and contested Mysteries, each with the context needed to judge it. Conventions are in [README.md](../README.md). Run folders named here are under `~/data/tablesage_summary_test/.cache/runs/`.

The definition changed twice:
- On 2026-10-25T03:10Z the user framed Mysteries as sources of investigative action.
- On 2026-10-25T19:42Z it was rewritten from the user's own definition file, `mystery_definition_and_scoring.md` (see [PREF-003](../preferences.md#pref-003)). That file is preserved under `~/.t3/userdata/attachments/` and its name is listed in [sources.md](../sources.md) R-06.

The user also wrote a 54-case **testbed** (`mystery_testbed.md`) of fictional excerpts with candidate questions. Its graded evaluation is in `~/data/tablesage_summary_test/artifacts/.trash/mystery-testbed-evaluation.md`, and the user judged it "more or less perfect". The testbed is the best calibration set for this matter: consult it before inventing new cases.

---

### EX-002 Incidental unknowns treated as Mysteries
- Verdict: bad
- Scope: mysteries
- Failure pattern: Ordinary unknown
- Session / run: Brandonsford Session 003 Mysteries, the input to the Session 003 Revelations runs diagnosed at 2026-10-25T18:43Z
- Source: SRC-33 (2026-10-25T18:50Z–18:54Z)

**The text** (verbatim):
> `mystery_8`: "Who is the huge undead swordsman stalking the Barrow Mound?"
> `mystery_10`: "What powers does Sir Brandon's sword have?"

**Context needed to judge it:** these two Mysteries were the link targets for the two weakest Revelations under review. The party's goal at that point was to get the sword and get out.

**User's reaction** (verbatim):
> I don't like either of these mysteries. Neither feel to me like investigative targets. Yes they are unknowns, but they are not questions the party is existed to find out for its own sake. Like, they could care less who the undead is, at long as they get the sword.

**Why it is bad:** every unidentified creature and unexamined magic item would produce a Mystery like these. Nothing makes the answer worth pursuing.

**Spot it:** would a different answer change anything the party wants or does, or reveal a hidden story? If not, the question is an ordinary gap in description. In the user's testbed, cases A01 ("What kind of undead creature attacked the party?") and A02 ("What magical powers does the sword possess?") are these two failures in generic form, and both are graded exclude.

**Outcome:**
- The user's definition rewrite (2026-10-25T19:42Z) states: "Missing tactical information, unidentified objects, unknown abilities, and routine information gaps do not qualify unless their answers promise a meaningful narrative revelation."
- **Check (st published outputs, 2026-10-26):** the Session 003 output (`artifacts/session_003/outputs/campaign-matters/Mysteries.json`) still holds "Who is the giant undead swordsman roaming the Barrow Mound, and why is he undead?" with grounding `high` and the other three dimensions `medium`. The added "why is he undead" may be what gets it through; the user has not reviewed this version. The port's deployment output (pt, 2026-10-28) has the same pattern: "Why does a huge undead figure with a greatsword roam the Barrow Mound?"
- In Session 004 the same question becomes "Why does Sir Alfred still walk as an undead guardian of the Barrow Mound?" and is then marked obsolete (EX-018).
**Links:** [PREF-003](../preferences.md#pref-003)

---

### EX-014 Undisclosed information is not a Mystery
- Verdict: bad
- Scope: mysteries
- Failure pattern: Undisclosed information
- Session / run: Session 001, runs `mysteries-brandonsford-001-hz_3mg9a` and `-5bkbrdfa` (2026-10-25T03:26Z). It appeared in two of three runs.
- Source: SRC-32 (2026-10-25T03:30Z). Diagnosis in `.cache/runs/mysteries-reeve-diagnostic-uyo01aqi/`.

**The text** (verbatim):
> What are the other problems Eric the Reeve faces besides the dragon?

`basis`: "Eric the Reeve said the dragon is only the first of his many problems, and he has been trying to find people to help." `relevance`: "Eric is the town's employer of adventurers, and his further problems could become paid work for the party."

**User's reaction** (verbatim):
> OK there is one here I don't like. The'what other problems does the reeve have? ' this is a hypothetical that could be asked of every npc in the game?

**Why it is bad:** a remark that more information exists establishes no particular subject to investigate. The extractor let potential usefulness ("paid work") stand in for a Mystery.

**Spot it:** could the same question be asked of any NPC who mentioned having more to say? Then it is not a Mystery.

**Outcome:**
- A rule was added and kept: "A statement that more information is available does not by itself establish a Mystery."
- The user required the prompt's example to be fictional and not echo session text. The first draft's guildmaster ("I have plenty of other problems") was replaced by an archivist saying "These shelves hold enough stories to fill a lifetime". See [PREF-012](../preferences.md#pref-012).
- It is still generated after the rewrite, as "What are the Reeve's other problems beyond the dragon?", but scores `low` on depth, payoff and potential, so the filter removes it (run `mysteries-brandonsford-001-326vkal4`).
**Links:** [PREF-003](../preferences.md#pref-003), [PREF-012](../preferences.md#pref-012)

---

### EX-015 An unexplained refusal is an obstacle, not a Mystery
- Verdict: bad
- Scope: mysteries (cross-matter: goal-impediments)
- Failure pattern: Unstated motive
- Session / run: Session 001, run `mysteries-brandonsford-001-yx6mz846` (2026-10-25T03:43Z)
- Source: SRC-32 (2026-10-25T03:45Z). Diagnosis in `.cache/runs/mysteries-shirt-diagnostic-wbgxi43x/`.

**The text** (verbatim):
> Why does Warwick refuse to sell his mithril chain shirt?

`basis`: "Gill says Warwick displays a beautiful mithril chain shirt, perhaps the best in the world, but always refuses to sell it, even though he has almost nothing else of value to sell." `relevance`: "…knowing why Warwick won't sell it could help them get it."

**User's reactions** (verbatim):
> It seems to me that while I can see a case for this, the player's just want the armor, and why is not yet an investigation target

> Yes if anything this is an impediment.

**Why it is bad:**
- Every NPC decision has unstated reasons.
- The `basis` invents a tension ("even though he has almost nothing else of value") between facts that do not conflict.
- What the party actually faces is an obstacle to getting the armor.

**Spot it:** is the "why" itself made strange by the evidence (a contradiction, a lie, a pattern), or would knowing it merely help overcome an obstacle? The second case is an Impediment.

**Outcome:**
- Guidance added with a fictional example. A ferryman refuses evening passengers: exclude. If he is then seen secretly ferrying hooded passengers at midnight: include.
- The candidate is still generated in the latest runs but ranks `low` on depth, payoff and potential, so it is filtered out.
**Links:** [PREF-003](../preferences.md#pref-003)

---

### EX-016 Knowing who holds a secret is not knowing what it is about
- Verdict: bad
- Scope: mysteries
- Failure pattern: Undisclosed information
- Session / run: Session 002, runs `mysteries-brandonsford-002-i6eohh5v`, `-jhmo_q8e` and `-q_777fvu` (2026-10-25T03:52Z), present in all three
- Source: SRC-32 (2026-10-25T03:53Z). Diagnosis in `.cache/runs/mysteries-secret-diagnostic-bbgq3zzf/`.

**The text** (verbatim):
> What secret does Naggeneen the Clurichen claim to know?

`relevance`: "Naggeneen offered the secret as a bargaining chip, and he remains reachable at the Golden Egg, where Sir Phidipaldi sleeps."

**User's reaction** (verbatim): the user asked "Can you do the same diagnostic analysis of the naganeen secret" right after the Reeve and shirt exclusions. When the diagnosis recommended exclusion, they replied:
> Make the change

**Why it is bad:** in the diagnosis's words, "Knowing who holds the information and its price does not establish its subject." The relevance describes access to the information, not a question.

**Spot it:** can you state what the answer would be *about*? If the only known facts are who holds it and what it costs, exclude.

**Outcome:**
- The rule was extended to cover named holders and prices.
- **Narrow miss:** in a later run (`mysteries-brandonsford-002-kpc4qwb8`, 2026-10-25T23:31Z) it scores `medium` grounding, depth and payoff. Only `low` investigative potential keeps it out.
**Links:** [PREF-003](../preferences.md#pref-003)

---

### EX-017 The treasure: central to the adventure, yet framed as its clues
- Verdict: contested (user expectation vs current output)
- Scope: mysteries
- Failure pattern: Clue framed as the question
- Session / run: Session 001 across many runs from 2026-10-19 to 2026-10-26
- Source: SRC-12 (2026-10-19T22:24Z) and SRC-32 (2026-10-25T04:00Z)

**The golden** (verbatim, Session 001 and Session 002 goldens, user-authored):
> Where and what is the treasure?

**Generated texts** (verbatim):
- 2026-10-25T03:26Z (`-hz_3mg9a`): "Which of the locations marked on the party's treasure map holds the treasure?", classified `closed_ended` and filtered out.
- 2026-10-26T20:19Z (`mysteries-brandonsford-001-_psx_7q7`, the latest): "Where is the treasure marked on the party's map?", with investigative depth `low` ("Mostly a matter of identifying a location") and narrative payoff `low` ("Finding it would be valuable to the party, but mainly in practical terms"). Filtered out.

**User's reactions** (verbatim):
- 2026-10-19: "why do you think we are having such problem with the treasure?  It seems to be central to the adventure"
- 2026-10-25: "Where did the feature mystery go? Do a diagnostic analysis" (the treasure had been dropped by the closed-ended filter)

**Why it matters:**
- The generated question narrows the real unknown (where *and what* the treasure is) to which map mark is right.
- The 2026-10-19 diagnosis: "a failure to distinguish the **underlying question from its clues**."
- Under the user's 2026-10-25 definition, a location wanted for a Goal scores low payoff because it is "primarily instrumental". So the current filter removes a question the golden keeps.

**Spot it:** is the question the underlying unknown, or one clue that bears on it? Keep "where and what is X" rather than "which marked spot".

**Outcome:**
- Location questions were made `open_ended` (2026-10-25T04:06Z).
- **Not resolved.** No treasure Mystery is published for Session 001, in either st (2026-10-26) or pt (2026-10-28), while both goldens keep one. This is a known target gap between the goldens and the current definition.
**Links:** [PREF-003](../preferences.md#pref-003)

---

### EX-018 Local mysteries should end when the episode ends
- Verdict: bad (lifecycle)
- Scope: mysteries
- Failure pattern: Stale open question
- Session / run: Session 004, run `mysteries-brandonsford-004-aa1fksqk` (2026-10-25T23:40Z)
- Source: SRC-34 (2026-10-25T23:53Z). Assessment in `.cache/runs/diagnose-mysteries-tomb-20261025-165356/assessment.md`.

**The text** (verbatim):
> Who does the noblewoman statue guarding Sir Brandon's tomb depict?
> Who is the giant undead swordsman stalking the Barrow Mound, and why does he still walk?

**Context needed to judge it:** by Session 004 the party had finished the tomb expedition, taken the loot and left. The prompt then said: "Inactivity, declining to investigate, leaving a location, or losing a lead does not close it."

**User's reaction** (verbatim):
> I was expecting these to be marked obsolete one they left the barrow mound

**Why it is bad:** questions that only mattered within a finished episode stay open forever and clutter later sessions.

**Spot it:** has the episode that made this question matter concluded, with the party disengaged and no evidence carrying it forward?

**Outcome:** an episode-ending rule was added. In the next review both tomb Mysteries "were marked **obsolete in all three Session 004 runs** and filtered out as intended." Kept.
**Links:** [PREF-013](../preferences.md#pref-013)

**General pattern (2026-11-01, SRC-58):** [PREF-051](../preferences.md#pref-051).

---

### EX-019 Golden Mysteries: bare questions about underlying truths
- Verdict: good
- Scope: mysteries
- Session / run: Session 002 golden (`artifacts/session_002/golden/campaign-matters.md`), user-authored
- Source: SRC-01 and R-01

**The text** (verbatim):
> - Where and what is the treasure?
> - How is this dragon related to the one Sir Brandon was supposed to have killed?
> - What is going on with the fairies?
> - What happened to Gill's sons?
> - Why does Warwick fill his smithy with lucky charms?
> - Why have supply shipments stopped?

**Why it is good:**
- Each is one short question with no clues or relevance attached in the text.
- Doubt sits on what the plot rests on ("supposed to have killed").
- Situations that went quiet (Gill's sons, the shipments) are included.

**Spot it:** one bare question, ten words or so, about an underlying truth.

**Outcome:** the Gill's sons question is absent from all current outputs (st 2026-10-26, pt 2026-10-28), and so is the treasure question (EX-017). The st Session 001 output reads close to this style: "Who or what is emptying Quinn's stock at the Golden Egg every night?" and "Why have shipments stopped arriving in Brandonsford?"
**Links:** [PREF-003](../preferences.md#pref-003)

**Gill’s sons eligibility clarification (2026-11-01, SRC-60; supersedes the older golden’s inclusion expectation for this evidence):** the agent presented “What happened to Gill’s sons?” and recommended allowing its omission because the known expedition does not establish a mysterious disappearance or unexplained event; its outcome is ordinary uncertainty. The user replied, verbatim: “Agreed”. Keep the golden as historical evidence of wording, but do not require this question on the current evidence. New evidence of an unexplained disappearance or another meaningful hidden truth could justify reassessment. This judgment is separate from the rejected Brewing Trouble (EX-045): a mystery does not require danger. Withdraw the sons-omission portion of SE-015’s pass 12 advisory; its treasure wording concern is separately recorded as minor under EX-017. No prompt or output changes.


---

### EX-020 Testbed calibration: include vs exclude
- Verdict: good (graded judgements the user approved)
- Scope: mysteries
- Source: SRC-34 (2026-10-25T21:57Z–22:06Z); R-06

**Include** (verbatim, case B01):
> Session evidence: Three villagers were murdered in locked rooms. Each held the same black flower, which does not grow locally. The killer remains unknown.
> Candidate: Who is murdering the villagers, and what connects the victims?

Graded: "include — Repeated murders and a shared anomalous clue establish a hidden connection." All four dimensions `high`.

**Exclude** (verbatim, case D02):
> Session evidence: The party enters an abandoned temple, defeats a giant spider, and collects coins. The temple's abandonment is not discussed.
> Candidate: What terrible secret caused the temple's abandonment?

Graded: "exclude — Abandonment alone does not establish a terrible secret." Narrative payoff `trivial`: "The proposed significance comes entirely from the wording."

**User's reaction** (verbatim):
> ok, your judgement on those was more or less perfect

**Why it is useful:** a fictional, labelled set the user accepted. The graded results matched a simple deterministic rule exactly ([APP-011](../approaches.md#app-011)).

**Spot it:** an evocative title must not raise the scores. Grade from the evidence, as in D02.
**Links:** [PREF-003](../preferences.md#pref-003), [APP-011](../approaches.md#app-011)

---

## Unjudged observations

These come from current outputs the user has not reviewed. They are candidates for review, not examples.

- Session 001 publishes both "Who or what is emptying Quinn's stock at the Golden Egg every night?" and "What is the Clurichen doing on its nightly visits into town?" (st). The pt deployment has the same pair. In Session 002 the Clurichen turns out to be the thief, so these may be one unknown counted twice.

---

### EX-062 Session 001's Mysteries under the unified pipeline
- Verdict: good
- Scope: mysteries
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`); each open-ended, with all four dimensions medium or higher
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim "Still unanswered"):
> - What empties Quinn's stock every night?
> - What happened to the shipments that stopped reaching Brandonsford?
> - Where did the black dragon come from?

**Context needed to judge it:** hidden by the filter in the same run:
- "Where are the locations marked on the party's treasure map, and which one holds the treasure?" (depth and payoff low);
- "What does the Clurichen do when it comes into town each night?" (payoff low);
- "Where does the black dragon lair?" (grounding, depth and payoff low);
- "Why is Warwick growing more paranoid and covering his shop with lucky charms and clovers?" (payoff low).

The user did not comment on the hidden ones.

**User's reaction** (verbatim):
> Mysteries: this is good

**Why it is good:** bare questions of about ten words, each about an underlying truth, with no clue attached (EX-019's style).

**Spot it:** one bare question about an underlying truth; no clue, source or background.

**Outcome:** the target for Session 001.
**Links:** [PREF-003](../preferences.md#pref-003), [EX-019](#ex-019-golden-mysteries-bare-questions-about-underlying-truths)

---

### EX-068 An intentional table revelation can settle an unknown
- Verdict: good (unified approach preferred); bad (requiring a separate in-character discovery after an intentional table revelation).
- Scope: mysteries, learned beats, revelations, unified `unknown` resolution.
- Definition in force: production versus unified pass 6, reviewed 2026-10-31. This is a hypothetical input and predicted behavior, not output from a generation run.
- Source: SRC-57 (current conversation; user preference stated 2026-10-31).

**Illustrative input** (verbatim):
> The characters are investigating who poisoned the mayor. In a cutaway narrated only to the players, the GM reveals that the mayor’s steward prepared the poison. None of the characters witnesses this or receives the information.

**Predictions, not generated output:** production explicitly preserves the characters' Mystery and may separately publish the player-facing Revelation. Unified may record the intentional disclosure as a learned beat, end the `unknown` as answered and remove it from Still unanswered. The agent recommended production's character-knowledge boundary; the user rejected that recommendation.

**User's preference** (verbatim; numbered response 4):
> I prefer the unified approach - information revealed at the table, if not an accidental slip, is established fact in the fiction and can be included.  (not your recomendation)

**Decision:** intentional information revealed at the table is eligible established fictional information even without an in-character witness. An intentional authoritative revelation can settle the unknown; do not require a second in-character discovery. An accidental slip is excluded from this preference. This does not convert an NPC's accusation, a player's guess or an uncertain claim into established truth, nor does it authorize inventing knowledge-transfer events for characters.

**Spot it:** is a resolved unknown being kept open solely because characters did not witness an intentional table revelation? Was the disclosure intentional and authoritative, or an accidental slip or merely an attributed claim?

**Future handling:** keep the unified approach; do not introduce the agent's proposed character-knowledge restriction. Preserve evidence, attribution and uncertainty, and exclude accidental slips. No pipeline changes or generation runs were made.
**Links:** [PREF-043](../preferences.md#pref-043), [PREF-003](../preferences.md#pref-003), [APP-034](../approaches.md#app-034).

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.


**EX-017 pass 12 wording/severity clarification (2026-11-01, SRC-60):** both Session Summaries ask, verbatim: “Where are the treasure map's marked locations, and which holds the treasure?” The agent recommended “Where and what is the treasure?” to express the underlying unknown rather than its clue, explicitly declining to treat word count alone as a meaningful problem in this case. The user replied, verbatim: “Your recommendation is certainly my preference, but again, another minor issue.” Verdict: underlying-question wording preferred; this occurrence is minor. This does not reject the question’s eligibility under the approved adventure-objective path. No prompt or output changes.
