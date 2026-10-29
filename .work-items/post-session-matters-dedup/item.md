---
name: "Remove duplicates in Post-Session Matters"
status: complete
---

# Remove Duplicates in Post-Session Matters

Post-Session Matters often contains several items with the same information, filed under different categories. For example, a single event may appear as a Development, an Opportunity and an Obligation, with each item's wording adapted to its category. The repeats add no new information, so they are extra reading or listening without value. This affects the assembled artifact and the Session Summary rendered from it.

## Intended Outcome

Use an LLM to find groups of items that carry the same content under different categories. Then let deterministic code remove the redundant copies from the assembled Post-Session Matters output.

## Clarified Scope

- **Cross-category duplication:** The target is the same content repeated across different Matters categories, each worded for its category. Duplicates within one category were not identified as the problem.
- **Assembled output only:** Remove duplicates only from the combined `post_session_matters.json`, and so from the Deterministic Session Summary built from it. The ten individual Matters artifacts stay unchanged, because extractors and later Sessions use them.
- **Division of labour:** The LLM identifies duplicates. Deterministic code performs the removal.

## Open Questions

The design questions were settled on 2026-10-27 and are recorded in [intent.md](intent.md). Only coverage reliability remains open. It is resolved by a manual check on real Sessions after the work is built.

## References

- [Intent](intent.md): settled design, contract changes, acceptance conditions and quality rubric
- [Idea](idea.md): the workshopped working direction
- [Plan](plan.md): phased implementation steps
- [Post-Session Matters specification](../post-session-matters/specification.md) (this work changes it)
- [Deterministic Session Summary specification](../deterministic-table-recap/specification.md)

## Completion Note

Closed on 2026-10-27 at the user's direction, without implementation. The user decided not to implement this work. No code, specification or documentation was changed, and no verification or rubric evaluation was performed.

The design and the plan were finished before the item was closed:
- [intent.md](intent.md): settled decisions and the rubric.
- [plan.md](plan.md): phased steps.

These open points were never resolved:
- Whether to block removal of items that remaining items link to. The recommendation was yes.
- Which workspace to use for the manual check. The recommendation was `deployment/campaigns/Brandonsford/`, after a backup.
- Which verification commands to use. The recommendation was the pre-commit set: `uv run ruff format --check`, `uv run ruff check`, `uv run ty check packages apps/tablesage-tui`.

Reopen the item to resume from Phase 1 of the plan.
