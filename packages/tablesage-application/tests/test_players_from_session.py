from __future__ import annotations

import uuid
from pathlib import Path

import pytest
import tablesage_application.players_from_session as players_from_session_module
from tablesage_application import Application
from tablesage_application.paths import ARTIFACTS, ArtifactName
from tablesage_application.players_from_session import Stage, select_enhancement_utterances
from tablesage_model.model import GAME_MASTER_ROLE, Campaign, Player
from tablesage_tools.embeddings import Embedding
from tablesage_tools.model import Transcript, Utterance


def _utterance(speaker: str, start: float, end: float, margin: float | None) -> Utterance:
    return Utterance(speaker=speaker, start=start, end=end, words=[], similarity_margin=margin)


# --- select_enhancement_utterances (pure, no I/O) ---


def test_select_enhancement_utterances_filters_by_speaker_margin_and_duration() -> None:
    utterances = [
        _utterance("Alice", 0.0, 2.0, margin=0.5),  # qualifies
        _utterance("Alice", 2.0, 3.5, margin=0.05),  # margin too low
        _utterance("Alice", 3.5, 3.6, margin=0.5),  # too short
        _utterance("Alice", 3.6, 15.0, margin=0.5),  # too long
        _utterance("Bob", 15.0, 17.0, margin=0.5),  # different speaker
        _utterance("Unassigned Speaker", 17.0, 19.0, margin=0.9),  # unassigned
        _utterance("Alice", 19.0, 21.0, margin=None),  # missing margin
    ]

    selected = select_enhancement_utterances(utterances, "Alice", min_margin=0.1, min_seconds=1.0, max_seconds=8.0)

    assert selected == [utterances[0]]


def test_select_enhancement_utterances_boundary_values_are_inclusive() -> None:
    utterances = [
        _utterance("Alice", 0.0, 1.0, margin=0.1),
        _utterance("Alice", 10.0, 18.0, margin=0.1),
    ]

    selected = select_enhancement_utterances(utterances, "Alice", min_margin=0.1, min_seconds=1.0, max_seconds=8.0)

    assert selected == utterances


# --- Application.enhance_players_from_session (orchestration) ---


async def _fake_extract_clip(input_path: Path, output_wav: Path, start: float, end: float) -> None:
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    output_wav.write_bytes(f"{start}-{end}".encode())


@pytest.fixture(autouse=True)
def _stub_extract_clip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(players_from_session_module, "extract_clip", _fake_extract_clip)


def _setup_session(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Application, uuid.UUID, Player, Player]:
    application = Application(tmp_path)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    campaign = application.create_campaign(Campaign(name="Iron Pact"))
    alice = application.create_player(Player(name="Alice"))
    bob = application.create_player(Player(name="Bob"))
    application.add_player_to_campaign(campaign.id, alice.id, GAME_MASTER_ROLE)
    application.add_player_to_campaign(campaign.id, bob.id, "Bob's Character")

    # roster membership predates session creation, so both are auto-seeded as attendees
    game_session = application.create_session(campaign.id, "Session One")

    session_folder = application.session_folder(game_session.id)
    (session_folder / ARTIFACTS[ArtifactName.INPUT_AUDIO].filename).write_bytes(b"fake audio")

    transcript = Transcript(
        utterances=[
            _utterance("Alice", 0.0, 2.0, margin=0.5),
            _utterance("Alice", 2.0, 4.0, margin=0.5),
            _utterance("Alice", 4.0, 4.05, margin=0.5),  # too short, excluded
            _utterance("Bob", 5.0, 7.0, margin=0.5),
            _utterance("Unassigned Speaker", 7.0, 9.0, margin=0.9),
        ]
    )
    transcript.save(session_folder / ARTIFACTS[ArtifactName.TRANSCRIPT].filename)

    return application, game_session.id, alice, bob


def test_enhance_players_from_session_extracts_qualifying_clips_and_recomputes_centroids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, session_id, alice, bob = _setup_session(tmp_path, monkeypatch)

    result = application.enhance_players_from_session(session_id)

    assert result.enhanced_player_count == 2
    assert result.clip_count == 3  # 2 for Alice, 1 for Bob

    alice_folder = tmp_path / ".tablesage" / "players" / "Alice"
    bob_folder = tmp_path / ".tablesage" / "players" / "Bob"
    assert len(list(alice_folder.glob("session-*.wav"))) == 2
    assert len(list(bob_folder.glob("session-*.wav"))) == 1

    updated_alice = application.get_player(alice.id)
    updated_bob = application.get_player(bob.id)
    assert updated_alice.centroid_embedding is not None
    assert updated_bob.centroid_embedding is not None


def test_enhance_players_from_session_reports_staged_progress(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application, session_id, _alice, _bob = _setup_session(tmp_path, monkeypatch)

    calls: list[tuple[Stage, int, int]] = []
    application.enhance_players_from_session(
        session_id, on_progress=lambda stage, completed, total: calls.append((stage, completed, total))
    )

    extracting_calls = [c for c in calls if c[0] == Stage.EXTRACTING]
    recompute_calls = [c for c in calls if c[0] == Stage.RECOMPUTING_CENTROIDS]
    assert extracting_calls[0] == (Stage.EXTRACTING, 0, 3)
    assert extracting_calls[-1] == (Stage.EXTRACTING, 3, 3)
    assert recompute_calls == [(Stage.RECOMPUTING_CENTROIDS, 1, 2), (Stage.RECOMPUTING_CENTROIDS, 2, 2)]


def test_enhance_players_from_session_rerun_replaces_prior_clips_as_a_unit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    application, session_id, alice, _bob = _setup_session(tmp_path, monkeypatch)

    application.enhance_players_from_session(session_id)
    alice_folder = tmp_path / ".tablesage" / "players" / "Alice"
    first_run_clips = {p.name for p in alice_folder.glob("session-*.wav")}
    assert len(first_run_clips) == 2

    application.enhance_players_from_session(session_id)
    second_run_clips = {p.name for p in alice_folder.glob("session-*.wav")}

    assert len(second_run_clips) == 2
    assert first_run_clips.isdisjoint(second_run_clips)


def test_enhance_players_from_session_zero_qualifying_utterances_still_retracts_prior_clips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    application, session_id, alice, _bob = _setup_session(tmp_path, monkeypatch)
    application.enhance_players_from_session(session_id)
    alice_folder = tmp_path / ".tablesage" / "players" / "Alice"
    assert len(list(alice_folder.glob("session-*.wav"))) == 2

    # Tighten the margin bar so nothing qualifies on the next run -- a fresh Application
    # pointed at the same directory, since AppSettings is only ever supplied at construction.
    tightened_enhance_voices = application.settings.enhance_voices.model_copy(update={"min_margin_for_voice_sample": 0.99})
    tightened_settings = application.settings.model_copy(update={"enhance_voices": tightened_enhance_voices})
    application = Application(tmp_path, settings=tightened_settings)
    monkeypatch.setattr(application, "_embed_clip", lambda path: Embedding(root=(1.0, 0.0)))

    result = application.enhance_players_from_session(session_id)

    assert result.enhanced_player_count == 0
    assert list(alice_folder.glob("session-*.wav")) == []
