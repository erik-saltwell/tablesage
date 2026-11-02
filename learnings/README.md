# Campaign Matters Learnings

This collection records what our conversations taught us about Campaign Matters, the Session Summary and the Table Recap:
- **Preferences:** what the user wants.
- **Approaches:** what was tried and how it went.
- **Examples:** the most important part. Real good and bad output, with the context needed to judge it.

The initial collection was mined from Claude Code and Codex conversations between 2026-10-18 and 2026-10-30; [sources.md](sources.md) lists them. The original plan is in [mining-plan.md](mining-plan.md). Codex and Claude maintain it during subsequent work using [maintenance.md](maintenance.md).

This is evidence, not current instructions. Current behavior lives in the prompts. Where the collection and a prompt disagree, the entry says so.

## Using it to judge new work

1. Read the scope file in `examples/` for the matter you are changing, plus `cross-matter.md`.
2. Run each example's **Spot it** check against the new output. A match means the new output repeats a known failure, or a known success.
3. Check [preferences.md](preferences.md) for the matter, and [approaches.md](approaches.md) before trying something already tried. Its "Lost or never shipped" table lists ideas that helped but did not survive.

## Conventions

- **IDs** are permanent and never reused: `PREF-###`, `APP-###`, `EX-###`, `SRC-##`. Numbers reflect the order of writing, not importance.
- **Verbatim:** quoted output text and user reactions are copied exactly, typos included. Whitespace and curly or straight quotes may be normalized. Text that could not be recovered is marked `not recovered`, never paraphrased. A word in [brackets] directly after a garbled dictated word is a gloss; the original word is kept.
- **Verdicts:**
  - `good` and `bad`
  - `borderline`: a reasonable case either way
  - `missing`: an expected entry that was not produced
  - `contested`: the user's expectation and the current definition disagree
- **Definition in force:** several matters were redefined during the window, so examples say which definition they were judged under.
- **Run folders** (`revelations-brandonsford-001-u63yrall` and similar) are under `~/data/tablesage_summary_test/.cache/runs/`. Each preserves the exact prompt, input and provider response. Use them, not `.cache/<matter>/<session>/run-N/`, which is overwritten by every validation run.
- **Summary and Recap names:** on 2026-10-27 the user decided that the content then generated as the Table Recap works better as the Session Summary. Summary and Recap entries record which name the artifact had at the time, and both share [examples/summary-recap.md](examples/summary-recap.md).
- **Unjudged observations** at the end of an example file are things noticed in current output that the user has not reviewed. They are not examples.

## Progress

| Scope | Status |
|---|---|
| Revelations | done: [examples/revelations.md](examples/revelations.md) |
| Mysteries | done: [examples/mysteries.md](examples/mysteries.md) |
| Cross-matter duplication | done: [examples/cross-matter.md](examples/cross-matter.md) |
| Summary and Recap | done: [examples/summary-recap.md](examples/summary-recap.md) |
| Goals, Goal Impediments, Opportunities | done: [goals](examples/goals.md), [goal-impediments](examples/goal-impediments.md), [opportunities](examples/opportunities.md) |
| Obligations, Brewing Troubles | done: [obligations](examples/obligations.md), [brewing-troubles](examples/brewing-troubles.md) |
| New Assets, Developments | done: [new-assets](examples/new-assets.md), [developments](examples/developments.md) |
| Goldens and output edits | done: [examples/goldens.md](examples/goldens.md) |

## By scope

| Scope | Preferences | Approaches | Examples |
|---|---|---|---|
| cross-matter | PREF-004, PREF-012, PREF-014, PREF-015, PREF-017, PREF-018, PREF-041, PREF-042 | APP-017, APP-034 | EX-003, EX-021 to EX-026, EX-056, EX-066, EX-067 |
| revelations | PREF-002, PREF-005, PREF-007, PREF-008, PREF-009, PREF-010, PREF-043 | APP-001 to APP-007, APP-034 | EX-001, EX-004 to EX-013, EX-068 |
| mysteries | PREF-003, PREF-013, PREF-043, PREF-054 | APP-008 to APP-013, APP-034 | EX-002, EX-014 to EX-020, EX-062, EX-068 |
| obligations | PREF-020, PREF-036, PREF-052 | APP-030 | EX-042 to EX-044, EX-056 |
| brewing-troubles | PREF-037 | — | EX-045, EX-046, EX-063 |
| new-assets | PREF-038, PREF-040, PREF-041 | APP-032, APP-034 | EX-047, EX-048, EX-065, EX-066 |
| all (goldens) | — | — | EX-049, EX-050 |
| developments | PREF-027, PREF-039, PREF-044 | APP-033, APP-034 | EX-057 (Session 001 golden), EX-069 (investigation deferred); see also EX-033 and the cross-matter examples |
| summary, recap | PREF-021, PREF-023 to PREF-029, PREF-031, PREF-048 to PREF-050 | APP-022 | EX-027 to EX-031, EX-033, EX-034, EX-064 |
| goals | PREF-033, PREF-051, PREF-053 | APP-027 | EX-035, EX-036, EX-051, EX-052, EX-058, EX-059, EX-081 |
| goal-impediments | PREF-034, PREF-042 | APP-028, APP-034 | EX-037 to EX-039, EX-060, EX-067 |
| opportunities | PREF-028, PREF-035, PREF-040, PREF-041, PREF-045, PREF-046, PREF-047 | APP-029, APP-034 | EX-040, EX-041, EX-053 to EX-055, EX-061, EX-065, EX-066, EX-080 |

