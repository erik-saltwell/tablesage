# TableSage RPG

TableSage turns recordings of tabletop roleplaying sessions into transcripts, recaps, and a lasting campaign record. It is a terminal application for game masters.

![The TableSage Welcome screen, offering Campaigns, Players, Settings, and Advanced Help](docs/images/getting-started/landing-screen.png)

## What It Does

- **Transcribes and identifies speakers.** ElevenLabs Scribe transcribes Session audio. Local voice recognition matches speech to Players, leaving uncertain assignments for review.
- **Learns your Players' voices.** Each Player has a voice print built from short samples. A new Player's first samples are found in the recording itself, and you confirm them.
- **Keeps your world's vocabulary straight.** Each Campaign has a Glossary of names and terms that informs spelling corrections and generated documents.
- **Puts you in charge of the record.** You review names, glossary terms, spelling, and speaker assignments before TableSage generates the final Session outputs.
- **Generates session artifacts.** Saves reviewed transcripts attributed to Players and Roles, then uses your chosen language models to generate a canonical record of play, a short recap, and a player-ready session summary.
- **Prepares the next session.** Campaign-level tools build a "Previously On" recap and suggest ways to bring earlier campaign elements back into play.

## Get Started

You need:

- Python 3.12 or newer (uv can install it for you).
- [uv](https://docs.astral.sh/uv/) to install TableSage.
- Git.
- FFmpeg with both `ffmpeg` and `ffplay`.
- An [ElevenLabs](https://elevenlabs.io/) API key.
- An API key for at least one of OpenAI, Anthropic, or Google Gemini. The default model choices use both OpenAI and Anthropic; to use a single provider, change the models in Settings.

Install TableSage:

```sh
uv tool install git+https://github.com/erik-saltwell/tablesage.git
```

Choose or create a workspace directory for your campaign data, then start TableSage from it:

```sh
mkdir -p ~/Documents/tablesage
cd ~/Documents/tablesage
tablesage
```

On first launch, open **Settings** to enter your API keys, choose your models, and save your settings.

TableSage stores its data in the directory you launch it from, so start it from the same workspace each time. [Install TableSage](docs/getting-started/installation.md) covers every step, including Windows and API-key setup.

## Learn More

- [Install TableSage](docs/getting-started/installation.md)
- [Concepts](docs/concepts/index.md): Players and voice prints, Sessions and processing, Campaigns and Glossaries
- [Guides](docs/guides/index.md): task walkthroughs for setup, processing, exports, and campaign preparation
- [Screen Reference](docs/reference/screens/index.md): every screen, key, secondary action, and dialog, with screenshots
- [Privacy and Data Handling](docs/reference/privacy.md): what leaves your computer and what stays on it
- [Advanced Help](docs/guides/advanced-help.md): ask Claude Code, Codex, or Gemini CLI for help from your workspace
- [Troubleshooting FAQ](docs/reference/troubleshooting-faq.md): problems the other pages don't explain
- [Processing State and Freshness](docs/reference/processing-state-and-freshness.md): completion metadata, dependencies, and recovery limits

## License

[CC BY-NC 4.0](LICENSE).
