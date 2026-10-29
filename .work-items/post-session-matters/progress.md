# Completion and Verification

Implemented the visible **Post-Session Matters** JSON artifact. Assembly preserves all ten filtered source publications, permanent IDs, field values and ordering in the approved historical/present/open groups. It performs no model call, filtering or ID allocation. Strict validation reuses the existing category schemas. Persistence uses the existing rollback-safe writer and completion records snapshot inputs before assembly.

The dependency graph schedules assembly after its ten current-Session sources and tracks the assembly implementation, envelope schema and Session UUID. Existing registry-driven Session Detail, regeneration, export and cleanup include the artifact. Generate Artifacts now requires it and preflights credentials only when the actual plan contains model work. Individual Matters remain hidden; Scene Log stays separate. Deferred recap, summary and campaign preparation generation remain disabled.

## Verification

- Replayed all four Sessions in a disposable copy using saved responses: 14 producers per Session complete and current; repeated generation plans empty. Forty Matters and eight Ledger/Scene Log prompt parity checks passed. Each combined publication exactly matches its ten source publications and Session UUID.
- Direct operational checks passed for strict schema validation, required empty arrays, copy independence, missing/malformed/stale inputs, failed-write rollback, preservation of completion records, concurrent input changes, schema-only invalidation and missing-output regeneration.
- Actual generation-step checks confirmed assembly-only execution skips credentials and model calls and preserves ID counters. A plan containing model generation still performs High-model credential preflight.
- Textual MCP verified the visible current artifact indicator, hidden individual Matters, selectable regeneration and JSON-only export. Actual regeneration succeeded with guards rejecting model calls and nonempty credential requirements. Exported bytes equal the stored Session 001 JSON; diagnostics reported no exception. MCP Session was stopped.
- Ruff and whole-repository `ty check --output-format concise` passed. `uv build --wheel` passed. The built wheel includes the implementation and schema; its imported schema validates and accepts the exported publication.
- Existing artifact graph/processing-state checks: 19 passed and the same seven pre-existing failures tied to the earlier narrative pipeline contract. No unit tests were added, expanded or disabled.
- All 13 saved hashes for the original verified-transcript baseline (database, role transcripts, reviewed transcripts and processing states) remain unchanged.

Initial verification used Git-ignored operational scripts under `deployment/matters-port-smoke/` and the disposable `deployment/matters-replay-bt862bs0/` workspace. Those directories are no longer present. The active shared deployment and fresh verification evidence are recorded below.

## Limits

The initial verification used provider-free replay and did not assess extraction quality. Its pre-existing Session 004 Brewing Troubles fixture used an obsolete contract, so that replay substituted a valid empty response for the category. The subsequent live run below regenerates that category with the current schema. No numerical rubric or narrative-quality assessment was performed. Changes have not been committed.


## Shared Deployment Restoration and Live Generation

The user requested the entire repo `deployment/` directory be shared through Syncthing as `tablesage_deployment` with Pixel 10 Pro XL. That root was an older three-Session workspace; the four-Session replay had been a separate disposable workspace. The root is now the authoritative four-Session test deployment.

Backed up the previous root outside the Syncthing share at `/home/eriksalt/data/tablesage-deployment-backups/20261027T010137Z/previous-deployment/`, then copied `/home/eriksalt/data/tablesage_summary_test/deployment/` into `/home/eriksalt/proj/tablesage/deployment/`. SQLite backup preserved a consistent source database. Syncthing was paused during the swap, its folder marker and Obsidian settings were retained, and sharing resumed afterward. Only Brandonsford is present; Dread Gods Teeth and the benchmark Campaign remain removed. The source deployment is unchanged. The new deployment README identifies the launch command and artifact locations.

Generated all active post-role outputs through the real Application and configured `anthropic/claude-opus-5-5` High model. All four `post_session_matters.json` files now live at `deployment/campaigns/Brandonsford/001/` through `004/`. No replay responses, placeholder categories, transcript rebuilding, recap or summary generation were used in this run.

Live generation exposed provider compatibility gaps. The tools LLM client now registers Opus 5.5 reasoning/adaptive-thinking capabilities so the explicit effort setting maps to the provider. Its Anthropic request schema retains field constraints, expresses nullable enums as typed alternatives, and moves regex/object-conditional constraints into descriptions to avoid rejected schemas and compiler complexity limits. Original source schemas remain unchanged and continue to validate every Matters response before normalization and publication. See the provider's [effort documentation](https://platform.claude.com/docs/en/build-with-claude/effort), [structured-output limitations](https://platform.claude.com/docs/en/build-with-claude/structured-outputs), and [LiteLLM effort mapping](https://docs.litellm.ai/docs/providers/anthropic_effort). One live Session 002 response contained an empty impediment title; validation rejected it, the failed response was retained as evidence, and retrying the producer succeeded without rebuilding current outputs.

Final verification passed:

- Four Sessions, all active outputs current, and empty repeat-generation plans.
- Eight role/reviewed transcript SHA-256 hashes match the verified source; saved review decisions and drafts match the source.
- Every combined file validates and exactly preserves all ten source publications and its owning Session UUID.
- All 40 category evidence files record the configured High model and medium effort.
- Database integrity and foreign-key checks pass.
- Textual MCP shows all four Sessions and a visible, current Post-Session Matters indicator in each; hidden Matters remain absent and no application exception occurred. MCP was stopped.
- Pixel synchronization reports 100% completion, zero pending items and zero folder errors after generation.
- Six existing LLM-client checks pass, Ruff and whole-repository type checks pass, the wheel builds, and `git diff --check` passes. Direct schema checks confirm source schemas are unchanged, nullable enums preserve membership in either type order, and original conditional validation still rejects invalid content. No unit tests were added or expanded.

Durable receipts, generation log, operational scripts, Textual MCP evidence and verification output are outside the share under `/home/eriksalt/data/tablesage-deployment-backups/20261027T010137Z/`. This run verifies schema/contracts, freshness, UI presence and preservation; it does not claim a human review of the generated narrative content. No commit was requested for these latest changes.
