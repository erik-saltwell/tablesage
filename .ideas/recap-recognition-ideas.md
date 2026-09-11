# Compact campaign recaps that support scene recognition

## Purpose and status

Create a minimal, readable, scene-by-scene TTRPG campaign log that helps players who attended recognize a scene and internally recover its important facts. The intended deliverable is an extraction prompt applied to a session play record, with previous campaign recaps available as comparison context.

The working abstraction is **reactivate an existing memory with the smallest useful cue**. Here, recognition means identifying a previously experienced scene; the additional recovery of its details is the desired next step. Recognizing a scene does not guarantee accurate or complete recall.

The cue-selection principles below were accepted as promising during exploration. The complete prompt is a proposed first version, not a tested or approved production specification.

## Agreed direction

- Optimize for players who attended. Bringing absent players up to speed is outside the core objective.
- Use only fictional events and descriptions in the play record. The source excludes table discussion, so table jokes and player reactions outside the fiction are not candidate cues.
- Preserve a distinctive fictional moment with enough context to identify its scene.
- Sensory descriptions—sights, colors, sounds, smells, and similar details—are eligible cues. They earn space through usefulness; they are neither required nor automatically preferred.
- Use previous campaign recaps, when available, to distinguish new scenes from similar earlier encounters.
- Minimize the record while maintaining readability and scene coverage.

## Borrowed mechanisms and their implications

### Episodic retrieval: connection plus distinctiveness

In two laboratory experiments, Badham and colleagues found that increasing the match between learning and retrieval cues benefited memory only when it also improved discrimination between the target and competing memories. This suggests considering both whether a cue connects to the original experience and whether it separates that experience from others. See [Badham et al., 2016](https://pubmed.ncbi.nlm.nih.gov/27831714/).

The proposed transfer is to select a specific action, interaction, object, phrase, or other identifying detail, with a person or place added when needed. A central event can itself be distinctive enough; a separate decorative hook is unnecessary.

Invented example:

> At the toll bridge, Mira paid the troll with the counterfeit royal portrait; it let us cross.

The payment tactic and portrait are candidate recognition cues, the bridge anchors the scene, and the final clause preserves its result.

**Limit:** laboratory cue effects do not validate a TTRPG recap method. An extractor cannot directly know what each player noticed or retained. A detail that is unusual in the record might have barely registered during play.

### Photo diaries: sensory details as possible retrieval cues

In a wearable-camera study with nine participants, reviewing photographs after initial recall prompted additional memories, including nonvisual information such as thoughts and feelings. This supports the possibility that a fragment of an experience can cue information beyond what it directly depicts. See [Finley & Brewer, 2024](https://pubmed.ncbi.nlm.nih.gov/39023007/).

The preferred adaptation from this domain is to consider distinctive sensory descriptions in the fictional record. The exploration initially suggested a compact textual snapshot; the user redirected the emphasis toward sensory cues that might bring back the scene.

Invented example:

> Beneath the bell tolling underwater, Sera bargains with the drowned priest for safe passage.

The sound is a candidate cue; the bargaining identifies the central event. The sensory detail should remain only if it contributes enough identification to justify its length.

**Limit:** photographs reproduce things participants actually saw. TTRPG players may imagine descriptions differently. The study does not establish that mentioning an imagined sound, color, or smell reinstates sensory memory, or that textual sensory cues outperform other details.

### Information retrieval: distinguish scenes within the collection

Search systems use inverse document frequency to reduce the weight of terms appearing across many documents and increase the relative weight of terms found in fewer documents. The mechanism addresses how well a term distinguishes records within a collection. See [Introduction to Information Retrieval: Inverse document frequency](https://nlp.stanford.edu/IR-book/html/htmledition/inverse-document-frequency-1.html).

The proposed transfer is a comparison step: ask whether a recap entry could also describe other available scenes. If it could, replace generic wording with an identifying detail. A recurring location or sensory motif may orient the reader without uniquely identifying an encounter.

**Limit:** rarity is not memorability. A surname mentioned once may distinguish a database record while meaning little to players. Borrow the comparison mechanism, not a rule that rare words are inherently good cues. Prior recaps also provide incomplete evidence about the campaign.

## Proposed compression rule

Ask of each detail: **Does removing it make the scene harder to identify or obscure what happened?** If neither, it can probably go.

The proposed prompt also retains the central event and its essential result explicitly. This is a hedge against the possibility that recognizing the scene will not restore its consequential facts. There is no agreed fixed word budget or validated minimum number of cues.

## Proposed extraction prompt

```text
Create the smallest readable, scene-by-scene recap of this TTRPG session that helps players who attended recognize each scene and remember what happened.

INPUTS
- Current session play record.
- Previous campaign recaps, when available.

PURPOSE
Each entry should give an attendee enough to think “I remember that scene” and recover its important facts. Preserve the central event and its essential result explicitly, since recognizing a scene may not restore every fact.

SCENE COVERAGE
Identify distinct scenes in chronological order. Use meaningful changes in location, time, immediate objective, or interaction to guide boundaries. Do not split every action into a scene or merge distinct scenes merely to shorten the recap.

Represent every scene, including quiet scenes. Do not invent a dramatic hook or consequence.

SELECT CONTENT
For each scene, identify:
- The central action, interaction, discovery, or decision.
- Its essential result or unresolved situation, if any.
- The smallest useful set of details likely to identify this particular scene to an attendee.

Possible recognition cues include:
- An unusual action, tactic, mistake, refusal, or reversal.
- A distinctive object or its use.
- A specific interaction between characters.
- A distinctive sight, color, sound, smell, texture, or other sensory detail.
- A recognizable phrase spoken within the fiction.
- A person or place that helps locate the event.

No cue category is mandatory or automatically preferred. A detail earns space when it helps identify the scene, anchors another cue, or preserves an essential fact. Prefer cues connected to the central event over incidental curiosities.

Favor details that received attention or shaped events in the supplied record. Unusualness alone does not establish that players will remember a detail.

DISTINGUISH SCENES
Compare candidate entries with other scenes in the session and, when supplied, previous campaign recaps.

Ask: “Could this entry describe another encounter?”
If so, replace generic wording with a more identifying detail.

Use previous recaps only as comparison and naming context. Do not import their events into the current session or assume they describe the entire campaign.

COMPRESS
Write one short, natural sentence per scene by default. Use a second sentence only when compression would lose an essential distinction or result.

Connect details through actions and relationships so the entry remains readable. Let the central event itself serve as the recognition cue when it is sufficiently distinctive.

Remove redundant names, routine actions, repeated context, decorative language, and details that add no useful identification or essential information. Preserve enough context to understand who did what.

Do not enforce a fixed word count or add separate labels for cue, action, and outcome.

FIDELITY
Use only fictional events and descriptions supported by the current play record. Exclude table discussion and player reactions outside the fiction.

Never invent sensory details, quotations, motives, consequences, or certainty. Preserve the distinction between what characters suspected and what they established.

OUTPUT
Return only the recap as chronological bullets, one bullet per scene. Include a session heading only if its identifier is supplied.
```

## Remaining uncertainties

- Which cues work across different players, and how their usefulness changes as the campaign ages.
- How reliably an extractor can infer player attention from the fictional play record alone.
- Whether a cue retrieves the scene's important facts rather than only familiarity with the scene.
- How much outcome information must remain explicit, especially for scenes with several consequential discoveries or decisions.
- Whether the proposed scene boundaries and sentence-length defaults work on actual session records.

No campaign record was processed and no player-memory evaluation was performed during this exploration.
