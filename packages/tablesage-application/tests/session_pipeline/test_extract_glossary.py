from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest
from tablesage_application import Application
from tablesage_application.llm import PromptName
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline import extract_glossary as extract_glossary_module
from tablesage_application.session_pipeline.extract_glossary import (
    AttendeePromptEntry,
    GlossaryPromptEntry,
    GlossaryProposal,
)
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_model.settings import AppSettings
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _role_transcript(path: Path) -> None:
    Transcript.from_words([TranscriptionWord(text="We meet Veyra.", type=SpeechType.WORD, start=0.0, end=1.0, speaker="Aria")]).save(
        path / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename
    )


@pytest.mark.anyio
async def test_extract_glossary_requests_structured_proposals(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    async def _stub_call(
        prompt: PromptName,
        template_data: object,
        model: str,
        response_model: object | None = None,
    ) -> str:
        captured.update(prompt=prompt, template_data=template_data, model=model, response_model=response_model)
        return '{"entries":[{"term":"Veyra","description":"An NPC envoy."}]}'

    monkeypatch.setattr(extract_glossary_module, "call_llm_with_prompt", _stub_call)
    attendees = [AttendeePromptEntry(player_name="Erik", roles=("Aria",))]
    glossary = [GlossaryPromptEntry(term="Ironhold", description="A city.")]

    result = await extract_glossary_module.extract_glossary("**Aria** - Hello", attendees, glossary, "test-model")

    assert result == [GlossaryProposal(term="Veyra", description="An NPC envoy.")]
    assert captured["prompt"] is PromptName.EXTRACT_GLOSSARY
    assert captured["model"] == "test-model"
    assert captured["response_model"] is extract_glossary_module.GlossaryExtractionResponse
    prompt_data = cast(extract_glossary_module.GlossaryExtractionPromptData, captured["template_data"])
    assert prompt_data.attendees == attendees
    assert prompt_data.glossary == glossary


def test_filter_existing_terms_is_trimmed_and_case_insensitive() -> None:
    proposals = [
        GlossaryProposal(term=" ironhold ", description="Different definition"),
        GlossaryProposal(term="Veyra", description=None),
    ]

    assert extract_glossary_module.filter_existing_terms(proposals, ["Ironhold"]) == [proposals[1]]


def test_application_extracts_context_and_filters_existing_terms(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application = Application(tmp_path, AppSettings(llm_model="test-model"))
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    player = application.create_player(Player(name="Erik"))
    application.add_player_to_campaign(campaign.id, player.id, "Aria")
    game_session = application.create_session(campaign.id, "Session One")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold", description="A city."))
    _role_transcript(application.session_folder(game_session.id))
    captured: dict[str, object] = {}

    async def _stub_extract(
        transcript: str,
        attendees: tuple[AttendeePromptEntry, ...],
        glossary: tuple[GlossaryPromptEntry, ...],
        model: str,
    ) -> list[GlossaryProposal]:
        captured.update(transcript=transcript, attendees=attendees, glossary=glossary, model=model)
        return [
            GlossaryProposal(term="ironhold", description="Different"),
            GlossaryProposal(term="Veyra", description="An envoy."),
        ]

    monkeypatch.setattr(extract_glossary_module, "extract_glossary", _stub_extract)

    result = application.extract_glossary(game_session.id)

    assert result == [GlossaryProposal(term="Veyra", description="An envoy.")]
    assert captured["attendees"] == (AttendeePromptEntry(player_name="Erik", roles=("Aria",)),)
    assert captured["glossary"] == (GlossaryPromptEntry(term="Ironhold", description="A city."),)
    assert captured["model"] == "test-model"
    assert "Veyra" in cast(str, captured["transcript"])


def test_complete_glossary_extraction_keeps_existing_and_first_reviewed_duplicate(tmp_path: Path) -> None:
    application = Application(tmp_path)
    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    game_session = application.create_session(campaign.id, "Session One")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ironhold", description="Original"))

    result = application.complete_glossary_extraction(
        game_session.id,
        [
            GlossaryProposal(term="Veyra", description="First definition"),
            GlossaryProposal(term=" vEYRA ", description="Second definition"),
            GlossaryProposal(term="ironhold", description="Replacement"),
            GlossaryProposal(term="Ash Sea", description=""),
        ],
    )

    assert result.added_count == 2
    assert result.skipped_duplicate_count == 2
    entries = {entry.term: entry.description for entry in application.list_glossary_entries(campaign.id)}
    assert entries == {"Ironhold": "Original", "Veyra": "First definition", "Ash Sea": None}
