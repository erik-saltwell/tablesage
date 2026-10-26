# Ledger and Summary Prompt Harness

Run one prompt experiment at a time using the production generators, structured-output transport (including internal streaming where production enables it), validators, retries, and Summary composition. Experiment outputs are separate from canonical Session files. No model call occurs without `--execute`.

The prepared workspace is `/home/eriksalt/data/tablesage_summary_test`. **20260901** is the comparison Session; **20260825** supplies the frozen prior recap. Existing `2026-09-01-ledger-good.json` and `2026-09-01-summary-bad.md` are the user-selected baselines. The good Summary is also preserved as a review reference. No additional baseline generations are needed. Original good-Ledger timing and generation provenance are unknown; content baselines do not establish runtime baselines.

## Workspace Layout

```text
inputs/
  manifest.json
  ledger.json                 # routed transcript slices, attendees/Roles, Glossary
  summary.json                # exact supplied good Ledger plus metadata/roster/Glossary
  composition.json            # prior recap and current introductions
  sources/                    # byte-for-byte source/reference copies
prompts/
  ledger/candidate/{system.md,template.j2}
  summary/candidate/{system.md,template.j2}
  ledger/ledger-<UTC-start>/   # complete immutable per-run bundle
  summary/summary-<UTC-start>/
output/
  ledger-<UTC-start>/
  summary-<UTC-start>/
```

A start datetime is captured once, with UTC and microseconds, before application imports. The same stem pairs the prompt bundle and output directory. Every retry stores its own rendered system/user messages and raw response. Ledger calls also preserve the structured response schema. A prompt bundle is saved before transport starts, including for failed calls.

Inputs are sealed with file hashes and checked on every run. Preparation refuses to overwrite an existing `inputs` directory. Changes require a separate input snapshot, selected with `--inputs`; they must not silently replace an earlier comparison's inputs. Editable candidates are separate from archived run bundles. Changing Ledger prompts or generating experimental Ledgers never replaces Summary's fixed good-Ledger input.

## Prepare Once

The real workspace has already been prepared. For a new workspace, close processing and run:

```sh
uv run python scripts/prompt_experiment.py --workspace /path/to/workspace prepare \
  --current CURRENT_SESSION_UUID --prior PRIOR_SESSION_UUID \
  --good-ledger /path/to/good-ledger.json \
  --bad-summary /path/to/bad-summary.md \
  --good-summary /path/to/good-summary.md
```

The good Summary is optional. Preparation validates transcript-section routing against the exact Role Transcript bytes, good-Ledger schema and Session name, introductions ownership/attendance, earlier recap selection, and composition. It records source paths and hashes. Schema checks do not certify narrative accuracy. A reference Ledger may retain its original workspace's Session UUID; its exact bytes are preserved rather than rewritten.

## Render Before Calling a Model

Edit `prompts/ledger/candidate/system.md` or `prompts/summary/candidate/system.md` and, where appropriate, `template.j2`. Both default to the current packaged prompts at preparation time. Alternatively, pass `--prompt-dir /path/to/candidate` containing those two files. Historical prompts must remain compatible with the current input variables and output contract; the harness does not silently translate old schemas.

```sh
uv run python scripts/prompt_experiment.py --workspace /home/eriksalt/data/tablesage_summary_test run ledger
uv run python scripts/prompt_experiment.py --workspace /home/eriksalt/data/tablesage_summary_test run summary
```

These commands archive and render the first attempt without calling a provider. The run is marked `prepared`, not successful generation.

## Generate One Result

```sh
uv run python scripts/prompt_experiment.py --workspace /home/eriksalt/data/tablesage_summary_test run ledger --execute
uv run python scripts/prompt_experiment.py --workspace /home/eriksalt/data/tablesage_summary_test run summary --execute
```

Model and timeout default to settings captured during preparation. Explicit overrides are available with `--model` and `--timeout`. Supported nonsecret controls use `--options '{"temperature": 0.2}'`: temperature, top_p, max_tokens, reasoning_effort, and seed. Only pass options supported by the chosen provider/model. Keep controls identical across a comparison. Production may apply model-specific defaults, such as Astra's medium reasoning when omitted; shared transport code hashes preserve the implementation of those defaults. Credentials use the application's personal credential loader; no credentials are archived.

One invocation yields one result, including normal production retries: at most three attempts. Ledger structural failures retry with validation feedback and the rejected candidate. Question-attendee warnings retain production's candidate selection. Summary marker failures retry. Provider errors terminate the run; failures retain completed attempts and the record. Repetitions use separate invocations, rather than mandatory two-run/four-candidate batches.

## Inspect Evidence

`output/<type>-<UTC-start>/run.json` records mode, model/options/timeout, exact input hashes, prompt provenance, source revision, dirty checkout indicator, relevant source-file hashes, all attempt timings/validation results, selected attempt, total elapsed time, and completion/failure status. Prompt and output directories are independently sealed. Raw responses are retained even when validation fails. Hard process termination can leave a record marked `running`; it never establishes success.

Ledger runs produce the joint response, `<type>-<UTC-start>.json` and `.md` for the Ledger, and Scene Breakdown content. Summary runs retain the raw template and composed `<type>-<UTC-start>.md`. Summary word counts distinguish generated body, inserted recap, inserted introductions, and complete output. Counts and schema validity support review; they are not quality scores. Token usage/cost are unavailable through the shared text-only interface. Dry-run/offline timings are not provider-efficiency evidence.

Offline verification can use `--response-file /path/to/response` instead of `--execute`. Ledger replay requires the joint response shape (`starting_situation`, `ledger`, `scene_breakdown`), not a persisted Ledger file. Summary replay requires both composition markers. These runs are explicitly marked `offline`; an invalid fixture repeats through the same production validation path.

The older [Session Summary Experiment](summary_experiment.md) utility remains available for its historical snapshots and blind-packet workflow. Its fixed repetition/packet requirements are not used by this harness.
