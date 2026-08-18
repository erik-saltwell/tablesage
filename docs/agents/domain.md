# Domain documentation

This repository documents its domain model, use cases, business rules, architecture, and TUI
design under `.documentation/` at the repository root — not the `CONTEXT.md` / `docs/adr/` layout
some other repositories use.

- `.documentation/tablesage_data_model.md` — the persistent relational model (SQLModel/SQLite):
  tables, fields, constraints, relationship rules.
- `.documentation/tablesage_use_cases.md` — product-level behavior, screen-agnostic.
- `.documentation/application_business_rules.md` — application-layer business rules (invalidation,
  voice-sample pruning/replacement, processing pipeline order, etc.), carried forward from a
  retired file-based implementation.
- `.documentation/system_architecture.md` — the package layering (`tablesage-tui` →
  `tablesage-application` → `tablesage-model`/`tablesage-tools`) and what belongs in each.
- `.documentation/tablesage_tui_screens.md` — the TUI screen inventory, navigation model, and
  reusable screen-taxonomy/binding conventions. Read before designing or implementing any screen.
- `.documentation/tablesage_implementation_plan.md` — the phased build-out plan for the current
  campaign/player re-architecture, with each phase marked complete as it finishes. Check this first
  for what's actually built vs. still planned.

Before architecture, diagnosis, TDD, PRD, or triage work:

1. Read the `.documentation/*.md` file(s) relevant to the task from the list above.
2. Use the documented domain terminology (Campaign, Player, CampaignPlayer roster, Session, etc.)
   in code, tests, issues, and explanations.
3. Keep the relevant doc in sync when a change alters the data model, use cases, architecture, or
   screen design — update it as part of the same change, not as a follow-up task.

If `.documentation/` does not exist (e.g. a different repository state), continue with the
codebase as the source of truth. Do not create domain documentation unless the task calls for it.
