# Canonical Ledger Format v3

*Supersedes the v2 declaration type schema and its field set. The v1 entry metadata does not carry forward: v3 uses a role/character `source`, represents chronology through array order, and has no time offsets or containment inheritance.*

The application flow that generates and persists this format is specified in [Generate Ledger](generate_ledger.md).

---

## 1. Governing commitment: format, not ontology

v3 begins from an explicit stance that v2 held only implicitly and inconsistently:

> **The ledger is a format, not an ontology.**

An **ontology** is a classification system whose success criterion is truth about structure — it aims to carve the domain at its joints, and a type earns existence by marking a real distinction. A **format** is a classification system whose success criterion is efficiency of representation — types are compression devices, paying context once in a label so that every entry of that type can say less, and fields are slots whose meaning is fixed by the type so they can be terse without being ambiguous.

The admission tests differ. Ontology asks *"is this distinction real?"* Format asks *"does this distinction pay for itself?"* These can converge but nothing guarantees it: a real joint that changes nothing downstream is ontological truth and format waste.

v2 was a hybrid: its type layer was built by ontological reasoning (the 2×2 geometry, the token-identity argument, the "cuts across subjects" test), while its field layer was built by format reasoning (universality, heavy-lifting, lean-on-content). The tell: v2's six types collapsed to four field-signatures, and its first, load-bearing decision-tree question (Event vs. State) licensed zero field differences.

v3 resolves the hybrid in favor of format. To the extent the type system happens to work as an ontology, fine — but that is a low priority and never a tiebreaker. The ontological work of the project lives in the definitional layer (play / game / RPG), where it belongs.

### The v3 admission test

> **A type earns first-class status only if knowing it changes how a reader — human or LLM — understands the move. The type set as a whole should teach the full universe of moves available at the table.**

This is a stricter test than v2's, and it is a *reader-context* test, not a truth test. Two corollaries:

- A distinction recoverable from adjacency or content, that does not change the reading protocol, does not earn a type (this killed Assert vs. Resolve — see §7).
- The type list itself is documentation. A newcomer reading the five type names should come away knowing what can be done at an RPG table.

## 2. What v3 classifies

v2 classified **what a declaration asserts about the fiction** — a change vs. a holding, located in a mind vs. in the world. v3 classifies **what move the utterance makes at the table**. This is a change of classified object, not merely a change of axes, and it follows directly from the project's RPG definition: an RPG is a game whose defining move is open-ended declaration of what happens in the fiction. The ledger is a record of those moves. Its types should therefore be *kinds of moves*, not kinds of fiction-content.

One visible consequence: the type names describe table-acts. "Expression" is the correct name for an entry recording a character's secret resentment — expressed by nobody *in the fiction* — because at the table, the player is expressing the character's inner life. This is the first place the move-classification and a content-classification visibly diverge, and the divergence is intended.

## 3. The base type: utterance

Every regular ledger entry is an **utterance**. The ledger is an incomplete semantic condensation of a transcript, not a lossless transcription: conversion may omit material, rephrase one transcript utterance, summarize several transcript utterances or speakers into one ledger utterance, or split one transcript utterance into several ledger utterances. It does not preserve source mappings.

Regular utterances form a chronological list in the order their content appeared during the session. Array order is authoritative; entries have no time offsets or explicit sequence numbers. Each utterance carries:

- `type` — one of the five lowercase discriminators defined below;
- `source` — the role or character associated with the move, not the human player at the table; and
- the fields belonging to its type.

`source` is a reusable string in the format itself. An application with a known Session role list may check it against those roles, but that contextual check does not narrow the portable schema to a session-specific enum.

**Terminology redefinition, on the record:** v2's terminology section rejected "utterance" as an entry name because it pointed at raw pre-gate speech, OOG chatter included. v3 explicitly redefines it as the post-gate base type. The upstream gate is unchanged — OOG, mechanical talk, and query utterances still never enter the ledger — so post-gate, "utterance" is unambiguous.

**"Declaration" is reserved.** It remains the theory-layer word for the defining move of RPGs ("open-ended declaration of what happens in the fiction"), where it describes *every* move type, not one. *Utterance* is the format-layer word for a ledger entry. The two words never cross layers. (This also permanently closes the v2-era collision in which the generic entry term blocked its use as a type name.)

## 4. The Ledger envelope and preamble

A Ledger has the following top-level fields:

| Field | Shape | Meaning |
|---|---|---|
| `version` | literal integer `3` | Format version |
| `session_id` | UUID | Identity of the Session represented |
| `session_name` | non-empty string | Display name of that Session |
| `preamble` | optional Preamble | Explicitly framed pre-session context |
| `utterances` | ordered list of ledger utterances | Regular session moves |

The Ledger must contain meaningful content in at least one place: a Recap, a Character Introduction, or a regular utterance. A Ledger with preamble content and no regular utterances is valid.

### Preamble

The Preamble captures two independently optional kinds of material that may occur before play begins. Neither, either, or both may be present. They remain outside the regular five-type utterance list because they are pre-session framing rather than in-session moves.

#### Recap

A Recap contains:

