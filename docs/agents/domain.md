# Internal domain and implementation documentation

The code is the source of truth for implemented behavior. Use these maintained documents to find its contracts and rationale; the old phased-build backlog is no longer a feature-status reference.

## Artifact contracts

Read the relevant spec before changing schema, prompt contracts, routing, persistence or freshness:

- [Ledger](../../specs/ledger.md): v4 moves and joint Ledger/Scene Breakdown generation.
- [Scene Breakdown and Recap](../../specs/scene-breakdown.md): complete scene record, pair persistence and selective recap.
- [Transcript Sections](../../specs/transcript-sections.md): opening ranges, active-play boundary and digest validation.
- [Player Introductions](../../specs/player-introductions.md): routed, optional introduction content.

## Implementation guides

- [Architecture](../../.documentation/system_architecture.md): package responsibilities, actual SQLModel persistence, settings and workspace layout. Exact table definitions are in [model/](../../packages/tablesage-model/src/tablesage_model/model/).
- [Use cases](../../.documentation/tablesage_use_cases.md): current product capabilities.
- [Screen inventory](../../.documentation/tablesage_tui_screens.md), [Session Detail](../../.documentation/session_detail_screen.md), [Player Detail](../../.documentation/player_detail_screen.md) and [Speaker Review](../../.documentation/speaker_review_screen.md): implemented navigation and actions.
- [Artifact dependencies](../../.scratch/artifact-dependency-tracking/design.md): missing/current/stale status and incremental generation.
- [Ledger generation](../../.documentation/generate_ledger.md), [Summary generation](../../.documentation/generate_summary.md) and [session-scoped outputs](../../.documentation/transcript_sectioning_and_session_scoped_outputs.md): processing details.
- [Settings](../../.scratch/settings/design.md), [Previously On](../../.scratch/campaign-aware-previously-on/proposal.md) and [Opportunities](../../.scratch/reincorporation-assistant/proposal.md): retained implemented feature designs.

Use Campaign, Player, CampaignPlayer roster, Session and attendance/roles consistently. Players are global, clips and generated artifacts are filesystem-backed, and normal invalidation preserves files while marking dependent outputs stale.

Read the relevant guide and code before changes, and update the guide when behavior changes. For new tracked work use [the work-item workflow](../../.work-items/workflow.md), not a new .scratch issue. Follow that workflow's verification policy.
