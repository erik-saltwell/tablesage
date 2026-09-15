# Internal document audit and cleanup

Audit date: 2026-09-15. Baseline: commit `1a6ac85` plus the existing, uncommitted work-item and agent-guide changes.

## Cleanup outcome

The user subsequently authorized deleting the Legacy documents and updating the Out of date documents.

- **43 Legacy documents deleted**, all previously tracked and recoverable from Git history (pre-cleanup commit `1a6ac85`).
- **36 Out of date documents updated** against current source code.
- **16 previously current documents retained**; the backchannel design also received a link/status repair after its completed ticket was removed.
- **52 of the original 95 internal documents remain.** This audit is additional to that inventory.
- A benchmark embedder docstring reference was repaired; the documentation-only cleanup did not change executable application behavior. Subsequent bug fixes are recorded below.
- Public documentation remains `captured`, not implemented or completed.

The tables below preserve the **original audit classifications and reasons** as a historical change ledger, not a current claim that 36 documents remain out of date. The new Disposition column records the cleanup. Removed paths are plain code text rather than broken links.

## Original audit results

| Category | Documents |
| --- | ---: |
| Legacy | 43 |
| Out of date | 36 |
| Up to date | 16 |
| **Total** | **95** |

Every originally in-scope file is classified once below. These are document-level judgments: a document with meaningful contradictions is Out of date even when most of it is correct.

- **Legacy:** superseded implementation direction, redundant completed migration/ticket, rejected experiment, or empty placeholder. A candidate to remove from active documentation, not automatic authorization to delete.
- **Out of date:** useful content that needs corrections to match current implementation or the repository's current workflow.
- **Up to date:** no material discrepancy found in the implementation contracts checked. This is not a guarantee that every sentence has been exhaustively verified.

Research, policies and explicitly future-facing plans do not describe runtime behavior. For those files, “Up to date” means a retained reference or current stated intent, **not** that the planned feature is shipped or external research has been fact-checked. The rows identify these cases. Work-item status judgments use the user's request to park documentation, not a code claim.

## Scope and limits

Included: internal design, planning, specifications, research, experiment records, agent/workflow guidance, developer/corpus READMEs and four empty component README placeholders. The inventory covers all Markdown files in the listed internal-document folders, plus the named root/component/corpus guides. Both tracked and untracked files were considered.

Excluded from the 95:

- Root README.md: public-facing project documentation, outside this internal-document audit.
- The seven files under .agents/skills/speech-to-text/: reusable operational skill/vendor reference material, not TableSage planning/specification documents.
- Packaged LLM system prompts, utility_prompts, prompt-optimization inputs, generated best prompts/checkpoints and other generated outputs: executable resources or experiment data, not documentation. Their implementation contracts were consulted where relevant.
- ASCII-art mockups, images, CSV measurements, scripts, caches, logs and runtime campaign/session artifacts.
- This audit itself, created after the inventory.

This was a source/document inspection, not an end-to-end application run, a benchmark rerun, or external research verification. Historical experiment measurements are not being certified as today's benchmark results. References to shelved code are not a guarantee that a local Git stash still exists.

## Main implementation evidence

