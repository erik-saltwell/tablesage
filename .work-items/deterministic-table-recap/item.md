---
name: "Deterministic Session Summary"
status: complete
---

# Deterministic Session Summary

Move the former deterministic Table Recap renderer to the existing Summary artifact, writing `summary.md` from Post-Session Matters and existing Scene Log/Session metadata without model calls. Preserve the current content and user-edited layout in [session_summary.j2](../../packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2). See [specification](specification.md), [plan](plan.md) and [progress](progress.md).

Archive existing summaries before requested replacement. Keep Table Recap files and existing UI entry points, but pause generation until its replacement is designed. Campaign preparation remains paused. The standalone command is `tablesage regenerate-session-summary --campaign NAME --session NUMBER`, run from the deployment workspace.

Implementation is authorized; no commit or live model regeneration is requested. Verify in a disposable workspace and preserve shared generated files. Historical progress below records the earlier Table Recap implementation.

Transition complete. See [verification and limits](progress.md). Shared files were preserved; changes are uncommitted.
