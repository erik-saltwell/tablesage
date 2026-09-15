# Transcript sectioning and session-scoped outputs

TableSage separates opening context from current-session play so the Ledger does not repeat a spoken recap or roll call. This is an overview of the implemented pipeline; the [artifact contracts](INDEX.md#artifact-contracts) own exact schemas and validation.

## Sources and routes

Role Transcript contains ordered `index`, `speaker`, `text` records. Indices are zero-based for that file's lifetime. Transcript Sections binds its routing to the exact Role Transcript bytes with SHA-256 and records inclusive, independently minimized ranges:

| Route | Consumer |
| --- | --- |
| recap_range | Inspection/evaluation; not the source of generated Recap Summary |
| introduction_range | Optional Player Introductions |
| starting_context_range | Shared starting situation for Ledger and Scene Breakdown |
| session_start_index to end | Current-session Ledger entries and scene events |

Ranges may overlap, including a mixed opening-to-play utterance. Ambiguity favors preserving active-play material. Sectioning does not filter rules talk or breaks after the boundary. Setup-only recordings may put the boundary at the utterance count. Downstream complete routing requires starting context rather than inventing a situation.

The routed slices contain speaker/text pairs; source indices remain in the Role Transcript/routing artifacts. [Transcript Sections](../.work-items/transcript-sections-artifact-contract/specification.md) defines exact bounds and digest checks.

## Generated artifacts

- **Ledger v4:** Session identity, attendees, starting situation and ordered Narration/Action/Speech/Expression/Correction/Question entries. No opening recap or character-introduction preamble.
- **Scene Breakdown v1:** generated in the same response as Ledger, with the same starting situation, complete ordered scenes and ending situation. Scene ranges partition every Ledger entry once. Application adds metadata and generation-time Ledger digest.
- **Player Introductions:** only explicitly introduced non-GM attendee roles from the introduction range. No range means a valid empty artifact without an LLM call.
- **Recap Summary:** selective current-session continuity from Scene Breakdown—not Ledger and not the recording's spoken recap. The prompt targets 180 words, at most 240 words/six bullets. Production checks flat nonempty Markdown bullets; the length budget is prompt/optimizer guidance, not a hard runtime rejection.
- **Detailed Summary:** generated from Ledger with metadata, attendees and glossary, then composed with the prior Session's recap and current introductions.

All are distinct from the ephemeral campaign-aware Previously On and Opportunities exports.

## Composition

The detailed Summary must contain each marker exactly once:

```html
<!-- RECAP -->
<!-- PLAYER_INTRODUCTIONS -->
```

Application substitutes the previous Session's `## Recap` section and the current `## Player Characters` section. Empty introductions remove the marker without an empty heading. The first Session has no previous recap. A previous Session is selected by date, with sequence breaking ties; undated sessions follow dated sessions in sequence order.

The generation planner can recursively rebuild the previous recap before composing a Summary. A missing required prior recap is not silently omitted by a direct Summary call.

## Generation, persistence and freshness

Generate Outputs requires a current completed review and ensures Role Transcript, Sections, joint Ledger/Scene Breakdown, Introductions, Recap and Summary in dependency order. It runs only missing/stale work and can report a no-op. Regenerate Artifact forces a selected step and refreshes its downstream outputs; the shared Ledger producer replaces both siblings.

Structured sectioning, Ledger/Scene Breakdown, introduction and Summary-marker validation use bounded retries. Recap formatting failures also retry up to three attempts; provider failures do not become an unlimited retry loop. The application adds the recap heading after validating the model's bullet-only response.

Handled joint-write failures restore the previous Ledger JSON, Markdown and Scene Breakdown bytes. An incomplete-pair marker blocks readiness/use after an interrupted replacement. Other artifacts follow their individual atomic-write contracts. A plan failure stops later work but does not undo earlier successful steps.

Normal input edits preserve old files. Freshness follows recursive file times, database input clocks, settings and packaged system prompts. Ledger and Scene Breakdown are siblings, not freshness dependencies of each other: their cross-references are generation-time provenance, not a requirement to compare against later hand-edited Ledger bytes. Replacing a recap makes the later Summary that consumes it stale; that later Summary is rebuilt when included in a generation scope, not immediately.

See [dependency tracking](designs/artifact-dependency-tracking/design.md), [Ledger](../.work-items/ledger-artifact-contract/specification.md), [Scene Breakdown and Recap](../.work-items/scene-breakdown-artifact-contract/specification.md), [Player Introductions](../.work-items/player-introductions-artifact-contract/specification.md) and [Summary generation](generate_summary.md).