1. **Preserved artifacts and dependency-driven generation.** [packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py) and [packages/tablesage-application/src/tablesage_application/application.py](../../packages/tablesage-application/src/tablesage_application/application.py) implement freshness, generation planning and cross-session dependencies. [apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/campaign_detail.py) also exposes campaign-wide regeneration. Older deletion-based and fixed-sequence plans are not current.
2. **Joint Ledger/Scene Breakdown, selective recap.** [packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_ledger.py), [packages/tablesage-application/src/tablesage_application/session_pipeline/scene_breakdown.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/scene_breakdown.py) and [packages/tablesage-application/src/tablesage_application/session_pipeline/generate_recap_summary.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/generate_recap_summary.py) establish current input, schema, validation and persistence behavior. The four specs are the best maintained contract references.
3. **Actual persistence boundary.** Application uses SQLModel/SQLAlchemy sessions directly. The current [packages/tablesage-model/src/tablesage_model/](../../packages/tablesage-model/src/tablesage_model) does not implement the proposed domain/repository/sqlite separation or the expanded data-model document's full table set.
4. **Implemented UI flows.** [apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/player_detail.py) and [apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py](../../apps/tablesage-tui/src/tablesage_tui/screens/session_detail.py) contain directory/audio import, cleaning choices and current action bindings. [packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py](../../packages/tablesage-application/src/tablesage_application/session_pipeline/artifacts.py) confirms export remains existence-based; freshness is not an additional export requirement.
5. **Campaign preparation.** [packages/tablesage-application/src/tablesage_application/previously_on.py](../../packages/tablesage-application/src/tablesage_application/previously_on.py), [packages/tablesage-application/src/tablesage_application/opportunities.py](../../packages/tablesage-application/src/tablesage_application/opportunities.py) and [apps/tablesage-tui/src/tablesage_tui/screens/opportunities.py](../../apps/tablesage-tui/src/tablesage_tui/screens/opportunities.py) implement the recent recap/opportunities designs.
6. **Speaker identification.** [apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml](../../apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml) and [benchmarks/speaker_id/candidates.py](../../benchmarks/speaker_id/candidates.py) identify the current duration-conditioned thresholds and widening/propagation configuration. Original experiment baselines must be labeled historically.
7. **Developer utilities.** [scripts/review_transcript_sections.py](../../scripts/review_transcript_sections.py) selects Astra for the first reviewer and juror despite stale Sol/Fable printed labels. [apps/optimize-prompts/src/optimize_prompts/optimize_section_transcript.py](../../apps/optimize-prompts/src/optimize_prompts/optimize_section_transcript.py) supports corpus-wide leave-one-out and prefix holdout. [apps/optimize-prompts/pyproject.toml](../../apps/optimize-prompts/pyproject.toml) defines the separate developer CLI and sibling dependency locations.
8. **Workflow authority (original finding).** The root guides conflicted between .scratch and .work-items. Cleanup aligned new tracked work with .work-items/workflow.md and retained .scratch designs as supporting references, without bulk-registering historical work.

## Per-file inventory

Paths are relative to the repository root. Reasons identify the principal classification basis, not an exhaustive list of every possible correction.

### .documentation

