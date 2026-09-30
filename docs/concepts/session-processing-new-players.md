# Processing with New Players

This workflow applies when at least one attendee has no usable [voice print](players.md#voice-prints), usually because they have no voice samples yet.

All stages described in [Processing with Returning Players](session-processing-returning-players.md) still apply. The difference is an additional sequence that establishes new Players' voices before speaker identification.

The complete workflow is:

1. **Import Audio** — The user supplies the Session's recording as the source for processing. The system cleans the audio of background noise if necessary.
2. **Create Transcript** — The system turns speech into text and groups it by anonymous speaker.
3. **Remove Bad Utterances** — The system removes brief acknowledgments that add no independent meaning.
4. **Review Name Corrections** — The user reviews proposed corrections to misheard Player and character names so they can support identity clues.
5. **Isolate New Speakers** — The system uses conversational evidence to propose utterances belonging to each new Player.
6. **Review New Speaker Assignments** — The user confirms who spoke the proposed utterances before they become voice samples, and can ask the system to find more utterances that sound like the confirmed ones.
7. **Seed Player Voice Samples** — The system builds initial voice prints from the confirmed speech.
8. **Identify Speakers** — The system matches utterances against the voice prints of all attendees, including the newly seeded ones, leaving uncertain identities for review.
9. **Extract Glossary Terms** — The user reviews suggested campaign names and terms and decides which to add to the Glossary.
10. **Spellcheck Against Glossary** — The user reviews proposed transcript corrections based on the Campaign's Glossary and player names.
11. **Review Transcript** — The user confirms the words and speaker assignments that will form the session record.
12. **Assign Roles To Players** — The system attributes speech to character names and other Session Roles.
13. **Generate Artifacts** — The system builds the ledger, scene breakdown, introductions, and summaries from the reviewed material, with user approval for any necessary rebuilding of prior Sessions.
14. **Improve Player Voice Prints** — The user decides whether to add more samples from the reviewed transcript to improve recognition in future Sessions.

The extra identity work gives new Players a voice reference before identification, while the later review ensures the Session's artifacts are built from an accepted transcript.

## Why New Players Need Extra Steps

Voice comparison needs a reference for each person it is meant to recognize. Without a new Player's voice print, TableSage cannot reliably identify that Player from the sound of their voice alone.

The transcript itself provides a starting point. Conversational clues suggest which lines belong to each new Player, human review confirms the evidence, and those confirmed lines become initial voice samples. Speaker identification can then use those samples to recognize additional speech in the Session.

The extra work sits between **Remove Bad Utterances** and **Identify Speakers**:

1. **Review Name Corrections** makes names reliable enough to use as evidence, letting the GM review alternate spellings or typos in names that may be in the transcript.
2. **Isolate New Speakers** proposes speech utterances belonging to each new Player.
3. **Review New Speaker Assignments** confirms whose voice the samples contain, and lets the user find other utterances that sound like the seeding set.
4. **Seed Player Voice Samples** builds initial voice prints from that speech.

The Session's attendance defines both established speakers and people whose voices need to be learned.

## Importing Audio and Transcription

**Import Audio**, **Create Transcript**, and **Remove Bad Utterances** work as they do for [returning Players](session-processing-returning-players.md#import-audio). They produce a cleaned transcript with anonymous speaker labels and retain the recording as evidence.

## Establish the New Players' Voices

Here are the steps used to find voice samples for a new Player.

### Review Name Corrections

An LLM compares the transcript with attendees' Player and character names and proposes corrections for mishearings such as *Thor grim* for *Thorgrim*. Human review determines which corrections are valid before they are applied.

Names matter here as clues to identity. An introduction such as *I'm Jordan, and I'm playing Brother Hald*, or an exchange addressed to *Hald*, can help establish who spoke. Correcting misheard names makes that evidence available to the next stage.

### Isolate New Speakers

An LLM reads the Session and proposes lines that belong to each new Player, citing conversational evidence. It also identifies anonymous speaker labels associated with those Players.

TableSage retains proposals that are not claimed for competing Players and contain enough speech to make useful samples. When those proposals provide too little speech, it can supplement them from the associated anonymous speaker group and filter additions for acoustic consistency.

The result is a set of candidate samples, not an established identity. Someone who barely spoke may still have too little evidence for a useful voice print.

### Review New Speaker Assignments

Human review checks whether each candidate really contains the intended Player's voice. Listening to the recording helps distinguish a person speaking from someone merely mentioning or addressing them.

For example, *Hald, do the Deep Kin have a name…* mentions Jordan's character, but Priya may be the one asking the question. Treating it as Jordan's speech would mix Priya's voice into Jordan's samples. A few certain lines are more valuable than a larger collection of mixed voices.

When more evidence is needed, TableSage can search for speech acoustically similar to the confirmed candidates, comparing it with competing voices. Those additions also require human review. This expands the evidence without letting a voice match alone become proof of identity.

### Seed Player Voice Samples

TableSage extracts confirmed utterances from the recording into the new Players' voice sample collections and computes their voice prints. Clips must meet a technical minimum length; duplicate and outlier samples are excluded from the computed voice print.

Seeding turns reviewed identity evidence into a reference for voice matching. A Player with enough usable samples can now be recognized in this Session and in future Sessions. Players with insufficient evidence still need human speaker assignment.

### Identify Speakers

TableSage compares utterance voices with the established attendees' voice prints and the new voice prints created during seeding. It can recognize speech beyond the initial sample set, which is why seeding happens before this stage.

Uncertain matches remain **Unassigned Speaker**. An initial voice print is a starting reference, and its assignments still need checking during transcript review.

## Complete Processing

The remaining stages follow the [returning-player workflow](session-processing-returning-players.md#extract-glossary-terms): **Extract Glossary Terms**, **Spellcheck Against Glossary**, **Review Transcript**, **Assign Roles To Players**, and **Generate Artifacts**.

Name corrections have already made Player and character names more reliable. Glossary extraction and spellchecking then establish consistent Campaign terminology. Transcript review checks speaker assignments and remaining text errors before the role transcript and artifacts are built.

New Players deserve particular attention during that review because their voices were learned from a small set of samples. Reviewing uncertain lines against the recording gives both the campaign record and any later voice learning a sounder foundation.

The optional **Improve Player Voice Prints** stage can add further samples from the reviewed transcript to all attendees' collections. Newly seeded Players can benefit especially from this additional evidence, provided the speaker assignments are correct.
