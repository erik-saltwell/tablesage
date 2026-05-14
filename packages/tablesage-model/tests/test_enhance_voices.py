from __future__ import annotations

from pathlib import Path

import pytest
from tablesage_model import _paths
from tablesage_model._actions.players.enhance_voices import (
    delete_voice_samples_by_source,
    enhance_voices,
    select_enhancement_utterances,
)
from tablesage_model._settings import AppSettings, EnhanceVoicesSettings
from tablesage_model.io import load_player, save_campaign, save_discourse, save_player, save_player_set, save_session
from tablesage_model.model.campaign import Campaign, Session
from tablesage_model.model.cast import Embedding, Player, PlayerName, PlayerSet, ProvenanceType, VoiceSample
from tablesage_model.model.transcription import Discourse, Utterance, Word
from tablesage_model.protocols import NullPhasedProgressSink


def _utterance(text: str, *, speaker: str, start: float, end: float, margin: float) -> Utterance:
    words = (Word(text=text, start=start, end=end, speaker=speaker),)
    return Utterance(text=text, speaker=speaker, words=words, similarity_margin=margin)


def test_select_enhancement_utterances_applies_speaker_margin_and_duration_filters() -> None:
    settings = EnhanceVoicesSettings(
        min_margin_for_voice_sample=0.15,
        min_clip_seconds=1.0,
        max_clip_seconds=8.0,
    )
    discourse = Discourse(
        utterances=(
            _utterance("hello", speaker="Ada", start=0.0, end=2.0, margin=0.30),  # KEEP (idx 0)
            _utterance("yes", speaker="Ada", start=2.0, end=2.4, margin=0.30),  # short, drop
            _utterance("um", speaker="Ada", start=3.0, end=4.5, margin=0.05),  # low margin, drop
            _utterance("long monologue", speaker="Ada", start=5.0, end=20.0, margin=0.40),  # too long, drop
            _utterance("paladin line", speaker="Bryn", start=21.0, end=23.0, margin=0.30),  # wrong speaker, drop
            _utterance("again", speaker="Ada", start=24.0, end=27.5, margin=0.22),  # KEEP (idx 5)
        )
    )

    selected = select_enhancement_utterances(discourse, attendee_name="Ada", settings=settings)

    indexes = [idx for idx, _ in selected]
    assert indexes == [0, 5]
    assert selected[0][1].text == "hello"
    assert selected[1][1].text == "again"


def _sample(name: str, provenance_type: ProvenanceType, source: str, index: int) -> VoiceSample:
    return VoiceSample(
        filepath=Path("voice_clips") / name,
        embedding=Embedding(root=(0.1, 0.2, 0.3)),
        provenance_type=provenance_type,
        source=source,
        index=index,
    )


def test_delete_voice_samples_by_source_retains_only_non_matching_samples() -> None:
    keep_import = _sample("import.wav", ProvenanceType.IMPORT, "/tmp/clips", 0)
    keep_other_session = _sample("other.wav", ProvenanceType.SESSION_ENHANCEMENT, "session-two", 4)
    drop_a = _sample("a.wav", ProvenanceType.SESSION_ENHANCEMENT, "session-three", 0)
    drop_b = _sample("b.wav", ProvenanceType.SESSION_ENHANCEMENT, "session-three", 9)

    player = Player(
        slug="ada",
        name="Ada",
        voice_samples=(keep_import, drop_a, keep_other_session, drop_b),
        centroid=Embedding(root=(0.1, 0.2, 0.3)),
    )

    result = delete_voice_samples_by_source(
        player,
        source="session-three",
        provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
    )

    assert tuple(result.kept.voice_samples) == (keep_import, keep_other_session)
    assert tuple(result.removed) == (drop_a, drop_b)


def _seed_for_enhance(
    *,
    attendee_slugs: tuple[str, ...] = ("ada", "bryn"),
    player_set_slugs: tuple[str, ...] | None = None,
) -> None:
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    members = player_set_slugs if player_set_slugs is not None else attendee_slugs
    save_player_set(
        "sable-crown",
        PlayerSet(players=tuple(PlayerName(slug=s, name=s.title()) for s in members)),
    )
    for slug in members:
        save_player(
            "sable-crown",
            Player(
                slug=slug,
                name=slug.title(),
                voice_samples=(),
                centroid=Embedding(root=(0.1, 0.2, 0.3)),
            ),
        )
    from datetime import date

    save_session(
        "sable-crown",
        Session(
            session_date=date(2026, 5, 14),
            name="Session Three",
            slug="session-three",
            audio_filename="raw.m4a",
            attendees={slug: ("Game Master",) if slug == "ada" else ("Paladin",) for slug in attendee_slugs},
        ),
    )


