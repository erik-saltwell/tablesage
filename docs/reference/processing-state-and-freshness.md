# Processing State and Freshness

Understand why Session artifacts are current, missing, or out of date using workspace metadata. This reference describes the installed application's completion rules and dependencies, including what blocks regeneration, without requiring Session narrative content or application source code.

## Locate the Session

Run diagnostics from the workspace containing `.tablesage/`. Start with `tablesage report-schema`, then query only the records needed to locate the Session:

```sh
tablesage run-query "SELECT c.name AS campaign, s.name AS session, s.sequence_number, s.session_date FROM session AS s JOIN campaign AS c ON c.id = s.campaign_id ORDER BY c.name, s.sequence_number"
```

Its files are under `campaigns/<Campaign name>/<NNN>/`, where `NNN` is the sequence number padded to three digits. Database processing status is not the source of artifact freshness. Read the Session's `processing_state.json` metadata and file listing instead. Follow [Advanced Help](../guides/advanced-help.md#boundaries-for-agent-diagnosis) to keep diagnosis read-only.

## How Freshness Is Determined

A file artifact is **missing** if its file does not exist. A section artifact is missing if its key is absent from `sections` in `processing_state.json`. An existing artifact is **out of date** if any of these apply:

- A required output from the same producing step is missing, even if the artifact itself exists.
- Its producing step has no completion record, or that record's `complete` flag is false.
- A currently required input has no recorded fingerprint.
- An artifact input is itself missing or out of date.
- An input's current fingerprint differs from the recorded fingerprint.
- An interrupted pair write left `.audio-import-incomplete` (Input Audio and Normalized Review Audio) or `.ledger-generation-incomplete` (Ledger and Scene Breakdown).

Otherwise the artifact is **current**. Artifacts with no producing step are current when present; companion artifacts share their producer's completion record. The record's `completed_at` timestamp is historical evidence, not the test of currentness. Obsolete recorded inputs are ignored when the installed version no longer requires them. A new required input absent from an older record makes the step out of date, even if no existing file changed.

Freshness propagates through dependencies. A missing Import Audio output can make Input Audio stale, which makes Transcript stale, and so on to reviewed transcripts and generated outputs. There can also be independent blockers farther down the chain: inspect the relevant records for missing required inputs even after finding an earlier stale dependency.

An unreadable or invalid `processing_state.json` makes the application try `processing_state.json.bak`; if both fail, it uses empty state. Report uncertainty when the metadata cannot be parsed rather than diagnosing it as an ordinary completed Session. Merely inspecting metadata does not perform the app's legacy import or migrations.

## Completion Metadata and Fingerprints

`records` maps the producer names below to `{complete, completed_at, inputs}`. Each input has a `sha256` digest. File inputs also store `size` and `mtime_ns`, allowing unchanged files to be recognized without hashing again. A changed file timestamp alone does not prove stale content: the app compares content hashes when those attributes differ. Section inputs hash canonical JSON with sorted keys and compact separators; they have no file size or modification time.

Input keys are `artifact:<name>` for this Session, `artifact:<NNN>/<name>` for another Session, and `prompt:<name>` for a packaged system prompt. System-prompt changes after an application upgrade can invalidate generated outputs. Input Audio and Normalized Review Audio share the `input_audio` producer record. Transcript JSON and Markdown share `transcript`; Ledger JSON, Ledger Markdown, and Scene Breakdown share `ledger`.

The following local Python example prints only metadata and fingerprints. Replace the Session path before running it. It parses JSON locally but does not print section values, drafts, transcripts, or audio. File hashing also stays local and emits only hashes. It locates packaged prompt data without reading source code or importing the application.

```sh
python3 - <<'PY'
import hashlib
import importlib.util
import json
from pathlib import Path

folder = Path("campaigns/Your Campaign/001")
state = json.loads((folder / "processing_state.json").read_text())
sections = state.get("sections", {})
section_hashes = {
    key: hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    for key, value in sections.items()
}
print(json.dumps({"version": state.get("version"), "records": state.get("records", {}),
                  "section_sha256": section_hashes, "draft_keys": sorted(state.get("drafts", {}))}, indent=2))
for path in sorted(folder.iterdir()):
    if path.is_file() and path.name not in {"processing_state.json", "processing_state.json.bak"}:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1048576), b""):
                digest.update(chunk)
        stat = path.stat()
        print(path.name, "bytes", stat.st_size, "mtime_ns", stat.st_mtime_ns, "sha256", digest.hexdigest())
spec = importlib.util.find_spec("tablesage_application")
if spec is not None and spec.origin:
    prompts = Path(spec.origin).parent / "llm" / "_prompts"
    for path in sorted(prompts.glob("*/system.md")):
        print("prompt:" + path.parent.name, "sha256", hashlib.sha256(path.read_bytes()).hexdigest())
PY
```

