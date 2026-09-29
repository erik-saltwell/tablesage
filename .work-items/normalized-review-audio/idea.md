# Normalized audio for session review

## Intended effect

Let reviewers keep a comfortable playback volume while reviewing transcript utterances and assigning utterances to new players. The feature improves playback for humans without changing audio used to create or identify the transcript.

## Agreed proposal

Import Audio creates two artifacts from the selected recording:

- `input_audio.wav`, the cleaned processing audio used by transcription, diarization, speaker identification, and saved player voice samples.
- A hidden, dynamically volume-normalized audio artifact used only to create playback clips for human review.

The Import Audio File step produces the pair atomically. It writes both artifacts to temporary files and replaces the existing pair only after both exports succeed. A failed normalization therefore does not leave the session with processing audio from one import and normalized review audio from another.

The Review New Speaker Assignments and Review Transcript manual decisions each declare the normalized review audio as a dependency. Their playback clips are extracted from that artifact. If the normalized artifact is missing, the artifact graph marks those decisions stale; rerunning Import Audio restores the required pair before review resumes. Later steps become stale through their existing dependencies on those decisions.

The normalized artifact appears in the artifact registry and graph but is hidden from the user interface and export lists.

## Rationale

Keeping a separate review-only copy makes low and high utterances easier to review at one chosen volume while preserving the established processing audio for automated work and voice samples. Modeling it as a required artifact makes missing playback audio visible through the same stale-state behavior used elsewhere in the session pipeline, without introducing a separate repair action.

Atomic paired output protects the timing and provenance relationship between the two audio versions.

## Deferred ideas

An option to play the original processing audio for an individual review utterance is deliberately deferred. It may be useful after evidence shows reviewers need it, but it is not part of the current proposal.

## Open questions

- Choose and validate dynamic-normalization settings against representative session recordings, including quiet speakers, laughter, brief interjections, and background noise.
- Decide how existing sessions gain the normalized artifact when they are first opened for review.
- Verify that the chosen audio pipeline preserves duration and exact timestamp alignment for review clips.
