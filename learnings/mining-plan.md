# Campaign Matters Learnings: Output Design and Mining Plan (draft for review)

Status: plan approved 2026-10-30. First mining pass complete on 2026-10-30 (all scopes); see README.md for progress. The sample entries in Part 1 use real, verified material.

Location: `~/proj/tablesage/learnings/`. Sources come from both `~/proj/tablesage` and `~/data/tablesage_summary_test`. Paths below starting with `artifacts/`, `.cache/` or `harness/` are relative to `~/data/tablesage_summary_test` unless marked otherwise.

The collection records what our conversations taught us about Campaign Matters, the Session Summary and the Table Recap. It has three kinds of entries:

- **Preferences:** what the user wants, either inferred from reactions to output or stated outright. A preference is kept even if the current prompts or concepts already encode it.
- **Approaches:** pipeline and prompt changes, whether each helped, hurt or did nothing, and whether it survives today.
- **Examples:** the most important kind. Each holds the actual good or bad text plus the context needed to see why. An example earns its place if it clearly shows a preference and future output can be checked against it.

---

## Part 1: Output structure

### File layout

```
learnings/
  README.md                  How to use the collection; indexes by scope and by failure pattern
  preferences.md             PREF-### entries, grouped by scope
  approaches.md              APP-### entries, grouped by scope, each with a current status
  examples/
    cross-matter.md          Duplication and wrong-section examples spanning categories
    goals.md
    goal-impediments.md
    opportunities.md
    obligations.md
    brewing-troubles.md
    mysteries.md
    revelations.md
    new-assets.md
    developments.md
    present-matters.md
    summary.md               Session Summary presentation
    recap.md                 Table Recap presentation
  sources.md                 SRC-## list of every mined conversation and repo source
```

One file per scope keeps each file small enough to read before working on that matter. Examples that span categories, mainly duplication and misplacement, go in `cross-matter.md` and are linked from each scope they touch.

### Shared conventions

- **IDs** are permanent and never reused: `PREF-###`, `APP-###`, `EX-###`, `SRC-##`.
- **Scope tags** name a matter type (for example `revelations`), `summary`, `recap` or `cross-matter`.
- **Provenance** is the store, the file or commit, and a UTC timestamp, so any entry can be traced back to its conversation.
- **Evidence type** for preferences is `stated`, `reaction` (inferred from a reaction to specific output) or `both`.
- **Verbatim rule:** quoted output text is copied exactly from a recorded source. If the text cannot be recovered, the field says `not recovered`. A paraphrase never goes in a quote field.
- **Summary/Recap names:** on 2026-10-27 the user decided that the content then generated as the Table Recap works better as the Session Summary. Summary and Recap entries record which name the artifact had at the time.
- **Cross-links:** each example links to the preference it shows and the approach it prompted. Preferences and approaches link back to their examples.

### README.md indexes

The README carries two indexes so a future agent can find relevant material either way:

```markdown
## By scope
| Scope | Preferences | Approaches | Examples |
|---|---|---|---|
| revelations | PREF-001 PREF-002 | APP-001 | EX-001 |
| mysteries | PREF-003 | — | EX-002 |
| cross-matter | … | … | EX-003 |

## By failure pattern
| Pattern | What goes wrong | Examples |
|---|---|---|
| Restates the problem | A Revelation describes the mystery's extent instead of reducing an uncertainty | EX-001 |
| Incidental unknown | A Mystery is an unknown nobody has reason to investigate | EX-002 |
| Open bargain restated | One unfinished deal is repeated in several categories | EX-003 |
```

The README also explains how to check new work against the collection: read the scope file and `cross-matter.md`, then run each example's **Spot it** check against the new output.

### Example entry template

```markdown
### EX-### <short title>
- Verdict: bad | good
- Scope: <matter or presentation>
- Failure pattern: <index pattern name>    (bad examples only)
- Session / run: <campaign session and run it came from>
- Source: SRC-## <store, file or commit, UTC timestamp>

**The text** (verbatim):
> …

**Context needed to judge it:** the linked matter, the duplicate elsewhere, classification fields, or whatever else makes the problem visible. Also verbatim where possible.

**User's reaction** (verbatim): > …

**Why it is bad / good:** one or two sentences.

**Spot it:** a one-line check that can be run against new output.

**Outcome:** what was changed in response and whether it held.
**Links:** PREF-###, APP-###
```

### Preference entry template

```markdown
### PREF-### <the preference as a rule>
- Scope:
- Evidence: stated | reaction | both
- Source: SRC-## …
- Quote (verbatim): > …
- Currently encoded in: <prompt, concept or filter path>, or "not encoded"
- Examples: EX-###
```

### Approach entry template

```markdown
### APP-### <what was tried>
- Scope:
- Date / source: SRC-## …
- Problem it targeted:
- What was done:
- Result: helped | hurt | no effect | mixed, with evidence
- Current status: kept | superseded by APP-### | reverted | lost in re-architecture | unknown
- Status checked against: <current path and date checked>
- Lesson:
- Examples: EX-###
```

"Lost in re-architecture" means an approach that helped but has no trace in the current prompts, schema or filters. These are listed together at the top of `approaches.md` because they may be worth restoring.

