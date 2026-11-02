# Developments Examples

Conventions are in [README.md](../README.md). Developments was the last matter added (2026-10-26, SRC-37). Its definition and presentation preferences are well recorded ([PREF-027](../preferences.md#pref-027), [PREF-039](../preferences.md#pref-039)). The user has not judged individual Developments in the mined conversations, except on wording (EX-033).

Related examples elsewhere:
- [EX-033](summary-recap.md#ex-033-a-headline-with-its-small-words-dropped): a clipped Development headline.
- [EX-003](cross-matter.md), [EX-021](cross-matter.md) to [EX-024](cross-matter.md): Developments restated by other categories.
- [EX-025](cross-matter.md): a Development and a Revelation that share a subject legitimately.

## Unjudged observations

- The st review report `artifacts/evaluations/developments-review-2026-10-26-131648.md` holds three-run comparisons of every Session 001–004 Development with all classifications. It is the place to start when collecting Development verdicts.

---

### EX-057 Session 001 "Last session...": the user's golden
- Verdict: good (golden for Session 001 Developments)
- Scope: developments, as the Summary's "Last session..."
- Session / run: Brandonsford Session 001, pass 5, 2026-10-30 (`pt/.work-items/unified-matters-pipeline/experiments/session-004/pass-5/runs/s001/summary.md`)
- Source: SRC-55 (2026-10-30, the user's review of `deployment/unified-review/9a`)

**The text** (verbatim):
> - The party reached Brandonsford at sunset, following a treasure map to places they did not recognize.
> - Reginald warned of a Clurichen trickster that comes into town from the riverbanks each night.
> - Eric the Reeve offered a bounty for the dragon. Sir Phidipaldi then slapped him and challenged him to a duel, which Eric did not accept.
> - Lady Hilda offered to join the party for pay, and Sir Phidipaldi said they would come back for her.
> - Drop Dead Ned offered himself and his killer wasp for hire, and Dr. Uriah said he would think about it.
> - Bentley and Gill told the party that supplies have stopped reaching Brandonsford.
> - Quinn promised Sir Phidipaldi 100 gold to help him get back at Bentley, whom he blames for stolen ale.

**Context needed to judge it:**
- One headline per thread, in story order, chosen in code from step 2c ratings: a thread shows when `narrative_impact` and `lasting_consequence` are both medium or high. The agent set that threshold provisionally (APP-034).
- Hidden by the same rule (impact and lasting both `low`):
  - Bentley sending Sir Phidipaldi to the Golden Egg for the night;
  - Farmer Gill's offer of the mule;
  - learning about Warwick's mithril shirt.

**User's reaction** (verbatim):
> Developments: this is maybe the best list we have created.  I want to treat this as a 'golden' for session 001 developments.   no notes

**Why it is good:**
- Seven short past-tense events, each one thread's change.
- Offers and bargains are told as events, with their terms left to the open headings.
- No gold paid, no damage, no precision.

**Spot it:** set a new Session 001 "Last session..." beside this list. Does it tell the same seven events, as briefly, and leave out the three hidden ones?

**Outcome:** kept as the Session 001 golden. It is one Session's evidence for the provisional threshold, not a calibration.
**Links:** [PREF-039](../preferences.md#pref-039), [PREF-027](../preferences.md#pref-027), [APP-034](../approaches.md#app-034)

**General pattern (2026-11-01, SRC-58):** [PREF-048](../preferences.md#pref-048), [PREF-049](../preferences.md#pref-049).

---

### EX-069 Investigate low-impact changes with high lasting consequences
- Verdict: borderline (decision deferred; investigation requested, no inclusion-policy change approved).
- Scope: developments, Summary Last session selection.
- Definition in force: production versus unified pass 6, reviewed 2026-10-31. This is a hypothetical input and predicted behavior, not output from a generation run.
- Source: SRC-57 (current conversation; user preference stated 2026-10-31).

**Illustrative input** (verbatim):
> The village ferryman agrees that the party may use his landing whenever they return. It is a modest improvement in access, but their established expedition requires repeated crossings. Nothing else changes in that thread this Session.

**Predictions, not generated output:** production could publish a qualifying Development rated low impact and high lasting consequences. Unified selection deterministically excludes it from Last session if assigned those ratings, because both dimensions must be medium or high; the access may survive under What could help. A medium impact rating would instead include it. The agent preferred allowing low-impact/high-lasting changes, but the user has not accepted that policy.

**User's direction** (verbatim; numbered response 5):
> I think we need to investigate this and see what impact it would have on our four test sessions.   Please make this investigation a new work items (allow low impact developments with high lasting consequences) and we will do an investigation later.   make no change to the unified pipeline for now.

**Decision:** retain the current unified rule. Investigate later on Brandonsford Sessions 001–004 before deciding whether to allow low-impact Developments with high lasting consequences. EX-057 remains the Session 001 golden; this is not approval to add the illustrative ferryman event or change that golden.

**Spot it:** for each Session, identify candidates rated low impact and high lasting consequence that the current rule excludes. Compare historical coverage and whether useful information already survives elsewhere. Preserve the baseline; distinguish selection-only differences from rating or generation variance.

**Outcome:** initially registered for later investigation. On 2026-10-31 the user requested a complete handoff and specified the intended with/without runs and per-difference attribution likelihood. The item is now `captured`, with [full investigation context](../../.work-items/allow-low-impact-developments-high-lasting-consequences/intent.md). No investigation, regeneration or pipeline change has begun.

**Follow-up requirement** (verbatim):
> My goal is to do a run with the change and without and show me the differences, and for each difference show me a likellihood the difference came from the change.

**Attribution guidance (agent recommendation, not measured results):** compare selection on frozen common inputs to identify direct rule effects, then compare generated outputs with unchanged-control repeats to assess LLM variation. Report a likelihood and its evidence for each difference; distinguish qualitative judgments from measured frequencies and do not invent calibrated percentages.
**Links:** [PREF-044](../preferences.md#pref-044), [EX-057](#ex-057-session-001-last-session-the-users-golden), [APP-034](../approaches.md#app-034).

---

### EX-079 Dunk's visit to Farmer Gill disappears as a historical event

- Verdict: missing. Scope: developments, summary, historical selection.
- Definition in force: unified pass 8 Last session requires narrative_impact and lasting_consequence both medium/high; Goals separately exclude incidental wants.
- Session/run: Brandonsford Session 001, pass-8/runs/s001; reviewed 2026-11-01, SRC-57 follow-up.

**User feedback, verbatim:**
> we lost any mention of dunk and farmer gill. Most of that is fine, but seems to deserve a development at least.

**Actual Last session output, verbatim:**
> The party reached Brandonsford at sunset, following a treasure map of places they did not recognize.
> Eric the Reeve offered a bounty for the black dragon. Sir Phidipaldi then insulted Eric and challenged him to a duel, which Eric declined.
> Bentley, Farmer Gill and Quinn said supplies have stopped reaching Brandonsford, leaving the taverns and smith short.
> Quinn hired Sir Phidipaldi to get back at Bentley, whom Quinn blames for stealing his ale.

No historical bullet tells Dunk's visit. Gill is named as a source in the supply bullet, and Where you are places Dunk drinking with Gill; these mentions do not preserve their encounter as an event. The omission judgment is about historical coverage, not proof all Gill information disappeared from every artifact.

**Relevant saved input:**
> beat_29: Dunk asked to sleep in the barn and think over the mule offer; Gill welcomed him and they drank from Gill's still on the porch.
> beat_32: Dunk kept Gill drinking for more gossip until the farmer was wobbling and having the time of his life.

Gill also told Dunk about the dragon, his sons, Warwick and Ingrid in beats 26–31. Thread_6, Shamus the mule, includes only beats 25, 26 and 29. Its historical candidate says:
> Farmer Gill offered Dunk the mule Shamus for 100 gold, and Dunk is considering trading work for it while staying in Gill's barn.

It is rated low narrative_impact (ordinary mount offer, unaccepted) and low lasting_consequence (pending mule offer/lodging considered minor), so code excludes it. Information from the encounter is distributed across other threads; the visit itself loses historical representation. This is not a case the deferred low-impact/high-lasting change would recover: this candidate is low/low.

**Agent recommendation, not yet implemented:** review how the historical candidate represents the encounter and its hospitality/contact/information exchange rather than judging it only as an ordinary purchase. Keep historical-event significance separate from whether the mule is a meaningful open Goal. A possible concise event is “Dunk drank with Farmer Gill and arranged to stay in his barn.” This is an agent-proposed example, not a user-authored golden. Do not promote the mule, invent a lasting alliance, force one bullet per character/scene, or silently lower the historical cutoff. The exact selection/rating change is still to be decided.

**Spot it:** does a supported character encounter vanish as an event because its thread/candidate is framed only around an incidental purchase, even though parts of the information survive elsewhere?

**Outcome:** judgment saved before changes. No behavior change or regeneration. Related: EX-072, EX-057, PREF-044 and the separately deferred cutoff investigation.

**General-fix discussion (EX-079, 2026-11-01, SRC-57):** the user asked “For Dunk and Farmer Gill, is there a general fix that won't be specific to this session that we can make?” Agent proposal, not yet approved or implemented: historical candidate generation should retain the encounter's context even when its beats are split among several threads. Supply scene/encounter context to the existing historical assessment and allow a distinct encounter-level candidate when its main event is not represented by a thread candidate. Judge whether it is a noteworthy event for the Session story separately from whether it creates a meaningful open Goal or lasting duty. Hospitality, an established contact or significant information exchange can matter; neither a long scene nor an incidental purchase guarantees a bullet. Keep one concise representation of an encounter's main event and avoid repeating discoveries already represented in other historical bullets.

This is a broader historical-coverage proposal, not an instruction to inflate lasting_consequence ratings until the existing filter passes. The present historical definition requires persistent change; encounter context alone cannot guarantee recovery of a genuinely low/low event. If narrative value warrants inclusion despite low lasting consequences, the eligibility definition must explicitly support that rather than silently changing the existing cutoff or launching the deferred low-impact/high-lasting investigation. Keep the mule Goal hidden, avoid invented alliances, and do not force one bullet per scene/character. No pipeline change made.

**Approval before implementation (2026-11-01, SRC-57):** the user said “Okay, please make these updates, then run a new pass for sessions one and two and copy them over to the unified review folder.” This authorizes the general encounter-context/historical-coverage proposal and a fresh two-Session run. Historical assessment may retain a noteworthy encounter independently of enduring consequences or open-goal significance; it must avoid duplicate historical representations and not force one bullet per scene. The exact missing/bad examples above remain preserved. The low-stakes commitment investigation remains deferred as explicitly requested; no new stake threshold is authorized. The separate low-impact/high-lasting comparison is not being run. Implementation and generation results pending.

**Implementation follow-up (EX-079, 2026-11-01):** pass 9 implements the approved general encounter channel in the existing step 2c call. It includes full scene context, honestly rated impact/lasting consequences, independent encounter value and explicit represented_by links. Code admits a noteworthy otherwise-unrepresented encounter, rejects duplicate historical representation against a selected candidate, and keeps open Goals unaffected. Focus beats reach Summary/Recap and historical JSON. 64 direct checks passed; fresh Sessions 001–002 are running. No new output-quality verdict yet. This expands historical coverage without starting either deferred threshold experiment.

**Fresh pass 9 outcome (EX-079, 2026-11-01; agent observations, no new user verdict):** Sessions 001–002 completed and were copied to [14-PASS9](../../deployment/unified-review/14-PASS9/0-START-HERE.md). Session 001 selects one of five encounter candidates, scene_4, independently of the incidental mule Goal. Exact generated history:

> Dunk heard Farmer Gill's legend of Sir Brandon and kept him drinking on his porch all evening.

The scene's encounter value is medium, with no represented_by link, and focus beats 27, 28, 29 and 33. Its impact and lasting consequence are also medium; do not claim this particular generated candidate demonstrated low/low admission (that boundary was verified directly with fixtures). Other scene candidates were low-value or represented by selected historical items. The mule remains absent from Goals. Session 002 selects the faun exchange and Uriah/Ingrid conversation as two added encounters. No character/scene quota or named exception was used.

Implementation hashes remained unchanged during the run. One Session 001 writing-only retry corrected a missing selected open-item ID; initial response is preserved. Session 002 needed no retry. Structural/copy/source checks passed and all Recap bullets meet the nominal word limit. Broader wording/selection changes between runs can include model variation; this was not a controlled A/B comparison. Quality awaits user review.

**Positive inclusion learning (EX-079, 2026-11-01, SRC-57):** the user requested, verbatim:
> Can your add the presence of the dunno gill thread as a development in session 001 as a learning

“dunno gill” refers to the Dunk/Farmer Gill encounter discussed immediately before this request. The actual pass 9 Session 001 Development is:

> Dunk heard Farmer Gill's legend of Sir Brandon and kept him drinking on his porch all evening.

**Verdict: good inclusion.** Retain the presence of this encounter as a positive historical-coverage example alongside the earlier missing-output example. A meaningful social encounter can deserve a concise Development even when its incidental shopping interest does not qualify as a Goal and its information is spread across threads. The user's request concerns the encounter's presence, not blanket approval of its exact wording, all pass 9 outputs, every social scene or a compulsory per-character bullet.

**Spot it, positive:** does historical coverage preserve Dunk's meaningful interaction with Gill as an event, while keeping the incidental mule Goal hidden and avoiding duplicate historical representations?

**Outcome:** explicit inclusion preference captured; no prompt/code/output changes or regeneration.

Pass 11 user judgments (2026-11-01, SRC-59) and exact outputs are preserved in [the Session 001–002 review](pass11-session-001-002-review.md). That record distinguishes accepted wording and historical inclusion, tolerated omissions, requested general fixes and proposed mechanisms. No behavior changed.


**EX-079 pass 12 wording tolerance (2026-11-01, SRC-60):** the reviewed Session 001 history bullet is, verbatim:
> Dunk drank with Farmer Gill, who offered him a mule and told how Sir Brandon once slew a dragon.

The agent recommended removing the mule offer while retaining the encounter and legend. The user replied, verbatim: “I am actually fine with this either way.” Including or omitting this short mule-offer detail within the wanted historical encounter is acceptable. Withdraw the Session 001 RC-016 finding about this detail and the corresponding portion of SE-001; do not require its removal in historical wording or goldens. This does not approve an independent mule Goal/opportunity or every incidental detail in other encounters. The missing duel-history component of SE-001 remains a separate, unjudged review issue. No prompts or outputs changed.
