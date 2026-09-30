---
name: "Consistent footer binding order"
status: complete
---

# Consistent footer binding order

Each list's New, Edit, and Delete bindings appear together, in that order, at the end of the left-aligned primary actions. Other actions stays last overall and docked right. Delete labels name their targets, and the explicit screen orders and role-dialog exception follow the user's decisions.

Player Detail is F Folder Import → M Edit Metadata → D Delete Voice Clip. D still deletes the selected voice clip. All agreed binding, button-label, documentation-flow, and screenshot changes are implemented.

- [Intent and final binding table](intent.md)
- [Completion and verification](progress.md)
- [All 112 refreshed screenshot assets](screenshots.json)

Completed on 2026-09-30. The existing TUI suite passes all 313 tests; lint, formatting, type checks, direct keyboard/mouse checks, screenshot inventory/hash checks, and documentation image-link checks pass. Full footers fit at 140 columns; the existing clipping at narrower widths is recorded in the documentation. No numerical rubric or assessment was introduced, and unrelated workspace changes were preserved.