## By failure pattern

| Pattern | What goes wrong | Examples |
|---|---|---|
| Restates the problem | A Revelation describes the Mystery's setup, extent or premise instead of reducing an uncertainty | EX-001, EX-005, EX-007 |
| Extractor supplies the connection | The entry's own wording ties a fact to the question; the evidence does not | EX-004 |
| Revelation from table talk | A PC's mistaken claim and its rebuttal become "news" | EX-006 |
| Expected finding absent | A finding the user expected is not produced | EX-008 |
| Dossier entry | One entry bundles identity, habits, state, wrong guesses and bookkeeping | EX-009 |
| Witnessed event recast as knowledge | What visibly happened is restated as something learned | EX-012 |
| Ordinary unknown | An unidentified creature, item property or detail becomes a Mystery | EX-002 |
| Undisclosed information | "There is more to tell," or a known holder of a secret, becomes a Mystery with no subject | EX-014, EX-016 |
| Unstated motive | An unexplained refusal or decision becomes a Mystery; it is usually an obstacle | EX-015 |
| Clue framed as the question | A clue (which map mark?) replaces the underlying question (where and what is the treasure?) | EX-017 |
| Stale open question | A local Mystery stays open after its episode ends | EX-018 |
| Open bargain restated | One unfinished deal is repeated in several categories | EX-003, EX-024 |
| Threat spread | A threat live at the end of the session appears as danger, trouble, impediment and event | EX-021 |
| Commitment restated | A promise made this session is a Development and again a Goal or Obligation, sometimes split in two | EX-022 |
| Revelation restated as Impediment | Learned knowledge reappears, near-verbatim, as an obstacle | EX-023 |
| Unchanged items repeated | The same open-item sentence is read out every week | EX-027 |
| Thread not updated | An obstacle is listed as if the party had not found its answer | EX-028 |
| Stale entry | A forward-looking item contradicts what the Summary says already happened | EX-029, EX-022 |
| Title case | Headlines in title case read like a newspaper | EX-031 |
| Clipped headline | Articles and small words dropped, so it sounds telegraphic aloud | EX-033 |
| Means listed as an end | A step toward another Goal is listed as its own Goal | EX-035, EX-081 |
| Dramatic method inflates a minor goal | A proposed method replaces the end, whose achievement would change little | EX-081 (PREF-053) |
| Unstable parent link | Whether an item is an end or a means flips between runs | EX-036 |
| Missing solution as impediment | Not yet having a fix is recorded as the obstacle | EX-037 |
| Anticipated obstacle shown as active | A future obstacle is listed as blocking now | EX-038 |
| Mechanical title format | A data link is glued into the title as a label | EX-039 |
| Sub-steps as siblings | Steps toward one opportunity are listed as parallel opportunities | EX-040 |
| Advice recorded as a commitment | Acknowledging someone's suggestion becomes a promise they are owed | EX-042 |
| Endless duty as open matter | A promise with no completion condition is listed as something to finish | EX-043 |
| Related progress taken as fulfillment | Finishing the deal's activity is treated as paying what is owed | EX-044 |
| Party-made trouble | The party's own scheme is listed as trouble coming at them | EX-046 |
| Profile instead of benefit | An asset entry describes a character instead of what was gained | EX-047 |
| Crowded sentence, source last | Several stacked clauses, with "X says" at the end | EX-034 |
| Clue in a goal | A lead or source is written into the goal, sometimes claiming more than play established | EX-051 |
| Commitment level in a goal | "Is considering" or a similar hedge rates how firmly the party took the goal up | EX-052 |
| Detail split into its own bullet | Caveats or a profile of an offer already listed become a separate opportunity | EX-053 |
| Price or direct means as opportunity | Paying a goal's price or meeting its terms is listed as an extra advantage | EX-054 |
| Low-value link as opportunity | A weak connection between two goals, with no action offered, is listed as an opportunity | EX-055 |
| Owed to the party listed as a debt | What someone owes the party appears under "Promises and debts" | EX-056 |
| Plan recorded as a promise | A method the party agreed to try is listed as something it owes | EX-056 |
| Motive in a goal | A reason for wanting the outcome is attached to the goal | EX-058 |
| Item detail in a goal | Detail about the wanted item, such as who it fits, is attached to the goal | EX-059 |
| Vague advantage | An opportunity's advantage is generic, such as "they can see what happens" | EX-061 |
| Explicit proposal required | An established option is hidden solely because nobody suggested acting on it | EX-065 |
| Distinct resources suppressed | Shared thread links are mistaken for resource identity | EX-066 |
| Immediate confrontation as lasting impediment | The same scene-local danger appears in current and open tiers | EX-067 |
| Intentional revelation ignored | An answered unknown is kept open solely because characters did not witness the revelation | EX-068 |
| One opportunity told twice | The same trigger toward the same goal is split into several bullets, often one restating the payoff | EX-073 (PREF-045) |
| Plan split into steps | One bullet's benefit is another's trigger, or complementary pieces of one plan are listed separately | EX-040, EX-073 (PREF-045) |
| Benefit is the goal itself | An "opportunity" whose benefit is just reaching the goal, its price, or having the item | EX-054, EX-074 (PREF-046) |
| Held help as an opportunity | Something already held is listed as an opening, with nothing left to trigger | EX-075 (PREF-047) |
| Stacked labels | Two identifying labels in one sentence, or descriptive traits, instead of one short role | EX-078 (PREF-049) |
| Detail the players wouldn't miss | A secondary event or description that changes nothing the players remember or do | EX-078 (PREF-050) |
| Floated pursuit kept alive | An unaccepted, considered or abandoned pursuit carried as if it were taken up | EX-070, EX-072 (PREF-051) |
| Offer hidden for not naming the goal | An actual offer of help is hidden because it didn't mention the goal it plainly serves | EX-080 (PREF-040) |
| Agreement as a promise | Agreeing, acknowledging advice or planning to return is listed as a debt nobody has a claim on | EX-042, EX-076 (PREF-052) |

