# Implementation Outcome and Validation Handoff

Implementation finished on October 4, 2026 against the agreed [intent and qualitative rubric](intent.md). All four user-supplied transcripts match their expected primary diagnoses; assessments and installation/documentation differences are recorded in [evaluations.md](evaluations.md). No production workspace was used, no unit tests were added or expanded, and unrelated existing working-tree changes were preserved.

## Delivered

- Existing root entry points already targeted cli.main. The legacy screens.main entry point now forwards to the CLI, keeping TUI exports lazy so old editable launchers also dispatch diagnostics correctly. Running with no command still routes to the TUI.
- Missing/outdated enabled agent guides now produce stderr warnings and do not stop reports or help. All commands still require a workspace. report-schema also exposes the installed app's expected settings version, so public docs no longer depend on private guide context for it.
- The generated guide is now a public-documentation pointer. Its previous command details, safety boundaries, and workspace explanations are in public docs. Normal startup also refreshes same-version template changes while preserving user-owned root pointers; diagnostic commands never refresh files.
- Public [Advanced Help](../../docs/guides/advanced-help.md), [Troubleshooting FAQ](../../docs/reference/troubleshooting-faq.md), and [Processing State and Freshness](../../docs/reference/processing-state-and-freshness.md) explain diagnostic boundaries, required outputs/inputs, metadata-only inspection, propagation, and supported recovery limits. The new page is linked from README and existing topics and bundled by the existing wheel configuration. No separate freshness representation or new diagnostic command was introduced.
- [setup_diagnostic_workspaces.py](../../scripts/setup_diagnostic_workspaces.py) builds four neutral case directories offline, reusing authored output writers, application creation/completion helpers, and the existing evaluator. Each has one Campaign and Session, plus fictional attendees. Existing destinations, source-checkout destinations, and paths inside existing workspaces are refused.
- [scripts/README.md](../../scripts/README.md#diagnostic-workspace-validation) provides reproducible wheel installation, setup, and fresh-conversation instructions. Expected results remain outside the case workspaces.
- Review-preserving migration is registered as [separate work](../normalized-review-audio-migration/). Reprocessing is supported; no targeted migration preserves old reviews across this contract change.

## Verification Actually Performed

- Built a wheel with `uv build --wheel --out-dir /tmp/tablesage-diagnostics-build-20261004`. Installed it and a separate editable distribution into new isolated virtual environments, using cached dependencies with `uv pip install --offline`. The wheel's application and public docs load from site-packages.
- Ran 146 direct executable checks across both installation modes and both command names, plus simulated legacy executable wrappers. Exercised topic listing/rendering, schema, read queries, forbidden SQL writes, unknown topics, missing databases, no-workspace errors, current/missing/stale guides, and invalid settings. Snapshot comparisons included contents, sizes, and modification times: no workspace changes. An import guard rejected TUI startup and Application imports during diagnostics; none occurred. No-argument routing was checked with a TUI dispatch sentinel rather than launching an interactive app.
- Ran the fixture script under the installed wheel with socket connections blocked: all four cases passed, with zero network connection attempts. The initial check exposed LiteLLM's import-time model-cost-map fetch; the script now delays heavy imports and forces bundled/offline metadata before them. No provider calls or model downloads were made.
- The evaluator reports every baseline artifact current. Audio-only faults make Import Audio stale; fingerprint-only faults leave Import Audio current but invalidate both reviews and descendants; the combined case has both independent faults. Setup prints evaluator results outside the case directories.
- Direct setup checks confirmed refusal of existing destinations, production-workspace descendants, and checkout destinations without changing sentinel data.
- Executed the public-doc metadata example with the installed app; it emitted fingerprints and selected metadata without authored narrative. Compared the public dependency table against all 27 existing producers in the single-Session graph: outputs and inputs agree.
- Checked normal same-version guide-template refresh and preservation of a user-owned AGENTS.md.
- Ruff lint and format checks passed for the four changed Python files. `ty check packages apps/tablesage-tui` passed. Existing startup/landing checks (`pytest -q apps/tablesage-tui/tests/test_main.py apps/tablesage-tui/tests/test_landing.py`, with bundled LiteLLM metadata selected) passed: 14 tests. No tests were changed for this item.
- Checked local links in changed public docs and work-item records, and scoped whitespace checks. An unrelated existing trailing-space change in build-campaign-glossary.md is outside this work.

## Qualitative Assessment and Limits

These judgments record the implementation assessment before user-run transcripts, using the rubric saved in intent.md; no numerical scores were agreed or measured. Later transcript assessments are recorded in [evaluations.md](evaluations.md).

| Dimension | Evidence and Remaining Uncertainty |
|---|---|
| Diagnostic completeness | Public rules and dependency table cover both independent faults; the four evaluator cases distinguish them. Fresh-agent explanations and wider failure coverage remain unassessed. |
| Source-independent usability | Installed public topics, metadata example, and neutral case instructions are usable without source imports. Whether fresh agents reliably discover and apply them awaits transcripts. |
| Operational safety | Diagnostics passed immutable snapshots and startup-import guards; fixtures run offline and refuse unsafe destinations. Read-only agent conduct is guidance, not a filesystem enforcement mechanism. |
| Recovery trustworthiness | Documentation distinguishes reprocessing from unsupported review-preserving migration and explains why WAV restoration alone is insufficient. Full recovery pipelines were not run on synthetic audio or production data. |

## Ready for User Validation

On October 5 the temporary verification environment was no longer available when the user followed the initial instructions. Rebuilt the wheel and installed cached dependencies into `/home/eriksalt/.cache/tablesage-diagnostics/20261005/app` using `uv`, which selected Python 3.12.13 without requiring a shell command named `python`. Created four fresh workspaces at `/tmp/tablesage-agent-review/case-01` through `case-04`; setup passed and the installed help-topic command returned output from case-01. Verified activation exposes the environment's Python. The README now creates a persistent user-cache run directory and selects Python with `uv venv --python 3.12`, so future setup does not rely on agent-created `/tmp` environments. Case workspaces made by the revised README also live under that cache directory; the already prepared `/tmp/tablesage-agent-review` cases remain disposable. Keep the setup script, this handoff, and expected answers out of the diagnosing agent's context.

Start a fresh conversation in each workspace with the installed environment active and ask:

> Can you check whether this Session's outputs are current? Explain your findings and any action I should take.

The case-01 transcript was supplied October 5 and correctly diagnoses the current baseline. Conditional advice about regenerating outputs after untracked metadata changes needs tightening, and some historical-change claims exceed the shown evidence; see [evaluations.md](evaluations.md). Cases 02–04 still await transcripts. Installed docs and case workspaces were left unchanged during this assessment so the remaining conversations use the same materials. The original production incident was not rerun; Linux/Python 3.12 was the verified platform, and fixtures do not assess narrative quality, speaker recognition, or cross-Session behavior.

## Automatic-Step Restart Clarification

On October 5 the user requested clearer documentation that automatic steps can be restarted. Verified the current UI permits a completed row without requiring a manual step, the coordinator reopens the selected step, and `Application.reopen_step` marks its outputs incomplete for rerunning. Arrow navigation skips automatic rows; clicking selects them. The checkout's correction guide and screen reference already describe this behavior, but the existing wheel installation still serves an older correction guide emphasizing manual reviews.

Added explicit instructions and examples to the public freshness reference and a direct question/answer in the FAQ. Included the existing warning that restarting before Review Transcript discards saved review edits and drafts, and clarified why Regenerate All Outputs can skip current outputs after untracked metadata changes. The installed environment and case workspaces remain unchanged; revised bundled help requires a wheel rebuild and reinstall. This documentation follow-up does not change the completed implementation status or the version evaluated in the case-01 transcript.

Verification: rendered both changed public topics with the installed help renderer and checked local links; item/index status agrees and scoped whitespace checks passed. Built `/home/eriksalt/.cache/tablesage-diagnostics/restart-docs-20261005/dist/tablesage_rpg-1.0.0-py3-none-any.whl` and compared its bundled freshness, FAQ, and correction-guide text with the checkout: exact matches. The wheel is ready to install; it has not replaced the earlier validation installation.

## Case-02 Validation

The supplied case-02 transcript correctly identifies the missing normalized audio, checks that both review fingerprints remain present, and explains downstream staleness and output-regeneration blockers. It does not compare all hashes and acknowledges that limitation. Selected-metadata inspection confirms the fixture's expected fault. The current installed freshness topic now matches the automatic-restart clarification, so the user-run cases span different documentation snapshots; preserve this distinction in comparisons.

Recovery wording still omitted the explicit action for reopening the recording picker. Verified that Continue resumes automatic Import Audio File with the saved source selection, whereas restarting the completed manual Import Audio step reopens selection. Clarified this distinction and the exact P / highlight Import Audio / R procedure in the public freshness reference. No installed package or case workspace was modified in this assessment; no recovery was executed. Cases 03–04 remain pending.

## Case-03 Validation

The supplied case-03 transcript correctly identifies both missing review fingerprints with both audio files present. It explains propagation, compares recorded hashes, distinguishes database status from artifact freshness, and recommends Continue through affected reviews without unnecessary re-import. Selected-metadata inspection confirms the expected fixture fault. Its claim about an older Session's history goes beyond the evidence; the missing inputs are compatible with that upgrade problem but do not prove it. Expanded scripts remain unavailable for a full audit, and no recovery was run.

Installed docs retain the automatic-restart clarification and have not received the later import-picker clarification. No package, workspace, public-doc, or code changes were made during this assessment. Case-04 remains pending. Work-item status remains complete for the delivered implementation, with ongoing validation limits recorded separately.

## Case-04 and User-Run Outcome

Case-04 correctly identifies both missing normalized audio and missing fingerprints, explains why file restoration alone is insufficient, and provides explicit recording-picker restart instructions. It also continues despite stale-guide warnings and acknowledges unverified prompt hashes. Selected-metadata checks confirm the combined fixture fault. No recovery was run.

The transcript reports TableSage 0.1.0. The default user uv-tool launcher matches that banner and serves the newer picker clarification; the prepared validation environment still reports 1.0.0 and serves the prior topic snapshot. The transcript does not expose executable resolution, so the matching default launcher is a likely explanation, not a verified identity. No package or case files were changed during this assessment.

All four primary diagnoses are supported by user transcripts, but the runs span changed docs and differing installations. A repeat of case-04 with the prepared environment activated would improve installation comparability; a final-wheel rerun of all cases would validate one documentation snapshot. Both remain unperformed. Original production diagnosis, paid recovery, full transcript-command auditing, and cross-Session/narrative evaluation remain outside demonstrated results.
