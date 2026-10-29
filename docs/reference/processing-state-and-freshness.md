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
- An interrupted pair write left `.audio-import-incomplete` (Input Audio and Normalized Review Audio) or an artifact’s `.ledger-v5-generation-incomplete`, `.scene_log-generation-incomplete`, `.summary-generation-incomplete`, or `.table_recap-generation-incomplete` marker. These suppress incomplete narrative outputs until recovery/regeneration; the older Ledger/Scene Breakdown marker is also recognized.

Otherwise the artifact is **current**. Artifacts with no producing step are current when present; companion artifacts share their producer's completion record. The record's `completed_at` timestamp is historical evidence, not the test of currentness. Obsolete recorded inputs are ignored when the installed version no longer requires them. A new required input absent from an older record makes the step out of date, even if no existing file changed.

Freshness propagates through dependencies. A missing Import Audio output can make Input Audio stale, which makes Transcript stale, and so on to reviewed transcripts and generated outputs. There can also be independent blockers farther down the chain: inspect the relevant records for missing required inputs even after finding an earlier stale dependency.

### Explicitly Adopted Reviewed Transcripts

A reviewed transcript can be explicitly accepted as a migration checkpoint after a human confirms that the existing review should remain authoritative. This is application support used by a separate maintenance utility; upgrades do not adopt transcripts automatically, and there is no migration action in the UI.

The `reviewed_transcript_checkpoint` field in `processing_state.json` records the Session ID, SHA-256 of `transcript_reviewed.json`, adoption date, source revision, and backup reference. The reviewed transcript is current while those file bytes match the accepted checksum. This acceptance replaces the requirement for its historical machine-processing inputs to be current; it does not certify or change those earlier steps. Generated outputs still follow their normal completion records and dependencies, and a maintenance update rebuilds them using the accepted review.

Missing or changed transcript bytes invalidate the checkpoint and downstream outputs. Explicitly restarting upstream processing or replacing the review revokes acceptance and resumes normal processing rules. Merely inspecting old review decisions leaves them intact. Earlier processing rows may remain out of date after adoption. The processing coordinator resumes after the accepted review; use output regeneration rather than explicitly restarting those earlier rows when preserving it. Back up the workspace before adoption, and retain its historical review decisions.

An unreadable or invalid `processing_state.json` makes the application try `processing_state.json.bak`; if both fail, it uses empty state. Report uncertainty when the metadata cannot be parsed rather than diagnosing it as an ordinary completed Session. Merely inspecting metadata does not perform the app's legacy import or migrations.

## Completion Metadata and Fingerprints

`records` maps the producer names below to `{complete, completed_at, inputs}`. Each input has a `sha256` digest. File inputs also store `size` and `mtime_ns`, allowing unchanged files to be recognized without hashing again. A changed file timestamp alone does not prove stale content: the app compares content hashes when those attributes differ. Section inputs hash canonical JSON with sorted keys and compact separators; they have no file size or modification time.

Input keys are `artifact:<name>` for this Session, `artifact:<NNN>/<name>` for another Session, `prompt:<name>` or `prompt:<name>/<file>` for packaged generation resources, and `value:<name>` for configuration/context values. Narrative outputs fingerprint their prompts, templates, schemas, generation controls, and relevant context. Input Audio and Normalized Review Audio share `input_audio`; Transcript JSON and Markdown share `transcript`. Each narrative JSON/Markdown pair has its own producer record.

Python source files are not freshness dependencies. Editing Application, generation, filtering or rendering Python code does not mark outputs out of date. Use **Regenerate Artifact** to force a rebuild when applying a code change. **Regenerate All Outputs** still refreshes only missing or out-of-date outputs. Older completion records may retain Python fingerprint entries; they are ignored and need no migration.

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
                  "reviewed_transcript_checkpoint": state.get("reviewed_transcript_checkpoint"),
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
| `transcript_sections` | `transcript_sections.json` | `role_transcript`, roster/bootstrap context, prompt bundle, input code, model and timeout |
| `ledger` | `ledger.json`, `ledger.md` | `role_transcript`, `transcript_sections`, Ledger bundle, model/options, roster, Glossary and bootstrap mode |
| `scene_log` | `scene_log.json`, `scene_log.md` | current `ledger`, prior recorded Session’s `present_matters`, roster, Glossary, predecessor identity, Scene Log bundle and generation controls |
| `player_introductions` | `player_introductions.json` | `role_transcript`, `transcript_sections`, roster, Glossary, Campaign name/system, Session date, prompt bundle, input code, model and timeout |
| `table_recap` | `table_recap.md` | Current Summary, presentation prompt/template/schema and model controls |
| `summary` | `summary.md` | `post_session_matters`, `scene_log`, Campaign name, Session date, renderer code and Jinja template |
| `voice_print_decision` | `voice_print_decision` section | `reviewed_transcript` |
| `voice_print_enhancement` | `voice_print_enhancement` section | `voice_print_decision` |

