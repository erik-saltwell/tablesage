# Artifact dependency tracking and incremental generation

## Status and purpose

Implemented design. This document describes TableSage's build-system-style dependency tracking, which replaces the fixed, invalidation-driven Session output pipeline. The goal is to regenerate only missing or stale work, preserve current artifacts, and correctly propagate freshness through transitive dependencies.

This design is reflected in [Ledger](../../specs/ledger.md), [Scene Breakdown and Recap](../../specs/scene-breakdown.md), [Player Introductions](../../specs/player-introductions.md), and [Transcript Sections](../../specs/transcript-sections.md).

## Implemented behavior

TableSage treats processing as a directed acyclic build graph. A build step declares:

- every file artifact it reads;
- every database-backed logical input it reads;
- every packaged LLM system prompt used by the step;
- one or more files it produces; and
- the operation that produces them.

One artifact may depend on several inputs of either kind. For example, Summary may consume the current Ledger, Player Introductions, the previous Session's Recap Summary, glossary state, attendance, and relevant Campaign and Session metadata.

`Generate Outputs` recursively evaluates the graph and runs only work that is missing or stale. It must not overwrite a current artifact merely because that artifact appears in the requested output pipeline.

## Freshness model

A build step is current only when:

1. all of its required canonical outputs exist;
2. every direct dependency is itself current; and
3. no file dependency or database-input timestamp is newer than any required canonical output.

Equivalently, a step is stale when any dependency is stale, even if that direct dependency's file is older than the step's output. Freshness is recursive rather than a one-level timestamp comparison.

For example:

```text
Role Transcript: 15:00
Scene Breakdown: 13:00
Recap Summary:   14:00
```

Recap Summary is stale. Scene Breakdown is stale because Role Transcript is newer, and that stale state propagates to Recap Summary despite Recap Summary being newer than Scene Breakdown. Generation first rebuilds Scene Breakdown, then reassesses and rebuilds Recap Summary.

The recursive invariant is:

```text
current(artifact) =
    artifact exists
    AND every dependency is current
    AND artifact is not older than any dependency
```

Filesystem comparisons should use nanosecond modification times where available. A successful `Generate Outputs` run guarantees that every target in that run's scope is transitively current.

### Database-backed inputs

Database state participates through explicit logical modification timestamps updated in the same transaction as the underlying change. The model supplies these timestamps (not every clock is a dependency of every step):

- Campaign glossary modification time (`Campaign.glossary_updated_at`);
- Campaign roster modification time (`Campaign.roster_updated_at`);
- Campaign metadata modification time (`Campaign.updated_at`) for fields actually used by generators;
- Session attendance modification time (`Session.attendance_updated_at`);
- Session metadata modification time for name and date; and
- player voice-profile or centroid modification time where it affects transcription.

Only real dependencies are declared. For example, existing Session outputs depend on that Session's attendance, not on the Campaign roster that originally seeded it; the roster clock is available for operations that do consume the current roster.

### Hand edits and UI edits

Editing a canonical artifact directly advances its filesystem modification time and makes its consumers stale. Editing a canonical artifact through the UI must atomically replace or touch the canonical file so it has the same effect. Editing database-backed inputs advances their logical timestamps.

Freshness propagation remains recursive in every case. If an edited Role Transcript makes Scene Breakdown stale, everything that consumes Scene Breakdown is also stale even when its own file is newer than the old Scene Breakdown.

Modification times will not detect an out-of-band replacement that deliberately preserves or backdates a file timestamp. Explicit forced regeneration is the initial fallback. Content hashing may be considered later if this limitation proves important.

### LLM system prompts

Every build step that invokes an LLM declares the packaged `system.md` file for each distinct
prompt it uses. These are regular modification-time inputs: changing a system prompt makes that
step stale and propagates staleness to its consumers. A step may declare more than one system
prompt when it performs multiple kinds of LLM call. Repeated calls using the same prompt require
only one dependency. User-message `.j2` templates are not prompt dependencies in this design.

The current mapping is:

- Transcript → Classify Backchannels;
- Transcript Sections → Section Transcript;
- Ledger + Scene Breakdown → Generate Ledger;
- Player Introductions → Generate Player Introductions;
- Recap Summary → Generate Recap Summary; and
- Summary → Summarize Session.

