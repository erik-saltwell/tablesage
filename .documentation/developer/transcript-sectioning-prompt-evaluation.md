# Transcript Sectioning Prompt Evaluation

## Overview

Prompt optimization evaluates how accurately a transcript-sectioning prompt identifies the opening structure of a real tabletop session. Each evaluation uses a real role transcript and attendee mapping, compares the generated routing decisions against manually reviewed golden sections, and favors preserving source material over excluding extra opening material.

## Key Concepts

- **Evaluation case:** A real session's role transcript and attendee mapping, rendered as input to the sectioning prompt.
- **Golden sections:** A manually reviewed copy of that session's `transcript_sections.json`. Its numeric ranges and `session_start_index` are the expected result.
- **Routing values:** `recap_range`, `introduction_range`, `starting_context_range`, and `session_start_index`.
- **Destructive omission:** A boundary that excludes required source material—especially a late session start or an early range end.
- **Over-inclusion:** A boundary that includes extra source material.

## Evaluation Flow

1. Generate transcript sections from an evaluation case using a candidate prompt.
2. Reject the case with a score of `0` if the response is structurally invalid.
3. Compare each routing value with its golden value.
4. Calculate component scores for recap, introductions, starting context, and session start.
5. Combine component scores into the case score.
6. Choose an execution mode: full-corpus training, leave-one-case-out rotations across all cases (`--run --cross-validate`, at least two cases), or a source-filename-prefix group holdout (`--run --holdout-prefix <prefix>`, at least one training and one held-out case). The corpus is not fixed at three sessions.

## Component Scores

Each component starts at `1.0`, accumulates applicable penalties, and is clamped to the range `0.0–1.0`.

| Component | Weight |
| --- | ---: |
| Session start | 40% |
| Starting context | 30% |
| Recap | 15% |
| Introductions | 15% |

Span F1 is reported as a diagnostic for non-null ranges, but is not part of the optimization score.

## Boundary Penalties

Distance is measured in raw utterance count.

- **Destructive omission:** `0.10 × (2^d − 1)`
- **Over-inclusion:** `0.025 × (2^d − 1)`

For a non-null golden range:

- A predicted start later than golden is destructive.
- A predicted end earlier than golden is destructive.
- A predicted start earlier than golden is over-inclusive.
- A predicted end later than golden is over-inclusive.

For `session_start_index`:

- A predicted value later than golden is destructive.
- A predicted value earlier than golden is over-inclusive.

## Nullability Rules

- A false `null` for a golden non-null range receives a `1.0` penalty for that component.
- A false non-null range for golden `null` receives a base `0.40` penalty plus the destructive curve applied to its predicted width.
- If a golden starting-context range exists but the prediction is `null`, the entire evaluation case scores `0`, because downstream generation cannot continue.

## Structural Validity

Malformed JSON, unexpected fields, invalid indices, reversed ranges, or any other response that cannot be persisted and routed causes the entire evaluation case to score `0`.

## Running and evidence

Use `uv run --project apps/optimize-prompts optimize-prompts section-transcript` from the repository root for preflight, adding `--run` and the selected mode for paid optimization/evaluation. See the [corpus guide](../../prompt_optimization/section_transcript/README.md) and [implementation](../../apps/optimize-prompts/src/optimize_prompts/optimize_section_transcript.py).

Cross-validation saves the selected prompt and rotation evidence; selection on held-out scores is not an independent final generalization test. The group holdout separates cases by source filename prefix, so use a consistent campaign prefix. Optimization writes candidate outputs but does not automatically deploy a production prompt.
