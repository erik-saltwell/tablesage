# Processing with Returning Players

This [Session Processing](session-processing.md) workflow applies when every attendee already has a usable [voice print](players.md#voice-prints). TableSage can recognize their voices from existing samples, so processing moves directly from transcription to speaker identification. The extra steps for establishing new Players' voices have no work to do.

The complete workflow is:

1. **Import Audio** — The user supplies the Session's recording as the source for processing. The system cleans the audio of background noise if necessary.
2. **Create Transcript** — The system turns speech into text and groups it by anonymous speaker.
3. **Remove Bad Utterances** — The system filters likely listener acknowledgments from short replies.
4. **Identify Speakers** — The system matches utterances against attendees' voice prints, leaving uncertain identities for review.
5. **Extract Glossary Terms** — The user reviews suggested campaign names and terms and decides which to add to the Glossary.
6. **Spellcheck Against Glossary** — The user reviews proposed transcript corrections based on the Campaign's Glossary and player names.
7. **Review Transcript** — The user confirms the words and speaker assignments that will form the session record.
8. **Assign Roles To Players** — The system attributes speech to character names and other Session Roles.
9. **Generate Artifacts** — The system builds the ledger, scene breakdown, introductions, and summaries from the reviewed material, with user approval for any necessary rebuilding of prior Sessions.
10. **Improve Player Voice Prints** — The user decides whether to add more samples from the reviewed transcript to improve recognition in future Sessions.

## Import Audio

TableSage imports the recording as the Session's **input audio**, converting it to 16 kHz mono for transcription and voice comparison. It also creates a normalized copy for review playback. Noise cleaning can make speech clearer in a noisy recording; recordings that have already been cleaned can skip noise removal. The original recording is left unchanged.

## Create Transcript

ElevenLabs transcribes the recording and groups speech by speaker, a process called **diarization**. ElevenLabs also omits filler words, false starts, and stutters, so the transcript is a clean record rather than a word-for-word one. TableSage adds punctuation. Speakers initially have anonymous labels such as *speaker_0*: grouping a voice does not yet identify the person it belongs to.

The result is the raw machine transcript.

## Remove Bad Utterances

TableSage tries to remove **backchannels**: brief listener acknowledgments such as *mm-hmm* that contribute no independent meaning. It finds short phrases that may be acknowledgments, then asks an LLM whether the preceding line was a question. Candidate replies to questions are kept; other candidates are removed.

This rule can also remove meaningful replies, such as an objection of *No* after a statement. The initial transcript preserves the text before this cleanup and remains available for comparison with the recording.

Backchannels are difficult to identify by voice because they contain little speech. Removing them reduces clutter and uncertain assignments in later steps.

## Identify Speakers

TableSage compares the voice in each utterance with the voice prints of the Session's attendees. Confident matches receive a Player's name; uncertain matches remain **Unassigned Speaker** for human review.

Attendance defines the possible speakers. An accurate attendee list therefore matters even when everyone's voice is already known. This step connects the anonymous speech groups from transcription to the people at the table.

## Extract Glossary Terms

Speech recognition often mishears a Campaign's invented names. The Campaign's Glossary provides an established spelling reference. An LLM proposes names and terms introduced in this Session, such as a newly discovered place, faction, or artifact. After human review, these are added to the Glossary.

This grows the Campaign's shared vocabulary while keeping speculative or incorrect suggestions out of its reference material.

## Spellcheck Against Glossary

An LLM compares the transcript with glossary terms and attendees' player names, then proposes spelling corrections for human review. Because extraction comes first, newly accepted terms can immediately help correct other occurrences in the same Session: *Tide Warden Coil* can become *Tidewarden Coil*, for example.

## Review Transcript

Human review establishes the **reviewed transcript**: the accepted account of what was said and who said it. It resolves unassigned speakers, corrects wrong attributions and text, and removes speech that does not belong in the record. The recording remains available as evidence for those decisions.

This is the last quality check before generation. An error left here can flow into the ledger, summaries, and any voice samples later taken from the Session.

## Assign Roles To Players

TableSage creates the **role transcript**, replacing player names with their Session Roles: *Thorgrim* rather than *Bob Martinez*, or *Game Master* rather than *Alice Chen*. Any brief acknowledgment still marked **Unassigned Speaker** after review is dropped at this point.

This connects the people who spoke to their identities in the game. Generated artifacts can then describe the fiction using the appropriate character names and table functions.

## Generate Artifacts

An LLM builds the Session's outputs through a sequence of dependencies:

1. **Transcript sections** locate the opening recap, character introductions, and actual play, so later outputs use the relevant parts of the Session.
2. The **ledger** records events, facts, and developments, accompanied by a scene breakdown that organizes the action. The ledger is the authoritative record of what happened inside the game during a Session.
3. **Player introductions** collect the in-character introductions of player characters from the opening of the Session, kept separate from what happened in play.
4. The **recap summary** distills the scene breakdown into a short account designed to be read at the table.
5. The **session summary** is a longer player-ready account built from the ledger. It includes the prior Session's recap summary, when available, and this Session's player introductions, and is designed to be sent to players before the next Session.

A session summary depends on the earlier recap selected by date; see [How the Prior Recap Is Chosen](sessions.md#how-the-prior-recap-is-chosen). When the required earlier outputs are out of date and can be rebuilt, generation asks to rebuild them first.

See [Session Artifacts](sessions.md#session-artifacts) for what each output contributes to the campaign record.

## Improve Player Voice Prints

After generation, suitable clips from the reviewed transcript can refresh the attendees' voice samples, replacing any earlier clips from this Session. This optional learning step gives future Sessions more evidence for recognizing the same people. See [Add Samples from a Session](../guides/manage-players-and-voice-samples.md#add-samples-from-a-session) for replacement details.

Its value depends on accurate speaker assignments. A mislabeled clip would teach TableSage the wrong voice, so only a carefully reviewed transcript should contribute samples.

## After Processing

The Session now has a reviewed transcript and generated artifacts that can be used for reference, shared with players, or carried into preparation for the next Session.

These outputs depend on the decisions made earlier. Changing an accepted spelling correction, for example, makes the later transcript review and artifacts out of date. Reprocessing the dependent stages restores a consistent record.
