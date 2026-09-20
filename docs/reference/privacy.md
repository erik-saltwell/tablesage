# Privacy and data handling

What TableSage sends to outside services, what stays on your computer, and
where your keys and data live.

## What leaves your computer

- **Session audio** is uploaded to [ElevenLabs](https://elevenlabs.io/) for
  transcription and speaker diarization. This happens every time you import
  a recording.
- **Transcript text** is sent to whichever language-model provider your
  current High, Medium, or Low model uses — Anthropic, OpenAI, or Gemini —
  when TableSage reviews a transcript, extracts glossary entries, identifies
  speakers, or generates recaps, summaries, and other campaign documents. See
  [update your settings](../guides/settings.md#models-high-medium-and-low)
  for exactly which action uses which tier, and
  [session artifacts](../concepts/session-artifacts.md) for what each
  generated document actually is.

Each of these services is a paid, third-party product with its own terms,
pricing, and data-handling policy. Review those policies before sending
recordings or transcripts that include your players, and before adding
anyone who hasn't agreed to have their voice or words handled this way.

## What stays local

- **Audio cleaning** (noise removal and punctuation) runs entirely on your
  computer using locally installed machine-learning models.
- **Voice matching**, which recognizes which player is speaking by comparing
  audio to each player's [centroid](../concepts/centroid.md), also runs
  locally. Player voice samples are never uploaded anywhere.
- Your session recordings, transcripts, and generated documents are stored as
  files in your workspace directory. Nothing is synced to a TableSage-run
  service, because there isn't one — TableSage only talks to the providers
  above, directly from your machine.

## API keys

TableSage needs one key per external service you use: ElevenLabs, plus
whichever of Anthropic, OpenAI, or Gemini your model settings select.

- Keys are stored once per user account, outside every workspace, so the
  same keys apply to every campaign you keep on your machine. See
  [where keys live](../guides/settings.md#where-keys-live) for exact file
  locations per platform.
- A key can instead be supplied through a shell environment variable
  (`ELEVENLABS_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `GEMINI_API_KEY`), which overrides the stored value for that service. See
  [how shell environment variables override
  keys](../guides/settings.md#how-shell-environment-variables-override-keys).
- TableSage itself never transmits your keys anywhere except in
  authenticating directly with the corresponding provider's API.

## Files on disk

Inside your workspace:

```text
.tablesage/
  tablesage.db      your campaigns, sessions, and generated results
  settings.yaml     this workspace's settings
  logs/             application logs
campaigns/
  <campaign name>/<session number>/   session audio and generated documents
players/            player voice samples
```

Outside the workspace, per user account:

- Your `.env` credentials file (see above).
- `~/.cache/tablesage/`, the standard Hugging Face cache directory, holding
  downloaded local machine-learning models.

None of this is uploaded or synced by TableSage. Deleting a workspace
directory or the cache directory removes what it contains; it does not touch
your stored keys, which live in the separate per-user credentials file.
