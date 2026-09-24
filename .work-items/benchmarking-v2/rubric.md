# Benchmarking v2: quality rubric

**Status:** the dimensions were agreed on 2026-09-24. The numerical anchors have **not** been defined yet (see "Unresolved").

## Subject and intended effect

This rubric judges the Benchmarking v2 design and, later, its implementation, as described in [idea.md](idea.md). In short:
- A reviewed session is captured into a benchmark folder.
- A run re-runs the automatic session-processing steps in isolation.
- The resulting role transcript is scored against the reviewed one: text accuracy, role accuracy (correct / unassigned / wrong) and a glossary-term score, plus a history of runs.

The benchmark exists to show, with repeatable numbers, whether code or settings changes improve the automatic pipeline.

## Scale

Every dimension uses a 0–10 scale where higher is better. A score between anchors is allowed when the reasoning supports it. Each dimension is scored on its own. There is no total score, no weights, no target and no pass/fail threshold.

## Dimensions

### 1. Measurement validity

The scores reflect real transcript quality that matters downstream: who spoke, what was said, and names. They move when the pipeline gets better or worse. They don't move because of scoring artifacts, such as:
- differences in utterance boundaries
- casing and punctuation
- backchannels removed on purpose

### 2. Production fidelity

A benchmark run uses the same code and settings as real session processing. No copied or simplified version of the pipeline can quietly fall out of sync, so a good score means the app is good.

Kept separate from Measurement validity on purpose: a well-designed metric can score a pipeline copy that has drifted from production, and the reverse is also possible.

### 3. Reproducibility

The same benchmark, code and settings produce the same scores, or scores within a small, known noise range. A run doesn't depend on live campaign data and has no side effects on real sessions or the campaign.

### 4. Diagnostic power

When a score changes, you can quickly see why:
- which role was mistaken for which
- which glossary terms were missed or wrongly inserted
- which commit or setting changed since the previous comparable run

### 5. Low friction

Capturing a reviewed session and running a benchmark each take little effort. Each benchmark uses a reasonable amount of disk. Running one is quick enough that you'll actually do it while tuning.

## How the dimensions stay independent

Each pair below describes a result that's strong on one dimension and weak on the other:
- **Validity vs. fidelity:** a well-designed metric applied to a drifted pipeline copy.
- **Reproducibility vs. validity:** a deterministic score that ignores name errors.
- **Diagnostic power vs. validity:** a correct single number with no breakdown.
- **Friction vs. the rest:** a rigorous benchmark that needs 40 minutes of manual setup.

## Deliberately excluded

- **Coverage** (how much of the pipeline and how many kinds of session it exercises). The scope is a deliberate decision: no new players, no Review Transcript, no import/cleaning, no LLM generation. As a dimension, coverage would mainly penalize those choices. It could be reconsidered if growing the set of benchmark sessions becomes a goal.

## Unresolved

- **Numerical anchors:** not yet proposed or agreed for any dimension.
- **Contrast check:** after the anchors are drafted, compare two plausible benchmark versions to confirm the rubric rewards what it should.
