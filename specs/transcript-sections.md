# Transcript Sections Artifact Specification

Transcript Sections is the routing artifact that identifies the opening recap, player-character introductions, starting-context evidence, and the first utterance of current-session active play. It does not summarize, filter, or classify the rest of the transcript.

## Purpose and position in the pipeline

The artifact is generated from `role_transcript.json` and the current Session attendee mapping before Ledger and Player Introductions generation. It is persisted as `transcript_sections.json` in the session folder and is not shown as a user-facing export.

It produces four views for downstream work:

```text
Role Transcript
 ├── recap_range ───────────────► Routed recap view (available to pipeline consumers)
 ├── introduction_range ────────► Player Introductions pipeline
 ├── starting_context_range ────► Ledger starting_situation
 └── session_start_index ───────► Ledger current-session utterances
```

The routes can overlap. Most importantly, a mixed recap-to-play utterance can be in a range and also be the first current-session utterance, so current-session content is never dropped at the boundary.

Replacing Transcript Sections leaves existing downstream files in place. Its newer modification time makes Ledger, Player Introductions, Recap Summary, and Summary stale through the recursive artifact dependency graph.

## Persisted schema

`transcript_sections.json` is a strict JSON object:

```json
{
  "version": 1,
  "role_transcript_sha256": "64 lowercase hexadecimal characters",
  "recap_range": {"start_index": 0, "end_index": 0},
  "introduction_range": null,
  "starting_context_range": {"start_index": 0, "end_index": 0},
  "session_start_index": 0
}
```

Each non-null range is inclusive and zero-based. `start_index` and `end_index` are non-negative, with `start_index <= end_index`, and both must identify an existing Role Transcript utterance. `session_start_index` is non-negative and must identify an existing utterance, except it may equal the utterance count for a setup-only recording with no active play.

`role_transcript_sha256` binds the routing result to the exact bytes of `role_transcript.json`. The dependency graph treats a newer Role Transcript as making Transcript Sections stale and regenerates it before downstream consumers run. Direct consumers still validate the digest rather than using stale routing.

The packaged Section Transcript `system.md` is also a modification-time dependency. Changing it
makes Transcript Sections and all transitive consumers stale.

## Section definitions

| Field | Required interpretation |
| --- | --- |
| `recap_range` | The smallest inclusive opening interval containing substantive recounting of prior-session events. Announcements, filler, reactions, transition language, and later callbacks do not extend it. `null` when no substantive opening recap exists. |
| `introduction_range` | The smallest inclusive interval enclosing explicit, opening-preamble introductions of attendee-listed player-character roles. It can contain recap material between introductions. `null` when no qualifying introduction exists. |
| `starting_context_range` | The smallest inclusive evidence needed to state the immediate opening situation: directly supported location, objective, conditions, threats, or obstacles. It may overlap recap or the active-play boundary. `null` only when no supported starting situation exists. |
| `session_start_index` | The first utterance of active play in the current session. It commonly is the Game Master's present-scene setup or action prompt. In a mixed transition utterance, use that utterance's index. |

The ranges are minimized independently. Overlap is valid and expected when transcript structure warrants it. When active-play onset is ambiguous, choose the earlier plausible index to preserve current-session material on the Ledger side.

## Routing behavior

The persisted ranges are converted to index-free `(speaker, text)` sequences:

- `recap`: the inclusive Recap Range, or an empty sequence;
- `introductions`: the inclusive Introduction Range, or an empty sequence;
- `starting_context`: the inclusive Starting Context Range;
- `session`: every Role Transcript utterance from `session_start_index` to the end.

Routing for the complete downstream bundle requires `starting_context_range` to be present. If sectioning cannot establish a usable starting situation, the application stops downstream generation rather than inventing one. Player Introductions can still independently slice its optional range: a missing Introduction Range becomes `None` and produces a valid empty artifact.

## Generation and validation

The sectioning LLM has at most three attempts. Each response must satisfy the strict response schema and transcript bounds; out-of-range endpoints, reversed ranges, or an invalid session start are rejected and retried. Successful routing metadata is persisted atomically after its digest is calculated from the current Role Transcript.

The sectioner must read the whole transcript and attendees before selecting boundaries. It only identifies opening structure; it must not skip rules talk, breaks, jokes, or other material after active play begins. Those records stay in the session suffix for later Ledger-level filtering.

## Authoritative implementation references

- Schema, validation, digest binding, and route construction: [`transcript_sections.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/transcript_sections.py)
- Prompt contract: [`section_transcript/system.md`](../packages/tablesage-application/src/tablesage_application/llm/_prompts/section_transcript/system.md)
- Session orchestration and recursive freshness: [`application.py`](../packages/tablesage-application/src/tablesage_application/application.py) and [`artifact_graph.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py)
- Evaluation fixture workflow: [`data_prompts/section_transcript/README.md`](../data_prompts/section_transcript/README.md)
