# Working, Source-Independent Agent Diagnostics

Agents should be able to explain workspace problems using the installed TableSage commands, help, and read-only metadata without access to TableSage source code or Session narrative content. A real support investigation exposed two gaps: installed diagnostic commands opened the interactive app, and available metadata did not explain why artifact freshness checks failed.

This document records the problem, incident evidence, and decisions from the October 4, 2026 workshop and subsequent fleshing-out discussion. The initial proposed solution was reset before this direction was developed. Implementation is finished with direct installed-command and synthetic-fixture verification; see [progress.md](progress.md) for results and limitations. The original production incident was not independently rerun. [evaluations.md](evaluations.md) records all four user-run transcript assessments: primary diagnoses match expectations, with documentation changes and a different case-04 installation limiting controlled comparison.

## Observed Incident

On October 4, 2026, all visible artifacts in three previously processed Sessions appeared out of date. Following `.tablesage/agent-guide.md`, the agent attempted:

```sh
tablesage output-help-topic reference/troubleshooting-faq
tablesage report-schema
```

Both commands launched the interactive TUI instead of printing diagnostic reports. The agent stopped the two extra processes it had started.

Inspection of the installed launcher showed that it called:

```python
from tablesage_tui.screens import main
```

The source contains a separate command handler in `tablesage_tui.cli.main`; the installed launcher bypassed that handler. This installation uses an editable checkout. Whether a newly installed distribution has the same entry-point problem remains unverified.

## Freshness Failure Revealed by Source Inspection

All three Sessions were processed September 27–28, 2026. They retained their original audio, transcripts, generated outputs, and completion records, but lacked:

```text
normalized_review_audio.wav
```

Commit `8436eb3`, dated September 29, added this file as a required output of Import Audio and added normalized review audio as an input to the speaker-assignment review and transcript-review steps.

The current artifact evaluator marks a step stale when any required output is missing, then recursively propagates stale status to dependent artifacts. The missing normalized audio therefore made Import Audio stale and invalidated the downstream chain.

The older review completion records also lack the newly required audio input fingerprint. Creating the missing file alone would not necessarily make all artifacts current. The supplied investigation identifies this as an upgrade compatibility gap; the appropriate migration behavior remains separate implementation work and is not decided here.

## Problem to Solve

When TableSage reports that previously processed Session artifacts are out of date, an agent working with the installed application and workspace cannot reliably determine why, how the affected artifacts relate, or what recovery is supported. The agent may have to inspect application source code to connect visible symptoms to the rules that produced them.

The supplied incident illustrates two barriers: documented help and metadata commands did not behave as promised in the observed installation, and available workspace metadata did not explain the application's freshness requirements. Files and completion records were present, but that did not establish that they met the current application's expectations.

This leaves the agent unable to confidently distinguish a shared underlying cause from additional independent problems, explain what changed between processing and the current installation, or advise the user about recovery without guessing. Diagnosis should not require access to Session narrative content or alter the workspace being investigated.

## Desired Outcome

An agent with the installed application and workspace can explain the observed problem, identify the evidence supporting that explanation and any remaining uncertainty, and distinguish supported recovery from unresolved compatibility issues. Its understanding of application behavior comes from the same public documentation users see on GitHub.

## Agreed Direction

The feature addresses three connected needs:

- **Commands that work:** Restore reliable execution of the existing installed diagnostic commands. They should return their output and exit, without starting the TUI or performing startup writes, migrations, or logging.
- **Trustworthy workspace facts:** Give the agent sufficient evidence about the installed application and workspace to establish what is present, missing, current, or inconsistent. Inspect existing capabilities before adding anything.
- **Shared public explanations:** Document how the application works, its dependencies, what blocks what, and supported recovery in the public docs. Diagnostic evidence must be interpretable through those docs alone.

