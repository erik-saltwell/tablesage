# Unified Matters Pipeline: Implementation Progress

## Approved Review Changes 1–3 (2026-10-31)

The user explicitly requested implementation of recommendations #1–#3 after recording their decisions in EX-065–EX-069. The approved scope is supported implicit opportunities, preservation of distinct resources during deduplication, and the boundary between immediate danger and lasting impediments. The earlier item-level statement that no implementation was authorized is superseded for this narrow scope. Production cutover is not authorized by this request.

Implemented as [pass 7](experiments/session-004/pass-7/README.md), preserving all earlier passes, generated Session outputs and review copies. The [runner](experiments/session-004/pass-7/run7.py), extraction/schema contracts and stopping-situation evidence implement these changes. Earlier experiment seeds are copied only as input context, not represented as new run results.

- Completed: rename opportunity classification to `action_supported` and allow grounded physical options and straightforward capability-to-need matches without an explicit proposal; continue to reject invented cooperation or exchanges.
- Completed: keep independent shared resources/offers separate, validate `resource_subject` references, and replace thread-only resource suppression with conservative equivalence against a selected home fact. Equivalence requires the same resource subject, form, helped thread, complete text and uncertainty. Pointer decisions identify their exact replacement. Distinct conditions and resources survive; paraphrased duplicates can still survive when extraction fails to give them one home.
- Completed: require `scope_basis` and `persists_beyond_scene` for obstacles; publish only lasting active impediments to shown live wants, debts or openings. Supply obstacles to the stopping-situation writer so it can cover the same immediate confrontation and prevent duplicate open publication, while preserving separate lasting restrictions.
- Completed: validate new classifications before publishing a chain, and make step 3/check fail for invalid new metadata.
- Completed: validate syntax, schemas, complete prompt JSON example, strict stopping-template rendering and CLI loading; 23 direct behavior checks passed. All 16 historical rating combinations retain the original cutoff. Verification used a temporary script outside the repository; no unit-test files or tooling were added.

