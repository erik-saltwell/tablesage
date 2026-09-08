# Recap Summary Metrics

## Overview

Recap summaries preserve the substantive content of the existing recaps while expressing it more concisely. They remain scene-complete, generally retaining one or two consequential facts per scene. The recap is a reminder of the prior session, not a detailed session review.

## Key Concepts

- **Existing recap**: the content reference for an evaluation case. It defines the facts the recap should preserve.
- **Coverage question**: a closed-ended question representing one must-preserve recap fact.
- **Session Ledger**: the factual authority used to verify that recap claims are supported.
- **Format validity**: a recap is a flat sequence of Markdown bullets, with no title, heading, nesting, commentary, or code fence.
- **Conciseness**: word-count compression relative to the Session Ledger.

## Coverage-question flow

1. Run a recap-specific utility prompt against each existing recap.
2. Extract substantive claims from each recap bullet.
3. Include scene context only when needed to make a claim understandable.
4. Manually edit the generated `questions` list, deleting facts that should not be enforced.
5. Treat every retained question as required; the coverage metric gives all questions equal weight.

The question generator may reason about optional details during review, but the final evaluation artifact has no question tiers.

## Scoring behavior

A candidate recap must pass all of the following before it can compete:

1. Valid flat-bullet Markdown format.
2. Complete coverage of every retained coverage question.
3. Ledger alignment of at least `0.95`.

Among passing candidates, rank solely by conciseness. This makes brevity the decisive optimization target while format, required facts, and factual support remain non-negotiable safeguards.

## Metric roles

- Reuse the existing coverage metric unchanged.
- Reuse the existing Ledger-alignment metric unchanged.
- Reuse the existing word-length compression metric unchanged.
- Add deterministic format validation as a gate.
- Add a recap-specific gated scorer; it does not alter any metric implementation.
