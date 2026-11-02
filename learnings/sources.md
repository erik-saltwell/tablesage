# Learnings Sources

The conversations and repo material mined for the learnings collection, triaged 2026-10-30. Every entry elsewhere in `learnings/` cites a `SRC-##` ID from this file.

- **Window:** 2026-10-18 to 2026-10-30.
- **Stores:**
  - Claude Code: `~/.claude/projects/<folder>/<id>.jsonl`
  - Codex: `~/.codex/sessions/YYYY/MM/DD/rollout-*-<id>.jsonl`, matched by the `cwd` in each file's `session_meta`
- **Folders:**
  - `st` = `~/data/tablesage_summary_test`
  - `dt` = `~/data/tablesage`
  - `pt` = `~/proj/tablesage`
- **Value:**
  - **high:** the user judged concrete output or set definitions against specific items
  - **med:** design decisions or preferences with little concrete output
  - **low:** mostly process; mined only for approaches
  - **drop:** off-topic, duplicate or empty
- **Timestamps:** UTC.

## Conversations

| ID | Start (UTC) | Store / id | Repo | Scope | Value | What to mine |
|---|---|---|---|---|---|---|
| SRC-01 | 10-18 17:12 | claude `f842c187` | st | all matters | high | Comparison of the user's handmade Session 002 matters (`pt/docs/delete_me/HandmadeCampaignMatters`) with generated output. Became the golden master. |
| SRC-02 | 10-18 19:17 | claude `7d799c98` | st | — | drop | Handoff prompt only. |
| SRC-03 | 10-18 19:18 | claude `a743a237` | st | revelations | high | Golden-derived vs generated definitions of Revelations. Litmus test: "keep a detail when it changes how the party could use the knowledge, and drop it when it only adds precision." Discussion of the slow-moving giant and the "three miles north" detail. Discoveries and Revelations must share one definition. |
| SRC-04 | 10-18 20:59 | codex `01a150cf` | st | — | drop | Repo cleanup process. |
| SRC-05 | 10-18 22:38 | codex `01a1512a` | st | — | drop | Phone-sync layout. |
| SRC-06 | 10-18 22:59 | claude `85acce6f` | st | goals | drop | One opening message only. |
| SRC-07 | 10-18 23:13 | codex `01a1514a` | st | goals | high | Session 001 golden review. Active Goals definitions from goldens vs generated. "Top-level" rubric dimension (Seamus purchase kept, Brandon's sword is a means). A goal stays active until achieved, abandoned, replaced or failed. Duel, Ned and map judged defensible. |
| SRC-08 | 10-19 02:38 | codex `01a15206` | st | opportunities | high | Golden vs generated definitions. An opportunity must imply a course of action. Add exclusions only when they are the only effective fix. Origin of the optimize-matter process. |
| SRC-09 | 10-19 02:56 | codex `01a15217` | st | — | drop | Harness freshness. |
| SRC-10 | 10-19 17:43 | codex `01a15543` | st | obligations | high | Recurring and negative terms ("I will not reveal your presence to King Hogboon") can never be completed, so they are excluded. George's lake advice is not a commitment. User asks for a generic rule over a situation-specific one. |
| SRC-11 | 10-19 18:19 | codex `01a15564` | st | brewing-troubles | med | Optimize Developing Threats. The judgements are in the assistant reviews; the user mostly approves. |
| SRC-12 | 10-19 20:43 | codex `01a155e7` | st | mysteries | high | Optimize Unresolved Mysteries. The "problem with the treasure" (central to the adventure, yet missed). Simplification experiment compared with the complex version, with the fallback kept. |
| SRC-13 | 10-20 15:51 | codex `01a15a02` | st | new-assets | med | Name and benefit as separate properties. The developer chooses what the recap shows. Verbosity fix: smallest improvement taken from the complex version. Golden vs generated New Assets. |
| SRC-14 | 10-20 17:11 | claude `240e779c` | st | — | drop | Duplicate of SRC-15. |
| SRC-15 | 10-20 17:11 | codex `01a15a4c` | st | recap | low | Session cue definition: the most memorable scene cue, used to identify a session. |
| SRC-16 | 10-20 18:40 | codex `01a15a9d` | st | cross-matter | med | **The split.** One prompt per matter, processing order and what feeds what. Prior Mysteries passed to Revelations. Medium effort. |
| SRC-17 | 10-20 21:56 | codex `01a15b50` | st | revelations | high | Optimize Revelations after the split. Ingrid admitted to the golden. The shirt question. Impact attribute added and mapped against golden inclusion. |
| SRC-18 | 10-21 03:07 | claude `f1c10469` | st | cross-matter, goals | med | Approach: remove Campaign Matters from the Scene Log. Active Goals renamed to Goals. Per-matter regen script. |
| SRC-19 | 10-21 17:02 | claude `f6898ad7` | st | goals | med | Goals prompt rewritten by the user. Stable goal IDs. |
| SRC-20 | 10-21 19:23 | claude `d3ec0aa3` | st | brewing-troubles | low | Developing Threats renamed to Threats. |
| SRC-21 | 10-21 20:23 | codex `01a16022` | st | goals | med | First code filter: open lifecycle, significance. Why is Warwick's mithril shirt missing from two runs? |
| SRC-22 | 10-21 21:36 | claude `564d116c` | st | brewing-troubles | low | Threats regen. Design-notes origin. |
| SRC-23 | 10-22 00:03 | codex `01a160eb` | st | brewing-troubles | med | Threat filter fields and thresholds. |
| SRC-24 | 10-22 00:24 | claude `064b96eb` | st | obligations, cross-matter | med | Obligations prompt rewritten by the user. Shared system prompt deleted ("I do not want to use it ever"). Combined Campaign Matters render dropped. |
| SRC-25 | 10-22 01:59 | codex `01a16155` | st | — | low | Sessions 003 and 004 added to testing (approach: more test sessions). |
| SRC-26 | 10-22 04:36 | codex `01a161e5` | st | obligations, brewing-troubles | high | Workflow: filter only after seeing unfiltered results. Obligations filter. Brewing Troubles review against the user's keep/no table (R-03): "unfolding rescue problem" test, existing vs brewing trouble, Ned as an opportunity, the party as the source of a trouble (Dunk), recurring and continuing harms. |
| SRC-27 | 10-23 18:21 | codex `01a169ff` | st | brewing-troubles | med | Troubles output review and fixes. |
| SRC-28 | 10-23 18:35 | codex `01a16a0b` | st | — | drop | Generic skills. |
| SRC-29 | 10-24 00:23 | codex `01a16b4a` | st | goal-impediments | high | New matter. Anticipated lifecycle (the flying). Brandon's sword vs impenetrable scales: the sword is an opportunity, not an impediment. Buyer for barrow valuables. "Impedes" wording tried, then reverted. |
| SRC-30 | 10-24 22:51 | codex `01a1701c` | st | new-assets | drop | One message; work continued in SRC-36. |
| SRC-31 | 10-24 22:55 | codex `01a17020` | st | opportunities | high | Goal-linked opportunities. Sleeping potion, Warwick's window and faun wine are steps toward the chain mail, not separate opportunities, so a parent opportunity is added and filtered on. Prompt change to stop encouraging sub-steps. |
| SRC-32 | 10-25 03:08 | codex `01a17107` | st | mysteries | high | Mysteries as sources of investigation. Open-ended attribute. "What other problems does the reeve have?" (askable of every NPC). The fix must use a non-session example. "Why won't Warwick sell the mithril shirt?" is an impediment. Naggeneen's secret. Location as a yes/no question vs open-ended. Origin of the diagnose skill. |
| SRC-33 | 10-25 04:19 | codex `01a17149` | st | revelations, mysteries | high | Revelations redefined. Supply disruption (EX-001). Brandon's sword is retrievable. Undead swordsman and sword-powers Mysteries (EX-002). Headline style. `trivial` progress level. |
| SRC-34 | 10-25 19:38 | codex `01a17492` | st | mysteries | high | Mysteries rewritten from the user's own definition and testbed (inline attachments). "Your judgement on those was more or less perfect" (good examples). Deterministic filter instead of an include/exclude field. Review report format preferences. Tomb Mysteries should become obsolete after leaving the Barrow Mound. |
| SRC-35 | 10-26 01:09 | codex `01a175c1` | st | revelations | high | Unexpectedness. "Woodsman George's Account Describes a Small Black Dragon…" "Black Dragons Are Real, Undercutting Sir Phidipaldi's Claim…": a Revelation cannot come from a PC correcting a PC. Final filter set. |
| SRC-36 | 10-26 03:59 | codex `01a1765d` | st | new-assets | high | New Assets restarted: must support an open goal, with goal, opportunity and impediment links. Filters on opportunity origin and goal support. |
| SRC-37 | 10-26 19:29 | codex `01a179b0` | st | developments | high | Developments are persistent state changes, not "Frank took damage." Headline title. Narrative impact, lasting consequences, screen time. |
| SRC-38 | 10-26 20:28 | claude `d5d11bf6` | st | cross-matter | med | Dropped articles and small words: "I generally like the phrasing and structure used. It is just about the dropping of words." Developments in chronological order. Porting guide. |
| SRC-39 | 10-26 22:28 | codex `01a17a53` | dt | summary, recap | high | Port to TableSage. Post-session matters. Table Recap built: no descriptions, "Previously on <campaign>:", bullet lists, session date and cue. Immediate goals dropping small words. Developments in past tense. Opportunity title. **2026-10-27 20:17: Table Recap content judged better as the Session Summary.** |
| SRC-40 | 10-26 22:49 | codex `01a17a67` | pt | — | drop | Work-item registration only. |
| SRC-41 | 10-27 21:09 | codex `01a17f31` | pt | obligations, summary | high | Commitment type and stake ("George could care less how Sir Phidipaldi kills the dragon, or whether he uses a lance"). Headline style in historical matters. |
| SRC-42 | 10-27 23:27 | claude `f7e61221` | pt | cross-matter | med | Post-session matters dedup work item: dedup only in the assembled matters; Present Matters may duplicate. |
| SRC-43 | 10-28 04:33 | codex `01a180c8` | pt | obligations, present-matters | med | Obligations told not to repeat goals, impediments and opportunities. Immediate goals removed. |
| SRC-44 | 10-28 17:20 | claude `11a39c4b` | pt | summary, recap | high | GM read-aloud review of the four summaries. Listenable headings, child bullets that read naturally after their heading, "Last session...", sentence case, second person reverted, immediate danger reserved for genuine threats. |
| SRC-45 | 10-28 22:54 | codex `01a184b8` | pt | recap, summary | high | Keep all summary content in the recap. Last session stays as bullets ("a big wall of text that nobody is good at reading"). Direct clauses. |
| SRC-46 | 10-28 23:15 | claude `13b6fb5d` | pt | summary, recap | high | Each bullet should be easy to understand on first reading and to say aloud: actor and action early, and more. |
| SRC-47 | 10-29 04:18 | codex `01a185e1` | pt | — | drop | |
| SRC-48 | 10-29 04:22 | codex `01a185e4` | pt | — | drop | |
| SRC-49 | 10-29 04:28 | codex `01a185ea` | pt | — | drop | |
| SRC-50 | 10-29 04:29 | codex `01a185ec` | pt | — | drop | |
| SRC-51 | 10-29 16:28 | codex `01a1887d` | pt | cross-matter | med | Dedup intent: developments appear across many matters without adding information. The old dedup item "got way off track and overly complicated." |
| SRC-52 | 10-29 16:42 | codex `01a1888a` | pt | — | drop | Prompt caching. |
| SRC-53 | 10-29 17:09 | claude `c8fc3c25` | pt | cross-matter | high | Duplication patterns P1–P6 across the four sessions (EX-003). |
| SRC-54 | 10-29 18:05 | claude `68c4e9ff` | pt | — | drop | Interrupted duplicate of SRC-55. |
| SRC-55 | 10-29 18:06 | claude `94c379c2` | pt | cross-matter, summary | high | Open bargains (Quinn, Ingrid, Warwick). Overlap is legitimate but costly. The previous, current and open framing leads to a new beats, threads and scenes pipeline that supersedes P1–P6. Side-by-side artifacts. Session 001 and 002 review copies on 2026-10-30. **Approach still in progress.** |
| SRC-56 | 10-30 16:50 | codex `01a18db8` | st | — | drop | |

Excluded before triage:
- this conversation
- Claude `dt` transcripts `e5fd9546` (context handoff only) and `95ad1527` (no user turns)
- everything dated before 2026-10-18

## Repo and file sources

| ID | Source | Use |
|---|---|---|
| R-01 | `st` git history of `artifacts/session_*/golden/` from `9414ec9c` (2026-10-18) on, and the handmade original from SRC-01 | User-authored targets. Diffs against generated output give good examples, and each hand edit is a preference with its text. |
| R-02 | `st` git history of `artifacts/session_*/outputs/` review Markdown | The user's direct edits to generated output. |
| R-03 | `st` `artifacts/session_001/brewing-troubles-review.md` | The user's keep/no/maybe verdict and reason for each Brewing Trouble. Ready-made verdicts with the text attached. |
| R-04 | `st` `artifacts/.trash/mysteries-review-*.md`, `artifacts/evaluations/developments-review-*.md`, `artifacts/regen-comparison.md` | Review-matter reports: verbatim titles with classifications. |
| R-05 | `st` `.cache/runs/diagnose-*/diagnostic/` (7 runs) | The item under diagnosis, verbatim, plus a critique. |
| R-06 | Inline attachments in SRC-34: `mystery_definition_and_scoring.md`, `mystery_testbed.md` | The user's own Mystery definition and graded test cases. |
| R-07 | `pt` `.work-items/matters-dup-*`, `reduce-session-matters-duplication/analysis.md`, `post-session-matters-dedup`, `matters-plain-language`, `historical-matters-readable-headlines`, `obligation-stake`, `obligation-commitment-type`, `remove-immediate-goals`, `diegetic-summary-recap`, `deterministic-table-recap` | Recorded intents, often with verbatim occurrences. |
| R-08 | `st` `.work-items/` for items active in the window (optimize-*, refactor-campaign-matters-prompt, add-*, campaign-matters-importance) and `artifacts/design_notes/` | Recorded findings and rationale. |
| R-10 | `pt/docs/.stversions/delete_me/` (Syncthing version history) | The user's own hand-written Session 002 matters and their revisions, 2026-10-17 and 2026-10-18 (EX-049). |
| R-09 | `pt` deployment review folder from SRC-55 (2026-10-30) | Latest side-by-side output under review. Cite only; its verdicts are pending. |

## Mining order

1. **Revelations and Mysteries:** SRC-03, 12, 17, 32–35, plus R-04 to R-06.
2. **Cross-matter duplication:** SRC-16, 18, 24, 42, 51, 53, 55, plus R-07.
3. **Summary and Recap presentation:** SRC-38, 39, 41, 44–46.
4. **Goals, Goal Impediments and Opportunities:** SRC-07, 08, 19, 21, 29, 31.
5. **Obligations and Brewing Troubles:** SRC-10, 11, 23, 26, 27, 43, plus R-03.
6. **New Assets and Developments:** SRC-13, 36, 37.
7. **Goldens and output edits** (R-01, R-02), run across all scopes.

## Subsequent Conversation Evidence

### SRC-57
- Date: 2026-10-31 (local date; exact timestamp and conversation identifier unavailable).
- Source: current Codex/T3 conversation in `/home/eriksalt/proj/tablesage`, production-versus-unified review and the user's numbered preferences 1–5.
- Evidence type: explicit judgments of hypothetical inputs and predicted behavior, not actual generated outputs or measured four-Session results.
- Captured in: EX-065 to EX-069 and PREF-040 to PREF-044. The user approves supported implicit options, distinct resources and the production immediate-danger boundary; prefers intentional table revelations over character-only Mystery resolution; defers the Developments cutoff decision pending a separately registered investigation.

SRC-57 follow-up: the user requested a complete item-5 handoff, actual with/without runs in the future, and a per-difference likelihood that each change was caused by the policy. Captured in the work item intent and EX-069/PREF-044; no experiment executed during the save.

SRC-57 implementation follow-up: the user said "ok now implement the other approved changes (#1-#3)". The bounded implementation is saved as unified experiment pass 7. Evidence is direct selection/schema/CLI verification, not an LLM generation run; EX-065–EX-067 and PREF-040–PREF-042 record those limits.

SRC-57 generation follow-up: the user requested "now please generate outputs for sessions 001,002,003, and 004, and copy them into the unified-review folder". Pass 7 artifacts, input hashes and repairs are retained in the experiment workspace; exact output copies and Markdown reviews are in `deployment/unified-review/12-PASS7/`. Generation completed 2026-10-31; structural checks passed, but no new user output-quality verdict has been given.

SRC-57 review follow-up: the user supplied Session 001 and 002 pass 7 notes and asked “We should make improvements here first before moving on.  Please propose fixes:”. Actual judgments, exact output and proposed remedies are retained in EX-070–EX-078 in `examples/pass7-session-001-002-review.md`. Mule treatment is explicitly unresolved; sorting algorithm and asset presentation are proposals. No behavior change or regeneration was authorized by this proposal request.

SRC-57 approval follow-up: user approved all nine Session 001–002 recommendations and required bad-example capture before behavior changes. Clarified that no explicit duel withdrawal exists, assets must be excluded from open matters, and immediate intentions appear only if established. Exact bad outputs and approval clarifications were saved in EX-070–EX-078 before starting implementation.

SRC-57 pass 8 implementation follow-up: all nine approved Session 001–002 fixes are implemented in a new preserved experiment pass. Bad-example/approval capture preceded behavior changes. Verification comprises 49 direct checks and syntax/schema/CLI/template checks, not regenerated outputs or model-quality evidence. Details and boundaries are recorded with EX-070–EX-078.

SRC-57 pass 8 generation follow-up: user requested “please run sessions 001 and 002 and move the summaries to the unified review folder”. Fresh chained outputs and exact copies are saved in deployment/unified-review/13-PASS8/. Structural checks passed, with two Recap length warnings. Targeted retries and an asset-role validator repair are preserved in provenance; EX-070–EX-078 records observed improvements and remaining unjudged issues. No fresh user verdict or quality score is claimed.

SRC-57 user-review follow-up, 2026-11-01: feedback on fresh pass 8 Sessions 001–002 asks for at least a Development covering Dunk/Farmer Gill and again rejects the lance statement as a duty to George, while expressly discouraging elaborate edge-case handling. Exact feedback and traces are in EX-079 and the EX-042 recurrence. This is actual user judgment, distinct from prior unjudged run observations. No implementation or regeneration was requested or performed in this feedback capture.

SRC-57 follow-up, 2026-11-01: user requested a deferred work item to explore filtering low-stakes commitments after other output quality is generally satisfactory, and asked for a general remedy for missing Dunk/Gill historical coverage. Registered filter-low-stakes-commitments; exact deferral/evidence are in the EX-042 follow-up. A proposed encounter-context/historical-significance remedy is recorded under EX-079, not implemented. Neither threshold experiment began.

SRC-57 implementation/generation request, 2026-11-01: user said “Okay, please make these updates, then run a new pass for sessions one and two and copy them over to the unified review folder.” EX-079 approval was saved before creating pass 9. Scope is general encounter-level historical coverage plus a fresh two-Session run; low-stakes commitment filtering remains deferred in its registered item.

SRC-57 pass 9 completion, 2026-11-01: implemented general encounter-level historical coverage, generated fresh chained Sessions 001–002 and copied results to deployment/unified-review/14-PASS9/. EX-079 records the actual recovered Dunk/Gill event and verification limits. One Summary-writing retry preserved original evidence; no implementation/prompt/schema edits during generation. Fresh outputs await user review; possible potion-plan overlap remains unjudged.

SRC-57 positive inclusion follow-up, 2026-11-01: user said “Can your add the presence of the dunno gill thread as a development in session 001 as a learning”. Context identifies the Dunk/Farmer Gill encounter in pass 9 Session 001. EX-079 records its presence as a good inclusion, with the exact generated bullet; no blanket wording/pass approval inferred.

### SRC-58
- Date: 2026-11-01.
- Source: Claude Code conversation in `/home/eriksalt/proj/tablesage`, transcript `~/.claude/projects/-home-eriksalt-proj-tablesage/fe415af7-ec90-4a39-8749-46d3719bbc9e.jsonl`. It covers the automated pipeline reviews work item, then an interview to turn the failing prompt checks into general patterns.
- Evidence type: the user's stated patterns, and agent proposals the user explicitly confirmed. No generated output was judged.
- Captured in: EX-080, PREF-045 to PREF-052, the PREF-014 application note and the 2026-11-01 reinterpretation of EX-074.

### SRC-59
- Date: 2026-11-01.
- Source: current Codex/T3 conversation in `/home/eriksalt/proj/tablesage`, user feedback on the pass 11 review; provider conversation identifier unavailable.
- Evidence: selected explicit judgments and a request to propose generic fixes. The user reframes the duel as a low-impact honor pursuit, rejects its alleged obstacle, reaffirms lifecycle/chronology/job-outcome/wording fixes and the irrelevance of the reporting hierarchy, accepts the map marking as history and the shirt benefit, tolerates the Session 001 origin omission for now while requesting the Session 002 loss be fixed, and requests protection from low-impact filtering for adventure-level goals. The user asks about deterministic ordering without selecting its mechanism.
- Captured in: [pass 11 review](examples/pass11-session-001-002-review.md), EX-081, PREF-053, PREF-054 and dated preference clarifications. Proposed mechanisms are not approved implementation.

**Approval (2026-11-01, SRC-59):** the user said “implement then run pass 12”, approving the seven proposed general rules: ends and completion significance, causal obstacles, job success conditions, a guarded adventure-objective question path, detail relevance across headings, concise contextual opportunity benefits with an essential second sentence allowed, and deterministic goal/event ordering. The request includes fresh chained Sessions 001–002 as in the preceding run. No production cutover or unrelated threshold investigation is included.


### SRC-60
- Date: 2026-11-01.
- Source: current Codex/T3 conversation in `/home/eriksalt/proj/tablesage`, interview following the pass 12 review about Gill’s sons as a Brewing Trouble; provider conversation identifier unavailable.
- Evidence: the user distinguishes established danger from inferred risk and lost potential benefits; explicitly confirms that quest acceptance and player action are not required. The user asks to save the learning and defer the prompt update until after discussing the remaining review feedback.
- Captured in: EX-045 dated clarification, PREF-037 and the deferred note in unified-matters-pipeline/progress.md. No prompt implementation or new run authorized at this point.

SRC-60 continued review: the user requests one issue per round, with context and recommendation, skipping expressly allowed items. For SE-008 the user replied “That matches” to allowing omission of the shirt refusal when no live shirt-acquisition pursuit is established. Captured in the pass 7 review’s pass 12 baseline clarification; the original pass 12 failure is withdrawn.

SRC-60 continued review: regarding removal of the mule offer from the pass 12 Dunk/Gill history bullet, the user said “I am actually fine with this either way.” EX-079 records acceptance of either historical wording; this does not approve a mule Goal or independent opportunity.

SRC-60 continued review: the user confirms the slap/unaccepted challenge is “a fine item to put into the last session or development section”, while its omission is “a relatively minor issue”. Captured in the pass 7 review’s SE-001 clarification; this does not restore the minor honor pursuit as an open Goal.

SRC-60 continued review: the user reaffirms outcome-only goal wording, calls the map reference in this particular goal “a very minor issue”, and emphasizes concern about the general case. Captured in EX-051 and PREF-033; not blanket approval of embedding leads or methods in Goals.

SRC-60 continued review: the user prefers “Where and what is the treasure?” to the map-framed question and calls the issue minor. Captured in EX-017; question eligibility remains accepted and distinct from wording.

SRC-60 continued review: user tentatively allows Ned’s short descriptor at first mention within a Summary and prefers opportunity action/benefit over hire-contract precision (fee and per-kill rebate unnecessary there; fee acceptable in Developments). Exact response in EX-080; PREF-049 and PREF-028 qualified. RC-060 for this occurrence withdrawn; prompt/guide updates deferred.

SRC-60 continued review: user says “No I agree that as long as it remains open, it should continue to be here.” Still-open eligible Summary matters may repeat unchanged across Sessions. EX-027’s older repetition-only objection is superseded; PREF-021 clarified and RC-019 advisory withdrawn.

SRC-60 continued review: user says “Yes” to prioritizing the adventure currently driving the party’s choices; EX-071 and PREF-033 record the generic priority rule and its Session 002 application. Revision deferred, with deterministic sorting retained.

SRC-60 continued review: user says “I prefer merged. Why are they not in the if.... then... Format?” about the window/potion plan. EX-040 records confirmed merging, exact generated text, and the distinction between the agent’s paraphrased excerpts and the actual conditional potion bullet. Deferred strengthening of conditional presentation is an agent recommendation, not a separately approved implementation.

SRC-60 continued review: “Great, I approve” explicitly approves the merged window/potion example and strengthening conditional opportunity wording from a preference to an explicit structure; recorded under EX-040 / PREF-028. Implementation remains deferred until remaining feedback is discussed.

SRC-60 continued review: the user explicitly rejects the map-checking opportunity because its benefit merely solves the goal instead of providing an advantage toward achieving it. Exact explanation preserved under EX-074; PREF-035 / PREF-046 clarified. Removal approved for the deferred generic revision.

SRC-60 continued review: “Yes” to the recommendation to preserve Session 002’s fairy-emergence question as a meaningful mystery. Recorded under the pass 7 review’s SE-014 clarification; Session 002 origin omission remains separately covered by SRC-59.

SRC-60 continued review: “Agreed” to omitting the Gill’s sons mystery because the expedition alone establishes no unexplained disappearance/event. EX-019 records the superseded golden inclusion expectation and distinguishes mystery eligibility from danger.

SRC-60 continued review completed: user says “Yes” to retaining Uriah’s penance obligation for now while keeping the general low-stakes commitment-filter investigation deferred. Recorded in obligations.md under the EX-042 deferred-filter boundary. All distinct pass 12 review issues have now been discussed or carried forward from express prior judgments. No prompt implementation or regeneration requested in this final answer.

SRC-60 implementation authorization: after all review items were discussed, the user said “Okay, please start by updating learning and prompts”. This authorizes consolidating the judgments and the generic prompt revision now, superseding the earlier wait-until-discussion-is-complete sequencing. It does not request fresh generation, production cutover or the deferred threshold investigations. Pass 13 and APP-034 preserve the implementation and verification limits.
