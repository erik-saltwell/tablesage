# Quality rubric: resumable session processing flow

This rubric judges whether the session-processing flow makes the normal path from audio to generated artifacts coherent while retaining safe, understandable checkpoints. It applies to the idea described in [idea.md](idea.md).

All dimensions use a 0–10 scale where higher is better. Reasoned intermediate scores are allowed. The dimensions are independent: this rubric has no aggregate score, weights, thresholds, or required targets.

## Guidance clarity

Rewards a user's ability to understand what Process will do, where they are in the flow, and what can happen next.

| Score | Meaning |
| --- | --- |
| 0 | Users must infer the pipeline from scattered actions or disabled controls. |
| 5 | The next action is usually apparent, but status, errors, or return paths can be ambiguous. |
| 10 | The `P` entry point, each screen, and the workflow rail accurately explain current state, next action, and what needs attention. |

## Resumability

Rewards safe interruption and return without loss of meaningful work or repetition of completed work.

| Score | Meaning |
| --- | --- |
| 0 | Leaving loses meaningful work or requires manually reconstructing progress. |
| 5 | Completed phases resume, but an interrupted review or error path can lose work or be confusing. |
| 10 | Users can deliberately save or discard in-progress review edits, return to the appropriate stage, and resume without repeating completed work. |

## State integrity

Rewards correct separation and handling of draft, completed, stale, and failed states.

| Score | Meaning |
| --- | --- |
| 0 | Draft, completed, stale, and failed states blur together; partial work can influence outputs. |
| 5 | Ordinary sequencing is correct, but backtracking, retries, or changed audio can leave edge-case ambiguity. |
| 10 | Persisted state is authoritative: drafts are non-final, generation uses only a completed review, and source changes/errors consistently invalidate or route downstream work. |

## Workflow efficiency

Rewards an economical happy path that avoids needless navigation or reprocessing while preserving necessary specialist operations.

| Score | Meaning |
| --- | --- |
| 0 | The normal path requires disconnected actions or repeats expensive completed work. |
| 5 | The primary path is shorter, but common revisions or returns still cause redundant navigation or processing. |
| 10 | One obvious path advances through only necessary work, skips current phases, and leaves specialist operations accessible without cluttering the main flow. |

## Calibration contrasts

These hypothetical examples test the dimensions; they do not assess the current idea.

- A polished linear wizard that advances quickly but discards review edits on exit can be strong in guidance clarity and workflow efficiency while weak in resumability.
- A durable flow that preserves drafts and handles invalidation correctly, but requires excessive confirmations and screens, can be strong in resumability and state integrity while weak in workflow efficiency.
