# Quality rubric: normalized audio for session review

This qualitative rubric was documented at the user's request after timing accuracy was added. It is the current definition for this work item.

Judge the human review experience of a separate, dynamically volume-normalized version of cleaned session audio. Use qualitative observations and examples from real listening sessions; do not assign scores, use numerical anchors, or collapse the dimensions into one rating.

## Listening comfort

Reviewers can set a comfortable playback volume and leave it there through ordinary changes in speaker and utterance. Consider whether quiet speech remains audible and loud speech, laughter, or sudden peaks remain comfortable. Evidence comes from listening across consecutive utterances, rather than judging isolated clips.

## Speech and voice fidelity

Normalization preserves intelligible words, natural speech dynamics, and cues that help a reviewer tell speakers apart. Listen for distortion, pumping, exaggerated breaths, and amplified residual noise. This is distinct from listening comfort: audio can have even volume while sounding less clear or less trustworthy.

## Timing accuracy

The normalized copy stays aligned with the original audio and the transcript's utterance timestamps. Normalization does not stretch, shorten, shift, or drift through the recording. Clips begin and end at the intended speech boundaries, including short utterances and passages near the start or end of a session. Compare corresponding moments in the original and normalized audio and check clips against the transcript. This is distinct from sound quality: a clear, comfortable clip can still be unusable if it plays the wrong moment.

## Reliability across difficult material

The benefit holds beyond clean, typical speech: quiet speakers, brief interjections, pauses, background noise, and abrupt volume changes remain usable for review. This asks how consistently the experience holds across real sessions, whereas listening comfort describes the experience within a passage.

## Review workflow reliability

Both review screens can play the expected utterance, including after an import is retried or source audio is replaced. Missing or failed normalization is visible through artifact staleness and recoverable by rerunning Import Audio. The user accepted full-import recovery during the workshop, superseding the earlier preference against rerunning unrelated processing; no special repair action is required. Judge this dimension from the reviewer's experience and practical recovery, rather than from the internal mechanism; the accuracy of clip boundaries belongs to timing accuracy.

## Design boundary

The normalized copy is only a playback source for human review. Automated transcription, diarization, speaker identification, and saved player voice samples use the original processing audio. Treat this as a required design boundary, separate from the qualitative dimensions above.