Reviewed Transcript, Benchmark Transcript, and Role Transcript are manual or mechanical steps and
therefore have no LLM system-prompt dependency.

## Logical artifacts, physical files, and build steps

The graph distinguishes logical artifacts from the files used to materialize them and from the build step that produces them.

### Multi-file outputs

Some logical artifacts are materialized as several files by one build step:

```text
Transcript
├── transcript.json       canonical
└── transcript.md         deterministic view

Ledger
├── ledger.json           canonical
└── ledger.md             deterministic view
```

All required files participate in the producing step's freshness. If one is missing or older than an upstream input, the step is stale. Downstream steps depend only on the particular canonical file they consume, so hand-editing a companion does not stale them unless that companion is explicitly declared as an input.

### Shared producers with sibling outputs

One expensive step may produce several canonical logical artifacts:

```text
Generate Ledger Data

Inputs:
- role_transcript.json
- transcript_sections.json
- applicable database timestamps

Outputs:
- ledger.json
- scene_breakdown.json
```

Ledger and Scene Breakdown are sibling outputs with a shared producer. Neither is a freshness dependency of the other. The shared step runs if an upstream input is newer than either required output, either output is missing, or the user explicitly forces the step. When it runs, it produces and safely replaces both outputs.

Consequently:

- hand-editing `ledger.json` stales Summary but does not stale Scene Breakdown or Recap Summary;
- hand-editing `scene_breakdown.json` stales Recap Summary but does not stale Ledger or the detailed Summary; and
- rebuilding Role Transcript or Transcript Sections stales the shared producer, which replaces both siblings and consequently stales both downstream branches.

This replaced the earlier exact-byte lifecycle binding from Scene Breakdown to Ledger. A shared generation identifier may remain as provenance, but it must not cause editing one sibling to invalidate or suppress the other.

## Representative dependency graph

This graph is illustrative rather than a complete declaration of every settings and database input:

```text
Input Audio
└── Transcription
    └── transcript.json
        └── transcript.md

Reviewed Transcript
└── Role Transcript
    └── Transcript Sections
        ├── Generate Ledger Data
        │   ├── Ledger
        │   │   ├── ledger.md
        │   │   └── Summary
        │   └── Scene Breakdown
        │       └── Recap Summary
        └── Player Introductions
            └── Summary

Previous Session's Recap Summary
└── Current Session's Summary
```

Each node may have multiple additional inputs. Summary, for example, also consumes glossary, attendance, and relevant metadata timestamps.

## Generation and regeneration

### Generate Outputs

`Generate Outputs` resolves its targets recursively in dependency order:

1. ensure each dependency is current;
2. reassess the target after dependencies have been processed;
3. skip the target if it is current; and
4. generate it if it is missing or stale.

This replaced the earlier fixed six-phase behavior and prevents stale transitive content from surviving a successful run.

### Forced regeneration

Ordinary regeneration does not delete the old output first. The selected build step is forced in the current processing plan:

1. resolve its prerequisites;
2. retain existing output files while generation runs;
3. stage new output files;
4. replace the old files only after successful generation; and
5. process downstream targets made stale by the replacement.

If generation fails, existing artifacts remain available. If a process stops after replacing an upstream artifact but before rebuilding its consumers, filesystem times make those consumers stale during the next run. A persistent stale manifest is therefore not part of the initial design.

`Clean Session` remains the exceptional destructive operation that deletes every Session artifact, including imported audio.

### Processing scope

Freshness guarantees apply to the targets included in a Generate operation. A current Session's Summary may recursively ensure a previous Session's Recap Summary because it is an upstream dependency. The inverse is not automatically true: regenerating a Session's recap does not necessarily rebuild a later Session's Summary unless later Sessions are included in the operation's target scope.

Session Detail G is session-scoped. Campaign Detail O, **Regenerate All Outputs**, is also implemented: it visits sessions in sequence order, selects those with imported audio and a current reviewed transcript, and calls the same stale-aware generate_outputs for each. It does not force already-current phases despite its label. Sessions awaiting review are skipped and counted; sessions without imported audio are outside this operation. A failure stops the run rather than guaranteeing that every campaign session becomes ready.

