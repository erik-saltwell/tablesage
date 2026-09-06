"""Generate a review draft of coverage questions from a persisted Ledger JSON file."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from prompt_model.config import LiteLLMConfig
from prompt_model.helpers import acomplete
from pydantic import BaseModel, ConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_NAME = "Brandonsford"
CAMPAIGN_DIRECTORY = REPO_ROOT / ".tablesage" / "campaigns" / CAMPAIGN_NAME
UTILITY_PROMPT_PATH = REPO_ROOT / "data_utility_prompts" / "generate_ledger_coverage_questions.md"
OUTPUT_DIRECTORY = REPO_ROOT / "data_prompts" / "ledger" / "coverage_questions"
QUESTION_MODEL = LiteLLMConfig(model="anthropic/claude-sonnet-5", timeout=1200)


class LedgerCoverageQuestionDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_candidates: list[str]
    optional_candidates: list[str]
    review_notes: list[str]
    questions: list[str]


async def complete(source: dict[str, object], *, log_suffix: str) -> LedgerCoverageQuestionDraft:
    return await acomplete(
        system_prompt=UTILITY_PROMPT_PATH.read_text(encoding="utf-8"),
        user_prompt=f"<ledger_json>\n{json.dumps(source, indent=2)}\n</ledger_json>",
        config=QUESTION_MODEL,
        response_format=LedgerCoverageQuestionDraft,
        log_name=f"generate_ledger_coverage_questions_from_ledger_{log_suffix}",
    )


def merge_drafts(drafts: list[LedgerCoverageQuestionDraft]) -> LedgerCoverageQuestionDraft:
    required = list(dict.fromkeys(question for draft in drafts for question in draft.required_candidates))
    required_set = set(required)
    optional = list(dict.fromkeys(question for draft in drafts for question in draft.optional_candidates if question not in required_set))
    notes = list(dict.fromkeys(note for draft in drafts for note in draft.review_notes))
    return LedgerCoverageQuestionDraft(
        required_candidates=required,
        optional_candidates=optional,
        review_notes=notes,
        questions=[],
    )


async def generate(session_number: str, *, chunk_size: int | None) -> None:
    ledger_path = CAMPAIGN_DIRECTORY / session_number / "ledger.json"
    output_path = OUTPUT_DIRECTORY / f"{CAMPAIGN_NAME}_{session_number}_draft.json"
    if not ledger_path.is_file():
        raise FileNotFoundError(f"Ledger not found: {ledger_path}")

    source = json.loads(ledger_path.read_text(encoding="utf-8"))
    if chunk_size is None:
        response = await complete(source, log_suffix=session_number)
        checkpoint_paths: list[Path] = []
    else:
        utterances = source.get("utterances")
        if not isinstance(utterances, list):
            raise ValueError(f"Ledger has no utterance list: {ledger_path}")
        chunks: list[dict[str, object]] = []
        for offset in range(0, len(utterances), chunk_size):
            chunk = dict(source)
            chunk["utterances"] = utterances[offset : offset + chunk_size]
            if offset > 0:
                chunk.pop("preamble", None)
            chunks.append(chunk)
        drafts = []
        checkpoint_paths = []
        for index, chunk in enumerate(chunks, start=1):
            draft = await complete(chunk, log_suffix=f"{session_number}_part_{index:02d}")
            drafts.append(draft)
            checkpoint_path = output_path.with_suffix(f".part-{index:02d}.json")
            checkpoint_paths.append(checkpoint_path)
            checkpoint_path.write_text(draft.model_dump_json(indent=2) + "\n", encoding="utf-8")
            print(f"Wrote checkpoint {checkpoint_path.relative_to(REPO_ROOT)}")
        response = merge_drafts(drafts)
    if response.questions:
        raise ValueError("The generated review draft must leave the final questions list empty.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.model_dump_json(indent=2) + "\n", encoding="utf-8")
    for checkpoint_path in checkpoint_paths:
        checkpoint_path.unlink()
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)} "
        f"({len(response.required_candidates)} required, {len(response.optional_candidates)} optional)"
    )


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sessions", nargs="+", help="Three-digit Brandonsford session numbers, such as 002 003.")
    parser.add_argument("--chunk-size", type=int, help="Generate from contiguous utterance chunks of this size.")
    args = parser.parse_args()
    if any(not session.isdigit() or len(session) != 3 for session in args.sessions):
        parser.error("Every session must be a three-digit number, such as 002.")
    if args.chunk_size is not None and args.chunk_size < 1:
        parser.error("--chunk-size must be positive.")
    await asyncio.gather(*(generate(session, chunk_size=args.chunk_size) for session in args.sessions))


if __name__ == "__main__":
    asyncio.run(main())