Use a Python environment containing the installed TableSage for the prompt hashes. If your shell's Python cannot locate it, file and section metadata remain useful, but prompt currentness is unverified. Do not read installed source to fill that gap. Hashes establish equality, not why a file changed or whether its narrative content is correct.

## Required Outputs and Inputs

These are the producer names used in `records`, their required outputs, and their fingerprinted inputs. A name without a file extension is a key in `sections`; a name prefixed `prompt:` is an installed system prompt. Artifact inputs use the producer/artifact names described in the table. New-Player steps may be skipped by normal processing but still have recorded sections and outputs representing that decision.

| Producer | Required Outputs | Required Inputs |
|---|---|---|
| `import_request` | `import_request` section | None |
| `input_audio` | `input_audio.wav`, `normalized_review_audio.wav` | `import_request` |
| `transcript` | `transcript.json`, `transcript.md` | `input_audio` |
| `cleaned_transcript` | `cleaned_transcript.json` | `transcript`, `prompt:classify_backchannels` |
| `name_correction_suggestions` | `name_correction_suggestions` section | `cleaned_transcript`, `prompt:suggest_name_corrections` |
| `name_correction_decisions` | `name_correction_decisions` section | `name_correction_suggestions` |
| `name_corrected_transcript` | `name_corrected_transcript.json` | `cleaned_transcript`, `name_correction_decisions` |
| `new_speaker_assignments` | `new_speaker_assignments` section | `name_corrected_transcript`, `prompt:isolate_new_speakers` |
| `reviewed_new_speaker_assignments` | `reviewed_new_speaker_assignments` section | `new_speaker_assignments`, `normalized_review_audio` |
| `seeded_voice_samples` | `seeded_voice_samples` section | `reviewed_new_speaker_assignments` |
| `identified_transcript` | `identified_transcript.json` | `name_corrected_transcript`, `seeded_voice_samples` |
| `glossary_suggestions` | `glossary_suggestions` section | `identified_transcript`, `prompt:extract_glossary` |
| `glossary_decisions` | `glossary_decisions` section | `glossary_suggestions` |
| `extracted_glossary_terms` | `extracted_glossary_terms` section | `glossary_decisions` |
| `spelling_suggestions` | `spelling_suggestions` section | `identified_transcript`, `extracted_glossary_terms`, `prompt:suggest_spelling_corrections` |
| `spelling_decisions` | `spelling_decisions` section | `spelling_suggestions` |
| `spellchecked_transcript` | `spellchecked_transcript.json` | `identified_transcript`, `spelling_decisions` |
| `transcript_review_edits` | `transcript_review_edits` section | `spellchecked_transcript`, `normalized_review_audio` |
| `reviewed_transcript` | `transcript_reviewed.json` | `spellchecked_transcript`, `transcript_review_edits` |
| `role_transcript` | `role_transcript.json` | `reviewed_transcript` |
| `transcript_sections` | `transcript_sections.json` | `role_transcript`, `prompt:section_transcript` |
| `ledger` | `ledger.json`, `ledger.md`, `scene_breakdown.json` | `role_transcript`, `transcript_sections`, `prompt:generate_ledger` |
| `player_introductions` | `player_introductions.json` | `role_transcript`, `transcript_sections`, `prompt:generate_player_introductions` |
| `recap_summary` | `recap_summary.md` | `scene_breakdown`, `prompt:generate_recap_summary` |
| `summary` | `summary.md` | `ledger`, `player_introductions`, `prompt:summarize_session`; previous Session's `recap_summary` when applicable |
| `voice_print_decision` | `voice_print_decision` section | `reviewed_transcript` |
| `voice_print_enhancement` | `voice_print_enhancement` section | `voice_print_decision` |