### Sample entries

The draft samples that were here have been replaced by the real entries: EX-001 and EX-002 in [examples/](examples/), PREF-002 in [preferences.md](preferences.md), and APP-001 in [approaches.md](approaches.md). EX-003 will be filed in `examples/cross-matter.md`. Those files are authoritative for every ID.

---

## Part 2: Collection and conversion plan

### Sources and time window

**Where the conversations are.** Both Claude Code and Codex conversations are included. Most of the work after the split ran in Codex.

| Store | Folders (cwd) | Conversations in window |
|---|---|---|
| Codex `~/.codex/sessions` | `data/tablesage_summary_test`, `data/tablesage`, `proj/tablesage` | about 35 from 2026-10-18 on, some trivial (listing items, settings) |
| Claude Code `~/.claude/projects` | the same three folders | about 20 from 2026-10-18 on |

Excluded:
- conversations before the window, including the nested subagent transcripts from 2026-09-30 and the `proj/tablesage-session-context` Codex session from 2026-09-06
- `-tmp-tablesage-agent-review-case-*`
- this conversation

**Window start.** 2026-10-18. The split itself began in the Codex session of 2026-10-20T18:40Z that loaded `refactor-campaign-matters-prompt`, which led to commit `f1862f7b`, "Split Campaign Matters into eight dependent category prompts." The window also includes the per-matter work just before it: the 2026-10-18 hand-crafted ideal matters and Session 001 golden review, Optimize Opportunities and Optimize Unresolved Mysteries on 2026-10-19, and the 2026-10-20 sessions before the split. Everything through 2026-10-30 is in scope, including the `~/proj/tablesage` porting and duplication work. Conversations in the window about something else, such as repo cleanup or settings, are dropped at triage.

**Repo sources**, in both repos, limited to the window:
- `.work-items/` intent, findings and analysis files, especially the `~/proj/tablesage` `matters-dup-*` items, which already hold verbatim duplicate pairs
- `artifacts/design_notes/`, `artifacts/evaluations/`, `artifacts/regen-comparison.md`
- git history of `artifacts/session_*/outputs/` and `golden/`. The user's hand edits to review Markdown and goldens are preference evidence with the text attached.
- `.cache/runs/diagnose-*/diagnostic/`. Seven runs exist; each holds the item under review verbatim plus a critique.

### Recovering verbatim text

The examples matter most, and their exact text is the hardest part to recover. Sources, best first:

1. Diagnostic inputs and analyses under `.cache/runs/diagnose-*`. These are unique per run and survive later runs.
2. Tool outputs inside transcripts, where an agent printed JSON or Markdown it was reviewing.
3. `git log -p` of session outputs and goldens.
4. Assistant messages that quote items, used only when they quote rather than paraphrase.

Good examples come from the same sources, plus golden diffs: a generated item next to the user's hand-edited version.

`.cache/<matter>/<session>/run-N/` is **not** used for examples. Every validation run overwrites those paths, so they no longer match what the user was reacting to.

### Steps

1. **Normalize.** One script reads both transcript formats (Claude `user` and `tool_result` records; Codex `response_item` messages and `*_call_output` records) and writes one turn file per conversation to scratch space outside both repos (`~/.cache/tablesage-learnings/`). Each terse answer such as "A" or "B, and that applies…" is paired with the question it answers. Context-handoff summaries are dropped, because they copy earlier threads from the other provider.
2. **Triage.** Build a per-conversation index: date, scope, a one-line purpose, and the turns where the user judged output, stated a preference or reported a result. Trivial conversations are dropped here. The index becomes `sources.md`.
3. **Extract candidates.** Read the flagged turns, one scope at a time, and draft preference, approach and example candidates with provenance.
4. **Verify.** Check every quote against its source with a byte-level search. Anything that does not match is marked `not recovered` or replaced with a verified copy from a better source.
5. **Merge and check status.** Combine duplicates across conversations, since the same complaint often recurs. Link examples, preferences and approaches. Check each approach's status against the current prompts, schemas and filters in both repos, and surface any "lost in re-architecture" entries.
6. **Review.** Deliver one scope file at a time, starting with the richest (Revelations, Mysteries, cross-matter duplication), so you can correct verdicts and wording before the rest is written.

Steps 2–3 can be split by scope across subagents to save time, but only if you approve; by default I do them myself in sequence.

### Risks

- **Reactions without the text.** Some reactions refer to items that were never printed. These become preferences without examples, or examples marked `not recovered`. They are never reconstructed.
- **The two repos have drifted.** An approach can be kept in one repo and changed in the port. Status records both where they differ.
- **Swapped artifact names.** Summary and Recap items from before and after 2026-10-27 may refer to swapped artifacts. Each entry records the name in use at the time.
- **Short answers.** Answers like "A" mean nothing without their question. Step 1's pairing handles this, and an entry is never built from the answer alone.

---

## Decisions

Settled 2026-10-30:
1. Both Claude Code and Codex conversations are mined.
2. The borderline sessions from 2026-10-18 to 2026-10-20 are included.
3. The collection lives in its own top-level `learnings/` folder in `~/proj/tablesage`.
