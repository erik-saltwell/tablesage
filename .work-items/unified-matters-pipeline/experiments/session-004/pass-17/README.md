# Pass 17: One "Last Session..." Item per Anchor Beat

On 2026-11-02 the user asked why Session 002's pass 16 Summary had more "Last session..." items than expected (12). The agent's analysis of their step 2c ratings found three patterns: two items told from the same beat, one plan told across three threads, and lasting-consequence ratings resting on guesses. The user chose option A, "Do A now": code shows at most one history item per anchor beat. Option B (require an established lasting consequence) is a separate work item, [Require established lasting consequences in Last session...](../../../../established-lasting-consequences/).

**Status:** implemented and checked offline. **Not generated.**

## The Change

| Part | Change |
|---|---|
| Step 5 | New `one_per_anchor`: when two shown "Last session..." items share an anchor beat, keep the one with the higher impact-plus-lasting rating; on a tie, the one whose thread's new or updated open facts are less fully shown under open headings; then the earlier one. The others are hidden with the reason in `selection.json` and `review.md`. Open headings are unaffected. |
| Everything else | Pass 16's: prompts (including step 6b and step 6's obstacle wording), runner, seeds and step 1–4 outputs (which are pass 14's). `run17.py` is `run16.py` plus the rule, its `RULES` text, and pass numbering. |

[generate.sh](generate.sh) reruns both chains from step 6, because the items step 6 writes change.

## Effect on Selection (offline, deterministic)

| Session | History items before → after | Removed | Open headings |
|---|---|---|---|
| 001 | 6 → 6 | none | unchanged |
| 002 | 12 → 11 | `thread_13`, "Dr. Uriah agreed to repay Father William for the map markings with penance and a donation." It shares `beat_53` with `thread_1`, "Father William marked the Barrow Mound and the witch's home on the party's map." Both are rated medium/medium; thread 13's new facts (the penance and donation debts) are 100% shown under "Promises and debts", thread 1's 33%. | unchanged |

Sessions 003 and 004 have no current-pass outputs to check.

## Verification and Limits

Recorded in [verification.json](verification.json): step 5 recomputed on the copied inputs for both Sessions, compared with pass 16's `selection.json`. Only the selection is checked; no Summary has been generated with the rule.