20 documents: 5 Legacy; 11 Out of date; 4 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `.documentation/application_business_rules.md` | Legacy | Mostly describes the retired YAML/slug store, DB-backed processing records and destructive invalidation; preserve any unique domain rules before removal. | Deleted |
| `.documentation/canonical_ledger_format_v3.md` | Legacy | Superseded by the v4 Ledger schema and completed Ledger contract work item; preamble is no longer part of Ledger. | Deleted |
| [.documentation/canonical_ledger_format_v4.md](../canonical_ledger_format_v4.md) | Up to date | The preamble-free canonical Ledger contract matches the current Ledger models; keep subordinate to the completed Ledger contract work item. | Retained |
| `.documentation/deepen_summary_generation_module.md` | Legacy | Old transcript-file-based summary redesign; current Summary orchestration consumes Ledger plus separately routed context. | Deleted |
| [.documentation/enhance_players_from_session.md](../enhance_players_from_session.md) | Out of date | Voice enhancement remains implemented, but the described deletion of reviewed/downstream artifacts on input changes conflicts with freshness tracking. | Updated against current implementation/workflow |
| [.documentation/export_artifact.md](../export_artifact.md) | Out of date | Export flow still exists, but the implementation section puts export_artifact in paths instead of session_pipeline/artifacts and its artifact examples are incomplete. Existence-based export itself is still correct. | Updated against current implementation/workflow |
| [.documentation/generate_ledger.md](../generate_ledger.md) | Up to date | Joint Ledger/Scene Breakdown response, structural validation, retry and pair persistence match current generation code. | Retained |
| [.documentation/generate_summary.md](../generate_summary.md) | Up to date | Ledger-based composition with introductions, starting context, previous-session recap and freshness dependencies matches Application. | Retained |
| [.documentation/import_player_from_filesystem.md](../import_player_from_filesystem.md) | Out of date | Directory import exists, but current UI uses SelectDirectory and a per-import cleaning choice, not the described picker/hardcoded cleaning behavior. | Updated against current implementation/workflow |
| [.documentation/import_players_from_audio_file.md](../import_players_from_audio_file.md) | Out of date | Core wizard survives; sibling session-import navigation, matching-setting references and claims about where playback is available need revision. | Updated against current implementation/workflow |
| [.documentation/player_detail_screen.md](../player_detail_screen.md) | Out of date | Describes implemented directory import/cleanup as stubs and an obsolete session-import entry point. | Updated against current implementation/workflow |
| [.documentation/session_detail_screen.md](../session_detail_screen.md) | Out of date | Contains current artifact states alongside old picker names, contradictory WAV cleaning instructions and the old role-transcript Markdown input description. | Updated against current implementation/workflow |
| [.documentation/speaker_identification_benchmark.md](../speaker_identification_benchmark.md) | Up to date | Harness stages, frozen fixtures, cost model, span-aware embedding cache and duration-bucket reporting match the benchmark implementation. | Retained |
| [.documentation/speaker_review_screen.md](../speaker_review_screen.md) | Out of date | Review binding and downstream-deletion rules are stale; document the current review/spelling flow and preserved-but-stale outputs. | Updated against current implementation/workflow |
| [.documentation/system_architecture.md](../system_architecture.md) | Out of date | Package/startup description is useful, but repository-interface-only persistence and domain/repository/sqlite directory seams are not how the current SQLModel code is organized. | Updated against current implementation/workflow |
| `.documentation/tablesage_data_model.md` | Legacy | Largely an abandoned expanded database design: MediaAsset, VoiceSample, ProcessingRun, SessionArtifact and related entities are not current tables. Replace with an actual-model reference. | Deleted |
| `.documentation/tablesage_implementation_plan.md` | Legacy | Old phased implementation checklist, obsolete stubs and v3 pipeline; superseded by implemented features and current specs. | Deleted |
| [.documentation/tablesage_tui_screens.md](../tablesage_tui_screens.md) | Out of date | Mixes the implemented opportunities/settings UI with obsolete import/cleanup stubs and navigation/deletion behavior. | Updated against current implementation/workflow |
| [.documentation/tablesage_use_cases.md](../tablesage_use_cases.md) | Out of date | Useful use-case inventory, but inactive/archive filtering, old discourse/summary model and media lifecycle do not consistently describe the product. | Updated against current implementation/workflow |
| [.documentation/transcript_sectioning_and_session_scoped_outputs.md](../transcript_sectioning_and_session_scoped_outputs.md) | Out of date | Still describes Ledger-sourced recap, fixed always-run phases and destructive invalidation; current recap consumes Scene Breakdown and generation is dependency-driven. | Updated against current implementation/workflow |

### .document

2 documents: 2 Legacy; 0 Out of date; 0 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `.document/recap-summary-implementation-plan.md` | Legacy | Superseded recap implementation/optimization plan: Ledger source and old acceptance/compression strategy differ from current Scene Breakdown pipeline. | Deleted |
| `.document/recap-summary-metrics.md` | Legacy | Old coverage/alignment/compression objective superseded by current recap coverage, recognition, exclusion, alignment and size constraints. | Deleted |

### .documents

2 documents: 0 Legacy; 2 Out of date; 0 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| [.documentation/developer/transcript-sectioning-prompt-evaluation.md](../developer/transcript-sectioning-prompt-evaluation.md) | Out of date | Boundary scoring remains relevant; fixed three-session/two-train-one-test rotations have become corpus-wide leave-one-out plus optional prefix holdout. | Updated against current implementation/workflow |
| [.documentation/developer/transcript-sections-review-utility.md](../developer/transcript-sections-review-utility.md) | Out of date | Flow remains valid, but code now selects Astra for the first reviewer and juror, with high reasoning; document still names Sol and a Fable ultra-thinking juror. | Updated against current implementation/workflow |

