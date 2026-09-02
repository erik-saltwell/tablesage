# TableSage Prompt Optimization

## Overview

TableSage prompts are evolved by calling the standard Prompt Forge binary with an exported evaluation bundle and an external TableSage metrics package. Prompt Forge remains domain-neutral: it provides generic structured-output and plugin extension points but contains no knowledge of TableSage, Ledgers, campaigns, or sessions. The first target is Ledger generation; Summary generation will later use the same integration with its own metrics. Optimization produces a candidate prompt and evidence report but never changes TableSage's production prompt automatically.

## Key Concepts

- **Evaluation bundle** — A versioned, self-contained export containing the rendered prompt input, production response schema, session metadata, and content hashes. Bundles contain private transcripts and are not committed.
- **Training session** — The session used to evaluate and revise candidate prompts. Initially Brandonsford 001.
- **Validation session** — An untouched session used only after optimization. Initially Brandonsford 002.
- **Golden completeness questions** — Generated questions that a human edits into the authoritative coverage set for a session.
- **TableSage prompt metrics** — An external package that supplies bundle loading, question generation, Ledger metrics, the composite scorer, caching, and reporting to Prompt Forge.
- **Prompt Forge extension points** — Generic configuration hooks through which the binary loads a response schema, evaluation cases, metrics, and a composite scorer.
- **Candidate prompt** — An evolved Ledger system prompt. The user template and response schema remain fixed.
- **Hard gate** — A condition that forces a candidate's reward to zero.
- **Weighted reward** — The quality score applied after all hard gates pass.

## Workflow

### Bundle export

1. TableSage exports the session's rendered Ledger input and current JSON response schema.
2. The bundle is versioned and content-addressed.
3. TableSage prompt tooling generates completeness questions from the transcript.
4. Generation replaces the canonical question file; the human is responsible for reviewing it again.
5. Each question contains:
   - Stable ID
   - Category
   - Question
   - Transcript evidence
   - Enabled flag

Question categories are `fiction_change`, `recap`, `introduction`, and `correction`.

### Question generation

1. Split the transcript into deterministic token-sized chunks at utterance boundaries.
2. Include a small utterance overlap between chunks.
3. Generate questions for every relevant fictional change, recap fact, and character introduction.
4. Retain source ranges or evidence with each question.
5. Semantically deduplicate questions.
6. Write the result as the canonical editable question set.

Completeness questions exclude table talk and mechanics. When mechanics establish a fictional consequence, the consequence is tested but the mechanic is not.

Corrected facts are tested using the final canonical state. Correction classification is evaluated separately within completeness.

### Prompt optimization

1. Use the current Ledger system prompt as the seed.
2. Keep the rendered user input and production schema fixed.
3. Invoke the standard Prompt Forge binary with configuration naming the bundle, JSON Schema, external metric factory, and external scorer factory.
4. Prompt Forge loads those components through generic plugin extension points.
5. Generate one schema-constrained Ledger response per evaluation pull.
6. Validate the response against the exported JSON Schema.
7. Evaluate hallucinations and re-check alleged unsupported claims.
8. If both hard gates pass, calculate the weighted reward.
9. Use Prompt Forge's critic and actor loop to create and rank candidate prompts.
10. Preserve transcript-derived evaluation inputs in a persistent cache, but generate candidate Ledgers freshly.
11. Write the winning candidate and an evidence report without modifying TableSage.

The target model is Fable 5.1. Sonnet 5 acts as both judge and prompt-revision actor. The target uses production-like provider defaults, judges are deterministic, and the actor uses moderate sampling.

### Validation and adoption

1. Optimize only against Brandonsford 001.
2. Evaluate only the final candidate against Brandonsford 002.
3. Afterward, evaluate the original prompt against 002.
4. Require the candidate to outperform the original while passing both hard gates.
5. Retain the seed and candidate Ledgers from both sessions for human inspection.
6. Adopt a candidate only through deliberate code review.

## Quality Model

### Hard gates

#### Schema correctness

The output must conform to the exported production JSON Schema. This gate is purely structural. TableSage's warnings about unknown names remain diagnostic and do not affect the gate.

#### No hallucinations

Every semantic claim in the user-visible Ledger must be supported by the transcript alone. Attendee, role, and glossary metadata do not count as evidence.

Candidate claims are checked dynamically because fixed questions cannot anticipate new hallucinations. A claim gates the candidate only when two independent passes both classify it as unsupported.

The discarded generation scratchpad is structurally validated but excluded from semantic evaluation.

### Weighted reward

After both gates pass:

- Completeness: 50%
- Table-talk exclusion: 20%
- Mechanics exclusion: 20%
- Concision: 10%

#### Completeness

Completeness is composed of:

- 90% coverage of enabled golden questions
- 10% correct classification of known corrections

A complete Ledger represents:

- Every change to the fiction
- Explicitly framed recap content
- Character introductions
- Final canonical states after corrections

Player strategy is excluded unless it establishes an in-fiction decision, action, speech, or state.

#### Exclusion metrics

The exclusion categories are mutually exclusive:

- **Table talk** — Non-mechanical out-of-game conversation
- **Mechanics** — Rules, rolls, statistics, and game procedures

