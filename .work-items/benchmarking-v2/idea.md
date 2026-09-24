# Benchmarking v2: idea

Workshopped 2026-09-24. The user agreed to every decision below unless it's marked otherwise, and considers the idea ready.

## Intended effect

Measure the automatic parts of session processing from start to finish using real sessions, so you can tell from repeatable numbers whether code or settings changes help. The benchmark scores the **role transcript** (`role_transcript.json`: an ordered list of `{index, speaker, text}` entries whose speaker is a character name or the GM). Every post-review LLM pass reads this artifact, so it's the natural thing to score.

It measures two separate things:

- **Who:** did each part of the transcript get the right role?
- **What:** is the text correct?

The existing benchmark in `benchmarks/speaker_id/` scores only speaker identification on a fixed set of utterances. This replaces that narrow view with an end-to-end one.

## Working direction

### Capture a benchmark after review

After a session has been fully reviewed, a separate command turns it into a benchmark. It creates a folder inside a new `benchmarks/` directory in the TableSage workspace, named after the session. The folder contains:

- **Audio:** the session audio as it is after import and cleaning, since those steps are excluded from the run.
- **Answer key:** the reviewed `role_transcript.json`.
- **Attendees:** a frozen copy of the attendees, each with their role/character name and their player's **centroid**.
- **Glossary:** a frozen copy of the glossary.
- **No voice samples.** They are too large to copy into every benchmark, and they aren't needed. When there are no new players, speaker ID reads only a player→centroid map (`transcribe_audio.py`'s `centroids: dict[str, Embedding]`), and the centroid is stored on the player (`Player.centroid_embedding`).

Why freeze the campaign data: a benchmark that read players, centroids, roles and the glossary from the live campaign would change score whenever campaign data changed. It could also end up containing its own answers. With a frozen copy, score changes come only from code or settings. The tradeoff is accepted: a benchmark won't benefit from better campaign data added later. If that's ever needed, it would be an explicit "re-capture" action.

### Run a benchmark

- **Entry point:** a hidden key binding on the landing page, with no visible call-to-action. It lists the folders in the benchmarks directory and lets you pick one.
- **Isolation:** a run uses only the folder's contents and a temporary working folder. It never reads from or writes to the real campaign or session.
- **Scope:** only sessions **without new players**.

Pipeline steps a run covers (from the step list in [session-processing-flow](../session-processing-flow/item.md)):

| Step | In the run |
|---|---|
| Import Audio / audio cleaning | Excluded; the saved audio is used instead |
| Create Transcript (transcription, diarization, speaker ID) | Yes |
| Remove Bad Utterances | Yes |
| Review Name Corrections, Isolate New Speakers, Review New Speaker Assignments | Skipped; they're already skipped when there are no new players |
| Enhance New Speaker Voice Samples | Expected to do nothing when there are no new speakers |
| Spellcheck Against Glossary | Yes; **every suggestion is accepted automatically** |
| Review Transcript | **Excluded.** Doing this by hand would test the reviewer's skill, not the algorithms |
| Assign Roles To Players | Yes |
| Generate Artifacts (LLM outputs) | Excluded |

### Score by aligned words, not utterances

The answer key and the output won't share utterance boundaries: diarization splits and merges turns, backchannels are removed on purpose, and transcription drops or invents segments. `RoleTranscript` also has no timestamps. So scoring works at the word level:

1. Flatten both transcripts into `(word, role)` sequences, after text normalization (case, punctuation, numbers).
2. Line the two sequences up with a WER-style edit-distance alignment.
3. Compute these metrics from that one alignment. They stay independent of each other:
   - **Text accuracy = 1 − WER.**
   - **Role accuracy**, a word-level diarization error measure similar to WDER. Among reference words that line up with an output word, it reports three shares: **correct**, **unassigned**, and **wrong**. They are kept separate on purpose: an abstention is cheap to fix during review, while a confident wrong assignment may never be noticed.
   - **Glossary-term score**, using the frozen glossary. It has two parts:
     - **term recall:** how many answer-key glossary terms the output reproduced at the matching spot, for example `41/46`, with misses listed as `Vel'Karath → Val Carath ×3`.
     - **false terms:** glossary terms that appear in the output where the answer key doesn't have them. This catches spellcheck being too eager.

     This score exists because names are about 1–2% of the words. Text accuracy barely moves when spellcheck fixes or breaks them, yet names matter most downstream.

Word-level scoring weights by length automatically, which was the original goal: a 40-word narration counts 40 times as much as "yeah."

The report also includes supporting detail:

- per-role breakdowns
- a role-confusion table (reference → output, in words)
- a summary of words that didn't line up (reference words dropped, including backchannels removed on purpose, and words inserted)

Illustrative shape:

```
session 20260825-end            text_acc  role correct/unassigned/wrong  words
  overall                        0.942     0.917 / 0.031 / 0.052          8,412
  by role: Game Master           0.951     0.968 / 0.012 / 0.020          4,980
           Zaria                 0.930     0.861 / 0.052 / 0.087          1,204
  glossary terms: recall 41/46 (0.89), false terms 3
  role confusion (ref → hyp, words): Zaria→Game Master 88, Thorn→Zaria 41
  unaligned: 213 ref words dropped (incl. 140 removed backchannels), 57 inserted
```

### Run history

Each run saves a record in `benchmarks/<name>/runs/` containing:

- timestamp
- git commit, including whether the working tree had uncommitted changes
- the settings that affect the covered steps (for example speaker-ID thresholds and the spellcheck model)
- a hash of the answer key
- the full scores

The results screen shows each number next to the **previous comparable run**, meaning the last run with the same answer-key hash, for example `role correct 0.917 (▲ 0.021)`. It flags settings that changed between the two runs.

## Approaches considered

- **Utterance-level scoring with length weighting** (the original proposal). Replaced: it assumes both sides have the same utterance list, which they don't, and an exact match on an utterance's text marks almost every long utterance wrong.
- **Scoring a reviewed run.** Rejected as the primary result: it measures the reviewer. Using the reviewed transcript as the answer key keeps the human's effort where it's useful.
- **Reading campaign data live.** Rejected in favor of a frozen copy; see "Capture a benchmark after review" above.
- **Copying voice samples.** Rejected: they're too large and speaker ID doesn't need them.
- **"Run all benchmarks" with combined results.** Deferred: worth adding once several benchmark sessions exist.

## Assumptions and known limits

- **The answer key is only as good as the review.** A misheard word the reviewer didn't fix counts as correct.
- **Automatic spellcheck acceptance** tests the suggestion algorithm, not the human choices made during review.
- **Sessions with new players aren't supported.** Bootstrap naming and new-speaker assignment aren't measured.
- **Text normalization rules and glossary-term matching** (terms made of several words, possessives such as "Zaria's") still need to be defined.
- The workshop reviewed `ground_truth.json` in `benchmarks/speaker_id/`, which uses player names and has timestamps, as possible existing data. The captured reviewed role transcript supersedes it as the answer key for this benchmark.

## Open questions

- Folder naming, the capture command's form (where it's triggered, how the name is chosen), and the format of run records.
- Exactly which settings go into a run record.
- Whether Enhance New Speaker Voice Samples truly does nothing when there are no new speakers (its runner doesn't exist yet).
- How the run screen reports progress and failures for a long end-to-end run.