### .ideas

4 documents: 3 Legacy; 0 Out of date; 1 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `.ideas/ledger-scene-breakdown.md` | Legacy | Early Ledger-derived breakdown proposal superseded by joint transcript-based Ledger/Scene Breakdown generation. | Deleted |
| `.ideas/recap-ideas.md` | Legacy | Earlier Ledger-prompt and recap budget sketch; selective continuity rationale survives but current prompt/spec supersede its concrete design. | Deleted |
| `.ideas/recap-recognition-ideas.md` | Legacy | Earlier scene-complete recap direction split into complete Scene Breakdown and selective Recap Summary; preserve recognition rationale if archiving. | Deleted |
| [.documentation/ideas/scene-description-gm-guide.md](../ideas/scene-description-gm-guide.md) | Up to date | Retained domain rationale for memorable scenes/signatures, not an implementation specification. Its research claims were not independently fact-checked in this code audit. | Retained |

### .research

2 documents: 1 Legacy; 1 Out of date; 0 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `.research/campaign-ui.md` | Legacy | Retired conditional root screens, YAML/slug storage, inactive/archive model and campaign-owned players differ materially from current UI/data model. | Deleted |
| [.documentation/research/tui_system_design_practices.md](../research/tui_system_design_practices.md) | Out of date | Useful research, but references missing awesome_tuis.md and presents keyboard/layout conventions that are not a verified TableSage UI contract. Restore provenance and distinguish guidance from implementation. | Updated against current implementation/workflow |

### .scratch

