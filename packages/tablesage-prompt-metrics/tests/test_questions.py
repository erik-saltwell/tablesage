from __future__ import annotations

from tablesage_prompt_metrics.questions import chunk_transcript


def test_chunk_transcript_is_deterministic_and_overlaps_lines() -> None:
    transcript = "\n".join(f"line {number} words" for number in range(1, 11)) + "\n"

    chunks = chunk_transcript(transcript, target_words=9, overlap_lines=1)

    assert [(chunk.start_line, chunk.end_line) for chunk in chunks] == [(1, 3), (3, 5), (5, 7), (7, 9), (9, 10)]
    assert chunks[0].text.endswith("line 3 words\n")
    assert chunks[1].text.startswith("line 3 words\n")
