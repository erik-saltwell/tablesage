from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.session_pipeline.generate_ledger import LedgerGenerationResponse
from tablesage_model.model import Campaign, GlossaryEntry, Player
from tablesage_prompt_metrics.bundle import EvaluationBundle, export_ledger_bundle
from tablesage_prompt_metrics.models import CompletenessQuestion, QuestionCategory
from tablesage_prompt_metrics.plugin import build_cases, build_metrics, build_scorer
from tablesage_prompt_metrics.profiles import write_profiles
from tablesage_tools.model import SpeechType, Transcript, TranscriptionWord


def _word(text: str, speaker: str) -> TranscriptionWord:
    return TranscriptionWord(text=text, type=SpeechType.WORD, start=0.0, end=1.0, speaker=speaker)


def _session(repo_root: Path) -> None:
    application = Application(repo_root)
    campaign = application.create_campaign(Campaign(name="Brandonsford"))
    player = application.create_player(Player(name="Alice"))
    application.add_player_to_campaign(campaign.id, player.id, "Zaria")
    game_session = application.create_session(campaign.id, "The Gate")
    application.create_glossary_entry(GlossaryEntry(campaign_id=campaign.id, term="Ashmoor", description="The blighted moorland."))
    transcript = Transcript.from_words([_word("The gate opens.", "Zaria")])
    transcript.save(application.session_folder(game_session.id) / ARTIFACTS[ArtifactName.ROLE_TRANSCRIPT].filename)


def test_export_ledger_bundle_contains_exact_inputs_schema_and_hashes(tmp_path: Path) -> None:
    _session(tmp_path)
    destination = tmp_path / "bundle"

    bundle = export_ledger_bundle(tmp_path, "Brandonsford", "001", destination)

    assert bundle.manifest.campaign_name == "Brandonsford"
    assert bundle.manifest.session_sequence == "001"
    assert "<known_session_roles>\n- Zaria" in bundle.user_prompt
    assert "<session_attendees>\n- Alice: Zaria" in bundle.user_prompt
    assert "<glossary>\n- Ashmoor: The blighted moorland." in bundle.user_prompt
    assert "**Zaria** - The gate opens." in bundle.transcript
    assert bundle.response_schema == LedgerGenerationResponse.model_json_schema()
    assert bundle.system_prompt

    reloaded = EvaluationBundle(destination)
    assert reloaded.user_prompt == bundle.user_prompt


def test_bundle_refuses_overwrite_and_detects_changed_exported_file(tmp_path: Path) -> None:
    _session(tmp_path)
    destination = tmp_path / "bundle"
    export_ledger_bundle(tmp_path, "Brandonsford", "001", destination)

    with pytest.raises(FileExistsError, match="already exists"):
        export_ledger_bundle(tmp_path, "Brandonsford", "001", destination)

    (destination / "transcript.md").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="changed since export"):
        EvaluationBundle(destination)


def test_profiles_reference_external_factories_and_exported_schema(tmp_path: Path) -> None:
    _session(tmp_path)
    bundle = export_ledger_bundle(tmp_path, "Brandonsford", "001", tmp_path / "bundle")

    smoke_path, full_path = write_profiles(bundle)

    smoke = smoke_path.read_text(encoding="utf-8")
    full = full_path.read_text(encoding="utf-8")
    assert "tablesage_prompt_metrics:build_metrics" in smoke
    assert "response-schema.json" in smoke
    assert "iterations: 1" in smoke
    assert "iterations: 8" in full
    assert json.loads((bundle.root / "manifest.json").read_text(encoding="utf-8"))["version"] == 1


def test_external_factories_load_bundle_components(tmp_path: Path) -> None:
    _session(tmp_path)
    bundle = export_ledger_bundle(tmp_path, "Brandonsford", "001", tmp_path / "bundle")
    question = CompletenessQuestion(
        id="q0001",
        category=QuestionCategory.FICTION_CHANGE,
        question="Did the gate open?",
        evidence="The gate opens.",
    )
    (bundle.root / "questions.json").write_text(
        json.dumps([question.model_dump(mode="json")]),
        encoding="utf-8",
    )
    context = SimpleNamespace(settings_dir=tmp_path, judge_llm={"model": "test-judge"})
    config = {"bundle": "bundle"}

    cases = build_cases(context, config)
    metrics = build_metrics(context, config)
    scorer = build_scorer(context, config)

    assert len(cases) == 1
    assert cases[0].retrieval_context == [bundle.transcript]
    assert [metric.name for metric in metrics] == [
        "schema_correctness",
        "no_hallucinations",
        "completeness",
        "table_talk_exclusion",
        "mechanics_exclusion",
        "concision",
    ]
    assert scorer.__class__.__name__ == "LedgerScorer"
