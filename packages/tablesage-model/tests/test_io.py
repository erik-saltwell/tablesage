from __future__ import annotations

from datetime import date
from pathlib import Path

from tablesage_model import _paths
from tablesage_model.io import (
    cleanup_orphan_campaign_dirs,
    cleanup_orphan_player_dirs,
    cleanup_orphan_session_dirs,
    create_campaign,
    delete_campaign,
    delete_player,
    delete_session,
    load_app_settings,
    load_campaign,
    load_campaign_set,
    load_campaign_summaries,
    load_discourse,
    load_player,
    load_player_set,
    load_session,
    load_session_set,
    load_summary,
    save_app_settings,
    save_campaign,
    save_campaign_set,
    save_discourse,
    save_player,
    save_player_set,
    save_session,
    save_session_set,
    save_summary,
)
from tablesage_model.model.artifacts import Summary
from tablesage_model.model.campaign import Campaign, CampaignSet, GlossaryEntry, Session, SessionSet
from tablesage_model.model.campaign.campaign_set import CampaignName
from tablesage_model.model.campaign.session_set import SessionName
from tablesage_model.model.cast import Embedding, Player, PlayerName, PlayerSet, ProvenanceType, VoiceSample
from tablesage_model.model.transcription import Discourse, Utterance, Word


def test_glossary_entry_constructs_with_term_and_description() -> None:
    entry = GlossaryEntry(term="Quarl", description="A lich-king who rules the Iron Pact")
    assert entry.term == "Quarl"
    assert entry.description == "A lich-king who rules the Iron Pact"


def test_glossary_entry_allows_empty_description() -> None:
    entry = GlossaryEntry(term="Quarl", description="")
    assert entry.description == ""


def test_campaign_set_round_trips() -> None:
    campaign_set = CampaignSet(campaigns=(CampaignName(slug="sable-crown", name="Sable Crown"),))

    save_campaign_set(campaign_set)

    assert load_campaign_set() == campaign_set


def test_create_campaign_adds_campaign_to_campaign_set_and_saves_campaign() -> None:
    save_campaign_set(CampaignSet(campaigns=(CampaignName(slug="sable-crown", name="Sable Crown"),)))

    slug = create_campaign("Iron Pact", default_gm="Ada", system="D&D 5e")

    assert slug == "iron-pact"
    assert load_campaign_set() == CampaignSet(
        campaigns=(
            CampaignName(slug="sable-crown", name="Sable Crown"),
            CampaignName(slug="iron-pact", name="Iron Pact"),
        )
    )
    assert load_campaign("iron-pact") == Campaign(slug="iron-pact", name="Iron Pact", default_gm="Ada", system="D&D 5e")


def test_create_campaign_scaffolds_empty_session_set() -> None:
    create_campaign("Iron Pact", default_gm="Ada", system="D&D 5e")

    assert load_session_set("iron-pact") == SessionSet(sessions=())


def test_create_campaign_scaffolds_empty_player_set() -> None:
    create_campaign("Iron Pact", default_gm="Ada", system="D&D 5e")

    assert load_player_set("iron-pact") == PlayerSet(players=())


def test_create_campaign_raises_on_slug_collision_and_leaves_existing_untouched() -> None:
    import pytest

    create_campaign("Iron Pact", default_gm="Ada", system="D&D 5e")
    before = load_campaign_set()

    with pytest.raises(FileExistsError):
        create_campaign("Iron Pact", default_gm="Mallory", system="Pathfinder")

    assert load_campaign_set() == before
    assert load_campaign("iron-pact").default_gm == "Ada"


def test_slugify_is_exposed_via_io_facade() -> None:
    from tablesage_model.io import slugify

    assert slugify("Iron Pact") == "iron-pact"


def test_campaign_round_trips_with_description() -> None:
    campaign = Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada", description="A grim tale of crowns.")

    save_campaign(campaign)

    loaded = load_campaign(campaign.slug)
    assert loaded.description == "A grim tale of crowns."
    assert loaded == campaign


def test_campaign_description_defaults_to_empty() -> None:
    assert Campaign(slug="sable-crown", name="Sable Crown").description == ""


