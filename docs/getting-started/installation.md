# Install TableSage

This page installs TableSage and gets you to a working first launch.

## Before You Begin

You need:

- A computer with a terminal and an internet connection.
- About 10 GB of free disk space to start, plus room for recordings and voice samples.
- An [ElevenLabs](https://elevenlabs.io/) API key, for transcription and speaker diarization.
- An API key for at least one language-model provider. TableSage supports OpenAI, Anthropic, and Google Gemini, and nothing else. The default model choices use OpenAI and Anthropic, but you can change this after installing the application.

Plan for these approximate storage needs:

| Material | Size |
|---|---|
| TableSage and its machine-learning libraries | 8 GB (less on macOS) |
| Downloaded models | 0.5 GB |
| Each Session's audio | 230 MB per hour of recording |
| Each Player's voice samples | Tens to a few hundred megabytes |

You will install **uv** to manage Python and install TableSage, **Git** to fetch its source, and **FFmpeg** to read and play audio.

## Install uv

[uv](https://docs.astral.sh/uv/) is the tool that installs and runs TableSage. It also downloads and manages the Python version TableSage needs, so you do not have to install Python separately first.

On macOS or Linux:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal afterward, then confirm uv is available:

```sh
uv --version
```

If the installer offers to add uv to your `PATH`, accept. If `uv --version` still fails after restarting the terminal, follow the `PATH` instructions the installer printed.

### Optional: Download Python Ahead of Time

TableSage requires Python 3.12 or newer. uv uses a suitable existing installation or downloads one when you install TableSage.

To download Python 3.12 ahead of time, run:

```sh
uv python install 3.12
```

By default, this adds a versioned Python executable and leaves your shell's `python` command unchanged. Other uv-managed applications can share that Python, while TableSage's dependencies stay isolated in its own [tool environment](https://docs.astral.sh/uv/concepts/tools/#tool-environments).

## Install Git

The installation command below uses Git to fetch the Tablesage application. If Git is not already installed, follow the [Git installation instructions](https://git-scm.com/install/) for your operating system. Make sure Git is added to your `PATH`, then restart your terminal and check:

```sh
git --version
```

This must work before you install or update TableSage.

## Install FFmpeg

TableSage checks for `ffmpeg` and `ffplay` before it opens and exits with an error if either is missing. Install an FFmpeg distribution that provides both commands, then restart your terminal.

```sh
# Ubuntu or Debian
sudo apt install ffmpeg

# macOS with Homebrew
brew install ffmpeg
```

On Windows, install an FFmpeg build and add its `bin` directory to your `PATH`. See the [FFmpeg download page](https://ffmpeg.org/download.html) for platform-specific options.

Confirm that both commands are available from your terminal:

```sh
ffmpeg -version
ffplay -version
```

Both must work. A build that ships `ffmpeg` without `ffplay` will not satisfy TableSage's startup check.

## Install TableSage

TableSage is currently installed directly from its GitHub repository:

```sh
uv tool install git+https://github.com/erik-saltwell/tablesage.git
```

This step downloads large machine-learning dependencies, so give it time. It installs two equivalent commands, `tablesage` and `tablesage-rpg`; either one starts the app. If uv asks to add its tools directory to your `PATH`, accept that change and restart your terminal before continuing.

To update later, run:

```sh
uv tool install --upgrade git+https://github.com/erik-saltwell/tablesage.git
```

## Create and Open a Workspace

Choose or create a directory for your TableSage data, then start the app from inside it.

```sh
mkdir -p ~/Documents/tablesage
cd ~/Documents/tablesage
tablesage-rpg
```

On Windows, in PowerShell:

```powershell
mkdir $HOME\Documents\tablesage
cd $HOME\Documents\tablesage
tablesage-rpg
```

Or in `cmd.exe`:

```bat
mkdir "%USERPROFILE%\Documents\tablesage"
cd /d "%USERPROFILE%\Documents\tablesage"
tablesage-rpg
```

TableSage always uses the directory you launch it from, so start it from this workspace every time.

On the first launch, TableSage creates a `.tablesage/` folder in the workspace and opens the Welcome screen with a warning: *Configure and save your settings before progressing. Press S to open Settings.* Until you save settings, the **Campaigns** and **Players** options on the Welcome screen are disabled. This is expected — configure settings first.

![The first-launch Welcome screen, with Campaigns and Players disabled until Settings are saved](../images/screens/landing-settings-required.png)

## Configure Your API Keys and Models

Press **S** to open Settings.

Enter your API keys and choose your language models. Settings asks for three models — High, Medium, and Low — so you can choose a stronger model for demanding work and a cheaper, faster one for simpler tasks.

For the default model choices, you need:

- an **ElevenLabs** key, for transcription and speaker diarization;
- an **OpenAI** key, for the High model; and
- an **Anthropic** key, for the Medium and Low models.

If you select different models, add a key for each provider those choices use. Model IDs must take the form `provider/model-name`, where the provider is `anthropic`, `openai`, or `gemini`. See [Update Your Settings](../guides/settings.md#models-high-medium-and-low) for the model defaults and uses, key storage, and shell environment overrides.

Choose **Continue** to save, or move focus out of a key field and press **C**. Saving validates your model IDs, writes your settings, tests each configured model and downloads local audio-processing models if they aren't already installed — this may take a while.

## If TableSage Does Not Start

- **Installation reports that Git is missing.** Follow [Install Git](#install-git), restart your terminal, and check `git --version` before retrying the installation.
- **`ffmpeg` or `ffplay` is missing.** Install an FFmpeg build with both commands, restart your terminal, and re-run the two verification commands above.
- **`tablesage-rpg: command not found`.** Restart your terminal so uv's `PATH` change takes effect, or follow the instructions `uv tool install` printed.
- **Settings will not save.** Check your model IDs. Each must use the `provider/model-name` form with `anthropic`, `openai`, or `gemini` as the provider. Settings moves focus to the first field with a problem.
- **A connection test fails but the key looks right.** Check whether the key is coming from your shell environment rather than from TableSage — see [How Shell Environment Variables Override Keys](../guides/settings.md#how-shell-environment-variables-override-keys).
- **"This workspace uses a newer settings schema."** The workspace was written by a newer version of TableSage than the one you have installed. Open it with that newer version.

If TableSage has opened this workspace before, an AI coding agent started in the workspace can look into the problem with you; see [Advanced Help](../guides/advanced-help.md).

## Next Steps

* [Start a Campaign](../guides/start-a-campaign.md) to set up your first Campaign and Session. 
* [Guides](../guides/index.md) cover everyday tasks such as processing a recording, exporting outputs, and preparing the next Session. 
* [Concepts](../concepts/index.md) explains how TableSage recognizes Players' voices, what happens when it processes a Session, and what each generated document is.
* [Advanced Help](../guides/advanced-help.md) explains how to ask Claude Code, Codex, or Gemini CLI for help with TableSage.