43 documents: 28 Legacy; 11 Out of date; 4 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `.scratch/ledger-md-tier1-sample.md` | Legacy | Historical rendering candidate containing v3 recap/characters preamble; not representative of current v4 output. | Deleted |
| `.scratch/ledger-md-tier2-sample.md` | Legacy | Historical rendering candidate containing the removed Ledger preamble; preserve only as design history. | Deleted |
| `.scratch/ledger-md-tier3-sample.md` | Legacy | Historical scene-grouped Ledger/preamble mockup; current Scene Breakdown is a separate sibling artifact. | Deleted |
| `.scratch/ledger-markdown-format-review.md` | Legacy | Old tiered renderer/preamble design review; current renderer, v4 schema and joint-generation spec supersede it. | Deleted |
| `.scratch/generate-summary-simplification-opportunities.md` | Legacy | Earlier simplification backlog for a pipeline whose input/rendering/invalidation contracts have since changed. | Deleted |
| `.scratch/campaign-list-screen/spec.md` | Legacy | Old landing/empty-screen design and early stubs have been superseded by the current landing and campaign list. | Deleted |
| `.scratch/implementation-plan/work-items.md` | Legacy | Historical completed phased-build backlog, including obsolete v3 and stub assumptions; not a current work index. | Deleted |
| [.documentation/designs/scene-breakdown/design.md](../designs/scene-breakdown/design.md) | Out of date | Core joint-generation design matches code; opening implementation status and unresolved-mechanics discussion need reconciling with the implemented spec. | Updated against current implementation/workflow |
| [.documentation/designs/campaign-aware-previously-on/proposal.md](../designs/campaign-aware-previously-on/proposal.md) | Out of date | Implemented campaign-aware recap design remains relevant, but the reserved/future Prepare Next Session description predates the opportunities assistant. | Updated against current implementation/workflow |
| [.documentation/designs/reincorporation-assistant/proposal.md](../designs/reincorporation-assistant/proposal.md) | Up to date | Implemented five-seed, ephemeral opportunities workflow, full campaign scene context and export requirements match current application/UI. | Retained |
| [.documentation/designs/artifact-dependency-tracking/design.md](../designs/artifact-dependency-tracking/design.md) | Out of date | Core graph/freshness/sibling design matches code; processing-scope text is contradictory and omits the now-implemented campaign Regenerate All Outputs action. | Updated against current implementation/workflow |
| [.documentation/designs/settings/design.md](../designs/settings/design.md) | Out of date | Detailed restricted settings editor largely matches code, but the opening promise to edit all workspace processing settings contradicts both the later resolved scope and actual editor. | Updated against current implementation/workflow |
| `.scratch/pipeline-work-items/README.md` | Legacy | Old pipeline implementation backlog/index; superseded by completed implementation and current artifact specs. | Deleted |
| [.documentation/designs/pipeline-work-items/01-design.md](../designs/pipeline-work-items/01-design.md) | Up to date | Batched pre-review question checking/backchannel-removal design and configurable 50/4/120 batching defaults match implementation. | Retained; removed-ticket link/status repaired |
| `.scratch/pipeline-work-items/01-pre-review-backchannel-removal-batched.md` | Legacy | Completed implementation ticket; surviving operational contract is in the design and current code. | Deleted |
| `.scratch/pipeline-work-items/02-design.md` | Legacy | Question-event rationale survives, but concrete v3/preamble/full-transcript design is superseded by the v4 spec. | Deleted |
| `.scratch/pipeline-work-items/02-question-ledger-event.md` | Legacy | Completed Question-event implementation ticket, superseded by current Ledger contract. | Deleted |
| [.documentation/designs/pipeline-work-items/03-design.md](../designs/pipeline-work-items/03-design.md) | Out of date | Glossary extraction design remains relevant, but claims of no downstream invalidation/existence-only gating predate glossary freshness dependencies. | Updated against current implementation/workflow |
| `.scratch/pipeline-work-items/03-glossary-extraction.md` | Legacy | Completed glossary implementation ticket with old lifecycle assumptions; retain current code and update the companion design. | Deleted |
| `.scratch/pipeline-work-items/04-single-action-generate.md` | Legacy | Completed fixed-sequence Generate plan superseded by dependency-driven generation. | Deleted |
| `.scratch/pipeline-work-items/05-finish-ledger-generation.md` | Legacy | Completed old Ledger implementation ticket superseded by v4 and joint Scene Breakdown generation. | Deleted |
| `.scratch/pipeline-work-items/06-finish-summary-generation.md` | Legacy | Completed old Summary ticket; current composition and artifact freshness are documented elsewhere. | Deleted |
| [.documentation/designs/pipeline-work-items/07-correct-spelling-post-punctuation.md](../designs/pipeline-work-items/07-correct-spelling-post-punctuation.md) | Out of date | Implemented spelling step remains relevant, but its reviewed_transcript.json filename differs from current transcript_reviewed.json and needs implementation-status reconciliation. | Updated against current implementation/workflow |
| `.scratch/no-preamble/01-implement-recap-summary.md` | Legacy | Completed migration ticket; its old recap generation/evaluation contract is superseded. | Deleted |
| `.scratch/no-preamble/02-implement-transcript-sectioning-and-session-scoped-outputs.md` | Legacy | Completed sectioning migration ticket with old fixed-pipeline/deletion behavior. | Deleted |
| `.scratch/no-preamble/implementation-plan.md` | Legacy | Completed no-preamble migration checklist; current artifact specs are the authoritative replacement. | Deleted |
| `.scratch/no-preamble/prompt-tutorials/01-transcript-sections-prompt.md` | Legacy | One-off migration instructions now embodied in the deployed sectioning prompt and current spec. | Deleted |
| `.scratch/no-preamble/prompt-tutorials/02-ledger-v4-prompt.md` | Legacy | One-off prompt migration predating the joint Ledger/Scene Breakdown response. | Deleted |
| `.scratch/no-preamble/prompt-tutorials/03-player-introductions-prompt.md` | Legacy | Completed prompt-edit instructions superseded by the deployed prompt and Player Introductions spec. | Deleted |
| `.scratch/no-preamble/prompt-tutorials/04-recap-summary-prompt.md` | Legacy | Old Ledger-based recap prompt instructions; current input is Scene Breakdown. | Deleted |
| `.scratch/no-preamble/prompt-tutorials/05-summary-composition-prompt.md` | Legacy | Completed one-off composition prompt instructions; retain deployed template and current Summary documentation. | Deleted |
| `.scratch/speaker-id-experiments/01-similarity-threshold-sweep.md` | Legacy | Historical eres2netv2/0.07 production tuning superseded by WeSpeaker and duration-conditioned thresholds. Archive experimental evidence. | Deleted |
| [.documentation/research/speaker-id-experiments/03-wespeaker-resnet34-embedder.md](../research/speaker-id-experiments/03-wespeaker-resnet34-embedder.md) | Out of date | WeSpeaker is now adopted; document still says not adopted and uses the old production baseline. Retain original measurements as dated results. | Updated against current implementation/workflow |
| `.scratch/speaker-id-experiments/04-titanet-large-embedder.md` | Legacy | Unadopted alternative; document explicitly notes removed runner/embedder. Archive results rather than treating it as a runnable plan. | Deleted |
| [.documentation/research/speaker-id-experiments/05-threshold-sweep-leaders.md](../research/speaker-id-experiments/05-threshold-sweep-leaders.md) | Out of date | Decision evidence remains valuable, but adoption is no longer pending and 0.08 is not today's general duration-conditioned assignment rule. | Updated against current implementation/workflow |
| `.scratch/speaker-id-experiments/06-two-pass-centroid-refinement.md` | Legacy | Shelved, unadopted algorithm; retain as experiment history, not production guidance. Stash recoverability was not verified. | Deleted |
| [.documentation/research/speaker-id-experiments/07-richer-decision-rule.md](../research/speaker-id-experiments/07-richer-decision-rule.md) | Up to date | Adopted short/long-duration margin rule remains part of current production, composed with later widening/propagation. | Retained |
| [.documentation/research/speaker-id-experiments/08-diarization-cluster-propagation.md](../research/speaker-id-experiments/08-diarization-cluster-propagation.md) | Out of date | Algorithm/measurements are useful, but recommendation-only adoption status predates its production composition in experiment 12. | Updated against current implementation/workflow |
| [.documentation/research/speaker-id-experiments/09-short-utterance-embedding-widening.md](../research/speaker-id-experiments/09-short-utterance-embedding-widening.md) | Out of date | Conservative widening is now implemented; recommendation/shelved wording should distinguish the experiment runner from the adopted production behavior. | Updated against current implementation/workflow |
| `.scratch/speaker-id-experiments/10-multi-prototype-references.md` | Legacy | Explicitly rejected/shelved matching direction. Archive the negative result so it is not needlessly retried. | Deleted |
| `.scratch/speaker-id-experiments/11-adaptive-score-normalization.md` | Legacy | Explicitly rejected/shelved normalization direction. Archive evidence; not a current implementation plan. | Deleted |
| [.documentation/research/speaker-id-experiments/12-production-composition-8-9.md](../research/speaker-id-experiments/12-production-composition-8-9.md) | Up to date | Production composition and its configurable conservative widening/cluster-propagation behavior match code. Recorded scores are historical, not rerun here. | Retained |
| [.documentation/research/speaker-id-experiments/experiments-log.md](../research/speaker-id-experiments/experiments-log.md) | Out of date | Later adoption entries are useful, but earlier 'currently optimal: 0.07' and pending-adoption language conflict with today's production baseline; separate historical from current status. | Updated against current implementation/workflow |

