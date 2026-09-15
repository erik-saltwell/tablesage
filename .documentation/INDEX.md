# Internal documentation

This collection is for maintaining and understanding TableSage, not the public user guide.
Tracked work is listed in [WORK-ITEMS.md](../WORK-ITEMS.md); its conventions live in
the [engineering workflow](../.work-items/workflow.md). Project-specific instructions
can be maintained by the user in [.agent_context.md](../.agent_context.md).

## Implementation guides

- [System architecture](system_architecture.md)
- [Implemented use cases](tablesage_use_cases.md) and [screen inventory](tablesage_tui_screens.md)
- [Session Detail](session_detail_screen.md), [Player Detail](player_detail_screen.md), and [Speaker Review](speaker_review_screen.md)
- [Directory voice import](import_player_from_filesystem.md), [From Audio import](import_players_from_audio_file.md), and [From Session enhancement](enhance_players_from_session.md)
- [Ledger generation](generate_ledger.md) and [Ledger v4 reference](canonical_ledger_format_v4.md)
- [Summary generation](generate_summary.md) and [transcript sectioning/session outputs](transcript_sectioning_and_session_scoped_outputs.md)
- [Artifact export](export_artifact.md) and [speaker-identification benchmark](speaker_identification_benchmark.md)

## Artifact contracts

- [Ledger](../.work-items/ledger-artifact-contract/specification.md)
- [Scene Breakdown and Recap](../.work-items/scene-breakdown-artifact-contract/specification.md)
- [Transcript Sections](../.work-items/transcript-sections-artifact-contract/specification.md)
- [Player Introductions](../.work-items/player-introductions-artifact-contract/specification.md)

## Retained feature designs

These are implementation rationale and historical decisions, not a second backlog.

- [Artifact dependency tracking](designs/artifact-dependency-tracking/design.md)
- [Previously On](designs/campaign-aware-previously-on/proposal.md)
- [Reincorporation assistant / Opportunities](designs/reincorporation-assistant/proposal.md)
- [Scene Breakdown](designs/scene-breakdown/design.md)
- [Settings](designs/settings/design.md)
- [Pre-review backchannel removal](designs/pipeline-work-items/01-design.md)
- [Glossary extraction](designs/pipeline-work-items/03-design.md)
- [Post-punctuation spelling correction](designs/pipeline-work-items/07-correct-spelling-post-punctuation.md)

## Developer references and research

- [Transcript-section prompt evaluation](developer/transcript-sectioning-prompt-evaluation.md)
- [Transcript-section review utility](developer/transcript-sections-review-utility.md)
- [TUI design practices](research/tui_system_design_practices.md)
- [Speaker-identification experiment log](research/speaker-id-experiments/experiments-log.md)
- [Speaker-identification experiment records](research/speaker-id-experiments/)
- [Scene-description and recall concept](ideas/scene-description-gm-guide.md): conceptual reference, not a registered implementation commitment

Developer and corpus READMEs remain next to their tools and data. Experiment runners,
CSV measurements, logs and artwork remain at their original paths; document links
point back to those assets where relevant.

## Maintenance history

- [Internal-document audit and cleanup](maintenance/internal-document-audit.md)

The workflow installation consolidated 20 reference documents from the former
`.scratch/`, `.documents/`, `.ideas/`, `.research/` document locations and the public
documentation work item's unrelated cleanup audit. Content and historical decisions
were retained, and references were rebased. No historical feature was reopened,
no item records or rubrics were backfilled, and Public documentation remains `captured`.
