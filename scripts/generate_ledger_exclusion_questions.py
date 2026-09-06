"""Generate review-draft Ledger exclusion questions from session transcripts."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from optimize_prompts.ledger_metrics import extract_session_transcript
from prompt_model.config import LiteLLMConfig
from prompt_model.helpers import acomplete
from prompt_model_metrics.summarization.prompt_schemas import PromptQuestions

REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_DIRECTORY = REPO_ROOT / "data_prompts" / "ledger" / "inputs"
OUTPUT_DIRECTORY = REPO_ROOT / "data_prompts" / "ledger" / "exclusion_questions"
UTILITY_PROMPT_PATH = REPO_ROOT / "data_utility_prompts" / "generate_exclusion_questions.md"
INPUT_FILENAMES = ("Brandonsford_001.txt", "Brandonsford_002.txt", "Brandonsford_003.txt")
QUESTION_MODEL = LiteLLMConfig(model="anthropic/claude-sonnet-5")


async def main() -> None:
    system_prompt = UTILITY_PROMPT_PATH.read_text(encoding="utf-8")
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for input_filename in INPUT_FILENAMES:
        input_path = INPUT_DIRECTORY / input_filename
        transcript = extract_session_transcript(input_path.read_text(encoding="utf-8"))
        response: PromptQuestions = await acomplete(
            system_prompt=system_prompt,
            user_prompt=f"<input>\n{transcript}\n</input>",
            config=QUESTION_MODEL,
            response_format=PromptQuestions,
            log_name="generate_ledger_exclusion_questions",
        )
        output_path = OUTPUT_DIRECTORY / f"{input_path.stem}.json"
        output_path.write_text(json.dumps({"questions": response.questions}, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(REPO_ROOT)} ({len(response.questions)} questions)")


if __name__ == "__main__":
    asyncio.run(main())