### specs

4 documents: 0 Legacy; 0 Out of date; 4 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| [Ledger contract](../../.work-items/ledger-artifact-contract/specification.md) | Up to date | v4 schema, joint generation, persistence and sibling freshness match current code. | Reclassified as complete work item |
| [Player Introductions contract](../../.work-items/player-introductions-artifact-contract/specification.md) | Up to date | Routed optional introductions, schema and artifact lifecycle match current code. | Reclassified as complete work item |
| [Scene Breakdown contract](../../.work-items/scene-breakdown-artifact-contract/specification.md) | Up to date | Joint response, index coverage, pair persistence, recap source and generation-time provenance match current code. | Reclassified as complete work item |
| [Transcript Sections contract](../../.work-items/transcript-sections-artifact-contract/specification.md) | Up to date | Ranges, session boundary, digest validation and downstream routing match current code. | Reclassified as complete work item |

### docs/agents

3 documents: 0 Legacy; 3 Out of date; 0 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| `docs/agents/domain.md` | Out of date | Still points agents at the old v3/domain/implementation-plan sources instead of the current artifact specs and implementation. | Removed during guidance consolidation |
| `docs/agents/issue-tracker.md` | Out of date | Directs new issue/PRD work to .scratch while the newly added work-item instructions direct it to .work-items; authority must be reconciled. | Removed during guidance consolidation |
| `docs/agents/triage-labels.md` | Out of date | Old issue-triage states coexist with the new work-item lifecycle without an explicit boundary or migration policy. | Removed during guidance consolidation |

