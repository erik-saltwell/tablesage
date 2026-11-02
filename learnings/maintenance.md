# Maintaining the Learnings

Codex and Claude follow this procedure during work on Campaign Matters, the Session Summary, the Table Recap, and their replacements. Routine capture is authorized by the standing instruction in [../.agent_context.md](../.agent_context.md); it needs no separate save request or approval. An explicit user request to defer writing takes precedence. Store evidence here rather than in agent memory.

The collection remains evidence under user review. Historical preferences and definitions do not automatically override current instructions or prompt contracts. Recording a problem does not authorize changing product behavior or starting a new work item.

## Before Changing Behavior

Read [README.md](README.md), the relevant scope files in `examples/`, and [examples/cross-matter.md](examples/cross-matter.md). Read the relevant entries in [preferences.md](preferences.md) and [approaches.md](approaches.md). Check for an existing failure, an earlier attempted fix, and any disagreement between the examples and current definitions.

Use the examples' **Spot it** checks when reviewing new output. Report a disagreement or unresolved expectation explicitly rather than silently choosing a historical definition.

## When to Capture

- The user identifies bad output, an omission, or a regression: preserve the evidence immediately, before a fix or regeneration can overwrite it. Bad examples take priority.
- The user approves concrete output or supplies a better version: preserve it when it teaches a useful distinction or provides a comparison for a known failure.
- The user states or changes a substantive preference: update the relevant preference with its evidence and scope.
- An experiment produces a meaningful result: record the approach, observed benefits and regressions, and whether it was kept, reverted, rejected, or remains in progress. Record inconclusive results honestly.
- An agent notices a possible problem without user judgment: record a useful candidate under **Unjudged observations** in the relevant example file. Do not assign it a user verdict or present it as an agreed preference.

Capture at the point the evidence is available. Complete related outcomes and links before handing work back; do not postpone all capture until the end of a long conversation. Routine edits without a new lesson need no entry.

## Preserve the Example First

For an example, follow the conventions in [README.md](README.md) and the existing scope files. Include:

- Exact output, including the other bullets when the failure is duplication or contradiction. For an omission, state that nothing was generated and quote the user's expectation rather than inventing output.
- Enough context to judge it independently: relevant input evidence, linked matters, classification fields, or before/after text. Identify the Campaign, Session, artifact, date, and run or revision when available.
- The user's exact reaction and its source. Keep the agent's explanation separate and label inferences as such. If the user explicitly rejects an entry without explaining why, record that limit rather than inventing their reason.
- The verdict, applicable definition, a short explanation, and a concrete **Spot it** check that can be applied to future output.
- The attempted fix and observed result when available. Until then, say that the outcome is pending.

Copy quotes from available evidence. Mark unavailable text `not recovered`; never reconstruct a quote from memory or a conversational summary. Preserve meaningful hedges and attribution. If evidence is missing and the judgment cannot be understood without it, keep a pending observation with the missing context identified.

Put the essential text and context in the entry itself. A link to a mutable output file or overwritten validation cache is insufficient. Reference a stable run folder or commit for larger prompt/input/response records when one exists; capture the relevant excerpts before overwriting mutable files. Exclude secrets and unrelated personal information.

## Update the Collection

1. Look for an existing entry before adding one. Add a dated recurrence and outcome when it is the same failure; add a new example when the evidence teaches a distinct failure or boundary. Preserve the original occurrence and verdict.
2. Use the relevant scope file; put examples spanning categories in `examples/cross-matter.md` and link from affected scopes. Follow the existing entry structure without adding empty fields or sections.
3. Allocate new IDs from the highest existing ID of that prefix across the collection. IDs are permanent. Re-read the affected files and ID allocations immediately before writing when other agents may be editing.
4. Add provenance to `sources.md` for new conversations or durable evidence sources. Use an available conversation identifier or transcript path and timestamp. If the identifier is unavailable, say so and identify the conversation by date and subject; never invent an ID supplied by a provider. Keep future additions separate from the original mining window.
5. Link examples to relevant preferences and approaches, with links back where useful. Update the README's scope and failure-pattern indexes for new entries or patterns. The original mining progress table records that initial pass, not the completion of ongoing maintenance.
6. When a preference changes, retain the earlier definition, mark it superseded, and link the new decision and reason. When an approach changes status, preserve its earlier results and add the dated outcome. Keep unresolved tensions visible.

An implementation or a successful run alone does not establish that the user likes the result. Separate observed behavior, the agent's assessment, and user approval. Do not mark an approach effective or a failure fixed without supporting output or verification; record the limits of the evidence and any regressions.

This collection has no additional approval gate. Keep pending judgments visible for the user's normal review, and promote an unjudged observation into an example only when the user supplies a judgment. Never treat silence as approval or rewrite the historical collection wholesale during routine capture.

## Before Handing Back

Check the changed entries for exact quotes, sufficient context, stable IDs, working local links, and consistent index references. Confirm that user judgments and agent observations remain distinguishable and that outcomes say only what was observed.

Briefly tell the user what was captured or updated, with the relevant example IDs or file links. Explain any evidence that could not be recovered. Keep unrelated work and existing review edits intact.
