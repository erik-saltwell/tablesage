# Investigate Session Summary Quality Regression

## Intended Outcome

Understand why generated Session summaries have become longer and less useful, distinguishing prompt effects from changes in source artifacts and variation between generations. The user and an LLM agent will review evidence together. The workshop concluded with the user accepting the experiment below as ready; rubric definition is next.

## Reference Examples and Workspace

Use an isolated testing workspace, with `~/data/tablesage_summary_test` as the proposed location. The user will hand-review two Sessions: a prior Session supplying recap context and a current Session. Generate all outputs for the reviewed Sessions before beginning the controlled prompt comparisons.

The user will also supply one good summary and one poor summary of the same general Session. Their generated transcripts differ because the Session was processed twice. Preserve both original summaries untouched, with their available source artifacts and generation details. Keep observations separately. These examples identify useful contrasts but cannot by themselves establish that the prompt caused the regression.

## Agreed Comparison Approach

- Review the good and poor examples together to identify concrete differences in usefulness, such as missing consequences, repeated events, excessive minor detail, or an unclear ending situation. These examples are possible review concerns, not an approved rubric or findings.
- Trace important differences backward through available artifacts: determine whether information was present in the summary's Ledger, present only in its transcript, or absent from both. Missing historical artifacts limit conclusions rather than supplying evidence of a cause.
- Generate upstream outputs once and freeze them for the controlled comparisons. Hold the model and generation settings constant. Re-run summary generation against those fixed inputs rather than regenerating the entire pipeline for every prompt.
- Begin with the current prompt and one historical checked-in prompt. Prefer the revision that produced the good reference summary, if it can be identified and is compatible with the frozen inputs.
- If the preferred historical prompt expects a different source format or pipeline, treat that as a separate pipeline comparison. Use a compatible historical prompt for the controlled prompt comparison; do not silently mix source changes into a wording comparison.
- Generate two independent outputs per prompt. Four initial candidates keep review manageable while revealing whether a problem recurs or varies across runs.
- Review candidates blind, without revealing their prompt versions. The user and agent first record useful details retained, important omissions, repetition, unnecessary length, and other observed issues. Reveal versions afterward and investigate the instructions associated with the differences.
- Record word counts as supporting evidence, not a substitute for usefulness. Distinguish the generated summary body from the prior recap and Player Introductions inserted by the application.
- Investigate upstream changes separately if the controlled prompt comparison does not explain the decline.

## Rationale and Limits

Fixed inputs and model settings make differences easier to attribute to prompts. Blind review reduces expectations about older versus newer versions. Two generations per prompt provide limited evidence about variability without turning the initial experiment into a large benchmark. Source tracing protects against blaming a summary prompt for information already lost upstream.

The experiment begins with one current Session and its prior recap context. Findings may be specific to these Sessions. Historical provenance and compatible prompt versions may be unavailable; do not invent missing inputs or generation settings. Conclusions should distinguish observed evidence, plausible explanations, and unresolved causes.

## Pipeline Context

The current [Summary generator](../../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py) receives the current Ledger plus metadata, attendees, and glossary. The application inserts the prior recap and current Player Introductions into the returned summary template. [Scene Breakdown and Recap specification](../scene-breakdown-artifact-contract/specification.md) describes these upstream artifacts and composition behavior. Historical prompt revisions have used different narrative sources, including role transcripts.

## Outstanding Choices

The precise workspace path, Sessions, reference files, historical prompt revision, model/settings, and run-storage mechanism have not been selected. No workspace has been created and no experimental generations or evaluations have been run. The user subsequently approved the qualitative investigation rubric saved in [intent.md](intent.md). The outstanding experimental choices remain for subsequent discussion; this document records the agreed direction rather than an implementation plan.

## Shared Prompt Harness Workshop

The later workshop expanded tooling to Ledger efficiency as well as Summary quality. Accepted decisions are recorded in [harness.md](harness.md), including independent fixed inputs, shared production generation, complete prompt/attempt evidence, one generation per invocation, and existing references as baselines without new baseline calls. This supersedes mandatory repetitions and a fixed initial blind packet; the broader investigation remains open.

## Agreed Investigation Sequence — 2026-10-06

The workshop on the general approach is closed with the user's agreement. The next investigation proceeds in this order:

1. Simplify the Summary prompt: make it shorter, clearer, and more focused while preserving its intended behavior and useful distinctions. Do not redesign the output sections or deliberately change the scene log's content allocation during this step.
2. Compare output from the simplified prompt against the existing reference evidence using frozen inputs and consistent model/settings. Check for lost useful information, weakened factual boundaries, or other regressions before carrying the simplified prompt into the next step. A shorter prompt is not itself evidence of better quality. The comparison is a checkpoint, not proof of broad performance; keep the first simplification pass bounded.
3. Then brainstorm how to compress the scene log so it is briefer and prioritizes information likely to be reincorporated at the table. The user's motivating concern is excessive scene detail and insufficient attention to clues, open loops, and clocks. Concrete section designs, length allocations, and prompt wording remain undecided.

Separating simplification from scene-log compression makes their effects easier to distinguish. Simplification may also make later design work easier by reducing overlapping instructions, but this benefit remains a hypothesis. Retain distinctions that cannot be shortened safely; do not pursue brevity at the expense of useful output.

The agent's earlier proposals for specific section responsibilities and output allocations were not adopted. Design of a simplified prompt is next, followed by the comparison checkpoint; scene-log redesign is deferred. No candidate prompt edits or new generation calls were made in this workshop.

The approved qualitative investigation rubric in [intent.md](intent.md) remains unchanged. The sequence supports explanatory confidence by separating changes, meaningful quality judgments by checking usefulness rather than prompt length alone, reproducibility through the existing harness, and practical effort through a bounded first pass. These are design judgments, not measured improvements.

This sequence supersedes earlier candidate-selection directions where they conflict. The historical comparison phases in [plan.md](plan.md) require revision before being used for the new investigation; the delivered [harness](harness.md) remains applicable. The opening setup choices in this document are historical; current workspace and input details are recorded in [item.md](item.md) and [progress.md](progress.md).

## Simplification Experiments — 2026-10-06

A workshop on step 1 settled the simplification design: one job per section, with the reincorporation categories distributed to the sections they serve; a one-sentence global filter; a single "How to read the Ledger" list for the fact and attribution rules; a short style block; one annotated output skeleton in place of the worked example and prose format section; and a mechanical Final Check. The user accepted each change. They are recorded as six experiments in [experiments.md](experiments.md). Running them cumulatively is an agent proposal the user has not yet confirmed. Scene-log compression remains deferred to step 3, and no prompt edits or generations have been made.

## Step 3 Moved to Its Own Work Item — 2026-10-06

At the user's direction, step 3 (scene-log compression for reincorporation) is now a separate work item: [Improve the summary scene log for reincorporation](../scene-log-reincorporation/). It needs its own summary-quality rubric and full lifecycle (rubric definition, borrowing brilliance, workshop, experiments), distinct from this investigation's rubric. It reuses this item's harness, frozen inputs in `/home/eriksalt/data/tablesage_summary_test/`, and reference summaries by link. The agent suggested `prompts/summary/experiments/combined-1346/` as its starting prompt so scene-log changes are measured on top of the simplification; the user has not yet decided. The motivating evidence is recorded in [experiments.md](experiments.md): no simplification brought the body near 700 words, and Scene Breakdown remains the bulk.
