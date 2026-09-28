# Implementation progress

- [x] Dim completed automatic rows and make manual labels visually primary.
- [x] Preserve visual prominence for automatic rows that are running or failed.
- [x] Make Up and Down skip automatic rows.
- [x] Verify the TUI behavior and relevant checks.

Automatic labels and completed checks are dimmed, while manual labels are bold.
An automatic row returns to normal emphasis when it is running or failed. The
processing-step table now overrides Up and Down to visit manual rows only;
mouse selection still permits interacting with an automatic row.

Verification: a direct Textual check confirmed Up/Down moves across automatic
rows and lands only on manual rows. `test_processing_coordinator.py` and
`test_processing_steps.py` passed (58 tests), as did Ruff lint/format and `ty`
checking for the modified screen.