def _discourse_for_two_attendees() -> Discourse:
    return Discourse(
        utterances=(
            _utterance("ada-hi", speaker="Ada", start=0.0, end=2.0, margin=0.30),
            _utterance("ada-um", speaker="Ada", start=2.0, end=4.0, margin=0.05),  # low margin
            _utterance("bryn-go", speaker="Bryn", start=5.0, end=7.0, margin=0.40),
        )
    )


@pytest.mark.anyio
async def test_enhance_voices_adds_session_enhanced_samples_with_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_for_enhance()
    save_discourse("sable-crown", "session-three", _discourse_for_two_attendees())
    # The cleaned audio file just needs to exist so the path resolves; ffmpeg.extract_clip is mocked.
    settings = AppSettings()
    cleaned_path = _paths.session_dir("sable-crown", "session-three") / settings.cleaned_audio_file
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.write_bytes(b"FAKE-CLEANED-AUDIO")

    async def fake_extract_clip(audio_path: Path, target: Path, start: float, end: float) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"FAKE-CLIP")

    class FakeEmbeddingFactory:
        async def extract_async(self, path: Path) -> Embedding:
            return Embedding(root=(0.5, 0.5, 0.0))

    import tablesage_model._actions.players.enhance_voices as mod

    monkeypatch.setattr(mod.ffmpeg, "extract_clip", fake_extract_clip)
    monkeypatch.setattr(mod, "EmbeddingFactory", FakeEmbeddingFactory)

    await enhance_voices("sable-crown", "session-three", AppSettings(), NullPhasedProgressSink())

    ada = load_player("sable-crown", "ada")
    bryn = load_player("sable-crown", "bryn")

    assert len(ada.voice_samples) == 1
    sample = ada.voice_samples[0]
    assert sample.provenance_type == ProvenanceType.SESSION_ENHANCEMENT
    assert sample.source == "session-three"
    assert sample.index == 0
    assert (_paths.player_dir("sable-crown", "ada") / sample.filepath).exists()

    assert len(bryn.voice_samples) == 1
    assert bryn.voice_samples[0].index == 2


@pytest.mark.anyio
async def test_enhance_voices_retracts_prior_samples_from_same_session_before_appending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _seed_for_enhance(attendee_slugs=("ada",))
    save_discourse("sable-crown", "session-three", _discourse_for_two_attendees())

    settings = AppSettings()
    cleaned_path = _paths.session_dir("sable-crown", "session-three") / settings.cleaned_audio_file
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.write_bytes(b"FAKE-CLEANED-AUDIO")

    # Pre-existing samples on Ada: one stale SESSION_ENHANCEMENT from session-three, one IMPORT to be preserved.
    ada_clips_dir = _paths.voice_clips_dir("sable-crown", "ada")
    ada_clips_dir.mkdir(parents=True, exist_ok=True)
    stale_path = ada_clips_dir / "stale.wav"
    stale_path.write_bytes(b"STALE")
    import_path = ada_clips_dir / "import.wav"
    import_path.write_bytes(b"IMPORT")

    relative_stale = Path(_paths.KnownDirectories.VOICE_CLIPS) / "stale.wav"
    relative_import = Path(_paths.KnownDirectories.VOICE_CLIPS) / "import.wav"
    stale_sample = VoiceSample(
        filepath=relative_stale,
        embedding=Embedding(root=(0.9, 0.0, 0.0)),
        provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
        source="session-three",
        index=99,
    )
    import_sample = VoiceSample(
        filepath=relative_import,
        embedding=Embedding(root=(0.0, 0.9, 0.0)),
        provenance_type=ProvenanceType.IMPORT,
        source="/tmp/clips",
        index=0,
    )
    save_player(
        "sable-crown",
        Player(
            slug="ada",
            name="Ada",
            voice_samples=(stale_sample, import_sample),
            centroid=Embedding(root=(0.5, 0.5, 0.0)),
        ),
    )

    async def fake_extract_clip(audio_path: Path, target: Path, start: float, end: float) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"FAKE-CLIP")

    class FakeEmbeddingFactory:
        async def extract_async(self, path: Path) -> Embedding:
            return Embedding(root=(0.5, 0.5, 0.0))

    import tablesage_model._actions.players.enhance_voices as mod

    monkeypatch.setattr(mod.ffmpeg, "extract_clip", fake_extract_clip)
    monkeypatch.setattr(mod, "EmbeddingFactory", FakeEmbeddingFactory)

    await enhance_voices("sable-crown", "session-three", AppSettings(), NullPhasedProgressSink())

    ada = load_player("sable-crown", "ada")
    sources = {(s.provenance_type, s.source) for s in ada.voice_samples}
    assert (ProvenanceType.IMPORT, "/tmp/clips") in sources
    assert (ProvenanceType.SESSION_ENHANCEMENT, "session-three") in sources
    assert not any(s.index == 99 for s in ada.voice_samples)  # the stale sample is gone
    assert not stale_path.exists()  # backing wav deleted
    assert import_path.exists()  # import wav preserved


