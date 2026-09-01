# Glossary extraction — design

## Overview

Glossary extraction is a per-session action that proposes campaign glossary entries from the
session's Role Transcript. The LLM receives the transcript, the session attendees and their
roles, and the current campaign glossary. Its proposals remain temporary until the user reviews
and completes them.

## Extraction

- Session Detail exposes `L` — **Extract Glossary** whenever `role_transcript.json` exists.
- Extraction is independent of Generate and can be rerun.
- The LLM proposes campaign-specific terms supported by the transcript, including NPCs, places,
  factions, artifacts, customs, and campaign-specific rules or concepts.
- Attendee names and their assigned player-character roles are known context and are not proposed.
  NPC names not present in that context remain eligible.
- Generic RPG vocabulary and speculative terms or definitions are omitted.
- Descriptions are requested but optional.
- Existing glossary entries are supplied to discourage duplicates. Proposals duplicating the
  current glossary are removed before review. If none remain, the user stays on Session Detail
  and is notified that no new terms were found.
- An extraction failure leaves the glossary unchanged.

## Review

The review screen owns an in-memory working copy. It uses the standard table actions:

- `N` adds an entry;
- `E` edits the selected term and description;
- `D` deletes the selected entry from the proposal;
- `F` opens the existing global Find & Replace interaction, applying replacement to both terms
  and descriptions across every row;
- **Complete** commits the remaining valid entries;
- **Cancel** discards the working copy.

Terms are ordered alphabetically without regard to case and re-sorted after edits. Descriptions
may be empty. Complete is blocked if any term is blank.

The proposal is not persisted. Leaving or cancelling the screen discards it; rerunning extraction
invokes the LLM again.

## Completion rules

Duplicate comparison uses trimmed, case-insensitive terms. On Complete:

1. Seed the duplicate set from the campaign's current glossary, so existing entries always win.
2. Process reviewed rows in their displayed order; the first occurrence of a new normalized term
   wins and later occurrences are dropped, even when their descriptions differ.
3. Write all accepted entries to the session's campaign glossary in one operation.
4. Return to Session Detail and report the counts added and skipped as duplicates.

The duplicate check is repeated at completion to cover review edits and glossary changes made
while review was open. Completed entries are ordinary campaign `GlossaryEntry` records with no
source-session provenance. Completion does not invalidate existing Ledger or Summary artifacts.

