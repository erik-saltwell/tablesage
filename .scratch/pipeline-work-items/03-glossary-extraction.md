# Glossary extraction

## Problem / desired outcome

The campaign Glossary (`GlossaryEntry`: `term` + optional `description`, campaign-scoped, unique
per term) is currently 100% manual — created/edited/deleted one at a time via
`entities/glossary.py` and whatever UI drives it (`dialogs/glossary_entry.py`). It's used as prompt
context for both Ledger and Summary generation (`known_roles` aside, glossary entries are the
other campaign-level context both consumers read). There's no automated way to populate it from
session content — a term coined mid-session ("the Sundered Vale", an NPC's title, a house rule)
has to be manually copied into the Glossary by the user after the fact, or it's simply missing
from future generations' context.

We want an LLM-driven extraction step: given a session's role transcript (and, if useful,
existing glossary entries to avoid duplicates), propose new glossary terms + descriptions for the
user to review and accept/reject/edit before they're written to the campaign Glossary.

## Open questions (why this is `needs-info`)

- **Trigger**: automatic as part of Generate (a fourth step after Role Transcript / Ledger /
  Summary), a separate on-demand action, or run against the Ledger instead of the raw
  role-transcript (the Ledger is already a condensation — might be a cheaper/cleaner extraction
  source)?
- **Review UI**: does the user get a proposal screen (accept/reject/edit each candidate, à la
  `SpeakerResolutionDialog`'s pattern) before anything is written, or does it write directly with
  dedup-by-term silently skipping collisions?
- **Scope**: per-session extraction only, or does it also need a "scan every session in the
  campaign" backfill mode?
- **Dedup**: how are near-duplicate terms handled (case variants, "the Sundered Vale" vs "Sundered
  Vale")? Exact-term uniqueness is already DB-enforced (`IntegrityError` on duplicate `term`), but
  extraction can't rely on the DB catching everything before the LLM call.

## Implementation context

- `packages/tablesage-application/src/tablesage_application/entities/glossary.py` — existing CRUD.
- `packages/tablesage-model` — `GlossaryEntry` model (`term`, `description`, `campaign_id`).
- `packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py`
  and `generate_ledger.py` — both existing consumers of glossary entries as prompt context; useful
  precedent for how extraction's own LLM call/prompt module should be shaped
  (`session_pipeline/generate_<x>.py` + `llm/_prompts/<x>/`).
- `session_pipeline/clean_transcript.render_role_transcript_text` — likely extraction source text.
- `dialogs/glossary_entry.py`, `dialogs/speaker_resolution.py` — existing dialog patterns for
  single-entry edit vs. multi-candidate proposal review, respectively.

## Triage state

`needs-info` — resolve trigger point, review UI, and scope questions above before writing
acceptance criteria.
