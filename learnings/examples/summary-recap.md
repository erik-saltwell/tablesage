# Session Summary and Table Recap Examples

Presentation examples for the Session Summary (emailed ahead of time) and the Table Recap (read at the table). They share one file because on 2026-10-27 the user decided that the content then generated as the Table Recap worked better as the Session Summary (SRC-39, 2026-10-27T20:17Z). The rendered Summary now has a spoken Table Recap derived from it. Each entry says which artifact it concerns.

Most bad examples come from a GM-style review of the four Brandonsford `summary.md` files in the port's deployment workspace (SRC-44, 2026-10-28T17:20Z). The reviewer quoted those files, and the files have since been regenerated; the deployment folder is git-ignored. The quotes are as recorded in that review. The user answered each finding in turn (2026-10-28T17:44Z), so each example records that answer.

---

### EX-027 The same lines repeated every week
- Verdict: historically bad; superseded for still-open Summary matters by the 2026-11-01 clarification below
- Scope: summary
- Failure pattern: Unchanged items repeated
- Session / run: pt deployment `summary.md`, Sessions 001–004, generated 2026-10-27
- Source: SRC-44 (review finding 2)

**The text** (verbatim, as quoted in the review; "word-for-word the same in all four sessions"):
> "Farmer Gill's three sons are already hunting the dragon and could kill it before the party, denying them the bounty."
> "Where did the new dragon near Brandonsford come from, given that Sir Brandon's dragon was killed centuries ago?"
> "Why have shipments stopped reaching Brandonsford?"

**User's reaction** (verbatim): "2) file a work item for this"

**Why it is bad:** in the reviewer's words, "Hearing the same sentence every week is how players learn to tune out."

**Spot it:** compare with the previous session's Summary. A bullet that is unchanged and still open needs no full restatement.

