# Utility scripts

This directory contains small, standalone Python utilities for development, maintenance, and one-off TableSage tasks.

Keep each utility in a single `.py` file when practical. Scripts should:

- run from the repository root with `uv run python scripts/<name>.py`;
- include a module docstring with purpose and usage examples;
- use `argparse` for command-line arguments;
- avoid becoming application code imported by production packages.

## Documentation sample data

`seed_docs_data.py --cwd .for-docs` populates an initialized, empty documentation deployment with fictional players and campaigns. Run it with a Python environment containing TableSage. It uses `seed_sample_data.py` for the basic entities and adds three complete Iron Pact sessions with transcripts, Ledgers, scenes, introductions, recaps, and summaries. All outputs are authored fixtures; the WAV files contain silence, and no provider calls or real voice prints are involved.

The script backs up the empty database before seeding, refuses existing user data, and verifies a marked fixture on subsequent runs without overwriting edits. Textual MCP launch instructions for the seeded deployment are kept in the git-ignored `.for-docs/session-processing/README.md`.

## Diagnostic Workspace Validation

`setup_diagnostic_workspaces.py` creates four separate offline workspaces, each containing one Campaign and one processed Session. It reuses the authored documentation fixtures and the application's completion helpers, then checks the cases with the existing freshness evaluator. Audio is silence, outputs are synthetic, and no real voice prints, provider calls, or model downloads are involved. Setup selects bundled LLM metadata to avoid an import-time pricing-map fetch.

The script requires a new output directory outside the checkout and outside any existing TableSage workspace. It refuses an existing destination rather than deleting or overwriting data. To repeat validation, create a new parent directory; retain old workspaces and transcripts for comparison. A failed setup may leave a partial disposable directory; use a fresh destination rather than diagnosing that partial fixture.

### Set Up an Installed App and the Cases

Run these steps in the repository checkout. `uv` selects Python, so no existing virtual environment or shell command named `python` is required. Build a wheel so the diagnosing agent uses packaged public docs and application data rather than an editable source checkout. Installing Python or dependencies may use the network; the fixture script itself runs offline. On a machine with cached dependencies, add `--offline` to the install command.

```sh
cd /path/to/tablesage
mkdir -p "${XDG_CACHE_HOME:-$HOME/.cache}/tablesage-diagnostics"
DIAGNOSTIC_RUN=$(mktemp -d "${XDG_CACHE_HOME:-$HOME/.cache}/tablesage-diagnostics/run.XXXXXX")
uv build --wheel --out-dir "$DIAGNOSTIC_RUN/dist"
uv venv --python 3.12 "$DIAGNOSTIC_RUN/app"
uv pip install --python "$DIAGNOSTIC_RUN/app/bin/python" "$DIAGNOSTIC_RUN"/dist/tablesage_rpg-*.whl
"$DIAGNOSTIC_RUN/app/bin/python" scripts/setup_diagnostic_workspaces.py --output "$DIAGNOSTIC_RUN/cases" > "$DIAGNOSTIC_RUN/setup-results.txt"
```

The script should exit successfully and create `case-01` through `case-04`. Run `printf '%s\n' "$DIAGNOSTIC_RUN"` and retain the printed path. The app and cases live in your user cache, so they do not depend on temporary verification environments under `/tmp`. In a new terminal, set `DIAGNOSTIC_RUN` to that saved path before following the next steps. Keep `setup-results.txt` for reviewing the evaluator's results; do not give it, this README, the script, or work-item documents to the diagnosing agent. These shell examples use the Unix virtual-environment layout.

### Run a Fresh Conversation in Each Workspace

1. Activate the installed environment: `source "$DIAGNOSTIC_RUN/app/bin/activate"`.
2. Enter the first case: `cd "$DIAGNOSTIC_RUN/cases/case-01"`.
3. Run `tablesage report-help-topics` yourself to confirm that the installed command returns output and exits. There is no need to launch the TUI.
4. Start a new agent conversation from that directory. Use a fresh session with no source checkout, implementation discussion, or other case's conversation in context. Its workspace instructions point to the installed public help topics. Keep its access focused on this workspace and the installed app; do not launch it from the parent directory or link the source checkout.
5. Ask exactly the same neutral question in every case:

   > Can you check whether this Session's outputs are current? Explain your findings and any action I should take.

6. Let it inspect the installed public docs and read-only workspace evidence. It should not launch the TUI, modify files or database records, inspect application source, or print Session narrative content. Do not tell it the planted fault or correct its diagnosis during the initial walkthrough.
7. Save the full conversation, including commands, tool outputs, errors, and final explanation, outside the case workspace. Label the transcript with the case directory and installed application version, and share it for validation and debugging.
8. Repeat steps 2–7 for `case-02`, `case-03`, and `case-04`, starting a fresh conversation each time. Keep the installed environment active so both `tablesage` and the Python used for metadata inspection refer to the same installation.

### Review the Findings after the Conversations

Keep this case mapping out of the diagnosing agent's context:

| Workspace | Arranged State | What the Diagnosis Should Establish |
|---|---|---|
| `case-01` | Current baseline | Outputs are current; no processing repair is needed. |
| `case-02` | Normalized review audio missing, review fingerprints retained | Import Audio lacks a required output and is stale; dependent work is stale. |
| `case-03` | Audio present, normalized-audio fingerprints removed from both review records | Import Audio is current, but speaker and transcript reviews lack a required recorded input; dependent work is stale. |
| `case-04` | Both faults | Both the missing required output and independent missing review fingerprints must be identified; restoring the WAV alone is insufficient. |

Freshness is being verified, not transcript accuracy or audio quality. The synthetic baseline is unsuitable for real transcription, speaker recognition, or assessing narrative output. Do not run paid recovery pipelines on these fixtures to validate diagnosis. Recovery guidance should cite supported app actions and disclose the absence of a targeted migration that preserves old reviews. Implementing such migration support is separate work.

## Transcript-section review

`review_transcript_sections.py` asks Astra (`openai/gpt-6-astra`) and Fable 5.1 (`anthropic/claude-fable-5-1`) for independent high-reasoning reviews of an existing `transcript_sections.json`, then sends both reviews to Astra with high reasoning for final adjudication. It prints all three responses and saves only the final response into the session folder.

```bash
uv run python scripts/review_transcript_sections.py "Campaign Name" "Session Name" /path/to/role_transcript_prefix.json
```

The supplied transcript is used as-is. It must preserve the original utterance indices and contain enough of the opening to support the ranges and active-play boundary under review.

The current script's printed Sol/Fable juror labels are historical and do not match all model selections. It validates the complete recommendation's bounds/version/hash but does not require every explanatory value-review entry. The former review-utility guide is retained only in the local archive. Calls use provider credentials and incur usage; the canonical sections file is never overwritten.
