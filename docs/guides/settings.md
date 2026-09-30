# Update Your Settings

Set up the service API keys and three language-model choices TableSage needs before it can process Sessions, then save and check them. See [Install TableSage](../getting-started/installation.md) for getting here the first time, and [Privacy and Data Handling](../reference/privacy.md) for what TableSage sends to which service.

Open Settings from the Welcome screen by pressing **S**. If a step needs a key you haven't set, TableSage also offers an **Open Settings** button.

For the usual setup, enter an ElevenLabs key, choose all three language models, and supply keys for the providers those models use. Then choose **Continue** to save and check the configuration. If you are moving to another workspace or computer, read [Move a Campaign to Another Workspace](move-campaign-workspace.md) for which configuration needs setting up again.

![The Settings screen, showing the Keys and LLM sections](../images/settings/settings-screen.png)

## Keys

The **Keys** section has one row per service: **ElevenLabs**, **Anthropic**, **OpenAI**, and **Gemini**. A row shows dots when a key is present, whether you typed it or it came from your shell (see below). Click a row and type to set or replace that key.

You only need keys for actively configured services, plus ElevenLabs:

- **ElevenLabs** is always required; it performs transcription and speaker diarization for every Session you import.
- **Anthropic**, **OpenAI**, and **Gemini** are only required for the providers named in your High, Medium, and Low model IDs, described below.

To remove a key, click its **Delete Key** button, or press **Tab** from its field to that button and press **D** or **Enter**. Removal takes effect on **Continue**. A key supplied by your shell environment can't be removed here; see below.

### Where Keys Live

Keys are not part of the workspace. They are stored once per user account, in a small file outside any workspace directory.

- Linux: `~/.config/tablesage/.env`
- macOS: `~/Library/Application Support/tablesage/.env`
- Windows: `%LOCALAPPDATA%\tablesage\.env`

This means you configure keys once, not once per campaign workspace. It also means removing a workspace directory never deletes your keys, and a key mistake affects every workspace until you fix it.

### How Shell Environment Variables Override Keys

Before TableSage reads its stored keys, it checks your environment variables for `ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, and `GEMINI_API_KEY`. These environment variables take precedence, and will override keys set at the locations above. In that case:

- The key field shows dots but is disabled, and its tooltip says the key is provided by your shell environment and overrides the stored one.
- The field is not editable.
- **Delete Key** cannot remove it, since there is nothing stored to remove; the environment variable stays active until you change your shell.

This is useful for CI, shared machines, or keeping a key out of the on-disk `.env` file entirely.

## Models: High, Medium, and Low

Settings asks for three model IDs, each handling a different weight of work.

| Model | Default | Used for |
|---|---|---|
| **High** | `openai/gpt-6-astra` | Writing a Session's outputs from its transcript and creating campaign-wide material |
| **Medium** | `anthropic/claude-sonnet-4-5` | Helping you review transcripts, build Glossaries, and find new Players' lines |
| **Low** | `anthropic/claude-haiku-4-5` | Short, high-volume checks while audio is imported |

Each field is a dropdown of bundled presets across Anthropic, OpenAI, and Gemini, plus **Custom…** if you want a different model from one of those three providers. A custom ID must take the form `provider/model-name`, where `provider` is exactly `anthropic`, `openai`, or `gemini`. Other providers are not supported at this time.

![The High model dropdown open, showing preset choices and Custom…](../images/settings/model-select.png)

### What Each Tier Actually Does

**High model.** Use your most capable model here. It does the long reading and writing that produces what you keep from each Session — see [Session Artifacts](../concepts/sessions.md#session-artifacts) for what each generated document actually is:

- **Process Session → Generate Artifacts**: the model reads the role transcript and writes the transcript sections, ledger and scene breakdown, player introductions, recap summary, and session summary.
- **Regenerate Artifact** and **Regenerate All Outputs**: the same generation, run on demand.
- **Create Previously On**: the model generates the recap.
- **Generate Opportunities**: the model generates opportunities.

These are the longest and most expensive calls TableSage makes.

**Medium model.** Handles moderate tasks where you check the result:

- **Process Session → Spellcheck Against Glossary**: The model proposes corrections based on the [campaign glossary](../concepts/campaigns.md#glossary).
- **Process Session → Extract Glossary Terms** and Session Detail's **Extract Glossary**: the model proposes new glossary entries based on the transcript.
- **Process Session → Review Name Corrections**: when a Session has Players without voice samples, the model proposes corrections for misheard Player and character names, which you review before they are applied.
- **Process Session → Isolate New Speakers**: for those same Players, the model reads the whole transcript and picks the lines each one most likely spoke; you confirm them in Review New Speaker Assignments.

**Low model.** Handles operations where a fast, inexpensive model is enough.

- **Process Session → Remove Bad Utterances**: after transcribing, the model removes brief listener acknowledgments that add no independent meaning. Short replies that convey meaningful information remain; see [Remove Bad Utterances](../concepts/session-processing-returning-players.md#remove-bad-utterances) for where this fits in processing.

## Saving

Choose **Continue**, or move focus out of an editable key field and press **C**, to save. Saving:

1. Validates every model ID and writes your settings and any key changes to disk.
2. Sends a very short test message to each of your three configured models, using your saved keys.
3. If every model responds, downloads any local audio-processing models that are not already installed (noise removal, voice embeddings, and punctuation). This may take a while the first time, since some voice models install locally; once they are installed, this step finishes immediately on later saves.

If a model test fails, Settings stays open and shows which model failed and why. Your settings are still saved even though the check failed, so correct the key or model ID and save again. The ElevenLabs key is not tested here — it is first exercised when you import session audio.

Leaving Settings with unsaved changes prompts you to save or discard them.

## Continue After a Successful Save

You are ready when the model checks and required local-model downloads finish successfully. Return to [Start a Campaign](start-a-campaign.md) for first-time setup, or reopen your Session's Process screen and choose **Continue** to retry work that stopped for missing credentials. If a key field is read-only, change its shell environment variable as described above rather than trying to replace it in Settings.