### Repository root

4 documents: 0 Legacy; 3 Out of date; 1 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| [AGENTS.md](../../AGENTS.md) | Out of date | Useful artifact/settings rules, but old .scratch issue guidance conflicts with the appended .work-items workflow. | Updated against current implementation/workflow |
| [CLAUDE.md](../../CLAUDE.md) | Out of date | Same issue/work-item authority conflict; artifact-spec guidance also needs parity with the current Scene Breakdown-aware guide. | Updated against current implementation/workflow |
| [GEMINI.md](../../GEMINI.md) | Up to date | Current reincorporation guidance and new work-item pointer are coherent within this file; policy document, not a claim of shipped functionality. | Retained |
| [WORK-ITEMS.md](../../WORK-ITEMS.md) | Out of date | Index matches item.md mechanically, but fleshing-out does not represent the user's request to park the documentation effort; captured is the workflow's parked state. | Updated against current implementation/workflow |

### .work-items

3 documents: 0 Legacy; 1 Out of date; 2 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| [.work-items/workflow.md](../../.work-items/workflow.md) | Up to date | Defines the newly installed work-item conventions and files present in this worktree; policy, not runtime behavior. Older entry-point guides still need reconciliation. | Retained |
| [.work-items/public-documentation/item.md](../../.work-items/public-documentation/item.md) | Out of date | Records documentation as actively fleshing-out despite the request to shelve it; update status/resume language when reconciling work tracking. | Updated against current implementation/workflow |
| [.work-items/public-documentation/intent.md](../../.work-items/public-documentation/intent.md) | Up to date | Accurately preserves the agreed future GM-facing README/MkDocs/GitHub Pages/screenshot direction. Explicit intent, not a claim that the site is implemented. | Retained |

### Component and corpus guides

8 documents: 4 Legacy; 4 Out of date; 0 Up to date.

| Document | Original category | Original finding | Disposition |
| --- | --- | --- | --- |
| [apps/optimize-prompts/README.md](../../apps/optimize-prompts/README.md) | Out of date | Current project-scoped commands and workflow are useful; sibling prompt-forge link climbs four directories instead of three. | Updated against current implementation/workflow |
| `apps/tablesage-tui/README.md` | Legacy | Empty placeholder; contains no documentation to preserve. | Deleted |
| `packages/tablesage-application/README.md` | Legacy | Empty placeholder; contains no documentation to preserve. | Deleted |
| `packages/tablesage-model/README.md` | Legacy | Empty placeholder; contains no documentation to preserve. | Deleted |
| `packages/tablesage-tools/README.md` | Legacy | Empty placeholder; contains no documentation to preserve. | Deleted |
| [scripts/README.md](../../scripts/README.md) | Out of date | Utility usage is relevant, but reviewer/juror model and reasoning-level description no longer matches review_transcript_sections.py. | Updated against current implementation/workflow |
| [prompt_optimization/recap_summary/README.md](../../prompt_optimization/recap_summary/README.md) | Out of date | Mostly current Scene Breakdown-based evaluation guide, but optimize-prompts commands omit --project apps/optimize-prompts required by the split developer app. | Updated against current implementation/workflow |
| [prompt_optimization/section_transcript/README.md](../../prompt_optimization/section_transcript/README.md) | Out of date | Corpus/holdout instructions remain useful, but CLI examples need the developer app's --project apps/optimize-prompts invocation. | Updated against current implementation/workflow |

