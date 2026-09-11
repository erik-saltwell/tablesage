# Ledger-derived scene breakdown

## Purpose and status

Generate a compact, data-centric scene breakdown from a Session's Ledger when generating outputs. It would serve two purposes:

- Supply enough information to generate a short session recap without processing the full Ledger again.
- Allow an LLM to read a whole Campaign's history when its accumulated Ledgers are too verbose.

This is a concept sketch, not an implemented artifact contract. The working direction is one entry per scene, preserving what happened, what matters afterward, and what makes the scene distinctive. The user explicitly wants a dedicated field for a distinctive sensory, thematic, or personal detail in every scene. The remaining schema and generation behavior are proposals.

The [Ledger specification](../specs/ledger.md) remains authoritative for the source artifact. The breakdown would be a derived, intentionally lossy layer between the detailed Ledger and downstream uses. No change to the existing Summary or Recap Summary pipeline has been decided.

## Candidate contents

| Field | Purpose |
| --- | --- |
| `title` | A short, descriptive handle for the scene. |
| `location` | Where the scene happened, when established. |
| `participants` | Characters and groups central to the scene. |
| `situation` / `goal` | What the characters were dealing with or trying to accomplish; the exact field choice is open. |
| `outcome` | What happened, including failure, interruption, or an unresolved ending. |
| `discoveries` | New information, retaining attribution and uncertainty. |
| `lasting_changes` | Commitments, relationships, possessions, threats, and other consequences likely to matter later. |
| `signature_detail` | One distinctive sensory, thematic, or personal detail that differentiates the scene from others in the adventure. This field's purpose is agreed; its name is proposed. |
| Ledger references | Access to supporting detail; representation is undecided. |

Outcome, discoveries, and lasting changes provide the substance for continuity. Orientation fields make the record understandable. Goals should not be invented to fill a mandatory field: some scenes are incidental or exploratory. Required fields, empty values, and overlap between categories remain undecided.

### Distinctive detail

The signature detail preserves a scene's recognizable identity when it is compressed further into a recap. A useful selection rule is to prefer the detail a player would use to remind someone which scene this was: “the one where you shot Squints.”

The detail can be sensory, thematic, or personal; it need not cover all three. Some overlap with an outcome or discovery is acceptable because the field identifies what should survive further compression. Use source-supported details without inventing atmosphere, humor, or symbolism.

This connects to the recognizable-fragment direction in [the recap ideas](recap-ideas.md).

### Clocks and time pressure

Preserve deadlines, advancing threats, and consequences of delay because they change what the characters can do next. Include newly established pressure, advancement of an existing threat, and resolution when supported.

The current proposal places these under `lasting_changes`; a separate clock field or full clock-tracking system has not been agreed. Preserve the timing actually established. “Soon” is meaningful pressure without being a precise countdown. Do not infer elapsed time, a deadline, or a resolved threat from insufficient evidence.

## Compression and source fidelity

- Group around a coherent interaction or problem. A location change can suggest a boundary, but multiple scenes can occur in one location. Exact boundary rules remain open.
- Preserve causal connections and consequential commitments, rather than reducing an encounter to a topic such as “negotiated with a ferryman.”
- Retain the difference between reported claims and established facts, and between a proposal and an accepted commitment.
- Apply accepted Ledger corrections when describing outcomes. Do not perpetuate a superseded result or count time from a retracted event.
- Keep a small amount of distinctive action where it helps a recap remain recognizable.
- Compression will lose potentially useful details. Proposed Ledger references allow an LLM to consult deeper evidence when the compact Campaign history is insufficient.

## Examples: Brandonsford Session 002

These are illustrative entries, not a complete breakdown or a finalized serialization format. They derive from the current version-4 [local Ledger for “the halfling corps”](../.tablesage/campaigns/Brandonsford/002/ledger.json). That generated local artifact may not be present in another checkout. Source-reference fields are omitted because their format is undecided.

```yaml
- title: George warns of the dragon
  location: George's woodsman's hut
  participants: [Sir Phidipaldi, George]
  goal: Learn about the black dragon.
  outcome: Sir Phidipaldi obtains George's account of his failed expedition.
  discoveries:
    - George places the dragon's lair at the foot of the northern mountains.
    - He reports poisonous jaws, sulfur spit, and scales that resisted
      his group's arrows and swords.
    - He doubts Eric the Reeve possesses the promised 1,000 gold.
    - He recounts that Sir Brandon killed such a dragon with a fairy-given sword.
  lasting_changes:
    - "New time pressure: George warns the dragon will soon be able to fly.
      No specific deadline is established."
  signature_detail: >
    George, the one-armed survivor, says he amputated his own poisoned
    arm after the dragon killed his companions.

- title: Dunk obtains faun wine
  location: Fauns Grove
  participants: [Dunk, the fauns]
  goal: Obtain faun wine for Ingrid's proposed sleeping potion.
  outcome: Dunk trades a tear-stained rabbit's foot for a flask of faun wine.
  discoveries:
    - The grove's trees bleed wine.
    - The fauns value sentimental curiosities as trade goods.
    - Dunk withstands the first drink without becoming drunk and remains
      conscious after the second.
  lasting_changes:
    - Dunk acquires the ingredient Ingrid requested; the potion is not yet made.
  signature_detail: >
    Dunk astonishes the reveling fauns by drinking their wine
    without becoming drunk.

- title: Rescue at the giant's cottage
  location: Giant's cottage on the route to Brandon's Barrow
  participants: [Trout, Squints, Dunk, Sir Phidipaldi, Dr Uriah, Brother Dirk, giant]
  goal: Free the unidentified captive without waking the giant.
  outcome: >
    Squints frees Brother Dirk, waking the giant. With the party's help,
    they escape and outrun its pursuit. Trout accidentally hits Squints
    with his sling during the escape.
  discoveries:
    - Dirk says he was seeking the sword at Brandon's Barrow to save the town.
    - Dirk says the giant intended to cook him in its stew.
  lasting_changes:
    - Brother Dirk is freed; the immediate threat of being eaten is resolved.
    - Squints suffers 2 damage from Trout's sling.
    - Dirk wants to return home; Sir Phidipaldi insists he accompany the party.
      Dirk's agreement is not recorded.
  signature_detail: >
    Trout's attempt to cover his new recruit's escape ends with
    his sling stone hitting Squints in the head.
```

The George example preserves urgency without manufacturing a countdown. Dunk's example uses the corrected result: the Ledger retracts an initial outcome of five hours of unconsciousness. The rescue leaves Dirk's next move unresolved because the current Ledger ends with Sir Phidipaldi's insistence, not Dirk's acceptance.

## Open choices

- How to segment scenes, including interleaved activity when the party splits.
- Which fields are mandatory, how short each entry should be, and how to handle a scene without a sufficiently distinctive source detail.
- Whether clocks need their own field and how to represent changes to existing pressures.
- How to identify supporting Ledger entries and keep references valid after regeneration.
- Where the artifact is persisted, when it is generated or invalidated, and which downstream outputs consume it.
- How much compression still supports both short recaps and useful Campaign continuity questions.

A suggested experiment is to break down one full real Session, then use only that breakdown to generate a short recap and answer continuity questions. This would test omissions and verbosity before committing to a schema; it has not been performed as part of this sketch.
