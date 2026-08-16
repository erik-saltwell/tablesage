# Domain documentation

This repository uses a single bounded-context documentation layout:

- `CONTEXT.md` at the repository root describes the domain language, model, and boundaries.
- `docs/adr/` contains architecture decision records.

Before architecture, diagnosis, TDD, PRD, or triage work:

1. Read `CONTEXT.md` when it exists.
2. Read relevant records under `docs/adr/` when that directory exists.
3. Use the documented domain terminology in code, tests, issues, and explanations.

If these paths do not exist yet, continue with the codebase as the source of truth. Do not create domain documentation unless the task calls for it.