EX-065 to EX-069 are hypothetical review examples with explicit user judgments, not observed generation failures. EX-069 defers a selection decision to a four-Session investigation; it establishes no new inclusion rule.

## General Patterns (2026-11-01)

On 2026-11-01 the user and the agent went back through the examples behind the overtuned prompt rules, and asked what was really wrong in each one apart from its Session (SRC-58). The resulting patterns are recorded as preferences. Apply them in place of case-specific rules:

- [PREF-045](preferences.md#pref-045): when several bullets are one opportunity (same trigger and goal; a chain; complementary pieces).
- [PREF-046](preferences.md#pref-046): an opportunity's benefit is an advantage toward a goal, never the goal itself.
- [PREF-047](preferences.md#pref-047): held help is not an opportunity; an action that uses it can be.
- [PREF-048](preferences.md#pref-048): history names the event; amounts and conditions go to the open bullet (minor).
- [PREF-049](preferences.md#pref-049): one short identifying role, only when needed (provisional).
- [PREF-050](preferences.md#pref-050): keep a detail only if the players would miss it or it would change what they do.
- [PREF-051](preferences.md#pref-051): how a pursuit was established decides how it ends.
- [PREF-052](preferences.md#pref-052): a promise exists only if not doing it would break faith (on trial).
- [PREF-014](preferences.md#pref-014)'s 2026-11-01 application: code, not the model, drops low-rated history candidates.

The user's verdict on the set, verbatim:
> update the learnings to include these new patterns, which I love and I think really get to the underlying issues we're talking about.

When a new failure comes up, first ask whether one of these explains it, and if none does, look for the general pattern before writing a rule for the case.

## Known gaps between goldens and current definitions

Output claims were checked against `st` published outputs (2026-10-26) and the `pt` deployment (2026-10-28).

- **Session 002 golden Revelations** follow the 2026-10-18 definition, which [PREF-005](preferences.md#pref-005) replaced. Several lines, such as the dragon's lair (EX-011), are excluded by the current definition.
- **Goldens for Sessions 001 and 002** keep "Where and what is the treasure?", which the current Mysteries filter removes (EX-017).
- **"What happened to Gill's sons?"** is in the Session 002 golden but in no current published output.
- **Opportunities:** the Session 002 golden keeps the window and the potion as separate Opportunities (now children) and Naggeneen's offer, which has no Goal link (EX-040, EX-041).
- **Brewing Troubles:** the pt Session 001 output has none, although the user marked the dragon "Yes-" (EX-045).
- **Casing:** `tablesage_summary_test` prompts use title case for Revelations headlines; the port uses sentence case ([PREF-002](preferences.md#pref-002)).

## Pass 7 Session 001–002 Review

[Actual user review and proposed fixes](examples/pass7-session-001-002-review.md): EX-070 (dropped/expired goals), EX-071 (goal ordering), EX-072 (mule significance, discussion pending), EX-073 (duplicate offers/plans), EX-074 (tautological opportunities), EX-075 (assets versus openings), EX-076 (agreement promoted to debt), EX-077 (missing immediate intention), EX-078 (headline wording). Also records positive section judgments. Recommendations remain unapproved and unimplemented; Sessions 003–004 review is deferred.

Pass 7 review status update: recommendations EX-070–EX-078 were subsequently approved and implemented in [pass 8](../.work-items/unified-matters-pipeline/experiments/session-004/pass-8/README.md), with assets explicitly excluded from open matters. Earlier proposal/unresolved labels describe the initial review; approval details and remaining model-verification limits are preserved in the review examples. No fresh outputs have been generated.

Pass 8 review update (2026-11-01): [EX-079](examples/developments.md#ex-079-dunks-visit-to-farmer-gill-disappears-as-a-historical-event) records missing Dunk/Gill historical coverage. The [EX-042 recurrence](examples/obligations.md#ex-042-recurrence-pass-8-and-renewed-user-judgment-2026-11-01) promotes the lance observation to an explicit bad-output verdict, with the user's preference for general distinctions rather than edge-case machinery. No behavioral changes have been made from this feedback.

EX-079 implementation/result update: the approved general encounter-coverage change is implemented in pass 9 and fresh Sessions 001–002 are in [14-PASS9](../deployment/unified-review/14-PASS9/0-START-HERE.md). Dunk/Gill now appears in Session 001 history; outputs remain unjudged. See EX-079 and the unjudged pass 9 cross-matter observation for evidence and remaining limitations.

EX-079 now includes a positive inclusion learning for pass 9 Session 001: the user explicitly requested preserving Dunk/Gill's presence as a Development. It remains paired with the earlier omission example; exact wording and the rest of the pass are not thereby approved.

## Pass 11 User Review

[Selected Session 001–002 judgments](examples/pass11-session-001-002-review.md), SRC-59: EX-081 distinguishes the actual end, its completion impact and a proposed method; PREF-053 records that significance test. PREF-054 records the adventure-level low-impact exemption request, with its precise Mystery-selection scope still unresolved. Existing preferences gain dated clarifications: the reporting hierarchy remains unimportant; history must be chronological; the job outcome and opportunity wording need work; map marking is acceptable history; the shirt benefit is accepted. The Session 001 origin omission is tolerated for now, while Session 002's missing origin question is worth fixing. The user asks about deterministic ordering. General mechanisms are being proposed; no implementation or new pass is authorized by this proposal request.


## Pass 12 Brewing Trouble Interview

The user’s Gill’s sons interview (2026-11-01, SRC-60) clarifies [EX-045](examples/brewing-troubles.md#ex-045-the-users-verdicts-on-the-session-001-brewing-troubles) and [PREF-037](preferences.md#pref-037): danger must be established by the adventure/play, rather than inferred from a risky activity; competition for potential benefits is insufficient. Quest acceptance is not required. The prompt update is deferred until the remaining review feedback has been discussed; see [the pending implementation note](../.work-items/unified-matters-pipeline/progress.md#deferred-prompt-update-established-danger-for-brewing-troubles).


## Pass 12 Review Decisions and Pass 13 Revision

The SRC-60 review is complete. Dated clarifications in EX-017, EX-019, EX-027, EX-040, EX-042, EX-045, EX-051, EX-071, EX-074, EX-079 and EX-080 record exact verdicts, allowances and severity. In particular: eligible open matters may repeat unchanged; omission of an obstacle without a live target and the sons mystery on current evidence is allowed; the historical mule detail is optional; penance stays for now; a first-mention descriptor is tentatively acceptable. Goal/question wording and missing challenge history were judged minor, not major defects. The user subsequently requested learning/prompt updates. [Pass 13](../.work-items/unified-matters-pipeline/experiments/session-004/pass-13/README.md) implements generic prompt refinements without new generation or threshold changes. Earlier deferral notes describe sequencing before this request; the review-driven prompt revision is now implemented, while the separate registered investigations remain deferred.