@pytest.mark.anyio
async def test_enhance_voices_skips_attendees_not_in_current_player_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Session has attendees [ada, cara], but PlayerSet only contains [ada] (cara was removed).
    _seed_for_enhance(attendee_slugs=("ada", "cara"), player_set_slugs=("ada",))
    save_discourse(
        "sable-crown",
        "session-three",
        Discourse(
            utterances=(
                _utterance("ada-hi", speaker="Ada", start=0.0, end=2.0, margin=0.30),
                _utterance("cara-go", speaker="Cara", start=3.0, end=5.0, margin=0.30),
            )
        ),
    )

    settings = AppSettings()
    cleaned_path = _paths.session_dir("sable-crown", "session-three") / settings.cleaned_audio_file
    cleaned_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned_path.write_bytes(b"FAKE")

    async def fake_extract_clip(audio_path: Path, target: Path, start: float, end: float) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"FAKE-CLIP")

    class FakeEmbeddingFactory:
        async def extract_async(self, path: Path) -> Embedding:
            return Embedding(root=(0.5, 0.5, 0.0))

    import tablesage_model._actions.players.enhance_voices as mod

    monkeypatch.setattr(mod.ffmpeg, "extract_clip", fake_extract_clip)
    monkeypatch.setattr(mod, "EmbeddingFactory", FakeEmbeddingFactory)

    await enhance_voices("sable-crown", "session-three", AppSettings(), NullPhasedProgressSink())

    ada = load_player("sable-crown", "ada")
    assert len(ada.voice_samples) == 1
    # Cara should not have a Player file written, since she's not in PlayerSet.
    assert not _paths.player_file("sable-crown", "cara").exists()


def test_invalidate_destructive_change_retracts_session_enhanced_samples_across_all_players() -> None:
    from tablesage_model._actions.invalidation import InputChange, invalidate

    _seed_for_enhance(attendee_slugs=("ada", "bryn"))

    # Set up Ada with: 1 import sample (keep) + 1 session-three sample (drop).
    # Set up Bryn with: 1 session-three sample (drop) + 1 session-other sample (keep).
    ada_dir = _paths.voice_clips_dir("sable-crown", "ada")
    bryn_dir = _paths.voice_clips_dir("sable-crown", "bryn")
    ada_dir.mkdir(parents=True, exist_ok=True)
    bryn_dir.mkdir(parents=True, exist_ok=True)

    ada_import = ada_dir / "import.wav"
    ada_import.write_bytes(b"IMPORT")
    ada_session = ada_dir / "ada-session.wav"
    ada_session.write_bytes(b"SESSION")
    bryn_session3 = bryn_dir / "bryn-session3.wav"
    bryn_session3.write_bytes(b"SESSION3")
    bryn_session_other = bryn_dir / "bryn-other.wav"
    bryn_session_other.write_bytes(b"OTHER")

    def rel(p: Path) -> Path:
        return Path(_paths.KnownDirectories.VOICE_CLIPS) / p.name

    save_player(
        "sable-crown",
        Player(
            slug="ada",
            name="Ada",
            voice_samples=(
                VoiceSample(
                    filepath=rel(ada_import),
                    embedding=Embedding(root=(0.7, 0.7, 0.0)),
                    provenance_type=ProvenanceType.IMPORT,
                    source="/tmp/clips",
                    index=0,
                ),
                VoiceSample(
                    filepath=rel(ada_session),
                    embedding=Embedding(root=(0.0, 1.0, 0.0)),
                    provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
                    source="session-three",
                    index=0,
                ),
            ),
            centroid=Embedding(root=(0.35, 0.85, 0.0)),
        ),
    )
    save_player(
        "sable-crown",
        Player(
            slug="bryn",
            name="Bryn",
            voice_samples=(
                VoiceSample(
                    filepath=rel(bryn_session3),
                    embedding=Embedding(root=(1.0, 0.0, 0.0)),
                    provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
                    source="session-three",
                    index=2,
                ),
                VoiceSample(
                    filepath=rel(bryn_session_other),
                    embedding=Embedding(root=(0.0, 0.0, 1.0)),
                    provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
                    source="session-other",
                    index=0,
                ),
            ),
            centroid=Embedding(root=(0.5, 0.0, 0.5)),
        ),
    )

    invalidate("sable-crown", "session-three", InputChange.PROCESS_SESSION_RERUN, AppSettings())

    ada_after = load_player("sable-crown", "ada")
    bryn_after = load_player("sable-crown", "bryn")

    assert tuple(s.source for s in ada_after.voice_samples) == ("/tmp/clips",)
    assert tuple(s.source for s in bryn_after.voice_samples) == ("session-other",)
    assert not ada_session.exists()
    assert not bryn_session3.exists()
    assert ada_import.exists()
    assert bryn_session_other.exists()
