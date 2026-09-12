# Player Introductions Artifact Specification

Player Introductions is a per-session sidecar containing concise descriptions of player characters explicitly introduced in the opening preamble. It deliberately captures neither a session recap nor a character dossier inferred from later play.

## Purpose and position in the pipeline

Transcript Sections identifies an optional Introduction Range in the Role Transcript. Player Introductions consumes only that range, plus attendee-role mappings and glossary spellings. It runs after the Role Transcript and Transcript Sections artifacts exist.

The persisted artifact is `player_introductions.json` in the session folder. It is later rendered to Markdown and inserted into the generated Summary at the Summary's Player Introductions composition marker. Replacing it makes `summary.md` stale by modification time, but does not affect the Ledger or Recap Summary.

When the Introduction Range is `null`, no LLM call is made and an empty introductions artifact is persisted. An empty artifact is therefore a valid and meaningful result.

The packaged Generate Player Introductions `system.md` is a build dependency. Changing it makes
the artifact stale even though a particular run may take the valid no-LLM empty-range path.

## Persisted schema

`player_introductions.json` is a strict JSON object with this shape:

```json
{
  "version": 1,
  "session_id": "UUID",
  "introductions": [
    {
      "character": "Exact eligible attendee role name",
      "description": "Concise, non-empty in-fiction description"
    }
  ]
}
```

Unknown fields are rejected. `character` and `description` are trimmed, non-empty strings. A character may occur at most once, case-insensitively. The Markdown rendering is a `## Player Characters` heading followed by one bullet per introduction; it renders as an empty string for an empty array.

## Eligibility and source rules

A qualifying character must meet both conditions:

1. Its name exactly matches a non-Game-Master role in the Session attendee mapping.
2. The Introduction Range explicitly presents it as part of an opening introduction or roll-call.

The attendee mapping is authoritative: player names, NPCs, and every Game Master role are ineligible, regardless of how much they are described. The speaker of the introduction need not be the introduced character; another player or the Game Master may give it.

Only explicitly stated, in-fiction introduction facts may appear in the description: for example, appearance, ancestry, occupation, class, personality, background, relationships, or an immediate motivation. The glossary may normalize a term that occurs in the slice, but it cannot establish a character or add a fact. Campaign metadata is orientation-only.

The Introduction Range is a smallest enclosing range, so it can include recap or other intervening content. The generator must classify individual utterances within that range rather than treating every utterance as introductory. It must consolidate qualifying statements about each character, preserve first-introduction order, and avoid connective prose or inference.

## Exclusions

Do not include:

- NPC or Game Master introductions;
- attendee/player names in the `character` field;
- prior-session recap and other intervening material;
- character information revealed incidentally in active play or only suggested by actions, abilities, equipment, or dialogue;
- rules, statistics, build explanations, and real-world inspiration, except the explicitly stated in-fiction component of a mixed statement;
- facts found only in the glossary or session metadata.

## Generation and validation

The generator makes at most three attempts. Each response must conform to the strict response schema, contain no duplicate character, and contain only eligible attendee roles. A failed attempt is discarded; all failures raise an error without persisting a replacement. Valid artifacts are written atomically.

Like the Ledger, this generator refuses a Transcript Sections artifact whose stored Role Transcript hash no longer matches `role_transcript.json`.

## Authoritative implementation references

- Schema, eligibility validation, persistence, and rendering: [`generate_player_introductions.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_player_introductions.py)
- Prompt contract: [`generate_player_introductions/system.md`](../packages/tablesage-application/src/tablesage_application/llm/_prompts/generate_player_introductions/system.md)
- Summary composition: [`generate_summary.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_summary.py)
- Session orchestration and recursive freshness: [`application.py`](../packages/tablesage-application/src/tablesage_application/application.py) and [`artifact_graph.py`](../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py)
