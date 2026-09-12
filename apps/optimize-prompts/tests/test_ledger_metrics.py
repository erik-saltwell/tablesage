import asyncio
import json
from pathlib import Path

import pytest
from optimize_prompts.ledger_metrics import (
    JsonQuestionFactory,
    LedgerConcisenessMetric,
    LedgerExclusionMetric,
    LedgerInputError,
    extract_session_transcript,
    ledger_content,
)
from prompt_model.config import EvalCase, LiteLLMConfig
from prompt_model_metrics.summarization.question_factories import MissingCuratedQuestionsError

_INPUT = """<known_session_roles>
- Game Master
</known_session_roles>

<session_transcript>
**Game Master** - The bridge collapses.
</session_transcript>
"""

_OUTPUT = """{
  "starting_situation": "The party is crossing an unstable bridge.",
  "ledger": {"utterances": [
    {
      "type": "narration",
      "source": "Game Master",
      "fact": "The bridge collapses."
    }
  ]},
  "scene_breakdown": {"ending_situation": "On the broken bridge.", "scenes": [
    {"title": "The bridge", "location": "Bridge", "participants": [], "situation": "Cross.",
     "outcome": "Bridge collapses.", "signature_detail": null, "carry_forward": [],
    "ledger_ranges": [{"start_index": 0, "end_index": 0}]}]}
}"""


def test_extract_session_transcript_uses_only_the_transcript_block() -> None:
    assert extract_session_transcript(_INPUT) == "**Game Master** - The bridge collapses."


def test_extract_session_transcript_rejects_content_after_the_transcript() -> None:
    with pytest.raises(LedgerInputError, match="Unexpected content"):
        extract_session_transcript(_INPUT + "\n<extra>not source context</extra>")


def test_extract_routed_sources_excludes_glossary_and_metadata() -> None:
    rendered = "<glossary>Do not treat as fiction.</glossary><starting_context>[]</starting_context>"
    rendered += '<session_utterances>[{"speaker":"GM","text":"The bridge collapses."}]</session_utterances>'
    source = extract_session_transcript(rendered)
    assert "The bridge collapses." in source
    assert "Do not treat as fiction" not in source
    with pytest.raises(LedgerInputError, match="Unexpected content"):
        extract_session_transcript(rendered + "extra")


def test_json_question_factory_uses_the_exact_input_filename(tmp_path: Path) -> None:
    (tmp_path / "Brandonsford_001.json").write_text(json.dumps({"questions": ["Did the bridge collapse?"]}), encoding="utf-8")
    factory = JsonQuestionFactory(tmp_path)

    questions = asyncio.run(factory.questions("ignored", "Brandonsford_001.txt"))

    assert questions == ["Did the bridge collapse?"]


def test_coverage_questions_cannot_be_empty(tmp_path: Path) -> None:
    (tmp_path / "Brandonsford_001.json").write_text('{"questions": []}', encoding="utf-8")
    factory = JsonQuestionFactory(tmp_path)

    with pytest.raises(MissingCuratedQuestionsError, match="empty"):
        asyncio.run(factory.questions("ignored", "Brandonsford_001.txt"))


def test_empty_exclusion_questions_are_not_scored(tmp_path: Path) -> None:
    (tmp_path / "Brandonsford_001.json").write_text('{"questions": []}', encoding="utf-8")
    metric = LedgerExclusionMetric(LiteLLMConfig(model="fake/model"), question_factory=JsonQuestionFactory(tmp_path, allow_empty=True))

    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT, source_path="Brandonsford_001.txt"), _OUTPUT))

    assert result.metric_name == "ledger_exclusion_not_applicable"


def test_conciseness_uses_transcript_not_prompt_scaffolding() -> None:
    metric = LedgerConcisenessMetric()

    result = asyncio.run(metric.evaluate("# Prompt", EvalCase(input=_INPUT), _OUTPUT))

    transcript_words = len(extract_session_transcript(_INPUT).split())
    expected_score = max(0.0, (transcript_words - len(ledger_content(_OUTPUT).split())) / transcript_words)
    assert result.score == pytest.approx(expected_score)


def test_ledger_content_excludes_scene_breakdown() -> None:
    assert "scene_breakdown" not in ledger_content(_OUTPUT)
    assert "signature_detail" not in ledger_content(_OUTPUT)
    assert "The bridge collapses." in ledger_content(_OUTPUT)
