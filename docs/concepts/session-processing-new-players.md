# Processing with New Players

This workflow applies when at least one attendee has no usable [voice print](players.md#voice-prints), usually because they have no voice samples yet.

All stages described in [Processing with Returning Players](session-processing-returning-players.md) still apply. The difference is an additional sequence, steps 4–7 below, that establishes new Players' voices between **Remove Bad Utterances** and **Identify Speakers**.

The complete workflow is:

1. **Import Audio** — The user supplies the Session's recording as the source for processing. The system cleans the audio of background noise if necessary.
2. **Create Transcript** — The system turns speech into text and groups it by anonymous speaker.
3. **Remove Bad Utterances** — The system filters likely listener acknowledgments from short replies.
4. <span style="color: #15803d;"><strong>NEW</strong></span> **Review Name Corrections** — The user reviews proposed corrections to misheard Player and character names so they can support identity clues.
5. <span style="color: #15803d;"><strong>NEW</strong></span> **Isolate New Speakers** — The system uses conversational evidence to propose utterances belonging to each new Player.
6. <span style="color: #15803d;"><strong>NEW</strong></span> **Review New Speaker Assignments** — The user confirms assigned utterances and gathers similar sounding clips.  The approved clips form seed clips for the next step. 
7. <span style="color: #15803d;"><strong>NEW</strong></span> **Seed Player Voice Samples** — The system builds initial voice prints from the confirmed speech.
8. **Identify Speakers** — The system matches utterances against the voice prints of  attendees, leaving uncertain identities for review.
9. **Extract Glossary Terms** — The user reviews suggested campaign  terms and decides which to add to the Campaign Glossary.
10. **Spellcheck Against Glossary** — The user reviews proposed transcript corrections based on the Campaign's Glossary and player names.
11. **Review Transcript** — The user confirms the text and speaker assignments for each utterance, forming the session record.
12. **Assign Roles To Players** — The system attributes speech to character names and other Session Roles.
13. **Generate Artifacts** — The system builds the ledger, scene breakdown, introductions, and summaries from the reviewed material.
14. **Improve Player Voice Prints** — The user decides whether to add more samples from the reviewed transcript to improve recognition in future Sessions.

## Why New Players Need Extra Steps

Voice comparison needs a reference for each person it is meant to recognize. Without a new Player's voice print, TableSage cannot reliably identify that Player from the sound of their voice alone.

TableSage solves this problem by looking for places in the transcript where Players refer to each other by name (or by their characters name) and using these cues to find a base set of utterances can be used to build an initial Voice Print.

## Processing Steps
### Importing Audio and Transcription

**Import Audio**, **Create Transcript**, and **Remove Bad Utterances** work as they do for [returning Players](session-processing-returning-players.md#import-audio). They produce a cleaned transcript with anonymous speaker labels and retain the recording as evidence.

### Establish the New Players' Voices

Steps 4–7 find and confirm voice samples for each new Player; **Identify Speakers** then uses them to recognize the rest of their speech.

#### 4. Review Name Corrections

An LLM compares the transcript with attendees' Player and character names and proposes corrections for mishearings such as *Thor grim* for *Thorgrim*. Human review determines which corrections are valid before they are applied.

Names matter here as clues to identity. An introduction such as *I'm Jordan, and I'm playing Brother Hald*, or an exchange addressed to *Hald*, can help establish who spoke. Correcting misheard names makes that evidence available to the next stage.

#### 5. Isolate New Speakers

An LLM reads the Session and proposes lines that belong to each new Player, citing conversational evidence. It also identifies anonymous speaker labels associated with those Players.

TableSage retains proposals that are not claimed for competing Players and contain enough speech to make useful samples. When those proposals provide too little speech, it can supplement them from the associated anonymous speaker group and filter additions for acoustic consistency.

The result is a set of candidate samples, not an established identity. Someone who barely spoke may still have too little evidence for a useful voice print.

#### 6. Review New Speaker Assignments

Human review checks whether each candidate really contains the intended Player's voice. Listening to the recording helps distinguish a person speaking from someone merely mentioning or addressing them.

For example, *Hald, do the Deep Kin have a name…* mentions Jordan Lee's character, but Priya Patel may be the one asking the question. Treating it as Jordan's speech would mix Priya's voice into Jordan's samples. A few certain lines are more valuable than a larger collection of mixed voices.

When more evidence is needed, TableSage can search for speech acoustically similar to the confirmed candidates, comparing it with competing voices. Those additions also require human review. This expands the evidence without letting a voice match alone become proof of identity.

#### 7. Seed Player Voice Samples

TableSage extracts confirmed utterances from the recording into the new Players' voice sample collections and computes their voice prints. Clips must meet a technical minimum length; duplicate and outlier samples are excluded from the computed voice print.

Seeding turns reviewed identity evidence into a reference for voice matching. A Player with enough usable samples can now be recognized in this Session and in future Sessions. Players with insufficient evidence still need human speaker assignment.

## Complete Processing

The remaining stages follow the [returning-player workflow](session-processing-returning-players.md#extract-glossary-terms): **Identify Speakers**, ***Extract Glossary Terms**, **Spellcheck Against Glossary**, **Review Transcript**, **Assign Roles To Players**, **Generate Artifacts**, and **Improve Player Voice Prints**.

New Players deserve particular attention during the final **Transcript Review** review because their voices were learned from a small set of samples. In addition, a reviewed transcript can be used by **Improve Player Voice Prints**, drastically increasing the number of Voice Samples for new Players.