## Verification and limits

Cleanup was checked against the original 95-file allowlist: all 43 deletion targets were tracked, all 36 correction targets were updated, and all 52 retained paths exist. Relative links and remaining references were checked after deletion; illustrative workflow paths are examples, not required files.

Verification performed:

- `git diff --check`: passed.
- Relative Markdown link scan across 65 documentation/resource Markdown files (excluding generated outputs and packaged prompts): no missing local link destinations.
- `uv run --project apps/optimize-prompts --no-sync optimize-prompts --help`: passed.
- `uv run --project apps/optimize-prompts --no-sync optimize-prompts recap-summary`: preflight passed, three cases and six metrics, no LLM calls.
- `uv run --project apps/optimize-prompts --no-sync optimize-prompts section-transcript`: preflight passed, eight cases and one deterministic routing metric, no LLM calls.
- Python AST comparison of benchmarks/speaker_id/embedders.py before/after, ignoring docstrings: executable structure unchanged.

The recap preflight exposed an additional stale model/temperature description; the corpus guide was corrected to its checked-in settings. No live GUI/provider workflow, benchmark rerun, new unit tests or external research verification was performed.

At cleanup time, the guides identified existence-based reviewed-file selection and the lack of an all-rejected directory-import safeguard. Both were subsequently fixed as described below. Remaining limits include non-transactional directory/audio-import replacement, campaign regeneration skipping sessions awaiting review, and recap corpus refresh not evaluating the entire freshness graph.

## Follow-up implementation and public-doc reset

The user authorized fixing the two implementation bugs found during cleanup, then committing and pushing all uncommitted changes. No numerical rubric was defined for this bug-fix task; implementation proceeded at the user's explicit request, with functional verification rather than numerical scoring.

- Manual Review, benchmark generation and From Session enhancement now select a current reviewed transcript, otherwise a current machine transcript, using Application's recursive artifact graph. If neither is current, they request retranscription before modifying clips or generated files. The benchmark dependency follows the selected source. Direct pipeline calls additionally avoid reviews older than the machine transcript.
- Directory imports with all new embeddings rejected preserve existing clips and the complete stored voice profile, including its computed timestamp. The UI reports no usable clips and zero replacements. Partial-success replacement and intentional zero-eligible session-clip retraction retain their existing semantics; this does not introduce general filesystem/database rollback.
- Updated the affected internal guides. Corrected existing enhancement-test fixture setup to include the required transcript companion and simulate retranscription after profile changes; no test cases or test tooling were added.
- The root README was emptied at the user's request. Project description metadata and LICENSE remain unchanged. Other retained documentation is internal; the new public documentation project remains parked at `captured`.

Verification: 149 existing targeted tests passed across session enhancement, directory voice clips, transcript review, artifact graph, transcript cleaning, and the review/session-detail screens. Direct temporary-workspace checks with stubbed audio/embedding operations verified current-review preference, stale-review machine fallback, benchmark freshness, stale-input rejection without clip mutation, and all-rejected import preservation with cleaning on and off. Changed Python files passed Ruff lint and formatting checks; `git diff --check` passed. No live provider-backed audio workflow was run.

The original policy/intent/research qualification still applies: retained plans are not claims of shipped features. Git history retains removed experiment narratives; the experiment log keeps their outcomes without linking to deleted files.
