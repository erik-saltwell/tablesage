---
name: "Remove Python source freshness dependencies"
status: complete
---

# Remove Python Source Freshness Dependencies

Per the user's explicit preference, edits to Python source files must not automatically invalidate generated outputs. Remove Python-file dependency declarations from Ledger, Scene Log, every Matters category, Transcript Sections, Player Introductions, Post-Session Matters and Summary. Keep prompt/template/schema resources, settings/control values, metadata, and artifact dependencies intact. Preserve normal validation, compatibility checks and explicit forced regeneration.

Old Python fingerprint entries can remain in completion records: the existing evaluator ignores inputs no longer declared, so no production metadata migration is needed. The graph should stop recording Python inputs on future completion. Removing Python tracking does not rebuild or rewrite campaign outputs. Regenerate Artifact can force a code-related rebuild; campaign Regenerate All Outputs remains a refresh of missing/stale outputs.

No engineering quality rubric was defined; proceed under the explicit implementation request. Existing shared Python fingerprints were responsible for the avoidable rebuilds diagnosed in this conversation. Source declarations have been removed and behavioral verification is complete. See the [Matters contract](../port-tablesage-matters-artifacts/specification.md), [Post-Session Matters contract](../post-session-matters/specification.md), and [Summary contract](../deterministic-table-recap/specification.md).

## Verification

A disposable snapshot of the four-session Campaign and database exercised the actual Application graph and planner. All 156 steps have zero Python-file dependencies, and fresh completion fingerprints contain no Python-file entries. Synthetic current completion records in that disposable copy deliberately retained stale/missing legacy Python hashes: all four normal generation plans remained empty. Creating, editing and deleting the obsolete Python input had no effect. Prompt edits still stale their category and downstream outputs; Summary template edits stale Summary alone; category schema edits stale consumers; prior Present Matters changes stale the next Scene Log; and generation-setting changes remain tracked. Forced Scene Log regeneration schedules its downstream closure without rebuilding a current Ledger, and forced Summary regeneration schedules Summary alone.

Ruff for both changed Python files, whole-project type checking, targeted whitespace checks and wheel build passed. No unit tests were created or expanded; no model calls, production metadata migrations or campaign output changes were performed. Evidence: [/tmp/tablesage-no-python-deps-793ypma2/report.json](/tmp/tablesage-no-python-deps-793ypma2/report.json). Wheel: `/tmp/tablesage-no-python-deps-wheel/tablesage_rpg-1.0.1-py3-none-any.whl`.