def test_campaign_round_trips_with_glossary() -> None:
    campaign = Campaign(
        slug="sable-crown",
        name="Sable Crown",
        default_gm="Ada",
        glossary=(
            GlossaryEntry(term="Quarl", description="A lich-king who rules the Iron Pact"),
            GlossaryEntry(term="Iron Pact", description=""),
        ),
    )

    save_campaign(campaign)

    assert load_campaign(campaign.slug) == campaign


def test_campaign_round_trips_with_empty_glossary() -> None:
    campaign = Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada")

    save_campaign(campaign)

    assert load_campaign(campaign.slug) == campaign


def test_delete_campaign_removes_only_metadata_entry_directory_remains() -> None:
    save_campaign_set(
        CampaignSet(
            campaigns=(
                CampaignName(slug="sable-crown", name="Sable Crown"),
                CampaignName(slug="iron-pact", name="Iron Pact"),
            )
        )
    )
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))

    delete_campaign("sable-crown")

    remaining = load_campaign_set()
    assert tuple(c.slug for c in remaining.campaigns) == ("iron-pact",)
    assert _paths.campaign_dir("sable-crown").exists(), "directory must remain after soft delete"


def test_delete_session_removes_only_metadata_entry_directory_remains() -> None:
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    save_session_set(
        "sable-crown",
        SessionSet(
            sessions=(
                SessionName(slug="s1", name="One", session_date=date(2026, 1, 1)),
                SessionName(slug="s2", name="Two", session_date=date(2026, 1, 8)),
            )
        ),
    )
    save_session(
        "sable-crown",
        Session(
            session_date=date(2026, 1, 1),
            name="One",
            slug="s1",
            audio_filename="r.m4a",
            attendees={"ada": ("Game Master",)},
        ),
    )

    delete_session("sable-crown", "s1")

    remaining = load_session_set("sable-crown")
    assert tuple(s.slug for s in remaining.sessions) == ("s2",)
    assert _paths.session_dir("sable-crown", "s1").exists()


def test_cleanup_orphan_session_dirs_removes_dirs_not_in_set() -> None:
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    save_session_set(
        "sable-crown",
        SessionSet(sessions=(SessionName(slug="kept", name="Kept", session_date=date(2026, 1, 1)),)),
    )
    kept_dir = _paths.session_dir("sable-crown", "kept")
    kept_dir.mkdir(parents=True)
    orphan_dir = _paths.session_dir("sable-crown", "ghost")
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "x.txt").write_text("stray")

    deleted = cleanup_orphan_session_dirs("sable-crown")

    assert deleted == ("ghost",)
    assert not orphan_dir.exists()
    assert kept_dir.exists()


def test_delete_player_removes_only_metadata_entry_directory_remains() -> None:
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    save_player_set(
        "sable-crown",
        PlayerSet(
            players=(
                PlayerName(slug="ada", name="Ada"),
                PlayerName(slug="bryn", name="Bryn"),
            )
        ),
    )
    save_player(
        "sable-crown",
        Player(slug="ada", name="Ada", voice_samples=(), centroid=Embedding(root=(0.1, 0.2))),
    )

    delete_player("sable-crown", "ada")

    remaining = load_player_set("sable-crown")
    assert tuple(p.slug for p in remaining.players) == ("bryn",)
    assert _paths.player_dir("sable-crown", "ada").exists()


def test_cleanup_orphan_player_dirs_removes_dirs_not_in_set() -> None:
    save_campaign(Campaign(slug="sable-crown", name="Sable Crown", default_gm="Ada"))
    save_player_set("sable-crown", PlayerSet(players=(PlayerName(slug="kept", name="Kept"),)))
    kept_dir = _paths.player_dir("sable-crown", "kept")
    kept_dir.mkdir(parents=True)
    orphan_dir = _paths.player_dir("sable-crown", "ghost")
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "stray.txt").write_text("x")

    deleted = cleanup_orphan_player_dirs("sable-crown")

    assert deleted == ("ghost",)
    assert not orphan_dir.exists()
    assert kept_dir.exists()


