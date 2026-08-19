from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import date
from pathlib import Path

from sqlmodel import Session
from tablesage_model import setup
from tablesage_model.model import Campaign, CampaignPlayer, GlossaryEntry, Player
from tablesage_model.model import Session as GameSession
from tablesage_model.settings import AppSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory

from . import campaigns, glossary, paths, players, roster, sessions


class Application:
    def __init__(self, cwd: Path | None = None, settings: AppSettings | None = None) -> None:
        self._cwd: Path = cwd if cwd is not None else Path.cwd()
        self._db_path: Path = setup.ensure_database(self._cwd)
        self._engine = setup.create_engine(self._db_path)
        self._embedding_factory: EmbeddingFactory | None = None
        self._settings: AppSettings = settings if settings is not None else AppSettings()

    # Campaigns

    def has_campaigns(self) -> bool:
        with Session(self._engine) as session:
            return campaigns.has_campaigns(session)

    def create_campaign(self, campaign: Campaign) -> Campaign:
        with Session(self._engine) as session:
            result = campaigns.create_campaign(session, campaign, paths.campaigns_root(self._cwd))
            session.commit()
            session.refresh(result)
            return result

    def list_campaigns(self) -> list[Campaign]:
        with Session(self._engine) as session:
            return campaigns.list_campaigns(session)

    def get_campaign(self, campaign_id: uuid.UUID) -> Campaign:
        with Session(self._engine) as session:
            return campaigns.get_campaign(session, campaign_id)

    def last_session_dates(self) -> dict[uuid.UUID, date]:
        with Session(self._engine) as session:
            return campaigns.last_session_dates(session)

    def rename_campaign(self, campaign_id: uuid.UUID, new_name: str) -> Campaign:
        with Session(self._engine) as session:
            result = campaigns.rename_campaign(session, campaign_id, new_name, paths.campaigns_root(self._cwd))
            session.commit()
            session.refresh(result)
            return result

    def update_campaign(self, campaign_id: uuid.UUID, description: str | None, game_system: str | None) -> Campaign:
        with Session(self._engine) as session:
            result = campaigns.update_campaign(session, campaign_id, description, game_system)
            session.commit()
            session.refresh(result)
            return result

    def delete_campaign(self, campaign_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            campaigns.delete_campaign(session, campaign_id)
            session.commit()

    def cleanup_orphan_campaign_dirs(self) -> list[str]:
        with Session(self._engine) as session:
            return campaigns.cleanup_orphan_campaign_dirs(session, paths.campaigns_root(self._cwd))

    # Players

    def create_player(self, player: Player) -> Player:
        with Session(self._engine) as session:
            result = players.create_player(session, player, paths.players_root(self._cwd))
            session.commit()
            session.refresh(result)
            return result

    def list_players(self) -> list[Player]:
        with Session(self._engine) as session:
            return players.list_players(session)

    def get_player(self, player_id: uuid.UUID) -> Player:
        with Session(self._engine) as session:
            return players.get_player(session, player_id)

    def rename_player(self, player_id: uuid.UUID, new_name: str) -> Player:
        with Session(self._engine) as session:
            result = players.rename_player(session, player_id, new_name, paths.players_root(self._cwd))
            session.commit()
            session.refresh(result)
            return result

    def delete_player(self, player_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            players.delete_player(session, player_id)
            session.commit()

    def cleanup_orphan_player_dirs(self) -> list[str]:
        with Session(self._engine) as session:
            return players.cleanup_orphan_player_dirs(session, paths.players_root(self._cwd))

    def list_voice_clips(self, player_id: uuid.UUID) -> list[players.VoiceClip]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            return players.list_voice_clips(paths.player_folder(self._cwd, player.name))

    def delete_voice_clip(self, player_id: uuid.UUID, filename: str, on_progress: Callable[[int, int], None] | None = None) -> Player:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result = players.delete_voice_clip(
                session, player_id, filename, folder, self._embed_clip, on_progress, outliers.min_sample_similarity, outliers.min_samples
            )
            session.commit()
            session.refresh(result)
            return result

    def recompute_centroid(self, player_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> Player:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result = players.recompute_centroid(
                session, player_id, folder, self._embed_clip, on_progress, outliers.min_sample_similarity, outliers.min_samples
            )
            session.commit()
            session.refresh(result)
            return result

    def cleanup_voice_clips(self, player_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> tuple[Player, list[str]]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result, deleted_filenames = players.cleanup_voice_clips(
                session, player_id, folder, self._embed_clip, on_progress, outliers.min_sample_similarity, outliers.min_samples
            )
            session.commit()
            session.refresh(result)
            return result, deleted_filenames

    def validate_import_source(self, source_dir: Path) -> None:
        players.validate_import_source(source_dir)

    def find_prior_import_clips(self, player_id: uuid.UUID, source_dir: Path) -> list[Path]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            return players.find_prior_import_clips(folder, source_dir)

    def import_voice_clips(
        self, player_id: uuid.UUID, source_dir: Path, on_progress: Callable[[int, int], None] | None = None
    ) -> tuple[Player, players.ImportResult]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result, import_result = players.import_voice_clips(
                session,
                player_id,
                player.name,
                source_dir,
                folder,
                self._embed_clip,
                on_progress,
                outliers.min_sample_similarity,
                outliers.min_samples,
            )
            session.commit()
            session.refresh(result)
            return result, import_result

    def _embed_clip(self, path: Path) -> Embedding:
        if self._embedding_factory is None:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._embedding_factory = EmbeddingFactory(device=device)
        return self._embedding_factory.extract(path)

    # Roster

    def add_player_to_campaign(self, campaign_id: uuid.UUID, player_id: uuid.UUID, default_role_name: str) -> CampaignPlayer:
        with Session(self._engine) as session:
            result = roster.add_player_to_campaign(session, campaign_id, player_id, default_role_name)
            session.commit()
            session.refresh(result)
            return result

    def list_roster(self, campaign_id: uuid.UUID) -> list[tuple[CampaignPlayer, Player]]:
        with Session(self._engine) as session:
            return roster.list_roster(session, campaign_id)

    def update_default_role(self, membership_id: uuid.UUID, default_role_name: str) -> CampaignPlayer:
        with Session(self._engine) as session:
            result = roster.update_default_role(session, membership_id, default_role_name)
            session.commit()
            session.refresh(result)
            return result

    def remove_from_roster(self, membership_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            roster.remove_from_roster(session, membership_id)
            session.commit()

    # Glossary

    def create_glossary_entry(self, entry: GlossaryEntry) -> GlossaryEntry:
        with Session(self._engine) as session:
            result = glossary.create_glossary_entry(session, entry)
            session.commit()
            session.refresh(result)
            return result

    def list_glossary_entries(self, campaign_id: uuid.UUID) -> list[GlossaryEntry]:
        with Session(self._engine) as session:
            return glossary.list_glossary_entries(session, campaign_id)

    def update_glossary_entry(self, campaign_id: uuid.UUID, entry_id: uuid.UUID, term: str, description: str | None) -> GlossaryEntry:
        with Session(self._engine) as session:
            result = glossary.update_glossary_entry(session, campaign_id, entry_id, term, description)
            session.commit()
            session.refresh(result)
            return result

    def delete_glossary_entry(self, campaign_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            glossary.delete_glossary_entry(session, campaign_id, entry_id)
            session.commit()

    # Sessions

    def create_session(self, campaign_id: uuid.UUID, name: str, session_date: date | None = None) -> GameSession:
        with Session(self._engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            result = sessions.create_session(session, campaign_id, name, session_date, paths.campaign_folder(self._cwd, campaign.name))
            session.commit()
            session.refresh(result)
            return result

    def list_sessions(self, campaign_id: uuid.UUID) -> list[GameSession]:
        with Session(self._engine) as session:
            return sessions.list_sessions(session, campaign_id)

    def cleanup_orphan_session_dirs(self, campaign_id: uuid.UUID) -> list[str]:
        with Session(self._engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            return sessions.cleanup_orphan_session_dirs(session, campaign_id, paths.campaign_folder(self._cwd, campaign.name))

    def get_session(self, session_id: uuid.UUID) -> GameSession:
        with Session(self._engine) as session:
            return sessions.get_session(session, session_id)

    def update_session(self, session_id: uuid.UUID, name: str, session_date: date | None) -> GameSession:
        with Session(self._engine) as session:
            result = sessions.update_session(session, session_id, name, session_date)
            session.commit()
            session.refresh(result)
            return result

    def delete_session(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            sessions.delete_session(session, session_id)
            session.commit()

    def _session_folder(self, session: Session, game_session: GameSession) -> Path:
        campaign = session.get(Campaign, game_session.campaign_id)
        if campaign is None:
            raise ValueError("Campaign not found.")
        return paths.session_folder(self._cwd, campaign.name, game_session.sequence_number)

    def session_artifacts(self, session_id: uuid.UUID) -> sessions.SessionArtifacts:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return sessions.session_artifacts(self._session_folder(session, game_session))

    def import_session_audio(self, session_id: uuid.UUID, source_path: Path) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            sessions.import_audio(source_path, self._session_folder(session, game_session))

    def can_process_session(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return sessions.can_process_session(session, session_id, self._session_folder(session, game_session))

    def can_generate_summary(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return sessions.can_generate_summary(self._session_folder(session, game_session))

    def list_attendance(self, session_id: uuid.UUID) -> list[sessions.Attendee]:
        with Session(self._engine) as session:
            return sessions.list_attendance(session, session_id)

    def add_attendance(self, session_id: uuid.UUID, player_id: uuid.UUID) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            sessions.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.add_attendance(session, game_session.campaign_id, session_id, player_id)
            session.commit()
            return result

    def remove_attendance(self, session_id: uuid.UUID, attendance_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            sessions.invalidate_downstream(self._session_folder(session, game_session))
            sessions.remove_attendance(session, attendance_id)
            session.commit()

    def set_attendance_roles(self, session_id: uuid.UUID, attendance_id: uuid.UUID, roles: list[str]) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            sessions.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.set_attendance_roles(session, attendance_id, roles)
            session.commit()
            return result
