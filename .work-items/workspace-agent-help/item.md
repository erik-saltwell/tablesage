---
name: "Workspace agent help"
status: complete
---

# Workspace Agent Help

Let a user launch Claude Code, Codex, or Gemini CLI from their TableSage workspace and get accurate help using the app, plus troubleshooting of their own workspace. The agent draws on bundled help topics, read-only database access, and a TableSage-owned agent guide that thin root `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` stubs point to. A Welcome screen **(H) Advanced Help** call to action makes the feature discoverable.

- [intent.md](intent.md): scope, expected behavior, acceptance conditions, settled decisions, and unresolved questions from the 2026-10-01 flesh-out session. It also holds the approved [quality rubric](intent.md#quality-rubric). Following the `define-rubric` skill, which the user invoked, the rubric uses descriptions without scores or anchors and is saved in `intent.md`. This differs from `.work-items/workflow.md`, which still describes numerical rubrics in `rubric.md`; reconciling the workflow is a separate change.
- [idea.md](idea.md): the earlier workshop result, how the idea evolved, risks, and what was set aside. `intent.md` governs where they differ.

- [progress.md](progress.md): implementation handoff, deviations from the intent, and verification results.

## Completion

Completed on 2026-10-01 at the user's explicit request. The code, documentation, packaging, and screenshots were implemented and checked directly, as recorded in [progress.md](progress.md): lint, formatting, and type checks pass; the commands, agent-file handling, opt-out, installed-wheel contents, Welcome screen layout, and docs links were exercised by hand. No tests were added, per the workflow.

Known limitations at completion, none of which block closure:

- **Validation not run:** the broken-workspace test with Claude Code and Codex (see [idea.md](idea.md#validating-the-bet)) has not been done. It is the only check of whether an agent diagnoses well from the Troubleshooting FAQ, and of whether Codex finds `AGENTS.md` and Gemini CLI follows the `@` import. Its results would decide the next FAQ entries and whether a `doctor` command is warranted.
- **Open decision:** launching TableSage in the home folder or a repo subfolder creates the agent stub files there, which Claude Code and Gemini CLI also read from parent folders. A guard (such as skipping the stubs in the home folder) was proposed and not implemented.
- **Existing test failures:** 3 `test_campaign_detail.py::test_new_session_*` tests fail because of the user's separate, uncommitted required-date change, not this work.
- **Quality rubric:** no evaluation was performed, so every dimension in [intent.md](intent.md#quality-rubric) is unassessed.
- **Not committed:** all changes remain in the working tree.
