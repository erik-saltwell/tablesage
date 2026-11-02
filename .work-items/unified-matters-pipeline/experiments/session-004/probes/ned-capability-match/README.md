# Probe: An Offer of Help That Doesn't Name the Goal

A research probe, not a pass (2026-11-01). Pass 10 hid Drop Dead Ned's paid offer as `generic_benefit`, while Lady Hilda's comparable offer was shown. The user judged them "the same" ([EX-080](../../../../../../learnings/examples/what-could-help.md)). This folder copies pass 10 and reruns step 3 on Session 001's threads only, from pass 10's own step 1 and 2 outputs. `probe.py` is `run10.py` with its pass 2 import path adjusted.

| Runs | Prompt | Ned (thread_5) | Hilda (thread_4) | Mule-for-dragon trade (thread_8, EX-055) |
|---|---|---|---|---|
| `control-1` to `-3` | pass 10 unchanged | `generic_benefit`, no helped goal: 3 of 3 | `enabling`: 3 of 3 | not run |
| `fix-1` to `-3` | three added sentences in `step3_facts_homes` | `enabling`, helps the dragon goal: 3 of 3 | `enabling`: 3 of 3 | `goal_pursuit`, hidden: 3 of 3 |

The three general sentences:
- an offer of help serves any want that what it brings plainly serves, with its conditions as its cost (fictional stonemason example);
- `generic_benefit` means a benefit that names nothing the trigger brings;
- an actual offer of help counts as offered terms even when it doesn't name the want.

Not tested: Session 002, where the boundary is Naggeneen's goal-less reward offer (EX-041), and anything downstream of step 3.
