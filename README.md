# TableSage RPG

A terminal app that turns tabletop roleplaying recordings into transcripts, session summaries, and a lasting campaign record.

![TableSage RPG Welcome screen](docs/images/screens/landing.png)

## Problem Solved

You've finished a great session. Your players made an unexpected alliance, uncovered a clue, and promised a favor you'll need to remember in three months. Now someone has to turn three hours of play into notes—and generate a summary before the next session.

TableSage helps you spend less time reconstructing the game and more time preparing what comes next:

- **Keep the story:** turn your recording into a transcript and campaign record, with a campaign Glossary to keep your world's names and terms consistent.
- **Bring everyone back into the game:** share a session summary with your players and start the next game with a "Previously On" recap.
- **Prepare with continuity:** draw on campaign history to find opportunities for earlier people, places, and promises to appear again.

## Demonstration

This is a summary TableSage generated from an actual play session. Omitted passages (removed for brevity) are marked with `...`.

> ### Starting Situation
>
> - The party seeks the magic sword said to be buried with Sir Brandon in his barrow — the weapon Father William wants used against the black dragon; the party rescued Brother Dirk, William's cleric, from a giant's sack and pressed him onward.
> - The giant is alive in the woods, hunting them.
> - Dunk owes Ingrid a return visit: her sleeping potion (brewed from faun wine Dunk secretly cut to quarter strength) unlocks his planned theft of Warwick's mithril chain shirt.
> - The party, plus Squints and the reluctant Dirk, stood outside Brandon's Barrow at sunset.
>
> ### Scene Breakdown
>
> #### The Barrow Door
>
> - Phidipaldi laid out a plan: sword, then the mithril shirt, poison protection from the witch or alchemist, strongarm the Reeve for an advance, hire Lady Hilda and the wizard, then kill the dragon.
> - Per legend, Brandon's sword did kill the dragon, and Brandon got it from a fairy; the current dragon may be new — or the same, if the tales are off.
> - The door had been opened recently; Dirk said Brandon is buried with his companions Alfred, Myrddin, and Wyllt.
> - The antechamber mosaics show Brandon slaying the dragon with a sword through the roof of its mouth; their color highlights are real inlaid gemstones.
>
> #### The Free Goblin Society
>
> - Four scraggly goblins claim the barrow as the first home of the Free Goblin Society, having fled King Hogboon.
> - Phidipaldi claimed to be Brandon's son; the party ceded the barrow, promised not to tell King Hogboon, and the property-rejecting goblins let them take anything.
> - Trout ignored the goblins' warning and unsealed the gray ooze they'd walled up; the party killed it, Squints landing the final stone.
>
> ...
>
>
> #### Statues and Chapel
>
> - Four knight statues bore words: Valor (Alfred), Piety (Myrddin), Wisdom (Brandon), Duty (Wyllt).
> - Phidipaldi cleaned the mossy St. Arthur statue, shrugged off a spore cloud, and gained +1 to all rolls for the rest of the barrow adventure.
>
> #### The Lower Corridor and Slime Pool
>
> - Three goblins lay dismembered at the stairs; scratching sounded from the corridor's far western end.
> - Waymon sold Ned the corpses at 5 gold each — they must be snuck past the goblins, who'd demand a proper burial.
>
> ...
>
>
> #### Brandon's Tomb
>
> - A statue of an unidentified noblewoman — matching no mural figure — asked what makes a true knight; answering Valor, Duty, Wisdom, Piety opened the doors.
> - Brandon's burial ship held five urns worth 100 gold each, a kite shield earmarked for Dunk, and a 600-gold chalice Trout pocketed, deflecting Dirk's claim it belongs to the church.
> - Phidipaldi took Brandon's silvery magic sword — etched with All shadows yield to my light — and donned Brandon's plate, handing his own down to his day laborer.
> - As they readied to leave, a seven-foot skeleton in rusted armor and a mustachioed death mask appeared in the doorway, dragging a great sword.
>
> ### Key Decisions & Events
>
> - Hiring Ned under murder-refund terms — the party is bankrolling an assassin who keeps bodies.
> - Ceding the barrow to the goblins and promising silence to King Hogboon buys goodwill but creates a secret.
> - Trout unsealing the ooze nearly broke goblin trust; Waymon repaired it.
> - Uriah wearing Saint Arthur's robes and Trout keeping the chalice offended Dirk — the church may hear of it.
> - Phidipaldi looted Brandon's sword and armor — the very sword Father William sent Dirk to retrieve.
>
> ### Ending Situation
>
> - The whole party — with Squints, Dirk, Ned, and the goblins in tow — stands in Brandon's burial chamber.
> - The seven-foot armored skeleton, likely Alfred, blocks the doorway with a great sword.
> - Dunk's business with Ingrid and the mithril heist remain pending in town.
>
> ### Open Loops
>
> - Who is the noblewoman of the statue, absent from all the murals?
> - Is the current dragon the same one Brandon slew, and what of the sword's fairy origin?
> - What is scratching at the far western end of the lower corridor?
> - Ned's purchased corpses must be smuggled past the goblins.
> - Uriah's secret copy of the treasure map is wrong.
> - Will Ingrid's potion, brewed from quartered faun wine, actually fell Warwick?
>
> ### Clocks
>
> - The black dragon cannot fly yet but soon will — every delay makes it deadlier.
> - The giant is alive in the woods between the barrow and town; the return trip risks another encounter.
> - Ingrid expects Dunk's return; the longer he stalls, the more suspicious she may grow. (inferred)