**Outcome:** the items `summary-new-changed-ongoing` and `table-recap-new-changed-ongoing` were filed, then closed without implementation on 2026-10-28 at the user's direction.
**Links:** [PREF-021](../preferences.md#pref-021)

**Current clarification (2026-11-01, SRC-60; supersedes the cross-Session repetition objection for still-open matters):** during pass 12 review the agent noted that both Summaries repeat “Find the treasure marked on the party's treasure map” and “Why have shipments stopped reaching Brandonsford?” The agent recommended retaining relevant open matters unchanged, with no omission or cosmetic rewording merely to avoid repetition. The user replied, verbatim: “No I agree that as long as it remains open, it should continue to be here.”

**Current rule / Spot it:** retain otherwise eligible open matters in each Session Summary while they remain open; unchanged wording across Sessions is not itself a defect. Withdraw RC-019’s pass 12 advisory and retire its repetition-only objection in the next guide refresh. This does not excuse stale/resolved matters, duplication within one Summary, or independently ineligible candidates (such as the inferred danger/competition framing in EX-045). Preserve the earlier judgment as history. No prompt or output changes.

---

### EX-028 An obstacle left standing after the party found the answer
- Verdict: bad (the user agreed; the fix was later dropped)
- Scope: summary (cross-matter: goal-impediments)
- Failure pattern: Thread not updated
- Session / run: pt deployment `summary.md`, Sessions 003 and 004
- Source: SRC-44 (review finding 3)

**The text** (verbatim, as quoted in the review):
> "Ordinary weapons cannot pierce the Black Dragon's scales"

**Context needed to judge it:** by Session 003 the party had Sir Brandon's magic sword. In Session 004 Vivian's plan was to drive it through the dragon's mouth. The reviewer's suggested line: *"Ordinary weapons can't pierce its scales — but you have Sir Brandon's sword."*

**User's reaction** (verbatim): "3) file a work item for this"

**Why it is bad:** the obstacle is listed as if nothing had changed. Pairing it with the thing that answers it is what lets the players form a plan.

**Spot it:** for each carried-forward Impediment, has the party since gained an Asset or Opportunity that answers it? If so, say so.

**Outcome:** `summary-connected-threads` and `table-recap-connected-threads` were closed without implementation on 2026-10-28.
**Links:** —

---

### EX-029 A danger that was already over, under a different name
- Verdict: bad
- Scope: summary (cross-matter: brewing-troubles)
- Failure pattern: Stale entry
- Session / run: pt deployment `summary.md`, Session 004
- Source: SRC-44 (review finding 5)

**The text** (verbatim, as quoted in the review), under "Meanwhile":
> "The giant undead skeleton is about to attack the party in Sir Brandon's tomb."

**Context needed to judge it:** the same Summary's "Previously" section says "Left the Undead Sir Alfred Incapacitated." The danger was settled that session. It is also named "Sir Alfred" in one place and "the giant undead skeleton" in another.

**User's reaction** (verbatim): "5) file a workitem"

**Why it is bad:** it contradicts the Summary's own account, and it uses an old name after the creature had been identified.

**Spot it:** does any forward-looking item contradict "Last session…"? Once something has a name, every section uses it.

**Outcome:** `summary-stale-content` was closed at the user's request; its record "does not assert that the issues above were implemented or verified."
**Links:** [PREF-013](../preferences.md#pref-013)

---

### EX-030 "Why it matters" endings: the reviewer wanted them cut; the user kept them
- Verdict: good, per the user (a rejected critique)
- Scope: summary
- Session / run: pt deployment `summary.md`, Opportunities
- Source: SRC-44 (review finding 6a)

**The text** (verbatim fragments, as quoted in the review):
> "…which could strengthen the hunt", "…blocking the party from killing it for the bounty", "…which could help the party against the dragon"

**Reviewer's position:** "Drop the 'why it matters' endings … The table knows why the dragon matters."

**User's reaction** (verbatim):
> (a) the why it matters, no i want to keep this for now

**Why it matters:** it shows that the user values the stated consequence, even at the cost of length. The later Opportunity `title` format makes the advantage explicit (PREF-028).

**Spot it:** do not strip an entry's stated consequence in the name of brevity.

The user rejected another review suggestion in the same reply: a "Resolved" line per session (finding 4: "4) I dont want this, but thanks").
**Links:** [PREF-028](../preferences.md#pref-028)

---

### EX-031 Title case reads like a newspaper, not speech
- Verdict: bad
- Scope: summary (historical matters)
- Failure pattern: Title case
- Session / run: pt deployment `summary.md`
- Source: SRC-44 (review finding 6b; 2026-10-28T20:26Z)

**The text** (verbatim, as quoted in the review):
> "Sir Phidipaldi Stripped Sir Brandon's Armor From His Corpse"

**User's reactions** (verbatim):
> (b) sentence case - file a work item for this

> I think it might be title cased and not sentence cased. Please check the session summaries.

**Why it is bad:** in the reviewer's words, it "reads like a newspaper headline, and it's harder to scan and to paraphrase."

**Spot it:** only the first word and proper nouns are capitalized.

**Outcome:** sentence case was written into every pt matter prompt ("Use sentence case: capitalize only the first word and proper nouns."). 
**Links:** [PREF-002](../preferences.md#pref-002), [PREF-024](../preferences.md#pref-024)

---


### EX-033 A headline with its small words dropped
- Verdict: bad
- Scope: developments, as shown in the Summary's "Last session..."
- Failure pattern: Clipped headline
- Session / run: Session 004, run `developments-brandonsford-004-z2iyiem3` (st, 2026-10-26T19:54Z)
- Source: SRC-38 (2026-10-26T20:28Z–20:33Z)

**The text** (verbatim):
> Cedric Signs 975 Gold Promissory Note for Party's Treasure, Payable When Caravans Resume

**Context needed to judge it:** a sibling run from the same batch (`-3tvvvdz3`) reads "Cedric Signs a 975 Gold Promissory Note for the Party's Treasure, Payable When Caravans Resume." The reviewer's other example of the problem was "Ingrid Left Crestfallen" for "Ingrid Is Left Crestfallen".

**User's reactions** (verbatim):
> Q1 - b
> Q2-other small words
> I generally like the phraising and structure used. It is just about the dropping of words

**Why it is bad:** read aloud after "Last session…", a clipped headline sounds telegraphic.

**Spot it:** read it aloud after its heading. Are articles, "is/are/was" and prepositions present?

**Outcome:** the prompt was changed in st Developments (2026-10-26). The same rule was applied to pt Revelations and New Assets on 2026-10-27, and to immediate goals in Present Matters.
**Links:** [PREF-002](../preferences.md#pref-002), [PREF-026](../preferences.md#pref-026)

---

### EX-034 A dense Opportunity, rewritten source-first
- Verdict: bad → good (before and after)
- Scope: opportunities, as shown in the Summary
- Failure pattern: Crowded sentence, source last
- Session / run: pt deployment output, 2026-10-28
- Source: SRC-46 (2026-10-28T23:22Z). The user posted this wording as their answer. It is recorded in `pt/.work-items/matters-plain-language/intent.md`.

**Before** (verbatim, "an actual Opportunity in the current output"):
> Getting the dragon to drink enough of Dunk's faun wine could knock it out so you can drive Sir Brandon's sword through its mouth, Vivian says.

**After** (verbatim, the target):
> Vivian says enough of Dunk's faun wine could knock the dragon out. If that works, the party could drive Sir Brandon's sword through its mouth.

**User's framing** (verbatim):
> I want each bullet to be easier to understand on the first reading and easier to say aloud.

**Why the after is good:** the source comes first, the mechanism is separated from its benefit, the hedge ("could") is kept, and it uses "the party" instead of "you" in the Summary.

**Spot it:**
- Who did, believes, offers or owes it: is that clear in the first few words?
- Is the attribution ("X says") at the front?
- Are there three or more clauses stacked in one sentence?

**Outcome:** `matters-plain-language` was implemented and is complete. Its intent notes that the pt Opportunities output example still ended "…, according to Father William", which contradicts the rule.
**Links:** [PREF-026](../preferences.md#pref-026)

---

## Unjudged observations

- The current pt Opportunity titles follow the user's opening + action + advantage request (PREF-028) but often run to two sentences. For example: "Lady Hilda will join the party against the dragon if they pay her. Her experience could help them kill it." `matters-plain-language` recorded that the prompt requires one sentence in three places.

---

### EX-064 "Where you are" with the party split
- Verdict: good
- Scope: summary (present matters, "Where you are")
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`). Step 4 received each character's last scene.
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> Sir Phidipaldi is at the bar of the empty Golden Egg Tavern with its owner, Quinn. Wayman Tisdale and Dr. Uriah are across the street in the Clumsy Fox Tavern. Dunk is at Farmer Gill's farm, drinking with Gill on the porch before bedding down in the barn.

**User's reaction** (verbatim):
> starting position: all good

**Context needed to judge it:** pass 3 placed only Sir Phidipaldi, because step 4 saw only the last scene.

**Spot it:** when the party is split, is every player character placed, one short sentence per group?

**Outcome:** the target form.
**Links:** —

Pass 7 user review follow-up (SRC-57): [EX-077–EX-078](pass7-session-001-002-review.md) records actual Session 001–002 judgments and proposed fixes. Relevant earlier unjudged repetitions now have explicit user duplicate verdicts; historical observations remain preserved. No new behavior has been implemented.

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.
