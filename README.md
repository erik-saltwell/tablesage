# TableSage RPG

Turn tabletop roleplaying session recordings into transcripts, recaps, and campaign summaries.
TableSage is a terminal application for organizing Campaigns, Players, and Sessions,
reviewing speaker attribution, and generating session notes.

This is an early-release README. A fuller walkthrough and screenshots will follow.

## Install and run

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[FFmpeg](https://ffmpeg.org/download.html), including both `ffmpeg` and `ffplay` on PATH.
For example, use `sudo apt install ffmpeg` on Ubuntu/Debian or `brew install ffmpeg`
on macOS. On Windows, install an FFmpeg build and add its `bin` directory to PATH.
TableSage checks for both executables before opening its interface.

Once the package is published on PyPI, install it persistently:

```sh
uv tool install tablesage-rpg
tablesage-rpg
```

The same installation also provides `tablesage`. If your shell cannot find either
command, run `uv tool update-shell` and restart the terminal.

Or run through uv's tool cache without a persistent installation:

```sh
uvx tablesage-rpg
uvx --from tablesage-rpg tablesage
```

Python 3.12 or newer is required; uv can provision Python. Linux is the initial
deployment-test target. macOS and Windows need end-to-end validation before we
claim full support. ML dependencies require substantial download and disk space;
models also download when first used.

## Your workspace and credentials

Run TableSage from a writable directory where you want to keep your game data:

```sh
mkdir my-games
cd my-games
tablesage-rpg
```

Each launch directory is an independent workspace. TableSage creates
`campaigns/` for campaigns and session artifacts, `players/` for player voice clips,
and `.tablesage/` for its database, settings, and logs.
Launching from another directory opens a different workspace; it does not move
or delete the first one. There is no parent-directory workspace search.

For an existing workspace using the older layout, close TableSage and move
`.tablesage/campaigns` to `campaigns` and `.tablesage/players` to `players` in the
workspace directory before reopening it. Leave the database, settings, and logs
in `.tablesage`. This release does not automatically move existing folders;
if destination folders already exist, resolve their contents before moving.

On first launch or a required settings update, the landing page shows a toast
directing you to Settings (S). Review and Save before progressing. Keys
are optional for setup. Return to Settings with `S` from the landing page to
edit model choices and personal keys in the LLM and Keys sections, with field help and defaults.
Changes apply to subsequent actions; Save validates the complete draft.

Settings manages personal keys for ElevenLabs (transcription) and Anthropic,
OpenAI, and Gemini (LLMs). Keys are stored for all your workspaces in the
OS-standard user configuration directory. On Linux this
is normally `~/.config/tablesage/.env`. Keys are plaintext: do not commit or share
that file. Exported shell variables override stored keys and are identified in
Settings. TableSage no longer reads workspace `.env` files; move existing keys
yourself or re-enter them in Settings.

Each key has a one-line masked input. Type to replace a key; leave it untouched to
keep it. Ctrl-S saves both keys and model changes. With a key focused, Ctrl-D
stages removal and Ctrl-T tests its saved configuration. Save edits before testing;
tests may incur usage charges.
Provider accounts and usage charges are separate from installation. A workflow
missing a required key offers an Open Settings dialog.

Workspace behavior is stored in `.tablesage/settings.yaml`. Other processing
options are not exposed in the editor and are preserved when saving or resetting
LLM choices. The TUI writes
canonical YAML; comments are not retained. First run and settings-schema upgrades
require a Settings save before normal navigation is unlocked. Malformed or
invalid files still require manual repair after a terminal error.

## GPU and CPU

`--torch-backend` belongs to **uv**, not to the TableSage executable. It selects
which PyTorch build is installed. To let uv choose a backend for the machine:

```sh
uv tool install --torch-backend auto tablesage-rpg
# Or:
uvx --torch-backend auto tablesage-rpg
```

For a CPU installation, particularly to avoid CUDA downloads on Linux:

```sh
uv tool install --torch-backend cpu tablesage-rpg
```

Audio enhancement uses ClearVoice's automatic GPU selection (CUDA or supported
Apple MPS) with CPU fallback. Speaker embeddings currently run on CPU because
the upstream WeSpeaker GPU path has a device-mismatch issue. Installing a CUDA
build does not make every processing stage use the GPU. CPU-only PyTorch cannot
use CUDA; changing hardware may require reinstalling with the desired backend.
See [uv's PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/).

## Development and local deployment

The repository root builds one distribution, `tablesage-rpg`, containing all
four internal Python packages. No separate TableSage dependency packages need
to be published.

```sh
uv sync
uv run tablesage-rpg
uv run pytest packages apps/tablesage-tui
```

Install the checkout as an editable tool from the repository root:

```sh
uv tool install --force --editable .
```

Then run `tablesage-rpg` from your game directory. Source edits become available
on the next launch. Repeat the install after dependency or entry-point changes.
The checkout must remain at the same path while the editable tool is installed.

To test the packaged release locally:

```sh
uv build --no-sources
uvx twine check dist/tablesage_rpg-0.1.0*
uv tool install --force --reinstall dist/tablesage_rpg-0.1.0-py3-none-any.whl
```

Use the actual version in the filenames. Run the installed command from a fresh
directory to exercise the first-launch experience. No PyPI upload is needed.

The separate prompt-optimization developer app requires the sibling
`../prompt-forge` checkout. It is an independent developer project: use
`uv run --project apps/optimize-prompts optimize-prompts --help`. Its dependencies
are not needed to install or develop the main app. To run its tests, use
`uv run --project apps/optimize-prompts pytest apps/optimize-prompts/tests`.

## Releases and updates

After fixing a bug: test locally, bump `version` in the root `pyproject.toml`,
refresh `uv.lock`, build and test the wheel, then commit and tag the release.
Publish only that version's wheel and source distribution using `uv publish`
with PyPI credentials or a configured Trusted Publisher. PyPI versions cannot
be overwritten. Automated GitHub publishing is not configured yet.

Users update a PyPI-installed tool with `uv tool upgrade tablesage-rpg`, or run
`uvx tablesage-rpg@latest`. To replace a local editable installation with the
published package, run `uv tool install --force tablesage-rpg`.

## Documentation to come

- First Campaign, Players, and Session walkthrough
- Audio preparation and speaker review
- Generated outputs and regeneration
- Platform troubleshooting and model requirements

## License

Copyright (c) 2026 Erik Saltwell. Original TableSage code and documentation are
licensed under [Creative Commons Attribution-NonCommercial 4.0 International](https://creativecommons.org/licenses/by-nc/4.0/).
See [LICENSE](LICENSE) for the full terms. Dependencies and downloaded models
retain their own licenses.