## Installation

You need:

- [uv](https://docs.astral.sh/uv/), Git, and FFmpeg with both `ffmpeg` and `ffplay`. uv can install the required Python 3.12 or newer for you.
- An ElevenLabs API key for transcription, plus an API key for at least one of OpenAI, Anthropic, or Google Gemini. The default models use OpenAI and Anthropic; you can select a single provider in Settings. These services charge for usage.

Once you have these, you can install with:

```sh
uv tool install git+https://github.com/erik-saltwell/tablesage.git
```

See [Install TableSage](docs/getting-started/installation.md) for dependency setup, Windows instructions, storage requirements, and troubleshooting. Installation downloads large machine-learning dependencies.

## Getting Started

Choose or create a workspace directory for your campaign data, then start TableSage from it:

```sh
mkdir -p ~/Documents/tablesage
cd ~/Documents/tablesage
tablesage
```

- TableSage stores its data in the directory you launch it from, so start it from the same workspace each time.
- On first launch, open **Settings** to enter your API keys, choose your models, and save your settings.

**Process your first recording into a transcript and session summary:** follow [Start a Campaign](docs/guides/start-a-campaign.md) to create your first Campaign and Session, then use [Process a Session with New Players](docs/guides/process-session-new-players.md) if TableSage hasn't learned your attendees' voices yet. If everyone already has a usable voice print, use [Process a Session with Returning Players](docs/guides/process-session-returning-players.md).

[Generate and Export Session Outputs](docs/guides/review-and-export.md) explains how to save copies to share. See [Guides](docs/guides/index.md) for more workflows and [Screen Reference](docs/reference/screens/index.md) for controls and screenshots.

## License

[CC BY-NC 4.0](LICENSE).

## Privacy

Session audio goes to ElevenLabs for transcription, and transcript text and campaign context go to your configured language-model providers as needed. Voice matching runs locally, and your workspace is stored on your computer. See [Privacy and Data Handling](docs/reference/privacy.md) for the details.

## Built With

- **Python and Textual** for the terminal application.
- **ElevenLabs Scribe** for transcription and speaker diarization.
- **LiteLLM** for calls to OpenAI, Anthropic, and Google Gemini models.
- **PyTorch and WeSpeaker** for local voice recognition.
- **FFmpeg** for audio processing and playback.
- **SQLModel and SQLite** for local records.

## Author

Created by [Erik Saltwell](https://eriksaltwell.com).