- `events` — a non-empty list of concise descriptions of things that happened previously in the campaign, kept in the order they were described in the transcript; and
- `opening_situation` — an optional text description of the situation in which the new session begins, when the transcript states one.

When opening-situation narration also functions as the first in-session Narration, it is represented in both places: once as `recap.opening_situation` and once as the first applicable regular Narration entry. This duplication deliberately preserves both the preamble's complete transition and the regular session chronology.

#### Character Introductions

`character_introductions` is an ordered list whose items contain:

- `character` — the introduced character's role name; and
- `description` — a condensed text description of the introduction.

An introduction spanning multiple transcript utterances is consolidated into one item per character. Items follow the order in which the characters were first introduced.

Recaps and Character Introductions are emitted only when the transcript explicitly frames early material that way. Similar-looking opening narration or dialogue is not enough to infer a Preamble.

## 5. The five types

Every type includes the universal `source` field from §3 plus the payload fields shown below. Serialized `type` discriminators are lowercase: `narration`, `action`, `speech`, `expression`, and `correction`.

| Type | The move | Fields | Reading protocol |
|---|---|---|---|
| **Narration** | Something is told to be true about the game state | `fact` | Append to canon |
| **Action** | An entity does a thing in the world | `entity`, `action` | Append as proposal; auto-canonizes unless contested |
| **Speech** | An entity says something in the world | `entity`, `statement` | Append to canon |
| **Expression** | An entity feels something | `entity`, `sentiment` | Append to canon |
| **Correction** | The game state is adjusted or corrected | `revision` | **Revise** — locate and amend prior canon |

Read as a list of moves: **what's told, what's done, what's said, what's felt, what's revised.** That list is the claimed universe of table-moves, and its legibility is a design goal, not a side effect.

### Narration

A statement of fact about the game state: "There's a tavern at the crossroads." "You slip; the guard hears you." "The room is cold and dark." Settled on arrival. Note that outcome-narration after a roll is simply Narration — see the Assert/Resolve rejection in §7.

### Action

An action taken by an entity in the game world: "I climb the wall." "The guard swings at Bran."

**The proposal/uptake ruling.** Every Action is structurally a proposal that auto-canonizes unless contested. This dissolves the intent/action boundary problem: classification never requires knowing whether resolution mechanics followed. "I walk over to the bar" and "I climb the sheer wall" are the same move; the second is merely a proposal the table routed through machinery. The provisionality that motivated a separate "Intent" type is a property of the *type*, paid once in this definition, rather than a property re-encoded per entry. The model also holds for GM actions ("the guard swings") — proposals contested approximately never — which is a point in favor of proposal/uptake as a true description of tables generally.

**Known cost:** the ledger's world-history is partly *derived* — a reader reconstructs settled canon by walking Actions and applying auto-canonization — rather than directly stated everywhere. Accepted deliberately.

### Speech

Something said by an entity in the world: "Surrender or die." A prayer, a muttered curse (v2 Ruling 4 carries forward: an addressee is optional; utterance suffices).

Speech remains first-class rather than folding into Narration because it has a distinct field signature and is a distinct move a reader should know exists: talking-as-a-character is not the same table act as narrating about the world.

**`statement`, not `verbatim` + text:** the field is deliberately named to promise no more precision than the data has — sometimes the log holds the character's actual words, sometimes a paraphrase. The v2 `verbatim` boolean is deleted (recorded in §7).

### Expression

Something felt by an entity: "Bran is furious." "Bran realizes the letter is forged." Expression absorbs both standing inner states and inner *changes*; the v2 Event/State axis is deleted wholesale, and with it Ruling 3's onset machinery (recorded in §7).

### Correction

An adjustment to prior game state: retcons, walked-back-then-revised facts, GM reversals. Correction is the one type with a genuinely different reading protocol — every other type appends; Correction instructs the reader to *revise something already held*. Without the flag, contradiction-detection becomes the reader's job (v2's "resolve precedence by time"); the type label is real compression of real work.

**Scope, strictly:** a Correction is an entry the table treats as revising prior canon. A failed climb needs no Correction — the attempt is canon, the outcome is Narration, nothing is revised.

**`revision` holds the new state as prose;** what is being corrected is referenced in prose, not by link. A formal `corrects` pointer was considered and fails heavy-lifting: it would require stable entry IDs, which the format deliberately does not have, and prose reference serves human and LLM readers fine. *Reconsider if* programmatic supersession-resolution becomes a real query.

## 6. Field design

The v2 admission tests carry forward — a field must be **universal within its type** and must do **heavy lifting** — with the v3 clarification that "lifting" is measured against the reader-context standard.

**Payload naming is role-flavored, uniformly.** Each type's payload field names what kind of thing it holds: `fact`, `action`, `statement`, `sentiment`, `revision`. This continues the v2 precedent of legibility over uniformity (`speaker`/`parties` rather than flattened `entity` everywhere). Considered and rejected for the Narration payload: `content` (generic bucket, says nothing), `claim` (claims can be false; narration *makes*), `truth` (grandiose). Considered and rejected for Correction: `amendment` (fine; `revision` marginally plainer). A uniform `fact` on both Narration and Correction was defensible — a correction's payload is also a fact now true — but the role-flavored precedent decides against it.

