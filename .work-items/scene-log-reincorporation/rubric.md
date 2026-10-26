# Scene Log Quality Rubric — Proposed

**Status: agent proposal, not yet agreed by the user.** It was drafted on 2026-10-06 from a borrowing-brilliance exploration of TV "Previously on" recaps, legal case briefs, I-PASS medical handoffs, retrieval-cue research and Harry Beck's Underground map. Dimensions, anchors and the open choices below may change during review.

## What Is Being Judged

The Summary's **Scene Breakdown** for one Session, read together with the forward-looking sections it serves (Key Decisions & Events, Open Loops, Clocks). The user agreed this framing: the scene log is a **memory anchor**. Its job is to give each forward-looking item the context a returning Player needs to remember why it matters. It is not a standalone story recap. The working abstraction: *the smallest set of memory cues that lets people who lived through events re-anchor each live thread.*

A **live thread** is anything a forward-looking section points to. An **anchor** is a scene bullet that a live thread depends on.

## Scale

Each dimension is scored independently from 0 to 10; higher is better. Anchors are given at 0, 5 and 10. Intermediate scores interpolate between them. There is no aggregate score, weighting, target or pass/fail threshold. Scores guide refinement; word counts and similar measures are supporting evidence, not scores.

## Dimensions

### 1. Anchor Coverage

Every live thread in Key Decisions & Events, Open Loops and Clocks has the setup it needs in the scene log. *(Source: case briefs' "include the facts used in the Argument"; recaps' payoff-driven selection.)*

- **0:** Most forward items refer to things the scene log never establishes; the reader must already remember them.
- **5:** Major threads are set up, but several forward items lean on context the log omits or only implies.
- **10:** Every forward item can be traced to a scene bullet that establishes it.

### 2. Materiality

Every scene bullet earns its place: removing it would leave a live thread unsupported or unclear (the **deletion test**). Detail that nothing depends on counts against the log, because in a recap inclusion signals importance. *(Source: case-brief materiality test; recap signal honesty.)*

- **0:** Most bullets fail the deletion test (names, mechanics, resolved incidents, color).
- **5:** Roughly half the bullets are anchors; the rest are harmless but unneeded detail.
- **10:** Every bullet passes the deletion test. Vivid detail appears only fused into an anchor as its hook (see Cue Distinctiveness).

### 3. Proportional Detail

Detail is allocated by a thread's heat (how active, uncertain or imminent it is), not by how long the scene ran at the table. Resolved or quiet scenes shrink to a line or merge. *(Source: I-PASS severity triage.)*

- **0:** Detail tracks table time; a long but resolved scene gets the most bullets, and the hottest thread gets the least.
- **5:** Hot threads get adequate detail, but cold scenes are still treated at length.
- **10:** The hottest threads get the richest anchoring; cold scenes are a single line or merged into a neighbor.

### 4. Cue Distinctiveness

Bullets and scene titles carry hooks specific to this Session (an image, object, name or the table's own phrasing, in indirect speech), so each one brings back a single memory. Generic wording matches every Session and brings back none of them. *(Source: encoding specificity; cue overload.)*

- **0:** Generic bullets and titles ("Upper Level", "the party fought a monster", "made a deal").
- **5:** Some bullets carry a specific hook; others and most titles are generic.
- **10:** Every title and anchor names a distinctive moment, such as Grimble's speaking stick or the noblewoman's riddle, that a player who was there would instantly recognize.

### 5. Economy

Each bullet is as short as its anchor and hook allow: one moment, no retold sequence, no redundant clauses. This is independent of Materiality: a log of only material bullets can still be wordy. *(Source: recap clips; I-PASS compressed history.)*

- **0:** Bullets retell sequences in multiple sentences; several bullets cover the same moment.
- **5:** Mostly single-moment bullets, but many carry unneeded clauses, values or asides.
- **10:** Every bullet is one terse moment; nothing could be cut without losing the anchor or its hook.

### 6. Thread Legibility

A reader can see which live thread each scene moved and where threads meet, without hunting across the log. *(Source: the Tube map's lines and interchanges.)*

- **0:** The log is a flat event list; connecting a bullet to its thread requires rereading everything.
- **5:** Threads can be followed, but connections between scenes and threads are implicit.
- **10:** Each anchor's thread is evident from its wording or placement, and scenes where threads cross read as interchanges.

### 7. Fact–Significance Separation

The scene log states what happened. Why it matters lives in the forward sections, and the forward sections do not retell scenes. *(Source: case briefs' rule against conclusions and editorializing in the facts.)*

- **0:** Scene bullets editorialize ("which may anger the church"), and Key Decisions largely repeats scene bullets.
- **5:** Some interpretation leaks into the log or some retelling into the forward sections.
- **10:** Clean division: the log is pure anchors, and every forward item adds significance without restating its anchor.

## Scoring Methods (Proposed)

- **Deletion test** (Materiality, Anchor Coverage): for each scene bullet, identify the forward item it supports; for each forward item, identify its anchor.
- **Read-back test:** a judge given only the composed Summary restates each live thread (what happened, where it stands, why it matters), and the restatement is checked against the Ledger. This informs Anchor Coverage, Cue Distinctiveness and Thread Legibility. Whether read-back fidelity should also be a dimension of its own is unresolved.
- **Supporting measures:** Scene Breakdown words and bullets, bullets per scene, generic scene titles, and anchors per live thread. These are evidence, not scores.

## Acceptance Conditions (Not Scored)

These are requirements carried over from the Summary contract. They are not quality dimensions:

- Every bullet traces to the Ledger; no invented events, motives or outcomes.
- The player-knowledge boundary and speech-attribution rules hold.
- Flat bullets, no quotation marks, existing section and marker contract.

## Calibration Examples (Baseline Bad Summary, 20260901)

These illustrate the anchors; they are not an evaluation.

- **Fails Materiality:** "Squints pocketed some ooze" as a standalone bullet; the goblins' four names; the mosaics' real gemstones (unless latent resources count; see below).
- **Passes Materiality:** "Ned offered 5 gold per body he didn't kill; the goblins would want proper burials", which anchors the unburied-dead clock and the Ned-versus-goblins loop.
- **Weak Cue Distinctiveness:** scene titles "Upper Level" and "The Lower Level".
- **Proportional detail problem:** The Free Goblin Society scene has 9 bullets, while Brandon's Tomb, where the hottest threads converge, has 4.
- **Separation problem:** Key Decisions & Events restates scene bullets such as Uriah wearing the robes and Trout deferring the chalice.

## Open Choices

- **Latent resources:** should an element with possible future utility (for example, the gemstone mosaics) count as material even when no forward item points to it, or should the forward sections be responsible for surfacing resources?
- **Read-back:** a scoring method only, or also a dimension?
- **Chronology:** the user is open to bending strict time order. The range runs from chronological scenes with thread-evident bullets to a fully thread-organized log; the degree is undecided. The current Summary contract makes the scene log chronological.
- **Absent Players:** distinctive hooks assume the reader was present. Accept this as a limitation, or add a dimension for readers who missed the Session?
- **Dimension overlap:** Anchor Coverage, Proportional Detail and Thread Legibility all concern ties to live threads; they are proposed as independent because a log can satisfy any one while failing the others. Confirm or merge during review.
- **Scale format:** this follows the project workflow's 0–10 scale with anchors. The parent investigation used a qualitative rubric without scores; confirm which form this item should use.
