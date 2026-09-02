from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from prompt_model.config import LiteLLMConfig
from prompt_model.helpers import acomplete
from pydantic import TypeAdapter

from .bundle import QUESTIONS_FILENAME, EvaluationBundle
from .cache import ContentCache
from .models import CompletenessQuestion, GeneratedQuestion, GeneratedQuestionList


@dataclass(frozen=True)
class TranscriptChunk:
    start_line: int
    end_line: int
    text: str


def chunk_transcript(transcript: str, *, target_words: int = 2500, overlap_lines: int = 8) -> list[TranscriptChunk]:
    if target_words <= 0:
        raise ValueError("target_words must be positive.")
    if overlap_lines < 0:
        raise ValueError("overlap_lines must not be negative.")
    lines: list[str] = transcript.splitlines(keepends=True)
    if not lines:
        return []

    chunks: list[TranscriptChunk] = []
    start: int = 0
    while start < len(lines):
        end: int = start
        word_count: int = 0
        while end < len(lines) and (word_count < target_words or end == start):
            word_count += len(lines[end].split())
            end += 1
        chunks.append(TranscriptChunk(start_line=start + 1, end_line=end, text="".join(lines[start:end])))
        if end >= len(lines):
            break
        next_start: int = max(start + 1, end - overlap_lines)
        start = next_start
    return chunks


async def _generate_chunk_questions(
    chunk: TranscriptChunk,
    judge_llm: LiteLLMConfig,
    cache: ContentCache,
) -> list[GeneratedQuestion]:
    cache_key: str = cache.key("questions-v1", chunk.start_line, chunk.end_line, chunk.text, judge_llm.model_dump(mode="json"))
    cached: GeneratedQuestionList | None = cache.load("question-chunks", cache_key, GeneratedQuestionList)
    if cached is not None:
        return cached.questions
    result: GeneratedQuestionList = await acomplete(
        system_prompt=(
            "Generate exhaustive closed-ended yes/no questions for the supplied RPG transcript chunk. Every question's correct answer must "
            "be yes from the transcript. Include every change to the fiction, explicitly framed recap fact, character introduction, and "
            "final canonical state after a correction. Exclude table talk, speculative strategy that establishes no fictional decision, "
            "and rules, rolls, statistics, or procedures. When mechanics establish a fictional consequence, ask only about the "
            "consequence. Preserve names, attribution, causality, and uncertainty. Each question must test one atomic fact. Evidence must "
            "be a short verbatim quote."
        ),
        user_prompt=(f"<source_range>lines {chunk.start_line}-{chunk.end_line}</source_range>\n<transcript>\n{chunk.text}\n</transcript>"),
        config=judge_llm,
        response_format=GeneratedQuestionList,
        log_name="tablesage_questions:generate",
    )
    cache.save("question-chunks", cache_key, result)
    return result.questions


async def _deduplicate_questions(questions: list[GeneratedQuestion], judge_llm: LiteLLMConfig) -> list[GeneratedQuestion]:
    if not questions:
        return []
    result: GeneratedQuestionList = await acomplete(
        system_prompt=(
            "Semantically deduplicate these RPG completeness questions. Merge only questions testing the same event or canonical state. "
            "Repeated events at different times are distinct. Preserve the most specific wording, category, and a verbatim evidence quote. "
            "Return questions in chronological order."
        ),
        user_prompt=json.dumps([question.model_dump(mode="json") for question in questions], ensure_ascii=False),
        config=judge_llm,
        response_format=GeneratedQuestionList,
        log_name="tablesage_questions:deduplicate",
    )
    return result.questions


async def generate_questions(
    bundle: EvaluationBundle,
    judge_llm: LiteLLMConfig,
    *,
    target_words: int = 2500,
    overlap_lines: int = 8,
) -> list[CompletenessQuestion]:
    chunks: list[TranscriptChunk] = chunk_transcript(
        bundle.transcript,
        target_words=target_words,
        overlap_lines=overlap_lines,
    )
    cache = ContentCache(bundle.root / ".cache")
    generated: list[GeneratedQuestion] = []
    for chunk in chunks:
        generated.extend(await _generate_chunk_questions(chunk, judge_llm, cache))
    deduplicated: list[GeneratedQuestion] = await _deduplicate_questions(generated, judge_llm)
    questions: list[CompletenessQuestion] = [
        CompletenessQuestion(
            id=f"q{index:04d}",
            category=question.category,
            question=question.question,
            evidence=question.evidence,
            enabled=True,
        )
        for index, question in enumerate(deduplicated, start=1)
    ]
    path: Path = bundle.root / QUESTIONS_FILENAME
    path.write_text(
        json.dumps([question.model_dump(mode="json") for question in questions], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return TypeAdapter(list[CompletenessQuestion]).validate_json(path.read_text(encoding="utf-8"))
