# Privacy and Data Handling

What TableSage sends to outside services, what stays on your computer, and where your keys and data live.

## What Leaves Your Computer

- **Session audio** is uploaded to [ElevenLabs](https://elevenlabs.io/) for transcription and speaker diarization during **Create Transcript**. Importing prepares the audio locally; creating or recreating the transcript uploads it.
- **Transcript text** is sent to your configured language-model providers — Anthropic, OpenAI, or Gemini — to propose corrections, extract glossary entries, find a new Player's lines, and generate session outputs.
- **Campaign context and preparation notes** are also sent to those providers as needed. This includes Player names, Roles, Glossary entries, campaign metadata, and generated records such as ledgers and scene breakdowns. **Create Previously On** and **Generate Opportunities** send campaign history and the notes you enter about the upcoming Session.

See [Models: High, Medium, and Low](../guides/settings.md#models-high-medium-and-low) for which model tier each action uses, and [Session Artifacts](../concepts/sessions.md#session-artifacts) for what each generated document contains.

Each of these services is a paid, third-party product with its own terms, pricing, and data-handling policy. Review those policies before sending recordings or transcripts that include your players, and before adding anyone who hasn't agreed to have their voice or words handled this way.

## What Stays Local

- **Audio cleaning** (noise removal) and **punctuation** run entirely on your computer using locally installed machine-learning models.
- **Voice matching**, which recognizes which Player is speaking by comparing audio to each Player's [voice print](../concepts/players.md#voice-prints), also runs locally. Player voice samples are never uploaded anywhere.
- Your session recordings, transcripts, and generated documents are stored as files in your workspace directory. TableSage connects directly to the processing providers; it does not operate a separate service that syncs your workspace.

## Local Model Downloads

When you save Settings, TableSage downloads any missing noise-removal, voice-embedding, and punctuation models from Hugging Face. These downloads do not send recordings, transcripts, or Player voice samples to Hugging Face. Once downloaded, the models process your audio locally. Their storage locations are listed below.

## API Keys

TableSage needs one key per external service you use: ElevenLabs, plus whichever of Anthropic, OpenAI, or Gemini your model settings select.

- Keys are stored once per user account, outside every workspace, so the same keys apply to every workspace on your machine. See [Where Keys Live](../guides/settings.md#where-keys-live) for exact file locations per platform.
- A key can instead be supplied through a shell environment variable (`ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`), which overrides the stored value for that service. See [How Shell Environment Variables Override Keys](../guides/settings.md#how-shell-environment-variables-override-keys).
- TableSage itself never transmits your keys anywhere except in authenticating directly with the corresponding provider's API.

## Files on Disk

Inside your workspace:

```text
.tablesage/
  tablesage.db      your campaigns, sessions, players, and glossaries
  settings.yaml     this workspace's settings
  logs/             application logs
campaigns/
  <campaign name>/<session number>/   session audio and generated documents
players/            player voice samples
checkpoints/        the noise-removal model, downloaded into the folder you launch from
```

Outside the workspace, per user account:

- Your `.env` credentials file (see [Where Keys Live](../guides/settings.md#where-keys-live)).
- `~/.cache/tablesage/`, holding the downloaded voice-embedding model.
- The standard Hugging Face cache (`~/.cache/huggingface/` unless you have set `HF_HOME`), holding the downloaded punctuation model.

TableSage does not sync these folders anywhere. The processing uploads described in [What Leaves Your Computer](#what-leaves-your-computer) are separate.

Deleting a workspace directory or a cache directory removes what it contains, but never your stored keys, which live in the separate per-user credentials file. Deleting a workspace also removes its `checkpoints/` folder, so TableSage downloads the noise-removal model again the next time you save settings in a new workspace.