def test_cleanup_orphan_campaign_dirs_removes_dirs_not_in_set() -> None:
    save_campaign_set(CampaignSet(campaigns=(CampaignName(slug="kept", name="Kept"),)))
    save_campaign(Campaign(slug="kept", name="Kept", default_gm="Ada"))
    orphan_dir = _paths.campaign_dir("ghost")
    orphan_dir.mkdir(parents=True)
    (orphan_dir / "stray.txt").write_text("leftover")

    deleted = cleanup_orphan_campaign_dirs()

    assert deleted == ("ghost",)
    assert not orphan_dir.exists()
    assert _paths.campaign_dir("kept").exists()


def test_player_set_round_trips() -> None:
    player_set = PlayerSet(players=(PlayerName(slug="ada", name="Ada"), PlayerName(slug="bryn", name="Bryn")))

    save_player_set("sable-crown", player_set)

    assert load_player_set("sable-crown") == player_set


def test_player_round_trips() -> None:
    player = Player(
        slug="ada",
        name="Ada",
        voice_samples=(
            VoiceSample(
                filepath=Path("voice_clips/ada-1.wav"),
                embedding=Embedding(root=(0.1, 0.2, 0.3)),
                provenance_type=ProvenanceType.IMPORT,
                source="/tmp/clips",
                index=0,
            ),
            VoiceSample(
                filepath=Path("voice_clips/ada-2.wav"),
                embedding=Embedding(root=(0.4, 0.5, 0.6)),
                provenance_type=ProvenanceType.IMPORT,
                source="/tmp/clips",
                index=1,
            ),
        ),
        centroid=Embedding(root=(0.25, 0.35, 0.45)),
    )

    save_player("sable-crown", player)

    assert load_player("sable-crown", player.slug) == player


def test_session_set_round_trips() -> None:
    session_set = SessionSet(sessions=(SessionName(slug="session-one", name="Session One", session_date=date(2026, 5, 13)),))

    save_session_set("sable-crown", session_set)

    assert load_session_set("sable-crown") == session_set


def test_session_round_trips_with_audio_filename() -> None:
    session = Session(
        session_date=date(2026, 5, 13),
        name="Session One",
        slug="session-one",
        audio_filename="session-one-raw.m4a",
        attendees={
            "ada": ("Game Master",),
            "bryn": ("Paladin",),
        },
    )

    save_session("sable-crown", session)

    assert load_session("sable-crown", session.slug) == session


def test_game_master_constant_is_canonical_string() -> None:
    from tablesage_model.model.cast import GAME_MASTER

    assert GAME_MASTER == "Game Master"


def test_summary_writes_markdown_body_literally_and_reads_back() -> None:
    body = "# Session One\n\nThe party met the **lich-king Quarl**.\n"
    summary = Summary(markdown=body)

    save_summary("sable-crown", "session-one", summary)

    on_disk = (_paths.session_dir("sable-crown", "session-one") / _paths.KnownFiles.SUMMARY).read_text(encoding="utf-8")
    assert on_disk == body
    assert load_summary("sable-crown", "session-one") == summary


def test_discourse_round_trips_to_disk() -> None:
    discourse = Discourse(
        utterances=(
            Utterance.from_words(
                (
                    Word(text="hello", start=0.0, end=0.4, speaker="ada"),
                    Word(text="world", start=0.5, end=0.9, speaker="ada"),
                )
            ),
        )
    )

    save_discourse("sable-crown", "session-one", discourse)

    assert load_discourse("sable-crown", "session-one") == discourse


def test_voice_sample_carries_provenance_and_round_trips_through_player() -> None:
    from tablesage_model.model.cast import ProvenanceType

    sample = VoiceSample(
        filepath=Path("voice_clips/x.wav"),
        embedding=Embedding(root=(0.1, 0.2, 0.3)),
        provenance_type=ProvenanceType.SESSION_ENHANCEMENT,
        source="session-three",
        index=7,
    )
    player = Player(
        slug="ada",
        name="Ada",
        voice_samples=(sample,),
        centroid=Embedding(root=(0.1, 0.2, 0.3)),
    )

    save_player("sable-crown", player)

    loaded = load_player("sable-crown", "ada")
    assert loaded.voice_samples[0].provenance_type == ProvenanceType.SESSION_ENHANCEMENT
    assert loaded.voice_samples[0].source == "session-three"
    assert loaded.voice_samples[0].index == 7


