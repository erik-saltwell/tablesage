# Approaches

Pipeline and prompt changes we tried, what happened, and what they taught. Read the **Lessons** first: they are the reusable part. Each entry then records one approach, its observed result and its status. Run-by-run detail for the unified pipeline lives with its experiments: the pass READMEs under [`.work-items/unified-matters-pipeline/experiments/session-004/`](../.work-items/unified-matters-pipeline/experiments/session-004/) and the item's [progress.md](../.work-items/unified-matters-pipeline/progress.md).

Status values: **kept**, **superseded by APP-###**, **reverted**, **not adopted** (tried and rejected), **lost** (it helped, but no trace remains), **in progress**.

## Lessons

1. **A threshold in code on a classification is reliable; a prompt clarification alone is not.** Borderline items survive prompt rules but are removed by filtering their ratings (APP-001, APP-011, APP-013). This is why the model classifies and code decides (PREF-014).
2. **A model rating can contradict its own stated evidence.** Make the model establish the evidence first, then rate, and prefer deterministic structural checks where possible (APP-030; EX-055's `action_offered: yes` beside "no terms were agreed").
3. **A case-specific fix in the learnings comes back as a disguised copy in the prompts.** Record the general pattern behind a judgment before writing the prompt rule, and use fictional examples whose situations have no test-Session counterpart (APP-013, APP-034; PREF-012).
4. **Generic ratings lose the per-matter distinctions the user built.** End versus means, direct versus step, articulated harm and open-ended question each needed their own fields (APP-034, pass 4).
5. **Guidance against repetition only covers the inputs a prompt actually sees** (APP-017). Structural placement (one home per fact) removes cross-heading restatement more reliably (APP-034).
6. **Fix wording where the text is generated**, not in a downstream rewriter (APP-022).
7. **A small, fictional, labelled testbed lets you derive a filter from approved judgments** instead of guessing thresholds (APP-011).
8. **Check a port against earlier rejections.** The lance promise was fixed on 2026-10-19 and came back after the port and again in the unified pipeline (APP-030, EX-042).
9. **Splitting selection from writing does not help when selection itself is the problem** (APP-002). A narrow verify-against-evidence role catches unsupported claims, but only with a strict keep, narrow or flag contract (APP-003).
10. **Simplify prompts for clarity, not token savings, and test on more than one run** (APP-008).
11. **Single runs do not separate model variation from a change's effect.** Report observed differences as observations, not causes, unless the comparison controls for variation.

## Lost or Never Shipped

| ID | What helped | Why it is not in the pipeline |
|---|---|---|
| [APP-003](#app-003) | An evidence-checking editor removed unsupported claims from Revelations | Kept "in development"; the single-call prompt shipped instead |
| [APP-004](#app-004) | A source-first selector working from literal quotes made the evidence checkable | Kept "in development"; superseded by the 2026-10-25 redefinition |

## Unified Pipeline

### APP-034
**Unified Matters pipeline: threads and typed facts, deterministic selection, one writer and a thread-organised recap.**
- Date / source: SRC-55, SRC-57 to SRC-60 (2026-10-29 to 2026-11-01)
- What was done: the user's four steps (PREF-015). Decide what is true (threads, beats and typed facts: `want`, `owe`, `blocked_by`, `could_use`, `unknown`, `threat`), what to keep (per-kind classifications filtered in code), where it goes (each fact on one home thread; history, open headings and the stopping situation), and how to phrase it (one writer).
- Result, in outline:
  - Pass 3: cross-heading restatement largely gone, but generic `importance`/`actionability` ratings lost per-matter distinctions and brought back fixed failures. Pass 4 restored per-kind fields and the user's own filters.
  - Passes 5–6: goal-wording and opening fixes (EX-051 to EX-061); deterministic pointer rules fixed duplicate offers, while ratings still ignored their own evidence (EX-055).
  - Pass 7: supported implicit openings, resource identity and the scene-local danger boundary (EX-065 to EX-067). Pass 8: the approved EX-070 to EX-078 fixes, including equivalence reconciliation and assets out of open headings. Pass 9: encounter coverage in history (EX-079).
  - Pass 10: every overtuned prompt rule restated from the general patterns PREF-045 to PREF-052; the automated review counted 11 failures against pass 9's 19 (agent observation).
  - Passes 11–13: offer matching (EX-080), significance, ordering and the adventure-question path (SRC-59), then the pass 12 review refinements (SRC-60). Pass 13 has not been generated.
- Current status: in progress. The user has not yet decided between this pipeline and the existing artifacts (PREF-018).
- Lessons: 3, 4, 5, 11.
- Examples: EX-003, EX-021 to EX-024, EX-051 to EX-081

### APP-017
**Pass upstream matters into downstream prompts, with do-not-repeat guidance.**
- Date / source: SRC-43 (2026-10-28)
- Result: duplication between Developments and the forward-looking categories continued (EX-022), because Developments were not an input.
- Status: superseded by APP-034.
- Lesson 5.

## Presentation

### APP-022
**Phrasing guidance inside each generating prompt, instead of a separate phrasing call.**
- Date / source: SRC-44 (2026-10-28)
- What was done: an earlier design put phrasing in its own LLM pass over the Summary. The user moved it: "rather than putting this into its own LLM call, can you just embed the guidance into each of the generated matters used".
- Status: kept.
- Lesson 6.

## Goals, Obstacles and Openings

### APP-027
**Goals as tracked objects: stable IDs, significance, parent goal and lifecycle, filtered in code.**
- Date / source: SRC-19, SRC-21 (2026-10-21)
- Result: the end-not-means rule is enforced in code, but the parent link varies between runs (EX-036).
- Status: kept; carried into the unified `want` classification.

### APP-028
**Obstacle lifecycle (`active`, `anticipated`, `resolved`, `obsolete`) and goal links.**
- Date / source: SRC-29 (2026-10-24), SRC-34
- Result: future flight was classified `anticipated` in all trials and excluded. After solution-versus-obstacle guidance, getting the sword no longer resolved the scales. The `impedes:` title suffix was tried and reverted (EX-039).
- Status: kept.

### APP-029
**Goal-linked openings with opening/action/advantage fields, lifecycle and a parent hierarchy.**
- Date / source: SRC-31 (2026-10-24 to 25)
- Result: the shirt cluster collapsed to one top-level opening (EX-040); goal-less reward offers dropped out (EX-041).
- Status: kept; superseded in the unified pipeline by reconciliation of equivalent and complementary openings (PREF-045).
- Lesson: a parent link plus a code filter keeps sub-steps in the data without showing them as parallel options.

## Promises

### APP-030
**Classify obligations by burden, consequence, commitment type and stake, then filter in code.**
- Date / source: SRC-26, SRC-41, SRC-43 (2026-10-22 to 28)
- Result: the commitment-type filter alone did not remove the lance; the model called it a `personal_promise`, and `stake` came back `medium` because "The model transferred the importance of the broader outcome onto the specific commitment, despite the rubric telling it not to." Establishing evidence of interest in the specific act first removed it. It returned in unified pass 8 with stake `low`, which the filter keeps.
- Status: kept.
- Lessons 2, 8.
- Examples: EX-042

## History

### APP-032
**Rebuild New Assets as goal-linked support, filtering weak assets that did not come from an opportunity.**
- Date / source: SRC-13, SRC-36 (2026-10-20, 2026-10-26)
- Result: concise names ("Squints the halfling recruit"); routine cash still appeared.
- Status: superseded by APP-034 (gains told in history; held assets in campaign state).

### APP-033
**Developments with impact, lasting-consequence and screen-time ratings, built after Revelations and New Assets.**
- Date / source: SRC-37, SRC-38 (2026-10-26)
- Result: Developments became "Last session..."; they were the item other categories most often restated (EX-003, EX-021 to EX-024).
- Status: superseded by APP-034, which keeps impact and lasting-consequence ratings for history.

## Revelations

All superseded by APP-034, which has no Revelations heading. Kept for their lessons.

### APP-001
**Clarify "progress" in the prompt, then classify and filter in code.**
- Date / source: SRC-33, SRC-35 (2026-10-25 to 26)
- Result: the prompt rule ("Extent, duration, or frequency alone is insufficient…") had no visible effect; the next run still saved the supply item (EX-001). The final code threshold (`substantial`/`resolved` progress, other ratings `medium`+) removed it. Few Revelations survived.
- Lesson 1.

### APP-002
**Two passes: select the content, then write it.**
- Date / source: SRC-17 (2026-10-20)
- Result: no effect. "The audit exposes decisions, but too much marginal material remains … the writer adds little beyond light rephrasing."
- Status: not adopted. Lesson 9.

### APP-003
**An evidence-checking editor as the second pass.**
- Date / source: SRC-17 (2026-10-20)
- Result: mixed. It removed unsupported claims but also swapped in unselected facts; a constrained claim editor stopped the additions, and a later run accepted an unsupported claim.
- Status: lost. Lesson 9.

### APP-004
**A source-first selector that returns literal quotes.**
- Date / source: SRC-17 (2026-10-20)
- Result: mixed. Every quote passed an exact-substring check and incidental candidates dropped out, but consequential qualifiers were cut.
- Status: lost. Lesson: literal evidence makes claims verifiable but does not guarantee the qualifiers are kept.

### APP-005
**An impact rating on each Revelation.**
- Date / source: SRC-17 (2026-10-20)
- Result: "Impact partly separates minor extras, but does not reproduce golden membership."
- Lesson: an importance rating is useful filter metadata; it does not replace a definition of what qualifies.

### APP-006
**Redefine Revelations as retrospective, with prior and current matters supplied as inputs.**
- Date / source: SRC-33 (2026-10-25)
- Result: far fewer entries; the diagnosis loop (EX-001, EX-004 to EX-008) became tractable; coverage of the older golden dropped by design (EX-011).

### APP-007
**An unexpectedness rating.**
- Date / source: SRC-35 (2026-10-26)
- Result: across 12 trials no item was rated trivial, and ratings varied between runs.

## Questions

### APP-008
**Simplify the Mysteries guidance.**
- Date / source: SRC-12 (2026-10-20)
- Result: worse in one run, which concurrent changes also disrupted; the saving was about 7% of the system prompt.
- Status: reverted. Lesson 10.

### APP-009
**Structured question fields: question, basis, relevance and question type.**
- Date / source: SRC-32 (2026-10-25)
- Result: made failures diagnosable: the extractor filled `basis` and `relevance` with weak content, exposing EX-014 to EX-016.
- Status: superseded by APP-010; `question_type` kept.

### APP-010
**Rewrite the prompt from the user's own definition, with four ranked dimensions.**
- Date / source: SRC-34 (2026-10-25)
- What was done: grounding, investigative depth, narrative payoff and investigative potential, each ranked `trivial` to `high` with a justification.
- Result: calibrated on the testbed (APP-011); the episode rule fixed the tomb questions (EX-018); the treasure question was filtered as instrumental (EX-017), later addressed by PREF-054.
- Status: kept; carried into the unified `unknown` classification.

### APP-011
**Calibrate on a labelled testbed, then replace the model's include/exclude with a deterministic filter.**
- Date / source: SRC-34 (2026-10-25)
- Result: "include when all four dimensions are `medium` or `high`" reproduced every approved include and exclude. Classification variance remains on real Sessions.
- Status: kept. Lessons 1, 7.
- Examples: EX-020

### APP-012
**Cumulative, linked, lifecycle-aware questions.**
- Date / source: SRC-34 (2026-10-25 to 26)
- Result: both tomb questions were marked obsolete in all three Session 004 runs (EX-018).
- Status: kept.

### APP-013
**Generic exclusion rules with fictional examples.**
- Date / source: SRC-32 (2026-10-25)
- What was done: each diagnosed false positive became a general rule plus a fictional include/exclude pair (the archivist, the ferryman, the sealed observatory), instead of a rule naming the Session case.
- Result: the rules alone did not stop the candidates; after APP-010 the model still generated them but ranked them low, so the filter removed them.
- Status: kept. Lessons 1, 3.
- Examples: EX-014 to EX-016
