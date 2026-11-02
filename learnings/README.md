# Campaign Matters Learnings

What our conversations taught us about the Session Summary, the Table Recap and the unified Matters pipeline that builds them: what the user wants, which particular outputs the user accepted, real good and bad output, and what was tried.

This is the user's judgment, not current behavior. Current behavior lives in the prompts and code. Where a rule here and a prompt disagree, the rule is what the user wants.

## Who Reads It and How

**`extract-learnings`, building the review guide:**
1. [preferences.md](preferences.md): each rule's current state, grouped by Summary heading. Most checks come from here, at the rule's status.
2. [allowances.md](allowances.md): particular outputs the user accepted. The review must not report them.
3. The `examples/` file for each heading: the evidence behind each rule, each with a **Spot it** test and, for golden or judged Session output, the exact text for Session-specific expectations.

**An agent changing prompts or pipeline behavior:**
1. The rules for the headings you are changing in [preferences.md](preferences.md), plus *Pipeline and Process* and *Across the Summary*.
2. The matching `examples/` file, to see what failure or success looks like.
3. The *Lessons* in [approaches.md](approaches.md) before trying something, and its entries for what was already tried.
4. Write general rules with fictional examples ([PREF-012](preferences.md#pref-012)). Never copy a test Session's names, situations or expected answers into a prompt.

When you capture new judgments, follow [maintenance.md](maintenance.md).

## Layout

| File | Holds |
|---|---|
| [preferences.md](preferences.md) | One current-state entry per rule (`PREF-###`), with status, boundaries, the user's words, evidence and a short history |
| [allowances.md](allowances.md) | Particular occurrences the user accepted (`ALW-###`), and what each does not extend to |
| [examples/](examples/) | Good, bad and missing output with the user's verdict (`EX-###`), one file per Summary heading |
| [approaches.md](approaches.md) | Reusable lessons, then what was tried (`APP-###`) and its status |
| [sources.md](sources.md) | Provenance for every `SRC-##` and `R-##` reference |
| [maintenance.md](maintenance.md) | How to capture new evidence and keep the collection current |

## Summary Headings

The unified pipeline's Summary order, the files that cover each heading, and the historical Matter names older evidence uses.

| Summary heading | Fact kind | Former Matter | Rules | Examples |
|---|---|---|---|---|
| Across the Summary | (all) | cross-matter, Summary and Recap | PREF-004, PREF-017, PREF-041, PREF-050, PREF-007, PREF-049, PREF-026, PREF-002, PREF-024, PREF-025, PREF-023, PREF-021, PREF-029, PREF-008, PREF-009, PREF-043 | [across-the-summary.md](examples/across-the-summary.md) |
| Last session... | thread beats, events, encounters; gains | Developments, Revelations, New Assets | PREF-039, PREF-027, PREF-048, PREF-038, PREF-044; superseded PREF-005, PREF-010 | [last-session.md](examples/last-session.md) |
| Your goals | `want` | Goals | PREF-033, PREF-051, PREF-053, PREF-055 | [your-goals.md](examples/your-goals.md) |
| Standing in your way | `blocked_by` | Goal Impediments | PREF-034, PREF-042 | [standing-in-your-way.md](examples/standing-in-your-way.md) |
| What could help | `could_use` (openings only) | Opportunities | PREF-035, PREF-046, PREF-045, PREF-047, PREF-040, PREF-028 | [what-could-help.md](examples/what-could-help.md) |
| Still unanswered | `unknown` | Mysteries | PREF-003, PREF-054, PREF-013 | [still-unanswered.md](examples/still-unanswered.md) |
| Promises and debts | `owe` | Obligations | PREF-036, PREF-052, PREF-020 | [promises-and-debts.md](examples/promises-and-debts.md) |
| Meanwhile | `threat` | Brewing Troubles | PREF-037 | [meanwhile.md](examples/meanwhile.md) |
| Where you are, Immediate danger | stopping situation | Present Matters | PREF-056, PREF-031 | [where-you-are.md](examples/where-you-are.md) |

Pipeline-wide rules that are not about one heading: PREF-014 (the model classifies; code decides), PREF-012 (fictional examples, general rules), PREF-018 (side by side), PREF-015 (three questions, four steps).

Held assets are not open matters: they stay in campaign state and are told only as gains in "Last session...".

## Conventions

- **IDs** are permanent and never reused: `PREF-###`, `ALW-###`, `APP-###`, `EX-###`, `SRC-##`. Numbers reflect the order of writing, not importance. An example keeps its ID and heading when it moves between files.
- **Verbatim:** the user's words and quoted output are copied exactly, typos included. Text that could not be recovered is marked `not recovered`, never paraphrased. A word in [brackets] after a garbled dictated word is a gloss.
- **Verdicts:** `good`, `bad`, `missing` (an expected entry was not produced), `borderline` (a reasonable case either way) and `contested` (the user's expectation and the definition then in force disagreed). An example judged under an older definition says so and gives its current reading.
- **Severity:** the user calls some faults minor. A minor fault is still a fault; an *allowed* occurrence is not (see [allowances.md](allowances.md)).
- **User judgment versus agent observation:** only the user's verdicts, quotes, goldens and approvals are judgments. Agent recommendations count only where the user approved them, and say so. *Unjudged observations* at the end of an example file are agent notes, not examples.
- **Hypothetical examples:** EX-065 to EX-069 judge illustrative inputs, not generated output.
- **Test Sessions:** the evidence comes from Brandonsford Sessions 001–004. Names from it appear throughout this collection as evidence; they must never appear in prompts.
- **History:** this collection was restructured on 2026-11-01 into current-state entries. The earlier layout, with dated clarifications, pass review files and full Revelation diagnoses, is preserved in git at commit `baaff43`.