`normalized_review_audio` is the companion of `input_audio`; `transcript_text` is `transcript.md`. Ledger and Scene Log are independent steps. Scene Log continuity follows recorded Session sequence numbers and the previous Present Matters. Table Recap follows Summary and uses an LLM for second-person presentation and closing prose. Summary is generated deterministically from Post-Session Matters. A missing/stale predecessor blocks later generation rather than producing a placeholder. Campaign preparation tools are temporarily disabled; see [Previously On and Opportunities](screens/previously-on-and-opportunities.md).

Narrative generation records its input fingerprints before making model calls. If an input changes during generation, the output remains out of date instead of being certified against the changed input. Ledger freshness includes the roster, Glossary, Session name and first-session bootstrap mode; model-generated narrative freshness includes model/options and generation timeout. Summary tracks its combined JSON input, Scene Log, Campaign name, Session date and Jinja template, with no model or length-setting dependency. Earlier audio/speaker processing still does not fingerprint every external configuration or later voice-print change.

Legacy Scene Breakdown and Recap Summary files are retained for reading/export, but do not satisfy the new Scene Log/Matters contract. Opening a workspace performs no model calls. Regenerate narrative outputs through normal actions once the reviewed transcript is current.

## Internal Matters Artifacts

Each Matters producer writes `<category>.json` with exactly its category key, plus `<category>.evidence.json` containing the raw response, normalized unfiltered response, model and options. Both files are required for completion. Raw attempts, including rejected responses, are retained separately under `.generation-records/`. Every call validates the complete raw response before normalizing IDs, checking links and filtering. Stored results preserve retained fields and order. Later calls and later Sessions consume only these filtered publications.

| Producer | Current Matter Inputs | Prior Matter Inputs |
|---|---|---|
| `present_matters` | None | Present Matters |
| `obligations` | Goals, Goal Impediments, Opportunities | Obligations |
| `goals` | None | Goals |
| `brewing_troubles` | Goals | Brewing Troubles |
| `goal_impediments` | Goals | Goal Impediments |
| `opportunities` | Goals, Goal Impediments | Opportunities |
| `mysteries` | Goals, Goal Impediments, Opportunities | Mysteries |
| `new_assets` | Goals, Goal Impediments, Opportunities | New Assets, Goals, Goal Impediments, Opportunities |
| `revelations` | Goals, Mysteries, Goal Impediments, Obligations, Opportunities | The same five categories |
| `developments` | New Assets, Revelations | None |

Every producer also consumes the full current Scene Log and its prompt, template, schema and effective generation controls. All except Developments consume attending party Roles. Non-bootstrap prior inputs are required dependencies, never replaced by empty state. A first Session uses explicit empty prior values. Revelations never consumes prior Revelations; Developments has no prior inputs. Scene Log uses prior Present Matters as context only, rather than earlier Open Matters.

All narrative and Matters calls use the configured High model. Ledger and Scene Log use high reasoning effort; Matters use medium effort. These effective options are fingerprinted. The Campaign-local `.matter-ids.sqlite3` reserves Goal, Impediment and Opportunity IDs transactionally, including IDs later filtered out. It survives Session cleanup and travels with the Campaign folder. Failed builds can leave unused numbers; numbers are never reassigned. Allocation metadata is deliberately not a freshness dependency, so allocating a new ID does not invalidate earlier outputs.

Hidden producers remain part of **Generate Artifacts** completion and dependency-driven regeneration, without new selectable artifact rows. Old files or legacy completion metadata never certify the new Matters producers.

## Post-Session Matters

`post_session_matters` produces the visible `post_session_matters.json` file after all ten Matters publications are current. Its completion inputs are those ten current-Session artifacts, the combined schema and the owning Session UUID. Prior Sessions, Scene Log and model settings participate through the existing source dependencies; assembly does not consume them directly. It uses no LLM, allocates no IDs and reapplies no filtering. The previous output is preserved if an input is missing, stale or invalid, or replacement fails.

The JSON has `version: 1`, `session_id`, `historical_matters` (Developments, Revelations, New Assets), `present_matters` (`current_position`, `present_danger`) and `open_matters` (Goals, Goal Impediments, Opportunities, Mysteries, Obligations, Brewing Troubles). Historical entries belong to the Session just completed. All arrays remain present when empty. Full nested validation reuses the source category schemas without duplicating their definitions.

