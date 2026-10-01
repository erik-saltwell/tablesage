---
name: "Workspace agent help"
status: implementing
---

# Workspace Agent Help

Let a user launch Claude Code, Codex, or Gemini CLI from their TableSage workspace and get accurate help using the app, plus troubleshooting of their own workspace. The agent draws on bundled help topics, read-only database access, and a TableSage-owned agent guide that thin root `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` stubs point to. A Welcome screen **(H) Advanced Help** call to action makes the feature discoverable.

- [intent.md](intent.md): scope, expected behavior, acceptance conditions, settled decisions, and unresolved questions from the 2026-10-01 flesh-out session. It also holds the approved [quality rubric](intent.md#quality-rubric). Following the `define-rubric` skill, which the user invoked, the rubric uses descriptions without scores or anchors and is saved in `intent.md`. This differs from `.work-items/workflow.md`, which still describes numerical rubrics in `rubric.md`; reconciling the workflow is a separate change.
- [idea.md](idea.md): the earlier workshop result, how the idea evolved, risks, and what was set aside. `intent.md` governs where they differ.

- [progress.md](progress.md): implementation handoff, deviations from the intent, and verification results.

## Resume Note

Implementation of the code, documentation, packaging, and screenshots is done and verified by direct checks (see [progress.md](progress.md)). The status stays `implementing` because one acceptance condition is unmet: the broken-workspace validation with Claude Code and Codex, which the user needs to run. Its results decide the next Troubleshooting FAQ entries and whether a `doctor` command is justified. Nothing has been committed.