The existing CLI supports `report-help-topics`, `output-help-topic`, `report-schema`, and read-only `run-query`. Public documentation already includes Advanced Help and a Troubleshooting FAQ explaining several blockers and processing fingerprints. Build on this foundation rather than replacing the documentation access mechanism. The incident indicates installed command dispatch failed; the handler's existence does not prove the installed executable works.

Workspace evidence supplies facts about a particular installation; public documentation supplies the meaning and rules. An agent must not need application source code or private behavioral instructions to interpret those facts. Documentation should match the installed application version; a bundled copy of the same public docs is compatible with this constraint. Workspace pointers may explain how to find that documentation, but must not become a separate source of application behavior.

Do not introduce a separately maintained representation of processing decisions, dependencies, or freshness rules for diagnosis. The user rejected that direction because code and documentation already need to remain synchronized; a third representation would add maintenance and drift risk. Any newly exposed facts must be justified by a concrete diagnostic gap. A new artifact-explanation report, its command name, and cause-first report organization are not agreed requirements.

## Diagnostic Access Decisions

- Every command, including the help commands, continues to require a workspace. Help outside a workspace is not part of this item.
- A missing or outdated `.tablesage/agent-guide.md` must not block diagnostics. Warn about the guide and continue using the installed version's bundled public documentation; do not require an interactive launch to refresh the guide before diagnosis. This changes the current CLI behavior that stops commands when enabled agent files are outdated.
- The agent may use ordinary shell tools to read file listings and selected metadata fields, alongside the existing TableSage commands. Public docs should explain the locations and meanings of relevant fields. Do not dump whole processing-state documents when they contain narrative content in sections or drafts.
- Diagnostic information remains read-only. Restoring command dispatch and changing guide handling must preserve the boundary against TUI startup, migrations, workspace writes, and app-start logging.

## Recovery Scope

If a case reveals that older Sessions need recovery the application does not support, document that limitation accurately and capture recovery implementation as separate work. This item does not expand into a migration or recovery implementation project. Guidance must distinguish supported user actions from unresolved compatibility behavior.

Inspection confirmed that reprocessing is supported, but there is no targeted migration certifying old reviews against the normalized-audio contract without repeating necessary processing. The separate [review-preserving migration registration](../normalized-review-audio-migration/) captures that follow-up without deciding its migration behavior.

## Case-Based Verification Approach

Start with concrete diagnostic cases using only the installed application, workspace evidence, and public docs. Each place where diagnosis gets stuck identifies a command failure, missing fact, or documentation gap. Repair command execution first, then address demonstrated gaps rather than designing a broad new diagnostic system in advance.

Use disposable synthetic workspaces created by a script, not the production workspace or its content. Setup runs entirely offline, without API keys, model downloads, real transcription, or real generation. Use small synthetic artifacts and existing application operations and helpers for completion records and fingerprints. Check the resulting valid baseline with the application's existing freshness evaluator. The script must not duplicate freshness rules or manufacture a separate explanation model.

Create four separate workspaces under one disposable parent directory, each built from the valid baseline. Each contains one Campaign with one processed Session; cross-Session dependencies are outside these initial cases. Apply narrowly defined changes to arrange these cases:

- **Current baseline:** Artifacts are correctly current, to check that evidence and documentation do not encourage false diagnoses.
- **Missing normalized audio only:** Remove normalized review audio while retaining the baseline review-input fingerprints.
- **Missing review-input fingerprints only:** Retain normalized review audio but remove its recorded fingerprints from the relevant review completion records.
- **Combined failure:** Remove both the normalized audio and those review-input fingerprints, reproducing the reported pair of faults and their downstream effects.

Separate workspaces avoid leftovers from switching cases and permit direct comparison. The exact baseline construction and script location remain implementation details to resolve. Starting conditions should be reproducible so recovery claims can also be checked. Verification uses direct execution and behavior checks, following the project's restriction on adding unit tests or unit-test tooling.

Successful walkthroughs should establish that the installed commands return useful output, the agent can distinguish the current and stale cases without source access or Session narrative content, and recovery guidance accounts for independent blockers instead of implying that restoring one file necessarily repairs everything. The diagnostic path remains read-only; creating or changing the disposable fixture is a separate setup activity.