**Regenerate Artifact** and **Regenerate All Outputs** assemble the file when needed and repair required missing or stale inputs through the same dependency graph. An assembly-only run does not require model credentials; a plan containing model generation still checks the configured High model's credentials. **Generate Artifacts** requires this combined output to be current before the step completes. **Export Artifact** copies its JSON directly, and **Clean Session** deletes it with the other artifacts. The individual Matters remain hidden. Interrupted assembly uses `.post_session_matters-generation-incomplete` and the existing recovery behavior.

## Deterministic Session Summary

`summary` reads the owning Session’s current `post_session_matters.json` and existing Scene Log Session cue, and writes only `summary.md`, intended to be read aloud at the table. The title includes the recorded Session date and that cue. It uses titles or primary text, skips empty categories and exact duplicates, and finishes with Current Position and Present Danger. It excludes descriptions, details, benefits, suggested actions, IDs, ratings and justifications. No LLM, API key, new filtering or ID allocation is involved. The read-aloud wording (sentence case, bullets that follow their heading) comes from the Matters prompts, which are told the Summary heading each primary field appears under. Any leftover `summary.phrasing.json` from a briefly used phrasing pass is archived and deleted on the next write. Prior `summary.md`, `summary.json` and `.summary-inputs.json` files are archived by content hash under `legacy/narrative/` before replacement. JSON/input companions are legacy files, not required current outputs.

The producer snapshots Post-Session Matters, Scene Log, Campaign name, Session date and template fingerprints before rendering. Missing, stale, invalid or foreign-Session inputs fail before replacement; interrupted or failed writes use the existing rollback mechanism. A source change stales Post-Session Matters and then Session Summary. A template-only change stales Session Summary and its dependent Table Recap; a Python renderer change requires explicit regeneration. Campaign name and Session date changes also invalidate the summary heading. **Generate Artifacts** requires Summary to be current; existing regeneration and Markdown export actions handle it. Table Recap also needs to be current for **Generate Artifacts** to complete; campaign preparation generation remains disabled.

### Editing the Session Summary Template

In a source checkout, edit `packages/tablesage-application/src/tablesage_application/session_pipeline/session_summary.j2` to change the title, headings, section order or Markdown layout. Headings live in the template's `headings` mapping. Each Matters prompt's "Read-aloud wording" section names the heading its primary field follows, so when you rename a heading, update that prompt too; the changed prompt then makes the affected Matters out of date. The template is packaged with the application and read on each render. Template edits make Summary out of date; use **Regenerate Artifact → Summary** or `tablesage regenerate-session-summary --campaign NAME --session NUMBER` from the workspace directory to apply them. Existing saved Markdown is preserved until regeneration.

`campaign_name` is the owning Campaign’s name, used as the main title. `session_date` is the recorded date as `YYYY-MM-DD`, or `None` for an undated Session; the default title omits absent dates. `session_cue` is the existing memorable cue from the current Scene Log, reused without another model call. Both appear in the title. `historical_matters` and `open_matters` expose category names with lists of prepared primary text. `present_matters.current_position` is a string; `present_matters.present_danger` is a list. Use `join(' ')` for paragraphs or Jinja loops for bullet lists. Python retains source validation, text cleanup, duplicate handling and exclusion of descriptions and metadata. A syntax error, unknown variable or empty rendered result fails without replacing the previous summary.

## Missing Normalized Audio after an Upgrade

Older processed Sessions may retain transcripts, outputs, and completion records while lacking `normalized_review_audio.wav`. The installed version requires that file alongside `input_audio.wav` for Import Audio. Input Audio therefore becomes out of date and invalidates downstream work. Both `reviewed_new_speaker_assignments` and `transcript_review_edits` also require `artifact:normalized_review_audio` in their recorded inputs.

Check all three conditions: the normalized file's presence, the speaker review's recorded audio fingerprint, and the transcript review's recorded audio fingerprint. Restoring the file alone cannot make a record current if its required fingerprint is absent. Conversely, missing fingerprints can invalidate review and outputs even when both audio files exist and Import Audio is current.

Do not create completion records, insert fingerprints, or manufacture the missing WAV by hand. Normal reprocessing is supported. An explicitly adopted reviewed-transcript checkpoint can preserve an accepted human review for downstream regeneration, but it does not certify the historical audio or speaker-review steps against the new audio requirement. Adoption requires a backed-up maintenance process and an explicit decision to keep the reviewed transcript authoritative.

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
