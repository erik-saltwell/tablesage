---
name: "Explain missing, current, and out-of-date artifact states with tooltips on Session Detail"
status: complete
---

# Artifact State Tooltips on Session Detail

Help users understand the artifact indicators on Session Detail by explaining Missing, Current, and Out of date states with tooltips.

The user approved brief state explanations and next steps, with Current replacing Complete. Keep the existing indicator symbols and styling; show the explanation when hovering over each artifact indicator. Missing artifacts direct users to Process the Session, Current artifacts explain that they are up to date with their inputs, and Out of date artifacts explain that processing is needed again. Input Audio's missing message refers to importing audio rather than creating an artifact.

No approved numerical quality rubric exists. The user explicitly requested implementation after the workshop, which used provisional qualitative dimensions of clarity, usefulness, and accuracy. No numerical assessment was performed.

Implemented in `apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py`. Tooltip text updates alongside each indicator whenever artifact states refresh.

Verification completed:

- Ruff lint and formatting checks passed for the changed screen.
- `uv run --no-sync ty check apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py` passed.
- Existing Session Detail tests passed: 30 passed.
- Direct Textual headless execution with tooltips enabled verified every visible indicator's tooltip refresh across all three states, missing audio's import wording, and actual Ledger hover display in each state. No tests were added or expanded.
- Scoped diff whitespace check passed. A repository-wide check found pre-existing trailing whitespace in an unrelated modified documentation file; it was left untouched.

Qualitative evidence supports clarity through explicit state labels, usefulness through next-action wording, and accuracy through generic stale-state explanations that do not invent a specific cause. Human usability has not been measured; no numerical quality scores are available. No remaining implementation work.