def test_app_settings_round_trip_via_save_and_load() -> None:
    from tablesage_model.settings import AppSettings

    settings = AppSettings(llm_model="anthropic/claude-3-7-sonnet")
    settings = settings.model_copy(
        update={"speaker_identification": settings.speaker_identification.model_copy(update={"similarity_margin_threshold": 0.42})}
    )

    save_app_settings(settings)

    loaded = load_app_settings()
    assert loaded.llm_model == "anthropic/claude-3-7-sonnet"
    assert loaded.speaker_identification.similarity_margin_threshold == 0.42


def test_load_app_settings_returns_defaults_when_file_missing() -> None:
    from tablesage_model.settings import AppSettings

    loaded = load_app_settings()

    assert loaded == AppSettings()


def test_app_settings_carry_enhance_voices_block_with_defaults() -> None:
    from tablesage_model.settings import AppSettings

    defaults = AppSettings()

    assert defaults.enhance_voices.min_margin_for_voice_sample == 0.15
    assert defaults.enhance_voices.min_clip_seconds == 1.0
    assert defaults.enhance_voices.max_clip_seconds == 8.0


def test_app_settings_clean_clips_on_import_defaults_to_false_and_round_trips() -> None:
    from tablesage_model.settings import AppSettings

    assert AppSettings().clean_clips_on_import is False

    save_app_settings(AppSettings(clean_clips_on_import=True))

    assert load_app_settings().clean_clips_on_import is True


def test_session_requires_audio_filename() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Session.model_validate(
            {
                "session_date": date(2026, 5, 13),
                "name": "Session One",
                "slug": "session-one",
                "attendees": {"ada": ("Game Master",)},
            }
        )


def test_load_campaign_summaries_computes_session_bounds_and_counts() -> None:
    slug = create_campaign(campaign_name="Iron Pact", default_gm="Ada", system="D&D 5e")
    save_session_set(
        slug,
        SessionSet(
            sessions=(
                SessionName(slug="s2", name="Two", session_date=date(2026, 3, 10)),
                SessionName(slug="s1", name="One", session_date=date(2026, 1, 5)),
                SessionName(slug="s3", name="Three", session_date=date(2026, 2, 14)),
            )
        ),
    )
    save_player_set(
        slug,
        PlayerSet(
            players=(
                PlayerName(slug="ada", name="Ada"),
                PlayerName(slug="bex", name="Bex"),
            )
        ),
    )

    (summary,) = load_campaign_summaries()

    assert summary.first_session_date == date(2026, 1, 5)
    assert summary.last_session_date == date(2026, 3, 10)
    assert summary.session_count == 3
    assert summary.player_count == 2


def test_load_campaign_summaries_empty_campaign_has_no_dates() -> None:
    create_campaign(campaign_name="Iron Pact", default_gm="Ada", system="D&D 5e")

    (summary,) = load_campaign_summaries()

    assert summary.first_session_date is None
    assert summary.last_session_date is None
    assert summary.session_count == 0
    assert summary.player_count == 0


def test_load_campaign_summaries_carries_campaign_fields() -> None:
    slug = create_campaign(campaign_name="Iron Pact", default_gm="Ada", system="D&D 5e")
    save_campaign(
        Campaign(
            slug=slug,
            name="Iron Pact",
            description="A grim pact campaign",
            default_gm="Ada",
            system="D&D 5e",
        )
    )

    (summary,) = load_campaign_summaries()

    assert summary.name == "Iron Pact"
    assert summary.description == "A grim pact campaign"
    assert summary.default_gm == "Ada"
    assert summary.system == "D&D 5e"


def test_load_campaign_summaries_preserves_campaign_set_order() -> None:
    create_campaign(campaign_name="Iron Pact", default_gm="Ada", system="D&D 5e")
    create_campaign(campaign_name="Sable Crown", default_gm="Bex", system="Blades")

    summaries = load_campaign_summaries()

    assert tuple(s.slug for s in summaries) == tuple(c.slug for c in load_campaign_set().campaigns)


def test_load_campaign_summaries_fails_fast_when_campaign_files_missing() -> None:
    import pytest

    save_campaign_set(CampaignSet(campaigns=(CampaignName(slug="phantom", name="Phantom"),)))

    with pytest.raises(FileNotFoundError):
        load_campaign_summaries()