At completion of the initial implementation, no LLM generation had been run with pass 7; the subsequent generation is recorded below. No four-Session impact investigation, quality scoring or user verdict on new outputs is claimed. The relevant existing rubric dimensions are Selection, Information preservation, No restatement, Best representation and Faithfulness; deterministic checks support the intended mechanics but do not establish model compliance or final output quality. The existing [quality rubric](intent.md#quality-rubric) remains unchanged.

## Resume

The requested narrow implementation is complete. Future generation and review should use pass 7, regenerate step 3 for the renamed/new metadata, and preserve the source snapshots and old review outputs. The CLI/order is in the pass 7 README. Check actual extraction against EX-065–EX-067, including the unknown-agreement case, chart/passage distinction, and guard confrontation. Do not silently apply the new schema to old step 3 files.

Keep the user's intentional-table-revelation preference (EX-068); no production-style character-only resolution guard was added. Keep the Last session rule unchanged. The [low-impact/high-lasting investigation](../allow-low-impact-developments-high-lasting-consequences/intent.md) is a separately captured future comparison; this implementation does not start it or adopt its candidate rule. When that investigation runs, use the same baseline revision and input snapshots for both conditions so these approved changes do not become confounds.

## Four-Session Generation Completed (2026-10-31)

The user requested pass 7 outputs for Sessions 001–004 and copies in `deployment/unified-review/`. The fresh chain completed in order for all four Sessions; 004 used 003's generated seed. The runner now supports all four labels and avoids pass 2's hand-made Session 004 seed override; seed high-water marks preserve ended IDs. `pass-7/generation-journal.json` records completed stages, source hashes and repairs. All review copies are saved under `deployment/unified-review/archive/12-PASS7/`, linked from the root review guide.

Generation exposed adapter/schema issues, corrected without selection-policy changes: preserve empty string text fields while normalizing only thread references; allow null role/support ratings only on resources with no goal link, which remain excluded. Session 003 thread 18 was retried once because it assigned resource metadata to an obstacle; its original response is preserved under `runs/s003-step3/attempts/initial/` and other thread responses were reused. The Last session cutoff remains unchanged. No four-Session quality assessment or user approval is claimed.

Completion verification passed for all four Sessions: schema/classification validity, prior thread/fact accounting, citations, deterministic selection replay, unchanged source Ledger/seed hashes, exact copied outputs, full-text Markdown renderings, recap thread counts and review links. All Recap bullets are within 35 words. [Review index](../../deployment/unified-review/archive/12-PASS7/0-START-HERE.md); [run notes](../../deployment/unified-review/archive/12-PASS7/run-notes.md); machine-readable evidence is in pass 7's `generation-journal.json` and `generation-verification.json`.

Current resume point: the requested generation and copying are complete; await the user's review of these pass 7 outputs. Remaining semantic repetition is recorded as unjudged observation, not silently corrected. Pipeline adoption/cutover and the separate low-impact/high-lasting comparison remain undecided/deferred.

## Session 001–002 Review Implementation (Pass 8)

The user approved recommendations 1–9 and clarified that assets are not open matters, the duel has no explicit withdrawal, and immediate intentions appear only if established. Exact rejected outputs and approvals were recorded in EX-070–EX-078 before creating [pass 8](experiments/session-004/pass-8/README.md). All nine fixes are implemented there; earlier generated outputs and production remain unchanged.

The implementation includes a bounded resource reconciliation call, explicit enabling-opening qualification, adventure-first goal ordering, asset exclusion from open publication, evidence-backed optional immediate intention, lifecycle and minor-goal prompt guidance, and simpler historical wording. Full fact metadata now survives both seed persistence and the inherited per-thread prompt adapter; continuity checks reject silent carried significance/commitment drift.

Verification: 49 direct behavior checks passed, plus Python syntax/CLI/schema/template checks. [Machine-readable evidence](experiments/session-004/pass-8/verification.json). Saved facts were explicitly adapted as direct-check fixtures; writing calls were stubbed. No LLM calls, regenerated Session outputs, quality scores or new user output verdicts are claimed. Model compliance, semantic fidelity and final wording remain to be assessed. No unit-test files or tooling were added.

Current resume point: the approved implementation is complete. Use the pass 8 README for fresh chained Session 001–002 generation and review when requested. The user wants those improved before moving to further Session review. Pass 7 review folders retain the exact judged evidence. This supersedes earlier resume instructions to use pass 7. The overall item remains implementing; production adoption and the separate historical cutoff investigation remain open/deferred.

## Pass 8 Generation Completed

The requested fresh Session 001–002 chain and review copies are complete. [Open review index](../../deployment/unified-review/archive/13-PASS8/0-START-HERE.md). Both summaries, Recaps, kept/dropped lists, source Markdown and JSON are preserved there; earlier review folders remain unchanged. Classification/citation/chaining/selection replay and copy/link checks passed. Two Session 002 Recap bullets exceed the nominal word limit; the requested summaries and all generated text remain unchanged for review.

Session 002 required one unchanged-prompt retry each for threads 2 and 10, followed by a validation-only asset-role schema repair. All other responses were reused. Initial evidence and schema are preserved; the 49 implementation checks passed again. See [pass 8 generation details](experiments/session-004/pass-8/README.md), generation-journal.json, generation-inputs.json and generation-verification.json. No semantic publication policy or prompt was tuned during generation.

Current resume point: user review of the new Sessions 001–002 summaries. Remaining unjudged observations are in review run-notes.md and learnings; do not silently fix them or proceed to 003–004 review. Overall status remains implementing for the broader pipeline; this generation/copy request is complete.

## Pass 9: General Encounter Coverage

The user approved the general EX-079 remedy and requested a fresh Session 001–002 chain and unified-review copies. Approval and exact prior omission were saved in learnings before changes. Implemented [pass 9](experiments/session-004/pass-9/README.md): one historical call now receives full scene context plus scene encounter candidates, selects otherwise-unrepresented noteworthy interactions independently from enduring consequences/open goals, and propagates only focus beats to the Summary and Recap. Existing base thread/event cutoff and all open-matter filters remain; the overall historical policy explicitly expands via the encounter channel.

64 direct checks passed, plus syntax/schema/CLI checks. Fresh generation is underway and provenance is retained in pass 9. Destination is deployment/unified-review/archive/14-PASS9/. Current task continues through generation, verification and copying; this is not a handback gate. Low-stakes commitment filtering remains registered/deferred, and the low-impact/high-lasting comparison is not being run.

## Pass 9 Generation and Copy Completed

The approved encounter-level change and fresh Sessions 001–002 run are complete. Outputs are in [14-PASS9](../../deployment/unified-review/archive/14-PASS9/0-START-HERE.md). Session 001 now includes Dunk's encounter with Gill as one added historical encounter; Session 002 adds two encounters (fauns and Uriah/Ingrid). Both preserve the hidden incidental mule Goal. Earlier review outputs remain unchanged.

64 direct checks passed before generation. Actual structural verification, selection replay, source accounting/citations, unchanged input/implementation hashes, exact copies, full-text source views, Recap counts/word limits and links passed. Session 001 had one writing-only retry for an omitted selected ID; original response is preserved. Session 002 completed without retries. No prompt/schema/implementation edits during generation. See pass 9 provenance, verification and review run notes. No semantic quality scores or user approval of these fresh outputs is claimed.

Current resume point: user review of the new Sessions 001–002 summaries. Remaining unjudged possible potion-plan overlap is recorded in learnings and run notes. The requested implementation/generation/copy task is finished; overall pipeline work remains implementing. Low-stakes commitment filtering and the separate low-impact/high-lasting comparison remain deferred. This supersedes earlier notes that generation was underway.

## Pass 10: Prompts From General Patterns (2026-11-01)

The `review-pipeline` review of pass 9 found its prompts overtuned to the test Sessions. The user and the agent interviewed each flagged rule down to a general pattern, recorded in `learnings/` as PREF-045 to PREF-052, plus a PREF-014 application and an EX-074 reinterpretation (SRC-58). [Pass 10](experiments/session-004/pass-10/README.md) rewrites every flagged prompt site from those patterns, with unrelated fictional examples. It also moves the drop of `low` standalone history beats from the model into code, which records what it drops. Verification without generation: compile, schemas and templates; pass 9 selection replay unchanged; a fixture for the new filter; an overtuning name sweep. No Session has been generated with pass 10.

Resume: when the user asks, generate pass 10 Sessions and review them with `/review-pipeline`. Production cutover and the deferred investigations remain out of scope.

Pass 10 generation (2026-11-01): Sessions 001–002 generated with no retries. The `/review-pipeline` review found 11 failures (pass 9: 19), with all prompt checks passing. The main recurrence is a Session 001 duel goal; see the pass 10 README. Awaiting the user's verdicts. Review copies have not been made.
- Probe (2026-11-01): [an offer of help that doesn't name the goal](experiments/session-004/probes/ned-capability-match/README.md) recovers Drop Dead Ned (EX-080) in three of three runs. Not yet applied to a pass.

## Pass 11 Generation (2026-11-01)

The user requested pass 11 for Sessions 001–002 and explicitly selected inclusion of the tested offer-matching fix. Created a new pass from pass 10, copying only prompts, schemas, helper code and the empty Session 001 seed. The facts prompt exactly matches the probe; no earlier generated outputs or Session 002 seed were reused. Other prompts and selection policy are unchanged. Syntax, schemas, templates and CLI loading passed before generation. Input/implementation hashes are in `pass-11/generation-inputs.json`; generation is running through `pass-11/generate.sh`, with the full provider log in `generation.log`. Continue through generation, structural verification and completion notes; no production cutover or deferred threshold investigation is included.

### Pass 11 Completed

Fresh Sessions 001–002 completed without retries, including Matters JSON, Summary, Table Recap, kept/dropped records, rendered prompts and raw responses. [Pass 11 results](experiments/session-004/pass-11/README.md) link both Summaries. Session 001 shows 9 history bullets and 11 open facts; Session 002 shows 12 history bullets and 19 open facts. Verification passed schemas, classifications, source references, prompt snapshots, selected/written IDs, exact deterministic selection replay, unchanged source/implementation hashes and fresh state chaining. One Session 002 Recap bullet (Ned) is 37 words against the 35-word target; outputs are preserved as generated.

Ned is shown as enabling toward the dragon in both Sessions; Naggeneen’s reward-only offer stays hidden in Session 002. These are observed classifications/publication outcomes, not approval of the wording or evidence from a controlled comparison. The duel Goal/obstacle recurrence remains in both Summaries. The requested run is complete; resume with user review or a separately requested `review-pipeline` assessment. Overall item remains implementing. No production cutover, threshold experiment or review-folder copy was performed.

## Pass 12 Approved Implementation and Generation

The user approved the seven general proposals with “implement then run pass 12”. Approval is recorded in SRC-59 and the pass 11 feedback record before changes. [Pass 12](experiments/session-004/pass-12/README.md) implements end/completion significance guidance, causal obstacles, job outcomes, a guarded adventure-objective question path, cross-heading detail relevance, contextual opportunity wording, and deterministic narrative/event ordering. Goals add primary/other adventure priority; questions add role, basis and validated goal linkage; history adds focused evidence and an event anchor sorted by Ledger position. No new model call or named Session exception. The established qualitative rubric remains in force; no numerical assessment was performed.

25 direct checks passed, including schema/examples, question guards, dependency suppression, priority continuity/order, chronology across interleaved scenes, invalid anchor rejection and focused writer inputs. Fresh chained Sessions 001–002 are starting through pass 12/generate.sh. Continue through generation, structural verification and recording actual outcomes. The derived review guide is being refreshed from approved evidence; no full pipeline quality review or adoption is claimed.

Pass 12 generation repair: the first Session 001 step 3 request was rejected by the provider for compiled-grammar size, before any fact response was returned. Preserved the original schema/prompt/log/manifest. A compact per-kind classification union replaces the all-kinds nullable transport object; per-kind validators and selection semantics are unchanged. All 25 direct checks still pass. Resume reuses valid steps 1, 2 and 2c and retries step 3 onward, recorded in generation-repairs.json.

### Pass 12 Generation Completed

The approved seven general refinements and fresh Sessions 001–002 generation are complete. [Pass 12 outputs](experiments/session-004/pass-12/README.md) link both Summaries, Recaps, state and kept/dropped records. All final source/schema/classification/reference/snapshot/writing/chaining/anchor checks and deterministic selection replay passed. 28 direct checks cover policy boundaries and transport decoding. Two pre-response provider grammar-size rejections were resolved by a compact encoded-classification transport with unchanged local per-kind validation. One Session 002 thread_2 metadata retry reused all other valid responses; originals and repair scripts are preserved. One potion Recap bullet is 37 words against 35.

Observed improvements: no duel Goal/obstacle, thief-catching job outcome, selected adventure-objective treasure question and valid chronological anchors. Remaining model output issues include both adventure goals rated primary (treasure still first), map-framed goal/question text, missing later dragon-origin question and recurring hierarchy detail. These remain unjudged fresh outputs, not proof the desired quality bar is met. No output rewriting or semantic mid-run tuning. Resume with user review of pass 12; broader status remains implementing.

Review guide refresh completed from learnings state `4979ca9f4264` after pass 12 outcome capture. All 126 EX/PREF entries are covered, IDs are preserved/retired explicitly, and added-checks.md is unchanged. Rebuild details and the prior guide are retained in pass 12. The requested implementation/run task is complete; overall status remains implementing for further output review.


### Deferred Prompt Update: Established Danger for Brewing Troubles

2026-11-01: the user finished an interview on Gill’s sons and requested a durable note for a prompt update **after the other pass 12 review feedback has been discussed**. Preserve that sequencing; do not implement this note yet. Evidence and exact judgments: [EX-045 clarification](../../learnings/examples/meanwhile.md#ex-045-the-users-verdicts-on-the-session-001-brewing-troubles), [PREF-037](../../learnings/preferences.md#pref-037), SRC-60.

Pending generic prompt change: require established danger/developing harm in the adventure/play’s framing, rather than an extractor’s inference that an activity could be dangerous. Mere competition for prospective loot, reward or other gain is insufficient. Do not require a rescue request, accepted quest or player action when actual danger is established and the party could affect it. Use general wording, with no Gill/sons/session-specific exception. Inspect existing harm-clarity/evidence classification before deciding whether any code change is needed; no new field or threshold has been selected.

Resume: continue discussing the remaining pass 12 review findings with the user, then include this deferred distinction in the subsequent generic prompt revision. No prompts, guide, generated outputs or selection code changed for this capture; overall status remains implementing. The saved review guide now predates this clarification and should be refreshed before the next full review.


### Pass 12 Review Discussion Decisions

Proceed one issue per round with context and a recommendation; skip expressly allowed cases and group duplicate check IDs that describe the same issue. SE-008: user agrees the missing Session 001 shirt-refusal obstacle is allowed without a live shirt-acquisition pursuit; withdraw that failure. Refresh baseline review expectations to condition preservation on current eligibility. See the dated clarification in learnings/README.md#summary-headings (SRC-60). Continue with the mule offer retained inside the otherwise wanted Gill historical encounter (RC-016 / part of SE-001); keep the missing duel-history issue separate. Prompt changes remain deferred while feedback is discussed.


Pass 12 discussion, next decision (SRC-60): mule-offer detail in Dunk/Gill history is acceptable either included or omitted (“I am actually fine with this either way”). Withdraw Session 001 RC-016 for this detail and remove that component of SE-001’s failure; revise the guide’s explicit historical mule exclusion accordingly when refreshing it. Evidence: EX-079 dated tolerance in learnings/examples/last-session.md. Next issue: missing historical duel/challenge encounter (remaining SE-001 component), distinct from the already excluded minor open Goal. Prompt changes remain deferred.


Pass 12 discussion (SRC-60): user accepts the challenge encounter as history and judges its omission relatively minor. Keep this as a minor historical-coverage improvement, separate from excluding the honor pursuit from open Goals. Evidence and exact verdict: learnings/README.md#summary-headings, SE-001 clarification. Next issue: unnecessary map reference in the treasure Goal in both Sessions (RC-030 / SE-002). Continue one issue per round; prompts remain unchanged.


Pass 12 discussion (SRC-60): outcome-only goal preference reaffirmed; map reference in the treasure goal is a very minor issue. Address the general rule rather than this example specifically; evidence EX-051 / PREF-033. Next issue: clue-framed treasure question in both Sessions (RC-044 / advisory RC-049), separate from goal wording and from the already accepted adventure-question eligibility change. Prompts remain unchanged while discussion continues.


Pass 12 discussion (SRC-60): underlying treasure question wording preferred over map-clue framing; user judges it another minor issue. Evidence: EX-017 dated clarification. Skip the expressly tolerated Session 001 origin omission and provisionally allowed recurring harm; carry forward the already explicit rejection of the reporting hierarchy (SRC-59) without needing a fresh verdict. Next new issue: Ned’s familiar-person profile label in Session 002 (RC-060), keeping his relevant hire terms distinct. Prompts remain unchanged.


Pass 12 discussion (SRC-60): user tentatively accepts Ned’s first-mention descriptor; withdraw this RC-060 finding. More substantive presentation preference: combat-hire opportunities can say hire -> fighting help without reproducing fee/rebate terms; 100 gold is acceptable in history. Evidence EX-080, PREF-028, PREF-049. Deferred generic revision must distinguish stored contract evidence from displayed precision and soften the absolute familiar-name rule; SE-032/033 must not demand every price/term in displayed wording. Next issue: advisory RC-019, unchanged still-open goals/questions repeated between Sessions (no approved remedy yet). No prompts or outputs changed.


Pass 12 discussion (SRC-60): retain eligible matters in subsequent Summaries while open, even word-for-word unchanged. Withdraw RC-019 advisory; next guide refresh must retire the repetition-only objection. Evidence EX-027 / PREF-021. No cosmetic variation or new/changed-only filtering requested. Next issue: Session 002 dragon-vs-treasure goal priority (SE-009); deterministic sorting exists but both goals were classified primary/high. Prompts and outputs unchanged.


Pass 12 discussion (SRC-60): user approves putting the adventure currently driving party choices first (dragon hunt above treasure in Session 002). Improve general priority classification feeding existing deterministic sorting; do not add named-goal exceptions or rank isolated immediate actionability. Evidence EX-071 / PREF-033. Next issue: separate window and sleeping-potion opportunities in Session 002 (RC-040 / SE-029 / part of SE-034). Prompts and outputs unchanged pending completion of feedback.


Pass 12 discussion (SRC-60): window/potion plan merge confirmed (“I prefer merged”). User asks why if/then format is missing. Actual potion bullet is conditional; window bullet is not. Agent had paraphrased both excerpts. Writing prompt says “preferably” If X,Y and permits source-first attribution; no deterministic format enforcement. Deferred recommendation: make conditional action/advantage structure explicit, with essential caveats allowed, and merge plan components before one-bullet-per-item writing. Evidence EX-040. Answer the user’s format question before moving to the map-checking-as-opportunity issue (RC-061 / RC-069 / SE-034). No prompt/output changes.


Pass 12 discussion (SRC-60): “Great, I approve” confirms the merged example and explicit conditional action/advantage opportunity format, with essential uncertainty in a second sentence allowed. EX-040 / PREF-028 updated. Apply general merging and wording rules in the later revision, not this named example. Next issue: map checking as an opportunity (RC-061 / RC-069 / SE-034). No prompts or outputs changed.


Pass 12 discussion (SRC-60): user explicitly approves removal of map-checking from What could help. General distinction: a trigger whose benefit merely achieves the same goal supplies no enabling advantage; trigger wording alone does not qualify. EX-074 / PREF-035 / PREF-046 updated. Next issue: missing fairy-emergence question in Session 002 (part of SE-014); the missing Session 002 dragon-origin question is already expressly judged worth fixing in SRC-59 and need not be re-litigated. Remaining later advisories include Gill’s sons question (distinct from established-danger trouble judgment) and penance recipient stake (filter investigation deferred). No prompts or outputs changed.


Pass 12 discussion (SRC-60): user approves preserving the fairy-emergence question as a meaningful mystery (SE-014). Capture grounded unexplained world-change candidates generically; no named-question insertion. Evidence: learnings/README.md#summary-headings, dated SE-014 clarification. Next issue: older golden’s “What happened to Gill’s sons?” as a mystery (SE-015), separate from the rejected Brewing Trouble. Then penance’s low recipient stake remains advisory/deferred. Prompts and outputs unchanged.


Pass 12 discussion (SRC-60): omit “What happened to Gill’s sons?” on current evidence; user agrees an expedition’s unknown outcome alone is no meaningful mystery. EX-019 updated; withdraw sons-omission advisory under SE-015 and adjust the old golden expectation on the next guide refresh. Do not require danger for mysteries or hardcode a sons exclusion. Last remaining distinct review note: penance’s low recipient stake (RC-053), with the general low-stakes commitment filtering investigation already deferred. Prompts and outputs unchanged.


### Pass 12 Review Discussion Completed (SRC-60)

User accepts keeping Uriah’s penance obligation for now; low-stakes commitment filtering remains deferred in its existing registered investigation. Exact verdict captured in learnings/examples/promises-and-debts.md. RC-053 is no longer an unresolved inclusion objection for this occurrence. All distinct review items are discussed or covered by express previous judgments; stop presenting already allowed cases. No prompt, code, guide or output changes were made during this feedback capture.

Pending subsequent generic revision: established rather than inferred Brewing Trouble danger (no rescue-acceptance requirement); current-adventure goal priority; complementary-plan merging and explicit conditional action/advantage opportunity wording; exclude direct goal pursuit from opportunities; reduce displayed contract precision while preserving state evidence; recover grounded meaningful question candidates; carry forward the previously rejected reporting-hierarchy detail. Outcome-only Goals and underlying-question wording remain preferences with these occurrences rated minor; challenge history is suitable but its omission minor. Review-guide refresh must reflect the allowed missing targetless obstacle, optional mule history detail, first-mention descriptor tolerance, repeated eligible open matters, omitted sons mystery and retained penance. Preserve all per-issue scope and tentative judgments from learnings rather than turning examples into named exceptions. Resume with the subsequent prompt/guide revision when requested; no new generation or threshold experiment is authorized merely by completing discussion.


### Pass 13 Learning and Prompt Revision Completed (2026-11-01, SRC-60)

The user’s “Okay, please start by updating learning and prompts” supersedes the earlier wait-until-review-is-complete notes. [Pass 13](experiments/session-004/pass-13/README.md) now implements the approved generic refinements in six system prompts. Parent pass 12, its inputs and outputs are preserved. New runner identity/version is 13; schemas, validators, classification transport, thresholds and executable selection semantics remain unchanged. The inherited fact example’s empty independent-goal reference was corrected to schema-required null.

All 28 offline direct checks passed: schema/example/template contracts, runner import/syntax, parent hashes, executable AST comparison, complete selection replay for both prior Sessions (only provenance version differs), writer input assembly and representative template rendering, existing priority/goal-pursuit/harm/question/low-stake guards, and a test-term sweep. These establish mechanics and prompt presence, not model compliance or fresh quality. No LLM generation, unit-test suite, production changes or deferred threshold investigation was performed.

Learnings retain exact feedback, first-mention tentativeness, the minor severity distinctions and explicit allowances. The derived review guide was incrementally synchronized with SRC-60 (not a fresh full-corpus skill extraction), preserving/rechecking coverage and retiring stale objections. Added RC-073–RC-075; retired RC-019 and RC-060. User-added checks are unchanged. See the pass’s review-guide-refresh.json for affected IDs and counts.

Current resume point: user inspection of pass 13 or a separately requested fresh generation. Fresh Session 001 must start from its empty seed and Session 002 must chain from that new result; no pass 13 runs exist. The current learning/prompt update request is complete. Overall pipeline item remains implementing; broader adoption and separate investigations remain open.

### Pass 14 Prompt Generality Revision (2026-11-01)

After a review of pass 13's prompts for guidance too specific to the four test Sessions, the user asked to "fix all of this". [Pass 14](experiments/session-004/pass-14/README.md) revises all eight system prompts: patch sections folded into their sections, the opportunity writing rule reduced to its distinctions, allowances removed from prompts, duplicated contract-precision and lifecycle text stated once, and fictional re-skins of Session details (statue question, dead dwarf, an ally's caveats, forecast questions, curator, map labels, "more experienced than", corrected distance, item fit) replaced. Runner, helpers, schemas and templates are unchanged apart from the pass number and selection version. Offline checks passed ([verification](experiments/session-004/pass-14/verification.json)). No generation has run.

Current resume point: a fresh chained Sessions 001–002 generation of pass 14 when the user requests it, then review with `review-pipeline`, which now drops allowed occurrences.

### Pass 15 Detail Field (2026-11-02)

The user proposed a `detail` field in the step 6 output to absorb extraneous detail the writer resists dropping. Agreed refinements: keep the bullet field named `text` (not `title` or `headline`), put `detail` before `text` in the schema, apply it to "Last session..." as well, state per heading what the bullet keeps as well as what moves out, and check over-pruning in review. [Pass 15](experiments/session-004/pass-15/README.md) implements this on copies of pass 14's step 1–5 outputs; `generate.sh` reruns both chains from step 6. Offline checks passed ([verification](experiments/session-004/pass-15/verification.json)): step 7 renders a byte-identical `summary.md` from pass 14's writing with detail added, and stores detail in `matters.json`. No generation has run.

Generated 2026-11-02 at the user's request; run 1 completed. Repeat runs showed the pass 15 writer omitting trailing open headings in 4 of 7 calls (pass 14's prompt: 0 of 5 on identical input), so run 1's Summaries remain in place and the failures are preserved. Details in the pass 15 README (unreviewed by the user).

The user then asked to revert the `detail` field. Pass 15's step 6 prompt and schema are pass 14's again; a single Session 001 run from step 6 completed with all items present.

### Pass 16 Split Step (2026-11-02)

The user's new approach: leave the step 6 writer unchanged and add a step 6b that only splits each written bullet into `text` (rendered) and `detail` (stored), never changing the bullet count. The user chose this over splitting step 6 into a de-duplication pass and a formatting pass, following the agent's recommendation: it gives a controlled comparison on pass 14's existing writing, and step 6's rules mix content and form too closely to divide cleanly. [Pass 16](experiments/session-004/pass-16/README.md) implements step 6b on copies of pass 14's step 1–6 outputs. Code enforces the count: a response with wrong IDs is retried once, then any missing bullet keeps its written text with an empty `detail`. Each run writes a phone-readable `split.md`. 17 offline checks with the model stubbed passed ([verification](experiments/session-004/pass-16/verification.json)). Not generated, at the user's direction.

In a heading-by-heading interview the user then approved per-heading split guidance (PREF-057, SRC-61), now in the step 6b prompt with a fictional example per heading. At the user's request step 6's obstacle wording no longer tells the writer to keep a way past the obstacle, so `generate.sh` now reruns from step 6 (`--from 6b` remains available for a split-only comparison on pass 14's writing). Offline checks passed again.

At the user's request `text` is now rewritten naturally from what stays rather than cut down (PREF-057 history). The user then asked to run the pass: `generate.sh` completed both Sessions on 2026-11-02 without retries or fallbacks, and the Summaries and split files are in `deployment/unified-review/pass-16/`. Agent observations, including three possible misses against the approved guidance, are in the pass 16 README.

### Pass 16 History Count and Pass 17 (2026-11-02)

The user found Session 002's pass 16 "Last session..." longer than expected (12 items) and asked for an analysis of the items' JSON. The agent found (unjudged): `thread_1` (map markings) and `thread_13` (penance and donation for them) share anchor beat `beat_53`, one bargain told twice, with the debt half fully shown under "Promises and debts"; Dunk's shirt plan is told across three items (`thread_9`, `thread_10`, `scene_10`); and four items passed on speculative lasting reasons ("may come up again", "may return", "is unsettled": `thread_3`, `beat_72`, `thread_14`, `thread_15`). Options offered: A one item per anchor beat; B a step 2c field for established versus possible lasting effect, required for medium/medium items; C drop medium/medium threads; D drop items whose lasting effect is wholly shown as open facts; E link threads serving one plan. The user said "Do A now, and add a woekitem to try b on all four sessions".

[Pass 17](experiments/session-004/pass-17/README.md) implements A in step 5. Offline, Session 002 goes from 12 to 11 items (`thread_13` hidden); Session 001 and all open headings are unchanged. Not generated. B is captured as [Require established lasting consequences in Last session...](../established-lasting-consequences/).

Current resume point: the user's review of the pass 16 Summaries; pass 17 generation when requested.

