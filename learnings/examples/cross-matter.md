# Cross-Matter Examples

Duplication and misplacement across categories. Conventions are in [README.md](../README.md).

Most bad examples here come from the Brandonsford regeneration in the port's deployment workspace (`~/proj/tablesage/deployment/campaigns/Brandonsford/00N/`, 2026-10-28 21:29–21:46). They were recorded verbatim in the duplication analysis (`~/proj/tablesage/.work-items/reduce-session-matters-duplication/analysis.md`, SRC-53). The user directed that analysis and filed its patterns P1–P6 as work items. The text quoted is the Session Summary bullet the reader sees.

**How the user came to see duplication (2026-10-29, SRC-55):** overlap between "what happened" and "what's ahead" is legitimate but still costs the reader. See [PREF-015](../preferences.md#pref-015). The pattern-specific fixes were then superseded by a redesigned pipeline ([APP-034](../approaches.md#app-034)), which is in progress.

---

### EX-003 Open bargain restated across categories (Quinn)
- Verdict: bad
- Scope: cross-matter (developments, goals, opportunities)
- Failure pattern: Open bargain restated (P6, also P1 and P2)
- Session / run: Session 001, pt deployment output of 2026-10-28
- Source: SRC-53, SRC-55; `pt/.work-items/matters-dup-open-bargain/intent.md`

**The text** (verbatim Summary bullets):
> Development: "Sir Phidipaldi agreed to help Quinn get back at Bentley for 100 gold by staging a fake ale shipment."
> Goal: "Help Quinn get back at Bentley for 100 gold."
> Opportunity: "Quinn will bring bottles for a fake ale shipment. If Sir Phidipaldi fills them with water and makes a show of delivering them, they could see who takes Quinn's ale."

**Context needed to judge it:** the Mystery in the same Summary, "Who or what empties Quinn's ale at the Golden Egg every night?", is distinct and should stay. Completed events such as catching Naggeneen appear only once.

**User's reaction** (verbatim, about this bargain and the Ingrid and Warwick ones):
> I mean the overlap is legitimate.  This does not mean the duplication isn't a cost, but that there are good reasons to keep in both Developments and at least one Open Matters.  So in a way i am saying that it is both a problem and not a problem, if that makes sense.

**Why it is bad:** the reader meets the same unfinished deal under "Last session...", "Your goals" and "What could help". The Goal adds nothing to the Development.

**Spot it:** for each unresolved two-sided deal in Developments, does another category restate the *whole deal* in its title, rather than only its own side (the task, the price, a way to carry it out)?

**Outcome:** filed as P6, then closed on 2026-10-29 as superseded by [APP-034](../approaches.md#app-034).
**Links:** [PREF-004](../preferences.md#pref-004), [PREF-015](../preferences.md#pref-015)

---

### EX-024 Open bargain restated across categories (Warwick)
- Verdict: bad (mixed: some entries add distinct facts)
- Scope: cross-matter (developments, goals, new-assets, opportunities, obligations, goal-impediments)
- Failure pattern: Open bargain restated (P6)
- Session / run: Session 004, pt deployment output of 2026-10-28
- Source: SRC-53 (worst offender #2)

**The text** (verbatim Summary bullets, with the analysis's relationship notes):
> Development: "The party promised to bring Warwick metal from the Dwarven mine in return for his mithril shirt." (original)
> Goal: "Bring metal from the Dwarven mine back to Warwick the smith." (restates the Development)
> New Asset: "Warwick's mithril chain shirt, lent to the party." (partial: adds that it is a loan)
> Opportunity: "The cave-in at the Dwarven mine looks diggable. If the party digs through it, they could reach metal for Warwick." (partial: mirrors the Impediment)
> Obligation: "The party must return Warwick's borrowed mithril chain shirt." (distinct: the price side)
> Goal Impediment: "A cave-in seals the Dwarven mine entrance. It blocks the party from bringing metal back to Warwick." (distinct)

**Why it is bad:** seven bullets for one deal. The Obligation and Impediment earn their place; the Goal and Opportunity mostly repeat.

**Spot it:** mark each bullet in a cluster as original, restates or distinct. A cluster with more than one "restates" is the failure.

**Outcome:** as EX-003.
**Links:** [PREF-004](../preferences.md#pref-004)

---

### EX-021 One threat spread across every threat category
- Verdict: bad
- Scope: cross-matter (developments, present-matters, goal-impediments, brewing-troubles, mysteries)
- Failure pattern: Threat spread (P4)
- Session / run: Session 003, pt deployment output of 2026-10-28
- Source: SRC-53 (worst offender #1)

**The text** (verbatim Summary bullets):
> Development: "A huge undead skeleton with a greatsword blocked the doorway of Sir Brandon's tomb."
> Present Danger: "A seven-foot brown skeleton in rusted armor and a mustachioed death mask stands in the tomb's doorway, dragging a huge greatsword…"
> Goal Impediment: "A huge undead skeleton with a greatsword roams the Barrow Mound. It stands in the way of clearing the mound's evil for the goblins."
> Brewing Trouble: "The huge undead skeleton in the tomb doorway may attack the party."
> Brewing Trouble: "The undead skeleton may kill more Free Goblin Society members in the Barrow Mound."
> Mystery: "Why does a huge undead figure with a greatsword roam the Barrow Mound?"

**Context needed to judge it:** the skeleton was standing in the doorway when play stopped, so it qualified for every forward-looking threat category. The analysis rates the Mystery distinct, though see EX-002 for the user's view of this Mystery. Two Brewing Troubles also split one threat within a single category.

**User's reaction** (verbatim, from SRC-51, which led to the analysis):
> some kind of developments seem to show up in many part session matters, and they don't seem to add any extra information. They are just things that could apply in multiple matters, so the llm phrases it in ways appropriate for different matters and they die up all the place.

**Why it is bad:** six bullets about one creature, four of which say "there is a dangerous skeleton".

**Spot it:** a threat that is live at the end of the session should appear once as danger. Other categories may add only a distinct link, such as which Goal it blocks.

**Outcome:** P4, superseded by APP-034. The user had already accepted Present Matters repeating other items ([PREF-017](../preferences.md#pref-017)).
**Links:** [PREF-004](../preferences.md#pref-004)

---

### EX-022 One promise as a Development and two Obligations
- Verdict: bad
- Scope: cross-matter (developments, obligations)
- Failure pattern: Commitment restated (P1), plus a split within one category
- Session / run: Session 002, pt deployment output of 2026-10-28
- Source: SRC-53 (worst offender #4)

**The text** (verbatim Summary bullets):
> Development: "Dr. Uriah promised Father William to do penance at the Barrow Mound and to donate 10 gold for its upkeep."
> Obligation: "Dr. Uriah must give penance at the Barrow Mound for Father William"
> Obligation: "Dr. Uriah must give Father William a 10 gold donation for the Barrow Mound's upkeep."

**Context needed to judge it:** both Obligations were still listed after the party had gone to the Barrow Mound, so they are stale as well as duplicated.

**Why it is bad:** together, the two Obligations restate the single Development and add nothing to it.

**Spot it:** do the Obligation titles together say anything the Development does not?

**Outcome:** P1, superseded by APP-034. Whether splits within one category are in scope was left unresolved.
**Links:** [PREF-004](../preferences.md#pref-004)

---

### EX-023 A Revelation repeated as a Goal Impediment
- Verdict: bad
- Scope: cross-matter (revelations, goal-impediments)
- Failure pattern: Revelation restated as Impediment (P3)
- Session / run: Session 002, pt deployment output of 2026-10-28
- Source: SRC-53 (worst offender #5)

**The text** (verbatim Summary bullets):
> Revelation: "George says arrows and swords cannot pierce the dragon's scales, and one poisonous bite kills."
> Goal Impediment: "George says nothing pierces the black dragon's scales. Arrows and swords have all failed against them."

**Why it is bad:** a near-verbatim restatement. The Impediment does not even name the Goal it blocks, which is the one thing it could add.

**Spot it:** if an Impediment's title could be swapped with a Revelation's, one of them is redundant. An Impediment should say what it blocks.

**Outcome:** P3, superseded by APP-034.
**Links:** [PREF-004](../preferences.md#pref-004)

---

### EX-025 Shared subject, distinct content
- Verdict: good
- Scope: cross-matter
- Session / run: Session 002, pt deployment output of 2026-10-28 (files in `deployment/campaigns/Brandonsford/002/`)
- Source: SRC-53, "Overlaps judged distinct"

**The text** (verbatim item titles):
> Development: "The party caught Naggeneen the Clurichen and handed him over to Quinn, who hung him in a bag behind the Golden Egg's bar"
> Revelation: "Naggeneen, the invisible Clurichen from the river, is the nightly thief drinking Quinn's ale. Bentley was not the culprit"

> New Asset: "Squints the halfling recruit"
> Obligation: "The party must let Squints pick second from the first treasure, after the elite members"

**Why it is good:** each pair shares a subject but carries different information. The first pair is an event and a fact; the second is a gain and a price. Removing either half loses something.

**Spot it:** state what each entry adds that the other lacks. If both answers are non-empty, the overlap is legitimate.
**Links:** [PREF-004](../preferences.md#pref-004), [PREF-015](../preferences.md#pref-015)

---

### EX-026 The user's own golden: one subject, several angles
- Verdict: good
- Scope: cross-matter
- Session / run: Session 002 golden (`st/artifacts/session_002/golden/campaign-matters.md`), user-authored
- Source: SRC-01, R-01

**The text** (verbatim golden lines about the dragon):
> Goal: "Kill the dragon and collect your 1,000 gold."
> Mystery: "How is this dragon related to the one Sir Brandon was supposed to have killed?"
> Threat: "The dragon will soon be able to fly."
> Revelation: "The dragon can't be killed without Sir Brandon's sword."
> Opportunity: "If you get Sir Brandon's sword, it can help slay the dragon."
> Opportunity: "If you steal Warwick's mithril chain shirt, it will protect you against the dragon."

**Why it is good:** the dragon appears in five categories, but each line says something different: what you want, what you don't know, what is getting worse, what you learned, and what you could do. Each line is short.

**Context:** the closest pair is the sword Revelation and the sword Opportunity. The user kept both deliberately: the knowledge and the action.

**Spot it:** the same subject across categories is fine when each entry answers that category's question and nothing more.
**Links:** [PREF-004](../preferences.md#pref-004)

---

### EX-056 Quinn's bargain under the unified definitions: no goal, and two non-debts as debts
- Verdict: bad (plus one missing entry)
- Scope: cross-matter (goals, obligations, opportunities)
- Failure pattern: Owed to the party listed as a debt; Plan recorded as a promise; Missing goal for a bargain's outcome
- Definition in force: unified pipeline (APP-034). Step 3 says "A task the party agreed to perform in exchange for something is `owe`, not `want`, even when the party also benefits from it."
- Session / run: Brandonsford Session 001, pass 4, 2026-10-30 (`pass-4/runs/s001/summary.md`; facts `fact_19`, `fact_20` and `fact_21` on the "Quinn's deal against Bentley" thread)
- Source: SRC-55 (2026-10-30)

**The text** (verbatim "Promises and debts" bullets):
> Quinn will pay Sir Phidipaldi 100 gold for helping him get back at Bentley.
> Sir Phidipaldi must stage a showy fake ale delivery of water-filled bottles at the Golden Egg with Quinn.

Under "Your goals": nothing about Quinn. Under "Still unanswered": "What empties or knocks over Quinn's stock every night?"

**Context needed to judge it:**
- `fact_19` was the party's `owe` ("Sir Phidipaldi agreed to help Quinn get back at Bentley…; Quinn promised him 100 gold for that help", `bargain`, stake `medium`). The writer phrased it from Quinn's side.
- `fact_20` was a second `owe` (`personal_promise`): the staged delivery.
- No `want` was written, because step 3 records a bargain's task as `owe`.

**User's reactions** (verbatim; "owl" is a dictation slip):
> there is no goal about catching quinns thief

> this is a section for the party making a Promise or owing a debt, not situations where somebody owes a debt or makes a promise to the party, which is what the first bullet is.

> The second bullet is also not a promise or a debt; it is actually an opportunity or a technique for uncovering who is stealing the owl [ale], which is a goal

**Why it is bad:**
- "Promises and debts" holds only what the party owes. Payment owed to the party is an asset or an opening (PREF-020's related quote).
- The staged delivery is a method toward catching the thief, so it is an opportunity.
- The user sees catching Quinn's thief as a goal. Under the unified rule, the bargain's task is only a debt.

**Tension:** in EX-003 the 2026-10-28 goal "Help Quinn get back at Bentley for 100 gold." was judged a restatement of the Development. The user's goal here is the outcome, catching the thief, not the deal. Whether a bargain's task can also be a goal when its outcome is wanted is unresolved under the unified definitions.

**Spot it:**
- Does every "Promises and debts" bullet say what the party owes someone? If it says what someone owes the party, it is misplaced.
- Is a plan or method listed as a promise? It belongs under "What could help".
- When the party has taken up a job, is its outcome stated as a goal?

**Outcome:** step 3 now treats a job paid on completion as a `want` with its reward, and an agreed method as a `could_use`; the writer keeps the party as the one who owes. In pass 5 (`pass-5/runs/s001/summary.md`, 2026-10-30; agent observation, not yet judged), "Promises and debts" is empty, and the delivery is "If Sir Phidipaldi makes a show of delivering Quinn's water-filled bottles to the Golden Egg, they can see what happens." The goal reads "Help Quinn get back at Bentley and collect his promised 100 gold." That is the deal's framing, close to EX-003's rejected goal, not catching the thief.
**Links:** [PREF-036](../preferences.md#pref-036), [PREF-020](../preferences.md#pref-020), [PREF-035](../preferences.md#pref-035), [EX-003](#ex-003-open-bargain-restated-across-categories-quinn)

---

### EX-066 Distinct resources must survive shared-thread deduplication
- Verdict: good (separate resources); bad (suppressing one merely because thread links match).
- Scope: cross-matter, opportunities, new-assets (`could_use`).
- Definition in force: production versus unified pass 6, reviewed 2026-10-31. This is a hypothetical input and predicted behavior, not output from a generation run.
- Source: SRC-57 (current conversation; user preference stated 2026-10-31).

**Illustrative input** (verbatim):
> The party wants to reach an island. Captain Sella gives them a coastal chart that adds little to their existing navigation knowledge. Separately, she offers passage aboard her boat for ten silver.

**Predictions, not generated output:** production could hide the low-support chart while keeping passage as an Opportunity. Unified should preserve the distinction too. Its conditional failure occurs if the chart is recorded on Sella's thread and passage is recorded elsewhere as a pointer to that thread: selection can hide passage because the home contains some open `could_use` for the same helped thread, without checking resource identity or whether the home fact is shown. Correct extraction placing both resources at home avoids this failure. No such failure was demonstrated by running this input.

**User's preference** (verbatim; numbered response 2):
> I prefer keeping these as seperate items, not combined (so closer to unfiied, but with changes you may recommend to increase the likelyhood of this. (i approve your recommendation)

**Decision:** the chart and passage are distinct facts and must remain separate records. Their publication eligibility is assessed independently; this does not require showing an otherwise ineligible chart or restating the same resource twice.

**Spot it:** do the two facts identify the same resource and advantage, or merely share a home/helped thread? Is a suppressed pointer's replacement actually selected and complete?

**Recommended future change:** identify the specific home fact/resource a pointer references; suppress only a proven duplicate whose selected home representation preserves its information. Preserve separate facts for distinct resources and evaluate each on its own. No implementation or regeneration; outcome pending.
**Links:** [PREF-041](../preferences.md#pref-041), [PREF-004](../preferences.md#pref-004), [APP-034](../approaches.md#app-034).

---

**Implementation follow-up (2026-10-31, SRC-57):** [pass 7](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-7/README.md) preserves separate shared resources and validates `resource_subject`. Selection suppresses a pointer only against a selected home fact matching resource subject, form, helped thread, full text and uncertainty. Direct checks confirm that unrelated/hidden home facts and differing conditions do not hide a passage pointer; exact selected duplicates can be suppressed. Matching full text is deliberately conservative, so equivalent paraphrases may remain. No new Session outputs or user quality verdicts exist.

### EX-067 A scene-local confrontation belongs in Immediate danger
- Verdict: good (immediate danger alone); bad (also publishing the same confrontation as a lasting impediment).
- Scope: cross-matter, goal-impediments, present-matters.
- Definition in force: production versus unified pass 6, reviewed 2026-10-31. This is a hypothetical input and predicted behavior, not output from a generation run.
- Source: SRC-57 (current conversation; user preference stated 2026-10-31).

**Illustrative input** (verbatim):
> The party is retrieving a stolen charter. At the end of the Session, a guard confronts them in the warehouse doorway with his sword drawn. This confrontation is the only established obstruction; there is no broader restriction on reaching the charter.

**Predictions, not generated output:** production should put the guard in Present Danger and exclude the scene-local impediment. Unified could extract both an active `blocked_by` and Immediate danger, and selection permits both: its danger-coverage suppression applies to `threat`, not `blocked_by`. A writer might reduce repetition but selection does not prevent it.

**User's preference** (verbatim; numbered response 3):
> I prefer production (i approve your recommendation)

**Decision:** publish this confrontation as Immediate danger alone, unless play establishes a distinct continuing obstruction. A published impediment must affect a live relevant pursuit. Supporting obligations and openings as well as wants need not be removed.

**Spot it:** does an impediment describe only the same immediate confrontation? Does the obstacle still obstruct a live relevant pursuit, and is there evidence of relevance beyond the scene?

**Recommended future change:** restore the lasting-relevance boundary and validate the live target of a published impediment. Assign an immediate confrontation to the current tier while preserving any distinct lasting obstacle as its own fact. No implementation or regeneration; outcome pending.
**Links:** [PREF-042](../preferences.md#pref-042), [PREF-034](../preferences.md#pref-034), [EX-021](#ex-021-one-threat-spread-across-four-categories), [APP-034](../approaches.md#app-034).

**Implementation follow-up (2026-10-31, SRC-57):** [pass 7](../../.work-items/unified-matters-pipeline/experiments/session-004/pass-7/README.md) adds explicit obstacle scope, live shown target validation, and stopping-situation coverage for `blocked_by`. Direct checks confirm that scene-local, covered, anticipated and stale-target obstacles stay hidden while distinct lasting obstacles to live wants, debts or openings survive. No LLM regeneration or new user output verdict has occurred.


## Unjudged Pass 7 Observations (2026-10-31, SRC-57)

The user requested generation for Sessions 001–004 after implementation. All four were freshly chained; no new output verdict has been supplied. These are actual outputs, not the hypothetical EX-065–EX-067 examples. Earlier user preferences remain unchanged.

In Session 001's `pass-7/runs/s001/summary.md`, What could help includes:

> If the party hires Lady Hilda, she will help them fight the dragon.
> If the party pays Lady Hilda, she will join them.

In Session 002's `pass-7/runs/s002/summary.md`, What could help includes:

> If the party pays Lady Hilda, she will fight the dragon alongside them.
> If the party hires Lady Hilda, they gain a seasoned fighter in chain mail with a shield.

It also includes:

> Father William says that if the party goes to Sir Brandon's Barrow Mound, they can retrieve the sword buried with him.
> If the party claims Sir Brandon's sword, they gain what is said to be the only way to kill the dragon.

Agent observation: paraphrased shared resources can remain under the conservative EX-066 implementation; it suppresses only matching complete content at an eligible home. These examples warrant user review for distinct useful information versus restatement. No additional prompt tuning or semantic filtering was applied during the run. See [exact review copies and notes](../../deployment/unified-review/12-PASS7/run-notes.md).

Pass 7 user review follow-up (SRC-57): [EX-073](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

## Unjudged Pass 9 Observation (2026-11-01, SRC-57)

Fresh Session 002, pass-9/runs/s002/summary.md, still includes potentially overlapping potion-plan openings:

> If Dunk helps Ingrid give Warwick her sleeping potion, Warwick should stay asleep while they are in his house. It may not work, since Dunk diluted the faun wine and Father William doubts Ingrid's skill.

> If Ingrid's sleeping potion keeps Warwick asleep, Dunk could take the mithril chain shirt.

Agent observation: this resembles EX-073's same-plan duplication, but these exact new representations have not received a user verdict. Pass 9 changes historical coverage only; open-matter filters/reconciliation were inherited unchanged. Source words and outputs were not manually edited. See [review notes](../../deployment/unified-review/14-PASS9/run-notes.md).
