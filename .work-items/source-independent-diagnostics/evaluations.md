# User-Run Agent Validation

Assessments use the agreed [qualitative rubric](intent.md#quality-rubric). Implementation checks are recorded separately in [progress.md](progress.md). These assessments concern supplied agent transcripts, not new executions of the diagnosing agent or recovery pipelines.

## Case-01: Current Baseline — October 5, 2026

**Evaluated version:** TableSage 1.0.0, wheel rebuilt and installed October 5, with workspaces prepared by `scripts/setup_diagnostic_workspaces.py`. The user supplied a fresh Claude Code conversation using Sonnet 5.5 in `case-01`, asking the agreed neutral question. The fixture's expected state is that all artifacts are current.

**Outcome:** The agent correctly identified the only Session, reported its outputs current, and recommended no action. Installed help and report commands returned output, with no visible TUI startup. It found and used the public freshness reference, checked completion records, outputs, input and prompt fingerprints, sections, drafts, failure markers, schema/settings versions, and the absence of a prior recap dependency. It distinguished freshness from narrative accuracy and recognized metadata that is not fingerprinted.

| Dimension | Assessment and Evidence |
|---|---|
| Diagnostic completeness | Correct baseline conclusion, supported by a broad set of relevant checks. This case does not establish identification of the independent faults in cases 02–04. The agent reported 26 completed steps; a selected-metadata check of the fixture shows 27 completion records, including `import_request`. Its counting convention is not visible, so the discrepancy remains minor and unresolved. |
| Source-independent usability | The visible workflow discovers the rules through installed public topics and obtains workspace facts using CLI reports, SQL, and Python metadata inspection. No application source reads are shown. Commands and their expanded outputs are partly collapsed in the supplied transcript, so the complete script and computation cannot be audited from this excerpt. |
| Operational safety | Visible commands are consistent with read-only diagnosis and the agent explicitly reports no narrative reads or workspace changes. There is no visible TUI startup or repair attempt. The excerpt alone does not independently prove absence of writes or narrative reads; immutable snapshot verification remains the separate implementation evidence. |
| Recovery trustworthiness | Recommending no action for this fixture is correct. Conditional advice to use **Regenerate All Outputs** after changes to untracked metadata is incomplete: that action refreshes missing/stale outputs and may skip artifacts still marked current. The installed version of the [correction guide](../../docs/guides/correct-processed-session.md) at evaluation time recommended explicit **Role Transcript** regeneration, with speaker assignments corrected first if attendees changed. The agent did not consult this topic in the visible workflow. The checkout guide has since been rewritten to explain automatic-step restarts. |

### Other Evidence Limits

The claim that nothing in the database changed after processing is broader than the selected metadata timestamps establish. Likewise, zero current voice samples and no current voice print do not prove that no historical voice-print change occurred. These observations can support a cautious explanation, but should not eliminate the documented limits of freshness tracking.

The interface suggestion “Regenerate all outputs anyway” appears after the response; it is not an executed command or a new instruction from the user.

### Follow-Up

Cases 02–04 remain pending. Keep the installed documentation and fixtures unchanged during this round. After reviewing the remaining transcripts, consider clarifying the public freshness topic's recovery guidance for metadata that is not fingerprinted, linking to the correction guide and explaining why regeneration of all outputs can skip it. This is a proposed documentation refinement; no app or installed-doc changes were made during this assessment.

The user subsequently requested clarification of automatic-step restarts. The checkout freshness reference and FAQ now explicitly explain selecting an automatic row by click and using **Restart from here**, with examples and the upstream transcript-review warning. The freshness reference also clarifies that regeneration of all outputs can skip current artifacts after untracked changes. The existing test installation still serves the earlier bundled docs; a rebuilt/reinstalled wheel is required to expose the new wording through its help commands. The original case-01 assessment remains tied to its earlier installed snapshot.

## Case-02: Missing Normalized Audio Only — October 5, 2026

**Evaluated version:** TableSage 1.0.0 in the existing validation environment. At assessment time its installed freshness topic matches the checkout's automatic-restart clarification, confirming that the documentation snapshot differs from case-01. The user supplied a fresh Claude Code/Sonnet 5.5 conversation in `case-02` with the neutral question.

**Outcome:** The agent correctly identified missing `normalized_review_audio.wav` as the cause of stale Input Audio and dependent outputs. It explicitly checked that both review records retain the required normalized-audio input, distinguishing this case from missing-fingerprint and combined failures. It did not claim to compare file or prompt hashes and explained that further checks could reveal additional faults but could not remove the known blocker.

| Dimension | Assessment and Evidence |
|---|---|
| Diagnostic completeness | Correct planted fault and downstream explanation. A selected-metadata check confirms input audio present, normalized audio absent, both review input keys present, all 27 records complete, and no drafts, failures, or interrupted-write markers. The agent again reports 26 completion records; the excerpt does not show its counting convention. Hash comparisons remain unassessed, as the agent acknowledged. |
| Source-independent usability | The visible workflow uses installed public topics, schema/query commands, and selected metadata; no source reads or TUI startup are shown. The expanded scripts and tool outputs remain partly collapsed, limiting auditability. |
| Operational safety | No visible repairs; the agent reports no workspace changes or narrative reads. Those claims are consistent with the shown tools but are not independently proven by the excerpt. |
| Recovery trustworthiness | Correctly rejects manual WAV/fingerprint fabrication and output-only regeneration as upstream repair. Recognizes repeated processing, provider costs, and lost transcript-review edits. The recording-picker instructions omit explicitly highlighting **Import Audio** and using **Restart from here**. **Continue** instead resumes automatic **Import Audio File** with the saved path when the selection remains complete. Repeating both reviews is not established for every recovery: later steps depend on actual freshness after import, except that upstream processing invalidates transcript-review work. No recovery was run. |

### Documentation Follow-Up

Clarified the freshness reference's recovery section: manual **Import Audio** selects the source; automatic **Import Audio File** creates the pair; **Continue** uses the saved selection, while restarting **Import Audio** opens the picker. The installed docs were inspected read-only and not replaced during this assessment. The new clarification requires another build/install to appear there. The terminal suggestion asking how to re-import is not an executed follow-up conversation. Cases 03–04 remain pending.

## Case-03: Missing Review Fingerprints Only — October 5, 2026

**Evaluated version:** TableSage 1.0.0, fresh Claude Code/Sonnet 5.5 conversation in `case-03` using the neutral question. The installed reference includes the automatic-restart clarification but not the later case-02 recording-picker clarification; this matches the topic length shown in the transcript. No installation changes were made for this assessment.

**Outcome:** The agent correctly identifies both missing `artifact:normalized_review_audio` inputs while both audio files exist. It distinguishes missing required fingerprints from mismatched recorded hashes, follows downstream dependencies, and recommends **Continue** at affected processing rather than re-importing audio or regenerating outputs alone. It also resolves the `reviewed_transcript` artifact's filename mapping instead of treating an initial unverified hash comparison as a fault.

| Dimension | Assessment and Evidence |
|---|---|
| Diagnostic completeness | Correct independent blockers and downstream explanation. Selected-metadata inspection confirms both audio files present, both normalized-audio input keys absent, 27 complete records, and no drafts, failures, or interruption markers. The agent reports comparisons of file, section, and packaged prompt hashes; collapsed scripts and output prevent independently auditing those comparisons from the transcript. |
| Source-independent usability | Uses installed public help, read-only schema/query commands, a file listing, and local metadata/hash inspection. No source reads or TUI startup appear. Correctly ignores database processing status as an artifact-freshness signal. |
| Operational safety | No visible repair or workspace mutation; the agent reports no narrative reads or changes. Full absence of writes/content reads cannot be proved from the excerpt alone. The backup recommendation is a user action, not an executed copy. |
| Recovery trustworthiness | Correctly identifies review processing as the repair path and avoids unnecessary audio import. Explains unsupported manual certification and output-generation prerequisites, with provider-cost and backup guidance. Completing affected reviews is required, but whether each review displays a screen or retains prior decisions depends on its inputs and proposals; no recovery was executed. |

The statement that this is an older Session processed before normalized audio was required should be phrased as a compatible explanation, not proven history. The metadata proves the missing inputs; this fixture deliberately removed them from a newly prepared baseline. Prompt-hash equality also establishes agreement with the current installation, not a complete upgrade history.

Case-03 supports the intended distinction between the two fault types. No new documentation or code change was needed for its primary diagnosis or recommended starting action. Case-04 remains pending to assess recognition of both faults together.

## Case-04: Combined Failure — October 5, 2026

**Evaluated version:** The supplied fresh Claude Code/Sonnet 5.5 conversation reports TableSage **0.1.0**, unlike cases 01–03, which report **1.0.0**. Read-only checks confirm the default `/home/eriksalt/.local/bin/tablesage` launcher resolves to the user's uv tool installation and reports 0.1.0, serving the newer import-picker clarification. The prepared validation environment still reports 1.0.0 and lacks that latest clarification. The transcript does not expose command resolution directly, so the default launcher is a matching explanation rather than proof of the exact executable used by Claude.

**Outcome:** Correctly identifies both planted faults: missing normalized review audio and missing normalized-audio fingerprints in both review records. Explains their downstream effects and that restoring the WAV alone cannot repair the missing recorded inputs. Gives explicit **P → highlight Import Audio → R** steps, explains lost transcript-review work, rejects manual certification and output-only regeneration, and acknowledges that prompt hashes remain unverified because its Python cannot locate the application.

| Dimension | Assessment and Evidence |
|---|---|
| Diagnostic completeness | Correct combined-fault diagnosis. Selected-metadata inspection confirms input audio present, normalized audio absent, both review input keys absent, 27 complete records, and no drafts or failures. The transcript reports matching other file hashes but the collapsed scripts cannot be fully audited. Prompt equality remains explicitly unverified. |
| Source-independent usability | Finds and applies public topics through functioning commands, despite stale-guide warnings. No source reads or TUI startup are shown. Correctly continues diagnosis when Python cannot locate installed prompts, rather than substituting source inspection. This demonstrates usable fallback, while exposing inconsistent executable/Python environments. |
| Operational safety | No visible workspace repair or mutation; the agent says it changed nothing. Stale-guide warnings do not require startup or guide refresh during diagnosis. The excerpt does not independently prove all reads/writes. |
| Recovery trustworthiness | Correctly treats file restoration and review certification as independent requirements and gives the supported restart route with review-loss and provider-cost guidance. No recovery was executed. Whether existing narrative outputs are useful as reference is unassessed; metadata alone cannot justify the agent's “probably usable” characterization. |

### Overall User-Run Findings

All four supplied conversations reach the expected primary diagnosis: current baseline, missing normalized audio only, missing review fingerprints only, and both faults together. Case-04 additionally demonstrates nonblocking stale-guide handling and an explicit limitation when prompt hashes cannot be located. The docs refinements address restart discoverability, current-output regeneration limits, and recording-picker controls.

These are not four runs of an identical installed snapshot. Documentation changed between cases, and case-04 used a command reporting 0.1.0 while the earlier cases reported 1.0.0. For a controlled comparison, repeat case-04 after activating the prepared 1.0.0 environment and starting a fresh conversation; retain its acknowledged older documentation snapshot in the result. If validating the final revised docs instead, build/install one final wheel and repeat all cases under that same environment. Neither repeat has yet occurred. No complete recovery pipeline, original production investigation, narrative-quality assessment, or cross-Session validation was performed.
