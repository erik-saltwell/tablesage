# TTRPG recap: ideas and reusable prompt

## Purpose and agreed frame

Turn a ledger of everything that happened in a TTRPG session into short bullets that can be read aloud at the table before the next session. The primary goal is to prepare players to act tonight. Sparking recognition and sustaining interest are the means: a recap that players tune out cannot prepare them.

The agreed working abstraction is **reactivate shared context with minimal cues**, using relevance to impending choices to decide which memories deserve space. The aim is useful recognition per spoken word, with enough connective tissue to follow events and consequences.

## Borrowed mechanisms and accepted directions

### 1. Television recaps: select backward from the return point

Jason Mittell describes a *Veronica Mars* recap that selects three brief scenes from different episodes to restore threads about to resume. Selection follows upcoming relevance rather than comprehensive chronology. Inclusion can also signal that something will matter, a limitation when adapting this to a game.

Source: [Previously On: Prime Time Serials and the Mechanics of Memory](https://justtv.wordpress.com/2009/07/03/previously-on-prime-time-serials-and-the-mechanics-of-memory/).

**Adaptation:** work backward from the party's known situation at the ledger's end. Recover live threads through recognizable moments and their remaining consequences. Do not predict the GM's plans.

**Accepted tradeoff:** fully resolved encounters can be omitted, even major ones, when they no longer matter to play.

Invented illustration:

> You bought entry with a forged wedding invitation. The steward still expects you at tomorrow's ceremony.

### 2. Musical motifs: preserve the recognizable fragment

Recurring motifs in Wagner's *Ring* refer to characters, objects, places, or emotions. Their usefulness depends on recognizing associations established earlier.

Source: [University of Texas: Ring Motives](https://www.laits.utexas.edu/wagner/ringmotives/ringmotives.html).

**Adaptation:** retain one distinctive detail from a relevant scene—an odd action, striking object, consequential mistake, or familiar phrase—while compressing surrounding description. The hypothesis is that a few recognizable words can recover a larger scene and hold attention.

**Accepted tradeoff:** preserve one such detail per bullet when available, even at the cost of a few extra words. Do not invent jokes or embellishments to manufacture interest.

Invented illustration:

> You bribed the guard with his own stolen boots; he'll leave the east gate open until midnight.

The boots cue the encounter; the gate and deadline restore its practical relevance.

### 3. Operational handovers: return control at the stopping point

The concrete researched example was air traffic control handover. The FAA procedure reviews current and pending traffic, calls out unusual conditions, and checks for omissions so the incoming controller understands the situation they inherit.

Source: [FAA: Transfer of Position Responsibility](https://www.faa.gov/air_traffic/publications/atpubs/atc_html/appendix_a.html).

**Adaptation:** silently check where the party is, what they were attempting, and what immediate pressure or unresolved action remains. End the spoken recap at that point. Keep the completeness check inside the prompt rather than reading a checklist to players.

**Accepted tradeoff:** the last bullet may be more practical than colorful. It should hand control back to the players without recommending their next move.

Invented illustration:

> You're outside the flooded crypt, carrying the stolen key. The water is rising; you haven't opened the door.

## Status and limitations

The user accepted all three directions. The prompt below is the resulting assistant-proposed synthesis; it has not been tested against a real session ledger in this discussion. Its numerical targets of 5–7 bullets and 120–160 words are proposed defaults, not separately established requirements.

The ledger may not clearly distinguish live and resolved threads or record the details players actually found memorable. An unusual detail is a candidate memory cue, not proof of shared recognition. Preserve player knowledge and uncertainty, and avoid inventing significance, consequences, or future developments. The source analogies generate plausible approaches; they do not validate the recap's effectiveness at a table.

## Reusable prompt

```text
Turn this TTRPG session ledger into a tight bullet recap to read aloud before tonight’s game.

Goal: get players ready to act by sparking “oh yeah!” memories. Maximize useful recognition per spoken word.

Select:
- Work backward from where the session ended. Prioritize events that explain the party’s current situation, live leads, obligations, threats, and unresolved choices.
- Omit resolved encounters unless their consequences still matter.
- Use only player-known information in the ledger. Preserve uncertainty; don’t invent connections, significance, or future developments.

Write:
- Aim for 5–7 short bullets and 120–160 words total. Use fewer when sufficient; never pad.
- Give each bullet one main beat. Preserve one distinctive detail when available: an odd action, striking object, consequential mistake, or exact phrase from the ledger.
- Connect that remembered moment to what it revealed or left in play. Let concrete details carry the interest.
- Use natural spoken language, active verbs, and “you” for the party. Keep names only when useful; add a brief identifying cue where needed.
- Arrange the bullets so events and consequences are easy to follow.
- End at the exact stopping point: where the party is, what they were attempting, and any immediate unresolved pressure established by the ledger. Leave the next move to the players.

Before answering, silently cut repetition, generic description, and details that neither trigger a useful memory nor prepare players to act. Read for spoken rhythm; split or shorten crowded sentences.

Output only the recap bullets.

SESSION LEDGER:
[Paste ledger here]
```
