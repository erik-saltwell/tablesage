---
name: "Remove immediate goals from Matters and Session Summary"
status: complete
---

# Remove Immediate Goals

Present Matters now generates only `current_position` and `present_danger`. Remove immediate-goal guidance and the schema field, bootstrap state, shared category list and prior-session Scene Log passage field. Adjust the Goal Impediments prompt to stop directing scene-local obstacles to the removed category.

Post-Session Matters inherits the reduced Present Matters schema automatically and preserves those two fields unchanged. Session Summary prepares and renders only position and danger in its closing orientation, removing the immediate-goals `Next` section and its duplicate-suppression input. Open Matters Goals remain unchanged. Update the [Matters contract](../port-tablesage-matters-artifacts/specification.md), [Post-Session Matters contract](../post-session-matters/specification.md), [Session Summary contract](../deterministic-table-recap/specification.md) and relevant public documentation.

Existing Present Matters and combined publications containing `immediate_goals` fail the updated strict schema and require regeneration through the normal pipeline. No stored campaign artifacts were migrated or regenerated. No engineering quality rubric was defined; implementation proceeded under the explicit request.

Verification passed: targeted Ruff, whole-project `ty check`, and `git diff --check`. Direct execution verified source/combined schema validation and rejection of the removed field; assembly; Summary rendering with and without danger; prior Scene Log passage construction; packaged prompt rendering; and bootstrap state. No model calls or unit-test additions were made. Model output behavior remains unassessed. Historical progress records and the old sample in `docs/delete_me/` retain their original content.
