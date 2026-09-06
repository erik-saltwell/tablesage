"""Generate review-draft Summary coverage questions from Brandonsford Ledgers."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from prompt_model.config import LiteLLMConfig
from prompt_model.helpers import acomplete
from prompt_model_metrics.summarization.prompt_schemas import PromptQuestions
from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS, ArtifactName

REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_NAME = "Brandonsford"
OUTPUT_DIRECTORY = REPO_ROOT / "data_prompts" / "summary" / "coverage_questions"
UTILITY_PROMPT_PATH = REPO_ROOT / "data_utility_prompts" / "generate_questions.md"
QUESTION_MODEL = LiteLLMConfig(model="anthropic/claude-sonnet-5")


def slugify(value: str) -> str:
    """Use underscores for whitespace and characters unsafe in a filename."""
    return re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")


async def main() -> None:
    application = Application(REPO_ROOT)
    campaigns = [campaign for campaign in application.list_campaigns() if campaign.name == CAMPAIGN_NAME]
    if len(campaigns) != 1:
        raise SystemExit(f"Expected exactly one campaign named {CAMPAIGN_NAME!r}; found {len(campaigns)}.")
    campaign = campaigns[0]
    system_prompt = UTILITY_PROMPT_PATH.read_text(encoding="utf-8")
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    for game_session in application.list_sessions(campaign.id):
        ledger_path = application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.LEDGER].filename
        if not ledger_path.is_file():
            raise SystemExit(f"{ledger_path} does not exist -- generate the Ledger for this session first.")
        response: PromptQuestions = await acomplete(
            system_prompt=system_prompt,
            user_prompt=f"<input>\n{ledger_path.read_text(encoding='utf-8')}\n</input>",
            config=QUESTION_MODEL,
            response_format=PromptQuestions,
            log_name="generate_summary_coverage_questions",
        )
        output_path = OUTPUT_DIRECTORY / f"{slugify(campaign.name)}_{game_session.sequence_number:03d}.json"
        output_path.write_text(json.dumps({"questions": response.questions}, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote {output_path.relative_to(REPO_ROOT)} ({len(response.questions)} questions)")


if __name__ == "__main__":
    asyncio.run(main())