**`entity`** carries forward from v2 with its name and rationale intact: not "character" (refuses to build characterhood into the schema), not "person" (narrower than fictional inner life). The mind-bearing constraint on Expression's entity is a validity condition carried by the type, not the field name.

## 7. Considered and rejected

- **The v2 six-type schema** (Speech/External/Internal Event, Bond/External/Internal State) — built to classify fiction-content rather than table-moves; its load-bearing Event/State axis licensed no field differences and failed the reader-context test. Retired in full. Its decision-tree discipline and its field admission tests survive as method.

- **The Event/State axis and Ruling 3 (onset machinery)** — deleted. Expression absorbs internal changes and internal states alike; Narration absorbs external ones. Explicitly recorded: this is a deletion of ratified v2 machinery, not an oversight.

- **The bond graph.** v2 called `parties` on Bond State "the strongest single payoff a ledger query layer can offer." v3 has no Bond type; the marriage, the debt, the trust are Narration content, and the relationship graph becomes content extraction. This is a knowingly surrendered payoff, weighed and paid, not a silent loss. *Reconsider* via an optional tag layer if graph queries become central.

- **Assert vs. Resolve as separate types** — Resolve encoded conversational role (this entry answers a prior Action), which is recoverable from adjacency and changes no reading protocol: a resolved outcome and a spontaneous assertion settle fiction identically. Collapsed into Narration.

- **"Intent" as the action type's name** — the provisionality it gestured at is real but belongs in the type definition (proposal/uptake), not the name. "Action" names the move as the type list should teach it.

- **Searle-lite illocutionary types** (Declaration/Directive/Expressive/Assertive…) — importing another discipline's ontology into a format-first project; built to be true about language, not to compress RPG tables; several categories would sit empty. The *spirit* of speech-act theory, run through the format admission test, yields the five types instead.

- **Radical two-type minimum** (Move/Canon) — the far endpoint that clarified the real question: how many reading protocols exist at the table? Answer: more than two, fewer than six.

- **The `verbatim` boolean on Speech** — deleted deliberately. The `statement` field name is calibrated to the data's actual precision (sometimes verbatim, sometimes paraphrase); a flag distinguishing the cases failed to earn its keep. This deletes the field that backed v2's token-identity bookkeeping; the token-identity *argument* was an ontological rationale and is no longer load-bearing under format-first.

- **A formal `corrects` link field on Correction** — fails heavy-lifting absent stable entry IDs; prose reference suffices for the format's readers. Deferred with a stated reconsideration trigger (§5, Correction).

- **Human `speaker`, time offsets, containment inheritance, and explicit sequence numbers** — deleted. The Ledger records role/character `source`; array position carries chronology; and the format does not preserve transcript provenance or nesting.

- **"Exposition" / "Establishment" / "Canon" / "Offer" / "Narreme"** as the Narration type name — respectively: connotes info-dumping; clunky noun; names the property all types share; wrongly implies other types aren't offers (and imports improv theory's frame); requires a glossary, failing the self-documenting standard.

- **`content` as the Narration/Correction payload name** — generic bucket; broke the role-flavored naming pattern.

## 8. Known seams and open questions

- **Correction boundary decidability.** Is "the tavern is actually on the *east* road" a Correction, or a Narration whose classifier doesn't remember it contradicts something? Working answer: *Correction only when the table treats the utterance as revising* — the classification tracks the move made, not a global consistency check. Wants counterexample testing against real transcripts before ratification hardens.

- **Speech cargo.** In-character speech carrying fact-cargo ("my father was a smith," said in voice) classifies as Speech; downstream consumers derive the assertion. Under format-first this is explicitly a *non-problem* — the content holds the information and the format's job was to compress, not to model — but the extraction task remains real for consumers and is noted here so it isn't rediscovered as a defect.

- **Compound utterances.** "Tom flies into a rage and flips the table" spans Expression and Action. Presumed handling carries forward from v2: split into multiple entries. Still not formally ruled.

- **Derived world-state.** With Actions auto-canonizing and Corrections revising, "current settled canon" is a derived view over the ledger, not a stored artifact. Fine for the format; a query layer that materializes it is future work.

- **Conversion prompt.** The v2 conversion prompt is invalidated by this schema. v3 conversion is one structured-output call over the complete role-rendered transcript. The prompt owns nuanced classification, condensation, explicit-Preamble recognition, and chronological-order instructions; the schema supplies concise field/type meanings and structural constraints.

## 9. Migration note

v3 is not field-compatible with v2. Approximate mapping for any existing v2 ledgers: Speech Event → Speech (drop `verbatim`); External Event and External State → Narration or Action by whether an entity performs it; Internal Event and Internal State → Expression; Bond State → Narration (parties fold into `fact` prose). Corrections have no v2 source type; none will exist in migrated data. Migration must also replace human `speaker` metadata with role/character `source`, discard offsets and containment, and add the v3 Ledger envelope.

---

*Status: proposal. Ratification pending transcript pressure-testing, per project practice.*