`normalized_review_audio` is the companion artifact of `input_audio`; `transcript_text` is `transcript.md`; `scene_breakdown` is the companion artifact of `ledger`. A Summary's previous Session comes from `.summary-inputs.json` when recorded, otherwise from Session dates. Its previous recap dependency applies only while that prior Session has a current reviewed transcript; otherwise generation can use a placeholder. Other campaign preparation tools still require current Scene Breakdowns; see [Previously On and Opportunities](screens/previously-on-and-opportunities.md).

Attendance, Roles, Session dates, campaign Glossary contents, model choices, and later changes to Player voice prints are not fingerprinted. Current marks do not promise those details are up to date; see [Correct a Processed Session](../guides/correct-processed-session.md).

## Missing Normalized Audio after an Upgrade

Older processed Sessions may retain transcripts, outputs, and completion records while lacking `normalized_review_audio.wav`. The installed version requires that file alongside `input_audio.wav` for Import Audio. Input Audio therefore becomes out of date and invalidates downstream work. Both `reviewed_new_speaker_assignments` and `transcript_review_edits` also require `artifact:normalized_review_audio` in their recorded inputs.

Check all three conditions: the normalized file's presence, the speaker review's recorded audio fingerprint, and the transcript review's recorded audio fingerprint. Restoring the file alone cannot make a record current if its required fingerprint is absent. Conversely, missing fingerprints can invalidate review and outputs even when both audio files exist and Import Audio is current.

Do not create completion records, insert fingerprints, or manufacture the missing WAV by hand. This version has no targeted migration that certifies those older reviews against the new audio requirement. Reprocessing is supported; preserving the old review decisions without repeating the necessary steps requires separate migration support.

## What Blocks Recovery and Generation

### Restart a Completed Step

**Restart from here** works on any completed processing step, including automatic steps whose outputs are still current. On **Session Detail**, press **P** (**Process**), click the step's row to highlight it, then press **R** (**Restart from here**). Arrow keys move between review steps only and skip automatic rows; an automatic row's dim styling does not prevent restarting it. Restart is available when no processing run is active and no processing blocker is present.

A manual step reopens its review; an automatic step runs again. For example, after editing Roles in **Attendance**, restart **Assign Roles To Players** to apply them. To obtain fresh spelling suggestions after a Glossary change, restart **Suggest Spelling Corrections**. Processing continues through affected steps and any required reviews. Unchanged results can leave later work current, but **restarting before Review Transcript discards its saved edits and drafts**, requiring a new transcript review. See [Correct a Processed Session](../guides/correct-processed-session.md) for recommended starting steps and [Process Session](screens/process-session.md#keys) for controls.

### Resume Stale Processing

On **Process Session**, **Continue** resumes at the first incomplete or out-of-date step. The manual **Import Audio** step saves your recording selection; the automatic **Import Audio File** step creates both audio files. When only an imported audio file is missing, the selection can remain complete. In that case, **Continue** runs **Import Audio File** using the saved recording path; it does not reopen the file picker.

To select the original recording again or change a saved path that no longer exists, open **Session Detail**, press **P** (**Process**), highlight the completed **Import Audio** row, and press **R** (**Restart from here**). Choose the recording and answer any import prompts, then follow processing through the affected steps. This imports both audio files and repeats affected transcription, review, and generation; it may require provider credentials and can incur costs. An upstream restart discards saved transcript-review edits and drafts. Keep the original recording available. Merely opening the app or updating its guide does not repair completion fingerprints.

If Import Audio is current but a speaker or transcript review is stale, complete the affected review and any downstream steps through **Process Session**. Missing normalized audio fingerprints mean those reviews have not been certified under the installed contract; do not assume a file-only repair preserves their currentness.

**Regenerate Artifact** requires a current reviewed transcript, so it cannot repair a stale import or review. **Regenerate All Outputs** skips Sessions without a current completed transcript review. Fix upstream processing first; see [Generate and Export Session Outputs](../guides/review-and-export.md). A Session without attendees cannot start processing; add them on **Session Detail**.

**Regenerate All Outputs** refreshes missing or out-of-date outputs; it does not force a fresh result for every current output. Changes to metadata that is not fingerprinted can leave all steps current, so **Continue** and **Regenerate All Outputs** may have nothing to do. Explicitly restart the step that uses the changed information, or use **Regenerate Artifact** for a supported individual output.

These instructions identify supported user actions, not permission for an agent to perform them or assurances that every compatibility case is recoverable. If the application still cannot proceed, report the remaining blocker and request migration support separately.
