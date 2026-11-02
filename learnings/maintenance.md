# Maintaining the Learnings

Codex and Claude follow this procedure during work on the Session Summary, the Table Recap, the unified Matters pipeline and their replacements. Routine capture is authorized by the standing instruction in [../.agent_context.md](../.agent_context.md); it needs no separate save request. An explicit user request to defer writing takes precedence. Keep the evidence here, not in agent memory.

Recording a judgment does not authorize changing prompts, code or outputs, or starting a work item.

## The Shape to Keep

The collection stays simple by keeping one current statement of each thing:
- A rule lives in one [preferences.md](preferences.md) entry, and that entry always states the rule as it is **now**.
- An accepted particular occurrence lives in one [allowances.md](allowances.md) entry.
- An example lives in one entry, in the `examples/` file for its Summary heading. A recurrence is added to that entry, not written as a new section elsewhere.
- Pipeline run details live with the pipeline's experiments (pass READMEs, `progress.md`), not here. An example's **Outcome** says only which pass fixed it or where it recurred.

Never append a dated "clarification" section to the end of a file. Fold the new judgment into the entry it changes, and add one dated line to that entry's **History**.

## When to Capture

- **The user judges output bad, missing or a regression:** preserve the exact output and the user's words immediately, before a fix or regeneration overwrites them. Bad examples come first. The user, verbatim: "Make sure that the examples i shared with you are put in the bad examples in learnings first before you change anything".
- **The user approves output or supplies a better version:** preserve it when it teaches a distinction or is a target for a known failure.
- **The user accepts a particular occurrence a check would flag** ("fine for now", "either way", "ok with this"): add or update an allowance.
- **The user states or changes a preference:** update the rule's entry.
- **An experiment teaches something reusable:** update the approach's entry and, if it generalizes, the *Lessons* in [approaches.md](approaches.md). Record inconclusive results honestly.
- **An agent notices a possible problem without user judgment:** add a short bullet under *Unjudged observations* in the relevant example file. Do not give it a verdict.

Capture as evidence arrives, and before handing work back. Routine edits that teach nothing new need no entry.

## Writing an Example

Add to an existing entry when it is the same failure; add a new entry when the evidence teaches a distinct failure or boundary. An entry has:
- a heading `### EX-### <short description>` and a line with verdict, Session, pass or run, and source;
- the rules (and allowances) it supports;
- **The text:** the exact output, including the other bullets when the fault is duplication. For an omission, say nothing was generated and quote what the user expected;
- only the context needed to judge it independently (the relevant evidence, not run paths);
- **User's words:** verbatim. Keep the agent's explanation separate and label it;
- **Spot it:** a concrete test that can be applied to future output;
- **Outcome**, when known: which pass fixed it or where it recurred.

Quote from available evidence. Mark unavailable text `not recovered`; never reconstruct a quote from memory. Exclude secrets.

## Updating a Rule

1. Rewrite the **Rule** so it states the current position, including the new boundary.
2. Add the user's new words to **User's words**.
3. Add a dated **History** line saying what changed. If the change reverses earlier guidance that examples were judged under, the history line keeps the old wording.
4. Update **Status** if it changed (`firm`, `provisional`, `on trial`, `superseded`). A superseded rule keeps its entry and points to its replacement.
5. If the judgment generalizes from one case, state the general pattern rather than the case ([PREF-012](preferences.md#pref-012)). If you can't find the general pattern, say so in the entry rather than writing a case-shaped rule.

A new rule gets the next `PREF-###` after the highest in use, under the heading it governs. Add it to the README's heading table.

## Writing an Allowance

Give the exact accepted text (or the omission), its Session, pass and heading; the user's words; its firmness (`firm`, `for now`, `tentative`); what it does **not** extend to; and the review-guide checks it would otherwise trigger. Link it from the rule it relates to. When the user later rejects the same occurrence, remove the allowance and record the reversal in the rule's history.

## IDs and Sources

Allocate each new ID from the highest in use for its prefix. IDs are permanent and never reused. Re-read the affected files immediately before writing when other agents may be editing. Add a `SRC-##` entry to [sources.md](sources.md) for each new conversation, with its identifier and date if available. If not, say so and identify it by date and subject; never invent an identifier.

## Before Handing Back

Check that quotes are exact, links and IDs resolve, the README's heading table lists any new rule, and user judgments stay distinguishable from agent observations. Tell the user briefly what was captured, with the IDs. The review guide is derived from this collection, so after substantive changes it needs a rebuild with `extract-learnings`.
