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

## Accepted design

See [03-design.md](03-design.md). Extraction is a separate per-session action over the Role
Transcript. Its LLM proposals are edited in a temporary review table and written to the campaign
glossary only on Complete. Existing terms win; trimmed, case-insensitive duplicates are dropped.

## Acceptance criteria

- Session Detail offers `L` — Extract Glossary when the Role Transcript exists.
- The LLM receives the Role Transcript, attendees and assigned roles, and current campaign
  glossary, and returns structured term/optional-description proposals.
- Attendee and player-character names are excluded while NPC names remain eligible.
- Existing-glossary duplicates are filtered before review; an empty result produces a notification
  without opening the review screen.
- Review supports standard New, Edit, Delete, Complete, and Cancel behavior plus global Find &
  Replace across terms and descriptions.
- Complete atomically adds valid unique entries, repeats duplicate checking against the current
  glossary, and reports added and skipped counts.
- Cancel and extraction failures leave the campaign glossary unchanged.
- Completion neither records source-session provenance nor invalidates Ledger or Summary artifacts.

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

`complete` — design: [03-design.md](03-design.md), implemented in commit `9c49dfa`.
