# Revelations Examples

Concrete good, bad, borderline and missing Revelations, each with the context needed to judge it. Conventions and the entry template are in [README.md](../README.md). Run folders named here are under `~/data/tablesage_summary_test/.cache/runs/`. Each preserves the exact prompt, input and provider response for that generation.

The definition changed on 2026-10-25 (see [PREF-005](../preferences.md#pref-005)). Examples before that date were judged against the earlier, broader definition; each one says which definition applies.

---

### EX-001 Supply problem restated as mystery progress
- Verdict: bad
- Scope: revelations
- Failure pattern: Restates the problem
- Definition in force: retrospective (2026-10-25)
- Session / run: Brandonsford Session 001, unfiltered validation run 2
- Source: SRC-33 (2026-10-25T17:37Z). The item is verbatim in `.cache/runs/diagnose-supply-scope-001-_7gh05cw/diagnostic/user.md`.

**The text** (verbatim):
> Brandonsford's supply problem is broader than one late shipment: Farmer Gill says nothing has come into town in months, and Quinn says no real shipments have arrived in a while.

**Context needed to judge it:** classified as `inclusion_basis: mystery_progress`, progress `limited`, impact `low`, evidentiary strength `medium`. The linked Mystery is "What happened to the supply shipment that never reached Brandonsford?" Runs 1 and 3 omitted the item from identical inputs. An earlier run (`revelations-brandonsford-001-azxe8ktd`, 2026-10-25T04:45Z) produced a variant that invents a contradiction between compatible accounts:
> Accounts of the supply problem don't match. Bentley says a single shipment is a week overdue, while Farmer Gill and Quinn say nothing has reached town in months. This suggests the disruption is older and wider than one lost delivery.

**User's reaction** (verbatim):
> the supply disruption is more then one large shipment

Earlier in the same thread (2026-10-25T04:49Z): "my feeling is that all of these represent way too little progress towards resolving the mystery to count as a revelation".

**Why it is bad:** it enlarges the problem without reducing any uncertainty about what happened to the shipment.

**Spot it:** name the specific uncertainty this finding reduces. If the answer is only *how big, how long or how often the problem is*, it is not progress.

**Outcome:** see [APP-001](../approaches.md#app-001). A prompt clarification did not keep it out; the progress threshold in code does.
**Links:** [APP-001](../approaches.md#app-001)

---

### EX-004 A possible culprit that nothing connects to the crime
- Verdict: borderline, leaning bad
- Scope: revelations
- Failure pattern: Extractor supplies the connection
- Definition in force: retrospective
- Session / run: Session 001, run `revelations-brandonsford-001-u63yrall` (2026-10-25T04:45Z). The finding recurs in almost every later Session 001 run.
- Source: SRC-33 (2026-10-25T04:49Z). Diagnosis in `.cache/runs/diagnose-revelations-001-hg2jlk_s/diagnostic/analysis.md`, finding 1.

**The text** (verbatim):
> Reginald the Frog warns that every night a small trickster creature called a Clurichen comes up from the riverbank into town, up to no good, and that people should stay away from wherever it goes. The town's thief could be someone other than a rival innkeeper.

**Context needed to judge it:** the Mystery is who drinks Quinn's ale at the Golden Egg each night. The source reports nightly visits to town but nothing about ale, Quinn or the tavern. Later runs hedge the same link: "though nothing yet ties the creature to Quinn's cellar" (`-lu2lkyjz`). In Session 002 the Clurichen did turn out to be the thief.

**User's reaction** (verbatim, about all six findings in the run):
> my feeling is that all of these represent way to little progress towards resolving the mystery

**Why it is borderline:** the diagnosis called it "a plausible but weak association, not a demonstrated advance on the culprit question. … The extractor supplied that connection." It was in fact a real clue.

**Spot it:** does the scene evidence itself tie the finding to the question, or does the entry's second sentence make the tie?

**Outcome:** under the final filters it is rated `limited` and excluded. The hedged variant is a useful test case: a true clue that the evidence alone does not yet connect.
**Links:** —

---

### EX-005 Restating the premise of a Mystery
- Verdict: bad
- Scope: revelations
- Failure pattern: Restates the problem
- Definition in force: retrospective
- Session / run: Session 001, run `revelations-brandonsford-001-azxe8ktd` (2026-10-25T04:45Z)
- Source: SRC-33. Diagnosis in `diagnose-revelations-001-hg2jlk_s/diagnostic/analysis.md`, finding 4.

**The text** (verbatim):
> Farmer Gill insists Sir Brandon's dragon was definitely killed centuries ago, dragged through town and ripped apart, so he assumes the black dragon now around Brandonsford is a different one. He doesn't know where it came from.

**Context needed to judge it:** the old dragon's death is the explicit premise of the supplied Mystery, which asks where this dragon came from, and Bentley had already said it. Run `-lu2lkyjz` hardens Gill's assumption into "must be a different creature", which the source does not say.

**User's reaction:** the same six-finding reaction quoted in EX-004.

**Why it is bad:** it confirms the setup of the question and does nothing to answer it.

**Spot it:** if this fact already appears in the Mystery's own `basis`, it is setup, not progress.

**Outcome:** excluded by the final `substantial`/`resolved` threshold.
**Links:** —

---

### EX-006 A player character corrected with general knowledge
- Verdict: bad
- Scope: revelations
- Failure pattern: Revelation from table talk
- Definition in force: retrospective
- Session / run: Session 001, run `revelations-brandonsford-001-5s943368` (2026-10-26T01:16Z), rated `mystery_progress: trivial`, impact `low`
- Source: SRC-35 (2026-10-26T01:31Z). Diagnosis in `diagnose-revelations-001-pc-correction-evedwmy_/`.

**The text** (verbatim):
> Black Dragons Are Real, Undercutting Sir Phidipaldi's Claim That the Dragon Is a Clurichen Illusion

**Context needed to judge it:** the Scene Log says Phidipaldi's claims were wrong and that Uriah and Eric "both knew it." No new discovery and no knowledge-check result were recorded. An earlier run (`-xwo4tb1g`) rated the same finding `limited`, impact `medium`.

**User's reaction** (verbatim):
> i just dont think a revelation can come from a pc, or from another pc correcting them

**Why it is bad:** a mistaken assertion followed by a rebuttal from already-held lore adds no new knowledge to the world.

**Spot it:** what new information did the session's evidence supply? If the only "news" is that one character was wrong and another already knew, exclude it. A PC *reporting* a real discovery still counts.

**Outcome:** a rule was added on 2026-10-26 and is kept in both repos: "A player character's assertion, speculation, or correction of another character using already-held general knowledge does not by itself qualify as a Revelation." (`revelations/system.md:67`)
**Links:** [PREF-008](../preferences.md#pref-008)

---

### EX-007 A secondhand account that sets up the Mystery
- Verdict: bad
- Scope: revelations
- Failure pattern: Restates the problem
- Definition in force: retrospective
- Session / run: Session 001, run `revelations-brandonsford-001-g7z2eeiq` (2026-10-26T01:16Z), rated `limited`, impact `medium`, unexpectedness `medium`
- Source: SRC-35 (2026-10-26T01:26Z). Diagnosis in `diagnose-revelations-001-george-3qveclp6/`.

**The text** (verbatim):
> Woodsman George's Account Describes a Small Black Dragon That Tore Off His Arm

**Context needed to judge it:** Eric relays George's story. The supplied Mystery asks what the dragon is and how one returned after the earlier dragon's death. The injury does not separate a real dragon from the proposed Clurichen explanation, which also covers limb theft.

**User's reaction:** the user asked for a diagnosis of this entry by name. Minutes later they set the filter to exclude `limited` progress (2026-10-26T01:35Z).

**Why it is bad:** in the diagnosis's words, "these details may establish the puzzle without meaningfully narrowing its answer."

**Spot it:** same check as EX-005. The account is part of how the party learned about the dragon, not an answer to where it came from.

**Outcome:** excluded by the `limited` threshold.
**Links:** [APP-001](../approaches.md#app-001)

---

### EX-008 Missing: Brandon's sword can be retrieved
- Verdict: missing (the user expected an entry)
- Scope: revelations
- Failure pattern: Expected finding absent
- Definition in force: retrospective
- Session / run: Session 002, published run 3
- Source: SRC-33 (2026-10-25T17:18Z). Diagnosis in `diagnose-sword-retrievability-002-43jd4f2v/`.

**The expected text:** not generated, so nothing to quote. The user's description:
> why don't we get a row for the revelation that Brandon's sword is retrievable?

**Context needed to judge it:** the model folded the burial location into the dragon reframing and produced no separate row. No supplied Mystery asks where the sword is. Opportunities did contain "Travel to the Barrow Mound and retrieve the sword."

**Why it matters:** the diagnosis concluded that the definition exposes a choice: "should discovering that a historical or legendary resource can now be sought count as a reframing of what is possible?"

**Spot it:** a legendary, presumed-lost resource that becomes reachable this session should appear as a reframing.

**Outcome:** no decision was recorded, so the question is still open.
**Links:** [PREF-005](../preferences.md#pref-005)

---

### EX-009 Case file instead of notecard
- Verdict: bad
- Scope: revelations
- Failure pattern: Dossier entry
- Definition in force: pre-2026-10-25 (golden era)
- Session / run: Session 002 combined Campaign Matters output, 2026-10-17. Preserved in T3 checkpoint commit `e30088fe` of `~/data/tablesage_summary_test`.
- Source: SRC-03 (2026-10-18T20:04Z)

**The text** (verbatim):
> The thief drinking Quinn's ale at the Golden Egg is Naggeneen, a clurichen who calls himself a good-luck spirit and says he just likes to drink and has a problem. It wasn't Bentley. Naggeneen crosses the river at night with a corked jug and can turn invisible, though his footprints still show. He is now tied up in a bag hanging behind the Golden Egg's bar. This solves who was drinking Quinn's ale.

**Context needed to judge it:** the user's handmade golden line for the same knowledge (`artifacts/session_002/golden/campaign-matters.md`):
> Naggeneen the clurichen was the one stealing booze from the Golden Egg.

**User's reaction:** the user wrote the golden by hand as the target: "My goal here is for us to make a golden master that is what we strive for." (SRC-01). The notecard-versus-case-file comparison is the assistant's characterization (SRC-03, 2026-10-18T19:18Z). The user did not comment on it directly but continued optimizing toward the golden.

**Why it is bad:** it bundles identity, self-description, a rejected guess, habits, powers, current state ("tied up in a bag") and mystery bookkeeping ("This solves…") into one entry of about 70 words. The golden line has 11.

**Spot it:** one point per entry. Delete anything that is current state, how it was learned, a wrong guess, or bookkeeping about which Mystery it answers.

**Outcome:**
- The notecard length was later replaced by the headline style ([PREF-002](../preferences.md#pref-002)).
- The current prompt removes "incidental precision, background, acquisition history" (`revelations/system.md:83`).
- Bookkeeping now lives in separate classification fields instead of the text.
**Links:** [PREF-007](../preferences.md#pref-007), [PREF-002](../preferences.md#pref-002)

---

### EX-010 Conflicting accounts accepted into the golden
- Verdict: good
- Scope: revelations
- Definition in force: pre-2026-10-25
- Session / run: Session 002 golden, added 2026-10-20
- Source: SRC-17 (2026-10-20T23:55Z); `.work-items/optimize-revelations/evaluations.md`, "Accepted follow-up after Run 8"

**The text** (verbatim, golden):
> Father William claims Ingrid can't make her own potions. Ingrid insists she makes all her wares herself.

**Context needed to judge it:** it was not in the original golden. The reviewer argued that the disagreement affects whether the party can rely on Ingrid's potion. The user accepted it ("can you add ingrid to the golden now that we have admitted it as a discover?").

**Why it is good:** two short attributed claims that stay uncertain. It matters because the party's plan depends on the potion.

**Spot it:** when accounts conflict about something the party is relying on, keep both claims and credit each, rather than choosing one.

**Outcome:** kept in the Session 002 golden. Under the retrospective definition it would need a supplied Opportunity or Mystery to reframe.
**Links:** [PREF-009](../preferences.md#pref-009)

---

### EX-011 Useful location, approved then excluded
- Verdict: good under the 2026-10-18 definition; excluded under the 2026-10-25 definition
- Scope: revelations
- Definition in force: both (shows the change)
- Session / run: Session 002 golden
- Source: SRC-03 (2026-10-18T20:45Z) and SRC-33 (2026-10-25T04:23Z)

**The text** (verbatim, golden):
> The dragon's lair is north at the foot of the mountains.

**User's reactions** (verbatim):
- 2026-10-18: "black dragon location: this is great"
- 2026-10-25: "Q1, a - no unless the location was a mystery or a reframing (they believed it was in a different place previously,)"

**Why it matters:** the same item flips verdict when the definition changes. The current prompt uses it as its exclusion example: "The party wants to kill the dragon and learns its lair's location, when no supplied Mystery concerns its location and no earlier location belief is corrected. Usefulness to the Goal alone is insufficient." (`revelations/system.md:73`).

**Spot it:** useful knowledge for pursuing a Goal is not a Revelation unless it answers a Mystery or corrects an earlier belief.

**Outcome:** the Session 002 golden still holds this line, so the golden now disagrees with the current definition. This is a known target gap.
**Links:** [PREF-005](../preferences.md#pref-005)

---

### EX-012 Something the party lived through, not learned
- Verdict: bad (tentative)
- Scope: revelations
- Failure pattern: Witnessed event recast as knowledge
- Definition in force: pre-2026-10-25
- Session / run: Session 002 proposal test against the frozen Scene Log
- Source: SRC-03 (2026-10-18T20:45Z–20:51Z)

**The text:** not recovered as a Revelation. The candidate was the giant's slowness, quoted from the Scene Log event: "The slow giant chased everyone across the field until he tired."

**User's reaction** (verbatim):
> The giant moves very slowly -this feels off but i am now sure why?  Is it already expected?  I don't think its problematic, but my spidey sense tingles a little

**Why it is bad:** the assistant's diagnosis was "the party didn't learn it, they lived it". The event already shows it, so restating it as knowledge adds nothing.

**Spot it:** if the knowledge is just what visibly happened in a scene, it belongs in the Scene Log, not Revelations.

**Outcome:** the proposed exclusion ("knowledge the party gained only by witnessing it firsthand, when the event itself shows it, isn't a revelation") was recorded as an open question. Run 8 noted that "giant slowness still conflicts with its saved exclusion". The rule is **not in the current prompt** in either repo.
**Links:** —

---

### EX-013 Paragraph to headline
- Verdict: good on headline structure. The casing was superseded on 2026-10-28: the "after" text is title case, which the user later rejected in favour of sentence case.
- Scope: revelations
- Definition in force: retrospective
- Session / run: Session 001. Before: run `revelations-brandonsford-001-kcpsrpnn` (2026-10-25T17:44Z). After: run `revelations-brandonsford-001-35ig4ayr` (2026-10-25T18:25Z).
- Source: SRC-33 (2026-10-25T18:11Z)

**Before** (verbatim):
> Farmer Gill suspects that Warwick's growing collection of lucky charms is meant to keep away Ingrid, the potion seller, who is hot for him.

**After** (verbatim):
> Farmer Gill Suspects Warwick's Growing Wall of Charms Is Meant to Ward Off Admirer Ingrid

**User's reactions** (verbatim):
- 2026-10-25: "I want the description to read like a new York times newspaper headline. No exclamation marks."
- 2026-10-27, in the port: "…headline style formatting, which is great, but they keep dropping articles and other small words to create that compressed, slightly harder to read headline."
- 2026-10-28, in the port: "I think it might be title cased and not sentence cased."

**Why it is good:** one restrained, attributed, specific headline. Later preferences refine it: keep the small words, and use sentence case.

**Spot it:** headline, no exclamation mark, sentence case, articles kept, attribution kept for suspicions.

**Outcome:** see [PREF-002](../preferences.md#pref-002). The two repos differ on casing.
**Links:** [PREF-002](../preferences.md#pref-002)

Related review decision: [EX-068](mysteries.md#ex-068-an-intentional-table-revelation-can-settle-an-unknown) accepts intentional authoritative table revelations even without an in-character witness; accidental slips are excluded (SRC-57, 2026-10-31).