## User-Run Agent Validation

After implementation, provide the user with step-by-step instructions for running the script, locating each workspace, starting a fresh agent conversation in each, and asking the same neutral question:

> Can you check whether this Session's outputs are current? Explain your findings and any action I should take.

The question must not reveal the planted fault. The diagnosing agent should receive only the installed application, that case's workspace, and the public documentation accessible through the existing help commands. Keep the setup script, expected answers, application source, and prior implementation context outside its diagnostic context. Source access is allowed for implementation and fixture setup, not for these conversations.

The user will run the conversations and provide their transcripts for debugging and validation. Direct command and fixture checks during implementation are separate from this user-run validation; do not claim fresh-agent validation has occurred before those transcripts are available. Inspect findings for accurate identification of both independent faults, downstream effects, correct recognition of the current case, and supported recovery guidance, using the quality rubric below. Transcripts can identify further evidence or documentation gaps to address.

## Quality rubric

Judge the feature's ability to support source-independent diagnosis through these accepted qualitative dimensions. These describe what matters; no numerical scale or performance anchors were agreed.

| Dimension | What it values |
|---|---|
| Diagnostic completeness | Explains underlying causes, downstream effects, and independent blockers, including missing outputs and input fingerprints. |
| Source-independent usability | Gives agents discoverable commands and understandable information using only the installed application, workspace evidence, and shared public docs. |
| Operational safety | Keeps diagnostics read-only, avoids interactive startup and startup side effects, and excludes Session narrative content. |
| Recovery trustworthiness | Grounds recovery guidance in supported behavior, distinguishes uncertainty and migration gaps, and explains what a proposed action can resolve. |

Completeness and recovery trustworthiness are distinct: a diagnosis can identify every cause while still suggesting a recovery that leaves older completion records incompatible. Workshop judgments concerned design potential, not demonstrated application performance; no completed verification or quality measurement is claimed.

## Remaining Validation and Limits

- Direct checks passed for new editable and wheel installs, and for a simulated old launcher importing `screens.main`. The original installed launcher was not rerun, and platforms other than Linux/Python 3.12 were not verified.
- The offline script lives in `scripts/setup_diagnostic_workspaces.py`, reuses the authored documentation artifact writers and existing completion/fingerprint helpers, and refuses existing destinations. Reruns use a new output directory. [scripts/README.md](../../scripts/README.md#diagnostic-workspace-validation) contains the setup and conversation instructions.
- User-run transcripts will establish whether a fresh agent can use the public explanations and metadata successfully, and reveal any remaining documentation or evidence gaps.
- Broader workspace failures and cross-Session dependencies remain outside these four initial cases. Synthetic artifacts do not verify transcription, narrative accuracy, or speaker recognition. Unsupported review-preserving migration remains separate work.

## Supporting References

These source references were supplied with the incident; they are pointers for subsequent investigation, not evidence of fresh verification during capture.

- [CLI command handler](../../apps/tablesage-tui/src/tablesage_tui/cli.py).
- [Application](../../packages/tablesage-application/src/tablesage_application/application.py): `*session*steps` dependency definitions.
- [Artifact graph](../../packages/tablesage-application/src/tablesage_application/session_pipeline/artifact_graph.py): `_evaluate` freshness evaluation.
- [Troubleshooting FAQ](../../docs/reference/troubleshooting-faq.md).
- Commit `8436eb3`: normalized review audio and dependency changes.
- [Workspace agent help](../workspace-agent-help/item.md): completed agent-help work and its diagnostic command contract.
- [Normalized audio for session review](../normalized-review-audio/item.md): completed artifact and review dependency change.

The completed [Session artifact state tooltips](../session-artifact-state-tooltips/) item covers explanations in the Session Detail UI. This item concerns installed commands, shared public documentation, and source-independent agent diagnosis.
