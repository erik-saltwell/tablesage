# Generate Ledger

## Overview

Generate a version-4 `ledger.json` containing only the starting situation and events from the
current Session. The format is defined in [Canonical Ledger Format v4](canonical_ledger_format_v4.md).

Ledger generation is an incomplete semantic condensation. It may omit irrelevant material,
rephrase one transcript utterance, combine several utterances or speakers, or split one utterance
into several entries. List order preserves semantic chronology.

## Inputs

Ledger generation depends on a compact `role_transcript.json` and a current
`transcript_sections.json` whose SHA-256 fingerprint matches the exact Role Transcript bytes. The
application uses the section metadata to build two index-free `{speaker, text}` arrays:

- **Starting Context** selects the inclusive `starting_context_range` and may be used only to
  establish the required `starting_situation`.
- **Session Utterances** is the complete suffix beginning at `session_start_index` and is the only
  source for regular Ledger entries.

The generation call also receives known Session roles, attendee-to-role mappings, and the campaign
glossary. The glossary supplies spellings and cannot introduce facts absent from the transcript.

If Transcript Sections is missing, stale, out of bounds, or has no Starting Context range, Ledger
generation stops before calling the LLM.

## Schema and Generation Response

All models reject extra fields. Persisted content strings are trimmed and non-empty. The generated
response contains:

```text
LedgerGenerationResponse
  scratchpad: text
  starting_situation: non-empty text
  utterances: ordered list[
    Narration | Action | Speech | Expression | Correction | Question
  ]
```

The persisted Ledger adds application-supplied `version: 4`, `session_id`, `session_name`, and
`attendees`. An empty `utterances` list is valid when the transcript establishes a starting
situation but active play never proceeds. Preamble, Recap, and Character Introduction fields do
not exist in v4.

Regular `source` values remain unrestricted non-empty strings. Question `asker` and `resolver`
values are checked against Session attendees as generation warnings.

## Generation Flow

1. Confirm that Role Transcript and Transcript Sections artifacts exist.
2. Verify the Transcript Sections fingerprint against the exact Role Transcript bytes.
3. Validate the persisted ranges and build Starting Context and Session Utterance slices without
   source indices.
4. Load and normalize known roles, attendees, and glossary entries.
5. Request a structured `LedgerGenerationResponse` using the configured high-effort model.
6. Retry malformed responses or responses containing unknown Question attendees up to a total of
   three attempts. Provider and configuration errors fail immediately.
7. Accept a warning-free response immediately. If every structurally valid candidate has warnings,
   choose the candidate with the fewest warnings; the earliest candidate wins ties.
8. Inject application-owned metadata and atomically replace `ledger.json` and its deterministic
   `ledger.md` companion.
9. Invalidate artifacts derived from the previous Ledger.

No attempt may use opening recap or introduction ranges as Ledger content. A stale fingerprint is
an error rather than an invitation to silently slice a changed transcript.

## Artifact and Rendering Behavior

`ledger.json` is canonical, visible in Session Detail, and exportable. `ledger.md` is its generated
read-only companion. The readable view contains the Session title, attendee roster,
`## Starting Situation`, a numbered `## Session`, and the Session/version footer. It contains no
Recap or Characters section.

A failed LLM call or failed atomic write preserves the existing Ledger and Summary. Successful
replacement invalidates downstream Ledger-derived artifacts. Existing v3 Ledgers are not read or
migrated; Sessions are reprocessed to create v4.

## Implementation Boundaries

- Transcript sectioning decides only the opening boundary and routing ranges; Ledger generation
  still decides which current-session material is relevant and how it should be classified.
- The application owns Session metadata, source-fingerprint verification, slicing, and atomic
  persistence.
- The LLM owns only `starting_situation` and the ordered semantic entries.
- `scratchpad` is discarded and never persisted.
