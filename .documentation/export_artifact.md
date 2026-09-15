# Export a session artifact

Session Detail's **X — Export** opens `ArtifactExportScreen`, a single-row-at-a-time export picker. This is separate from campaign/player ZIP transfer and the campaign preparation Markdown exporters.

## Selection and flow

The list contains `ARTIFACTS` entries whose `should_show_in_ui` flag is true and whose files are present according to `session_artifacts`. Current visible entries include Input Audio, Transcript (Markdown), Reviewed Transcript, Role Transcript, Ledger, Recap Summary and Summary. Internal JSON transcript, routing, introductions, benchmark and Scene Breakdown files are not offered.

**Export is existence-based, not freshness-gated.** An old file can be exported even when Session Detail marks it stale. An interrupted Ledger-pair marker suppresses the affected Ledger/Scene Breakdown/recap/summary entries in the presence helper.

1. Select a row and use E, Enter or double-click.
2. Ledger asks for readable Markdown or canonical JSON. Markdown regenerates `ledger.md` deterministically from the canonical JSON without an LLM call.
3. The shared FileSave picker starts at the user's home directory and suggests the artifact filename.
4. Confirming copies the selected file to the destination. The screen stays open for another export; cancelling leaves it unchanged.

FileSave allows overwrite without the additional confirmation used by campaign preparation exporters. Do not assume all export screens have identical overwrite or destination policies.

## Source behavior

Ordinary export uses `shutil.copyfile` and does not move/delete the source or create a new artifact record. Readable Ledger export is the exception to a strictly read-only source operation: it refreshes the reproducible `ledger.md` companion before copying. Canonical `ledger.json` remains unchanged.

The list refreshes when loaded/refreshed rather than watching background filesystem changes.

## Implementation

- [paths.py](../packages/tablesage-application/src/tablesage_application/paths.py): artifact registry and visibility.
- [session_pipeline/artifacts.py](../packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py): presence filter, export gate and copy helper.
- [Application](../packages/tablesage-application/src/tablesage_application/application.py): session resolution and Ledger Markdown rendering.
- [artifact_export.py](../apps/tablesage-tui/src/tablesage_tui/screens/artifact_export.py): list, representation choice and shared FileSave wrapper.

No extra settings, multi-select or export-all session action is involved. Player and campaign archive exports are implemented elsewhere, not through this registry.
