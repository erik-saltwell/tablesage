"""Ephemeral reincorporation seeds grounded in a complete Campaign recap."""

from pathlib import Path
from tempfile import TemporaryDirectory

from litellm.exceptions import ContextWindowExceededError
from pydantic import Field

from .campaign_recap import CampaignSceneRecap, Record, Text
from .llm import PromptName, call_llm_with_prompt


class Opportunity(Record):
    title: Text
    from_campaign: Text
    opportunity: Text


class OpportunitySet(Record):
    opportunities: tuple[Opportunity, ...] = Field(max_length=5)


class OpportunityResult(Record):
    campaign_name: Text
    prompt: Text
    pitches: OpportunitySet

    def markdown(self) -> str:
        sections = [f"# {self.campaign_name} — Reincorporation Opportunities", f"## Upcoming Session\n\n{self.prompt}"]
        for pitch in self.pitches.opportunities:
            sections.append(f"## {pitch.title}\n\n### From the Campaign\n\n{pitch.from_campaign}\n\n### Opportunity\n\n{pitch.opportunity}")
        if not self.pitches.opportunities:
            sections.append("No strong opportunities were found for this situation. Try revising the prompt.")
        return "\n\n".join(sections) + "\n"


class PromptData(Record):
    recap: str
    upcoming: Text


async def generate(recap: CampaignSceneRecap, prompt: str, model: str, timeout: float) -> OpportunityResult:
    data = PromptData(recap=recap.model_dump_json(), upcoming=prompt)
    try:
        raw = await call_llm_with_prompt(PromptName.GENERATE_OPPORTUNITIES, data, model, response_model=OpportunitySet, timeout=timeout)
    except ContextWindowExceededError as exc:
        raise ValueError("This Campaign is too large for Generate Opportunities in this version.") from exc
    return OpportunityResult(campaign_name=recap.campaign_name, prompt=data.upcoming, pitches=OpportunitySet.model_validate_json(raw))


def save(result: OpportunityResult, destination: Path, *, overwrite: bool = False) -> None:
    """Stage the complete document before replacing an explicitly approved destination."""
    with TemporaryDirectory(prefix=".opportunities-", dir=destination.parent) as staging:
        temporary = Path(staging) / "opportunities.md"
        temporary.write_text(result.markdown(), encoding="utf-8")
        if overwrite:
            temporary.replace(destination)
        else:
            # Atomic no-clobber publication, including files created while the picker was open.
            import os

            os.link(temporary, destination)
