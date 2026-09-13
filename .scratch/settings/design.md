# TableSage Settings and Personal Credentials

Status: implemented in the working tree. This document records the agreed design
and the implementation choices made for its open details.

This design makes the TUI the supported interface for configuring TableSage. Users can enter personal API keys and edit all workspace processing settings without locating or editing configuration files themselves.

## Ownership and storage

A **workspace** is the directory from which TableSage is launched and the `.tablesage/` state it contains. Settings apply to all Campaigns and Sessions in that workspace, not to an individual Campaign.

| Configuration | Storage | Scope |
| --- | --- | --- |
| Processing and model settings | `<launch directory>/.tablesage/settings.yaml` | Current workspace |
| Named API credentials | `.env` inside the OS-standard TableSage user configuration directory, resolved with `platformdirs` | All workspaces for that OS user |
| Exported environment variables | Inherited process environment | Override stored credentials for that invocation |

On Linux, the normal user credential path is `~/.config/tablesage/.env`; other platforms use their standard user configuration locations. Neither file lives beside the installed application. There is no global `settings.yaml` layer and no stored workspace credential layer.

Global-only stored credentials are a deliberate simplification. The Settings screen has no local/global selector, workspace-key removal rules, or local/global override hierarchy. An exported shell variable remains the advanced way to use a different key for a particular launch.

The application will stop loading `<launch directory>/.env`. There is no automatic migration, legacy fallback, or migration banner; the user will handle migration manually.

## Settings entry and mandatory review

Add `[S] Settings` to the landing page. The same screen is reachable from a missing-credential workflow dialog.

Settings must be reviewed on first use of a workspace and when an upgrade requires a settings-schema review:

- Store an explicit `settings_version` in `settings.yaml`, independent of the application release version.
- Until review is completed, users cannot proceed from the landing page into ordinary application work; Settings is the available setup route.
- On first use or a required schema review, remain on the landing page and show
  a toast explaining that settings must be configured and saved before progressing.
  Pressing S opens Settings with defaults prefilled where needed.
- On a required upgrade review, show newly introduced fields prefilled with recommended defaults. One successful Save acknowledges the review and unlocks normal navigation; individual confirmations or changed-from-default values are unnecessary.
- Credentials are optional for completing setup. Users may save valid settings without configuring any provider.

Malformed YAML or settings that fail validation retain the terminal-error/manual-repair behavior. Do not add an automatic reset, backup, or TUI repair flow for such files. A settings-version review is distinct from repairing an invalid file.

## Settings editor scope

Updated decision: the editor exposes exactly two sections, **LLM** and **Keys**.
LLM presents three model roles — High, Medium, and Low — as selectors. Each selector
always offers the same common model catalog and `Custom…`; selecting Custom opens a
model-ID dialog. A saved custom ID remains visible as that selector's current value.
Keys manages the four named provider credentials. Other processing
settings remain in `settings.yaml` and are preserved when saving or resetting
LLM settings. The global reset of workspace processing settings is no longer exposed.

This supersedes the earlier full-editor scope and all-section reset requirements
recorded below. Draft validation, unsaved-change protection, credential behavior,
and mandatory settings review remain applicable.

### Earlier full-editor scope (superseded)

The TUI edits all workspace behavior settings, including nested processing options and the three LLM model roles. The existing schema is the field inventory; do not limit the implementation to the commonly used fields.

Use labeled, collapsible sections reflecting the YAML structure, with commonly changed sections initially expanded. The agreed groupings include Audio, Transcription & Diarization, Speaker Identification, Voice Enhancement, Backchannel Removal, and LLM Models. Include outlier cleanup and other current fields as well; the final placement of each field is an implementation detail.

Each field provides a short plain-language explanation and its default value beneath the input. A `?` help view provides longer explanations and examples where useful. This UI guidance replaces YAML comments as the supported documentation surface.

Editing and saving rules:

- Edits form a draft. Save validates the entire form and reports field-specific errors. Invalid drafts leave the existing file untouched; do not partially save valid fields.
- A successful Save writes canonical, validated YAML. Preserving comments or hand formatting in `settings.yaml` is not required.
- Saved settings apply immediately to subsequent actions. A job already running keeps its existing settings.
- Leaving with unsaved changes offers Save, Discard, and Cancel.
- Each section has Reset to defaults. A separate Reset all workspace settings action requires confirmation.
- The TUI is the sole supported settings editor. No file watching or external-change conflict-detection flow is required.

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
- Show a shell-provided credential as read-only and identify its source. A user may still save a global value, but explain that it will not become effective until the shell override is unset.
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
`openai/gpt-6-astra`, `openai/gpt-5.6-sol`, `openai/gpt-5.6-terra`,
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

As part of implementing this feature, remove the current generic advice to back up the entire `.tablesage/` directory. Workspace export/import and its treatment of credentials will be designed later; this document sets no export or backup policy.

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
- [TUI screen conventions](../../.documentation/tablesage_tui_screens.md): existing landing navigation and interaction conventions. The draft-and-Save Settings editor is an explicit new behavior alongside existing inline metadata editors.
- [Startup composition root](../../apps/tablesage-tui/src/tablesage_tui/screens/main_app.py): loads personal credentials and workspace settings, then applies the review gate.
- [Configuration service](../../packages/tablesage-application/src/tablesage_application/configuration.py): credential ownership and atomic settings persistence.
- [Settings screen](../../apps/tablesage-tui/src/tablesage_tui/screens/settings.py): complete editor and credential controls.
- [Settings path helper](../../packages/tablesage-model/src/tablesage_model/_paths.py) and [settings loader](../../packages/tablesage-model/src/tablesage_model/setup/settings.py): current workspace path, first-run default deployment, and validation.
- [Settings schema](../../packages/tablesage-model/src/tablesage_model/settings/app_settings.py) and [packaged YAML defaults](../../apps/tablesage-tui/src/tablesage_tui/resources/settings.yaml): field inventory, defaults, constraints, and explanatory material for UI help.
- [LLM adapter](../../packages/tablesage-tools/src/tablesage_tools/llm/client.py) and [ElevenLabs adapter](../../packages/tablesage-tools/src/tablesage_tools/transcription/elevenlabs.py): current provider call boundaries.

Preserve the repository's settings boundary during implementation: `Application` receives loaded settings, and calls into `tablesage-tools` receive plain parameter values rather than `AppSettings` objects.
