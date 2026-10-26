# Accepted Prompt Harness Design

The user approved a shared prompt-only harness for Ledger efficiency and Summary quality. It preserves the simple workspace structure: `inputs`, `output`, and `prompts/ledger` plus `prompts/summary`. Capture one execution-start datetime and pair archived prompts and outputs by prompt type and that timestamp.

## Workshop Decisions

- Freeze all inputs once. Ledger tests use fixed production-routed starting-context/current-play transcript slices, known Roles, attendees, and Glossary. Summary tests independently use the supplied good Ledger, metadata, attendees/Glossary, prior recap, and introductions. Experimental Ledger outputs never automatically replace Summary input.
- Reuse production generation functions directly, with explicit experimental prompt injection. Preserve common transport, internal streaming, schemas, validation, retries, candidate selection, and Summary composition.
- Save the complete system prompt, template, and actual rendered messages before transport; preserve retry messages and every raw response. Include Ledger's response schema.
- Save a timestamp-matched JSON run record with input hashes, model/settings, code version, overall/per-attempt timings, validation results, and output measures. Capture Ledger entry count and Summary body/recap/introductions/complete word counts separately.
- One invocation produces one generation, including production retries. Repetitions are explicit when needed. The earlier mandatory two repetitions and four-output packet are superseded for this harness.
- Existing good Ledger and current bad Summary are the baselines. The user explicitly rejected extra baseline calls. Preserve both unchanged; also retain the good Summary for quality review. Original good-Ledger runtime is unknown, so it supplies a content baseline rather than a measured efficiency baseline.
- No new rubric or numerical quality scores. The approved investigation rubric in intent.md remains applicable. Ledger prompt optimization remains a separate registered work item; building shared tooling does not merge or complete those investigations.

## Implementation and Verification Plan

- [x] Add optional prompt text/attempt-observer injection to the common renderer and both production generators; default production calls remain unchanged.
- [x] Implement `scripts/prompt_experiment.py` with one-time preparation, frozen hash-checked inputs, editable candidates, isolated timestamp-paired evidence, dry rendering, one generation per invocation, and offline replay.
- [x] Prepare the real **20260901** inputs with **20260825** recap and preserve the supplied references; initialize current candidate prompts.
- [x] Verify existing generation/helper checks, lint/type checks, direct offline runs, retries/feedback, failure retention, independent inputs, and hash rejection.
- [x] Document usage and update handoff. Do not make paid calls during implementation verification.

## Qualitative Assessment

The accepted design supports explanatory confidence by holding prompt inputs independent and using production behavior. Human comparison against the references remains necessary for meaningful quality judgments. Archived messages, inputs, controls, code hashes, attempts, and timings support reproducibility. One invocation per result avoids unnecessary early repetition costs and keeps practical effort small. These are design judgments; no candidate performance or quality improvement has been demonstrated.

See [Ledger and Summary Prompt Harness](../../scripts/prompt_experiment.md) for usage. The older setup plan is historical where it requires fresh human transcript review, regenerated baseline calls, or a fixed four-output initial packet. This harness is complete only as tooling; experiment conclusions remain outstanding.

Verification passed: 41 existing helper/Ledger/Summary checks, Ruff, and project type checks. Direct disposable offline runs verified both output paths, Summary composition, timestamp pairing, Ledger schema/feedback retry, Summary marker retry, three-attempt failure retention, fixed good-Ledger input, and modified-input rejection. Both real-workspace dry renders passed. No paid model calls or canonical Session output replacements occurred. Candidate performance and quality remain unassessed.
