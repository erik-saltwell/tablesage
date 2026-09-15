# TableSage Settings and Personal Credentials

Status: implemented in the working tree. This document records the agreed design
and the implementation choices made for its open details.

This design makes the TUI the supported interface for configuring TableSage. Users can enter personal API keys and choose the three LLM models in the TUI. Other processing settings remain configurable in the deployed YAML; this screen preserves them but does not expose or reset them.

## Ownership and storage

A **workspace** is the directory from which TableSage is launched and the `.tablesage/` state it contains. Settings apply to all Campaigns and Sessions in that workspace, not to an individual Campaign.

| Configuration | Storage | Scope |
| --- | --- | --- |
| Processing and model settings | `<launch directory>/.tablesage/settings.yaml` | Current workspace |
| Named API credentials | `.env` inside the OS-standard TableSage user configuration directory, resolved with `platformdirs` | All workspaces for that OS user |
| Exported environment variables | Inherited process environment | Override stored credentials for that invocation |

On Linux, the normal user credential path is `~/.config/tablesage/.env`; other platforms use their standard user configuration locations. Neither file lives beside the installed application. There is no global `settings.yaml` layer and no stored workspace credential layer.

Global-only stored credentials are a deliberate simplification. The Settings screen has no local/global selector, workspace-key removal rules, or local/global override hierarchy. An exported shell variable remains the advanced way to use a different key for a particular launch.

The application does not load `<launch directory>/.env`. There is no automatic migration, legacy fallback, or migration banner; the user will handle migration manually.

## Settings entry and mandatory review

`[S] Settings` is available on the landing page. The same screen is reachable from a missing-credential workflow dialog.

Settings must be reviewed on first use of a workspace and when an upgrade requires a settings-schema review:

- Store an explicit `settings_version` in `settings.yaml`, independent of the application release version.
- Until review is completed, users cannot proceed from the landing page into ordinary application work; Settings is the available setup route.
- On first use or a required schema review, remain on the landing page and show
  a toast explaining that settings must be configured and saved before progressing.
  Pressing S opens Settings with defaults prefilled where needed.
- On a required upgrade review, load defaults for missing fields and show the supported model/key editor; non-exposed processing fields remain in the settings snapshot. One successful Save acknowledges the review and unlocks normal navigation; individual confirmations or changed-from-default values are unnecessary.
- Credentials are optional for completing setup. Users may save valid settings without configuring any provider.

Malformed YAML or settings that fail validation retain the terminal-error/manual-repair behavior. Do not add an automatic reset, backup, or TUI repair flow for such files. A settings-version review is distinct from repairing an invalid file.

## Settings editor scope

The editor exposes exactly two sections, **LLM** and **Keys**.
LLM presents three model roles — High, Medium, and Low — as selectors. Each selector
always offers the same common model catalog and `Custom…`; selecting Custom opens a
model-ID dialog. A saved custom ID remains visible as that selector's current value.
Keys manages the four named provider credentials. Other processing
settings remain in `settings.yaml` and are preserved when saving or resetting
LLM settings. The global reset of workspace processing settings is no longer exposed.

The earlier proposal for a full processing-settings editor was narrowed to model/key controls. The deployed YAML and schema remain the reference for other processing options; no all-section reset or universal help screen is exposed.

### Draft and Save behavior

- Save validates the visible draft merged into the complete settings snapshot; invalid values do not partially update the settings file.
- A successful Save writes canonical YAML, without preserving its comments or formatting.
- Saved settings apply to subsequent actions. An already running job retains its snapshot.
- Dirty exit offers Save, Discard and Cancel.
- LLM reset affects the model choices, not hidden processing fields.
- There is no file watcher or external-edit conflict-resolution UI.

## Named credentials

Always display these four providers, whether or not the workspace currently uses them:

| Service | Stored variable | Use |
| --- | --- | --- |
| ElevenLabs | `ELEVENLABS_API_KEY` | Transcription |
| Anthropic | `ANTHROPIC_API_KEY` | LLM calls |
| OpenAI | `OPENAI_API_KEY` | LLM calls |
| Gemini | `GEMINI_API_KEY` | LLM calls |

Each provider occupies one terminal line: name and password input. ElevenLabs is labeled `ElevenLabs (transcription)`; shell overrides are identified in input tooltips. One blank line separates Gemini from the LLM divider, and test results use notifications. Stored keys use a fixed-length placeholder mask, never the actual secret or a suffix. Typing replaces a key; an untouched empty input preserves it. Ctrl-D stages removal of the focused stored key; Ctrl-T tests the focused provider after edits have been saved. Save commits both model and credential drafts; Discard discards both.

Credential handling rules:

- Exported shell variables take precedence over the global credential file.
- Identify a shell-provided credential in the input tooltip. The inherited value itself is not edited by this screen, but the stored-key input remains editable: a user may save a personal value that will not become effective until the shell override is unset.
- Credential changes, including removals, take effect only on Save for subsequent calls. Removing a stored key does not unset an inherited shell value.
- Store credentials in plaintext `.env` format. Do not implement permission enforcement or permission-mode warnings. The editing screen must explain that keys are stored in plaintext and should not be committed or shared.
- Modify only the four managed variables. Preserve comments and unrelated variables in the credential file. This preservation rule applies to `.env`, even though `settings.yaml` is rewritten canonically.
- Never require a successful network test before saving; offline setup must work.

