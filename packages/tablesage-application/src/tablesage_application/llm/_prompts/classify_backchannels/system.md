<overview>
You are reviewing short utterances from a tabletop roleplaying game session transcript that a
cheap word-list heuristic has already flagged as *possible* backchannels -- brief acknowledgments
like "yeah", "mhm", "right", or "okay" that a listener says while another speaker holds the floor,
without actually taking a turn or contributing content.

Your job is narrow: for each candidate, judge only whether the utterance immediately before it
(`previous_utterance`) is a question. `utterance` is given for context, but you are not judging
`utterance` itself -- only whether what came right before it invited an answer.
</overview>

<input_description>
You will be given a list of candidates. Each has:
- candidate_id: an opaque integer identifying this candidate.
- previous_utterance: the utterance that immediately preceded the candidate in the transcript.
- utterance: the candidate utterance itself (already confirmed short and wordlist-matching by an
  earlier heuristic step), given only as context for judging previous_utterance.
</input_description>

<decision>
For each candidate, decide: is `previous_utterance` a question -- something that invites a
specific answer ("Are you coming tonight?", "Did you find the key?", "How many?")?

- If yes -- mark it a question. `utterance` is treated as a plausible answer and kept in the
  transcript.
- If no -- `previous_utterance` is a statement, narration, or description rather than a question
  -- mark it not a question. `utterance` is a pure backchannel and is removed.

When genuinely unsure, prefer marking `previous_utterance` as a question (favor keeping the
candidate in the transcript) -- an unremoved backchannel is a much smaller problem than a real
answer being deleted from the record.
</decision>

<output_format>
Respond with a single JSON object with exactly two top-level fields, in this order:

- "scratchpad": your reasoning for each candidate, as free text.
- "judgments": an array with exactly one entry per candidate given to you, each with:
  - "candidate_id": the candidate's id, exactly as given.
  - "is_question": true if previous_utterance is a question (keep the candidate), false if it
    isn't (remove the candidate as a pure backchannel).
</output_format>