Mechanical discussion is excluded while its fictional consequences remain eligible for inclusion.

Each violation receives a fixed deduction:

- Major: -0.30
- Moderate: -0.15
- Minor: -0.05

Every deduction identifies the offending Ledger entry and supporting evidence.

#### Concision

Concision consists of:

- 80% semantic duplication
- 20% compression

Two entries are duplicates when they represent the same fictional change, even if phrased differently. Repeated events at different times are distinct. Corrections are distinct from the assertions they supersede.

The duplication score starts at 1.0 and deducts 0.25 per duplicated event group, floored at zero.

Compression is:

`1 - min(semantic Ledger words / transcript words, 1)`

Only user-visible semantic Ledger content is counted.

## Operational Rules

- Provide `smoke` and `full` run profiles.
- A pull evaluates one response; it does not reproduce TableSage's three-attempt retry behavior.
- Persistently cache only transcript-derived material such as reviewed questions, source claims, evidence indexes, and token counts.
- Never cache candidate outputs when measuring repeated-pull reliability.
- Reports include:
  - Candidate prompt
  - Prompt diff
  - Gate results
  - Per-metric scores and evidence
  - Training and validation results
  - Seed and candidate Ledgers
- Prompt Forge contains no TableSage-specific code.
- The Prompt Forge binary loads external case, metric, and scorer factories from configured Python entry points or import paths.
- The external TableSage package contains separate Ledger and future Summary adapters.
- Exported campaign bundles are ignored by version control.

## Execution Plan

### 1. Define the TableSage evaluation bundle contract

- Add a versioned bundle manifest.
- Include the rendered user prompt, transcript, response JSON Schema, session metadata, and content hashes.
- Add bundle loading and validation tests in the external TableSage prompt package.

### 2. Add the TableSage exporter

- Export sessions by campaign name and session ID.
- Generate the schema directly from `LedgerGenerationResponse`.
- Keep bundle generation deterministic and model-free.
- Ignore exported bundles in Git.

### 3. Add generic Prompt Forge extension points

- Allow optimizer configurations to provide an optional JSON Schema response format.
- Pass the schema to the target LLM.
- Retain raw JSON output for metrics and reports.
- Preserve existing unstructured prompt behavior.
- Allow the binary to load an external evaluation-case factory.
- Allow the binary to load an external metric factory.
- Allow the binary to load an external composite-scorer factory.
- Keep every extension point domain-neutral and cover it with generic plugin fixtures.

### 4. Create the external TableSage prompt metrics package

- Add the package to the TableSage repository without making it part of the production application runtime.
- Implement the configured case, metric, and scorer factories consumed by the Prompt Forge binary.
- Add a shared evaluation-bundle loader.
- Add Ledger as the first domain adapter.
- Leave an extension point for a future Summary adapter.
- Provide `smoke` and `full` profiles.
- Configure Fable 5.1 as target and Sonnet 5 as actor and judge.

### 5. Build completeness-question generation

- Put question generation in the external TableSage prompt package rather than Prompt Forge.
- Chunk transcripts deterministically at utterance boundaries with overlap.
- Generate categorized questions with IDs and transcript evidence.
- Deduplicate questions semantically.
- Replace the canonical question file on regeneration.
- Add validation for edited question files.

### 6. Implement deterministic gates

- Validate output against the exported JSON Schema.
- Exclude scratchpad content from semantic evaluation.
- Extract Ledger claims and verify them against the transcript only.
- Re-check unsupported claims independently.
- Gate only when both passes agree that a claim is unsupported.

### 7. Implement weighted metrics

- Implement completeness using 90% golden-question coverage and 10% correction classification.
- Implement table-talk exclusion with severity deductions of 0.30, 0.15, and 0.05.
- Implement mechanics exclusion with the same severity model and a disjoint scope.
- Deduct 0.25 per duplicate event group.
- Calculate compression as `1 - min(ledger words / transcript words, 1)`.
- Combine the metrics using the agreed 50/20/20/10 weights.

### 8. Add caching and reporting

- Implement TableSage-specific caching and report assembly in the external package.
- Cache transcript-derived questions, claims, evidence indexes, and token counts.
- Do not cache candidate generations.
- Report prompt diffs, gates, metric evidence, scores, and generated Ledgers.
- Never modify the TableSage production prompt automatically.

### 9. Prepare evaluation data

- Export Brandonsford 001 and 002.
- Generate and manually edit both question sets.
- Install the external package into the Prompt Forge execution environment.
- Call the standard Prompt Forge binary with the smoke profile to verify the complete workflow.

### 10. Optimize and validate

- Call the standard Prompt Forge binary with the full profile using 001 only.
- Evaluate the final candidate on 002.
- Then evaluate the original prompt on 002.
- Require the candidate to pass both gates and outperform the original.
- Review all four retained Ledgers before adopting the prompt.

### 11. Adopt through TableSage code review

- Apply the selected system-prompt diff manually.
- Run Ledger generation and application tests.
- Record the optimization report with the change.

Implementation proceeds in four stages: bundle and application infrastructure (steps 1-4), evaluation behavior (steps 5-7), operability and data preparation (steps 8-9), and the first optimization experiment (steps 10-11).