In the current implementation, the ElevenLabs adapter explicitly reads its environment variable. LLM calls pass the selected model to LiteLLM, which resolves provider authentication. This includes medium, low, and high model roles; `llm_model_lite` is the stored low-model role, not the name of the LiteLLM library. Credential updates must retain the distinction between inherited shell values and values loaded by TableSage.

## Supported models

Support exactly Anthropic, OpenAI, and Gemini as LLM providers in this version. ElevenLabs is separately supported for transcription.

Users may select any of the three LLM providers for each role:

- `llm_model`: medium work.
- `llm_model_lite`: low-cost work.
- `llm_model_high`: demanding generation work.

Ship the same curated catalog for every role, displaying the exact saved IDs:
`anthropic/claude-fable-5-1`, `openai/gpt-6-astra`, `openai/gpt-5.6-sol`, `openai/gpt-5.6-terra`,
`anthropic/claude-sonnet-4-5`, `anthropic/claude-opus-4-5`,
`anthropic/claude-haiku-4-5`, `gemini/gemini-2.5-pro`, and
`gemini/gemini-2.5-flash`, plus Custom. Custom opens a model-ID dialog and the
chosen ID remains visible as the current selector value. Every selector label
adds a readable company prefix (for example, `OpenAI: openai/gpt-5.6-sol`) while
the value saved to `settings.yaml` remains the model ID. Restrict custom IDs to
the three supported provider prefixes on Save. Other providers, including
OpenRouter and Groq, are unsupported even if LiteLLM can use them. Do not fetch
model catalogs when Settings opens.

## Testing credentials and recovering from missing keys

Test connection is an explicit per-provider action after saving. Display useful distinctions between success, authentication failures, quota failures, and network errors.

For LLM providers, testing checks the model selected for each role using that provider with a minimal request. This validates the configured models as well as authentication; these requests can incur small usage charges.

If a workflow needs a provider key that is absent, show a blocking dialog naming the provider and model, with Open Settings and Cancel actions. Do not merely disable the workflow shortcut or depend on a generic error toast. Missing credentials do not prevent unrelated application use or initial setup completion.

## Documentation changes and deferred details

Campaign and player ZIP import/export are implemented separately. They are not a complete workspace/settings/credential backup policy. Personal credentials live outside the workspace and should not be committed or shared; this feature does not add full-workspace export or automatic credential migration.

Implementation choices for details left open in the discussion:

- The bundled catalog v1 keeps existing default model IDs and adds Gemini 2.5
  Flash and Pro, listed in the [Google model catalog](https://ai.google.dev/gemini-api/docs/models).
  Catalog updates ship with the app; supported custom IDs remain available.
- ElevenLabs testing reads the account endpoint without uploading audio. An
  unused LLM provider asks the user to select and save a model before testing.
- Tests use saved settings and test identical model IDs once per provider.
- Credential edits share the explicit Save/Discard lifecycle with the workspace behavior draft, although they remain stored in a separate personal file.
- Existing unversioned settings have version zero and require review. A schema
  version newer than the app is rejected. Invalid files still require manual
  repair. Future field renames/removals need an explicit migration decision when
  introduced; this release establishes version one.

## Current implementation references

These references identify the implementation and its supporting architecture.

- [System architecture](../../.documentation/system_architecture.md): package responsibilities, current startup loading, and settings injection into `Application`.
- [TUI screen conventions](../../.documentation/tablesage_tui_screens.md): existing landing navigation and interaction conventions. The draft-and-Save Settings editor is a distinct behavior alongside existing inline metadata editors.
- [Startup composition root](../../apps/tablesage-tui/src/tablesage_tui/screens/main_app.py): loads personal credentials and workspace settings, then applies the review gate.
- [Configuration service](../../packages/tablesage-application/src/tablesage_application/configuration.py): credential ownership and atomic settings persistence.
- [Settings screen](../../apps/tablesage-tui/src/tablesage_tui/screens/settings.py): supported model editor and credential controls.
- [Settings path helper](../../packages/tablesage-model/src/tablesage_model/_paths.py) and [settings loader](../../packages/tablesage-model/src/tablesage_model/setup/settings.py): current workspace path, first-run default deployment, and validation.
- [Settings schema](../../packages/tablesage-model/src/tablesage_model/settings/app_settings.py) and [packaged YAML defaults](../../apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml): field inventory, defaults, constraints, and explanatory material for UI help.
- [LLM adapter](../../packages/tablesage-tools/src/tablesage_tools/llm/client.py) and [ElevenLabs adapter](../../packages/tablesage-tools/src/tablesage_tools/transcription/elevenlabs.py): current provider call boundaries.

Preserve the repository's settings boundary during implementation: `Application` receives loaded settings, and calls into `tablesage-tools` receive plain parameter values rather than `AppSettings` objects.
