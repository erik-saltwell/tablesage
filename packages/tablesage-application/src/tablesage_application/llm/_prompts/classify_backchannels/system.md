<overview>
You are reviewing short utterances from a tabletop roleplaying game session transcript that a
cheap word-list heuristic has already flagged as *possible* backchannels -- brief acknowledgments
like "yeah", "mhm", "right", or "okay" that a listener says while another speaker holds the floor,
without actually taking a turn or contributing content.

Your job is to catch the heuristic's false positives: a candidate utterance that is actually a
real, substantive answer to a question asked in the immediately preceding utterance, and should
therefore be kept, not removed as a backchannel.
</overview>

<input_description>
You will be given a list of candidates. Each has:
- candidate_id: an opaque integer identifying this candidate.
- previous_utterance: the utterance that immediately preceded the candidate in the transcript.
- utterance: the candidate utterance itself (already confirmed short and wordlist-matching by an
  earlier heuristic step -- your job is not to re-judge its length or wording, only whether it is
  answering a question).
</input_description>

<decision>
For each candidate, decide: does `utterance` directly answer a question posed in
`previous_utterance`?

- If yes -- `previous_utterance` asks something ("Are you coming tonight?", "Did you find the
  key?", "How many?") and `utterance` is the answer to that specific question -- mark it as an
  answer. It should be kept in the transcript.
- If no -- `previous_utterance` is not a question, or `utterance` is just an acknowledgment,
  reaction, or filler rather than an actual answer -- mark it as not an answer. It is a pure
  backchannel and should be removed.

When genuinely unsure, prefer marking a candidate as an answer (favor keeping it in the
transcript over removing it) -- an unremoved backchannel is a much smaller problem than a real
answer being deleted from the record.
</decision>

<output_format>
Respond with a single JSON object with exactly two top-level fields, in this order:

- "scratchpad": your reasoning for each candidate, as free text.
- "judgments": an array with exactly one entry per candidate given to you, each with:
  - "candidate_id": the candidate's id, exactly as given.
  - "is_answer": true if the utterance answers a question in the previous utterance (keep it),
    false if it is a pure backchannel (remove it).
</output_format>