## UI design

### Artifact states

The Session artifact panel shows exactly three computed states:

```text
● Current
◐ Stale
○ Missing
```

The UI does not need to explain why an artifact is stale. Dependency reasoning remains internal.

### Generate Outputs

Keep `G — Generate Outputs`, with changed behavior:

- recursively process missing and stale targets;
- skip current targets;
- preserve existing outputs until replacements succeed;
- display progress only for steps that actually run; and
- report a successful no-op when every target is current.

### Regenerate Artifact

`R — Regenerate Artifact` is implemented. It opens a selector of user-meaningful logical artifacts or build steps, including shared steps labeled by all canonical outputs they replace, for example `Ledger + Scene Breakdown`.

Before starting, the confirmation may list the artifacts that will be replaced and the downstream artifacts expected to update. It does not need to display dependency reasoning or explain stale status.

A separate selector is preferred over making the main artifact indicators interactive because it can expose useful internal build targets without cluttering the Session screen.

### Clean Session

Keep `C — Clean Session` as the confirmation-gated action for deleting all Session artifacts. It is not part of ordinary incremental regeneration.

## Architectural responsibilities

### Dependency graph and orchestrator

The graph owns:

- file and database-input declarations;
- packaged LLM system-prompt declarations;
- multiple-output build-step declarations;
- recursive freshness evaluation;
- topological execution order;
- target and forced-build planning; and
- the Current, Stale, and Missing status reported to the UI.

### Individual generators

Generators own:

- operation-specific validation;
- generation of their declared outputs;
- staged, safe replacement; and
- local cleanup after failed writes.

Generators do not broadly delete downstream artifacts. Replacing an output advances its modification time, and the dependency graph consequently identifies its consumers as stale.

## Changes to existing lifecycle contracts

The implementation replaced the earlier contracts that:

- delete all downstream artifacts whenever an upstream generator runs;
- represent only artifact presence rather than Current, Stale, and Missing;
- always run every Generate Outputs phase;
- reject Scene Breakdown solely because Ledger bytes changed; and
- treat Ledger and Scene Breakdown as mutually invalidating rather than sibling outputs.

The current Transcript Sections digest remains an integrity check at its consumers. Modification times drive normal freshness; a deliberately timestamp-preserving out-of-band replacement may therefore require forced regeneration.

## Resolved design choices

### Cross-session generation scope

Session Detail Generate Outputs is Session-scoped. It may recursively rebuild an earlier Session's Recap Summary required by its Summary, but does not proactively rebuild later consumers. The separate Campaign Detail O operation includes all eligible reviewed audio sessions as described under Processing scope.

### Scene Breakdown references after Ledger edits

Scene Breakdown's Ledger index ranges and digest are generation-time provenance. They are validated when the siblings are generated, but are not revalidated against a subsequently hand-edited Ledger. This preserves sibling freshness semantics at the cost of allowing those historical references to stop describing the edited Ledger.

### Timestamp limitations

The initial design accepts modification-time limitations in exchange for a small, understandable implementation. Hash-based provenance remains a possible later enhancement rather than an initial requirement.

## Current implementation and limits

[Application._artifact_graph and generation_plan](../../packages/tablesage-application/src/tablesage_application/application.py) declare inputs and plan builds; [artifact_graph.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py) evaluates freshness; [Campaign Detail](../../apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py) owns the campaign loop. Deployed settings.yaml modification time is also a dependency of processing/generation steps. Transcript depends on attendee identity/profile clocks as well as attendance and audio.

Manual Review, benchmark generation and From Session voice enhancement prefer a current reviewed transcript, fall back to a current machine transcript, and reject the operation when neither is current. Application validates recursive freshness before passing the selected source to the pipeline. Direct pipeline callers only get file-age selection unless they pass a validated source. The benchmark dependency follows the review when it is no older than the machine transcript, otherwise the machine transcript; transitive freshness still accounts for upstream inputs.

Export and glossary extraction still select sources by file existence. Do not infer that every operation enforces the graph merely because the indicator panel does.
