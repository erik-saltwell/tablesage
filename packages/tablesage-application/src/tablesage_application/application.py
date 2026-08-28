from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import date
from pathlib import Path

import widelog
from sqlmodel import Session
from tablesage_model import setup
from tablesage_model.model import Campaign, CampaignPlayer, GlossaryEntry, Player
from tablesage_model.model import Session as GameSession
from tablesage_model.settings import AppSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import Transcript

from . import paths, player_import_from_audio, players_from_session
from ._fs import delete_named_entity_folder, named_entity_folder_exists
from .entities import campaigns, glossary, players, roster, sessions
from .llm import PromptName, call_llm_with_prompt
from .session_pipeline import artifacts, import_audio, processing, transcribe_audio, transcript_review
from .session_pipeline import generate_summary as generate_summary_pipeline
from .voice_clips import clips


class Application:
    def __init__(self, cwd: Path | None = None, settings: AppSettings | None = None) -> None:
        self._cwd: Path = cwd if cwd is not None else Path.cwd()
        self._db_path: Path = setup.ensure_database(self._cwd)
        self._engine = setup.create_engine(self._db_path)
        self._embedding_factory: EmbeddingFactory | None = None
        self._settings: AppSettings = settings if settings is not None else AppSettings()

    @property
    def settings(self) -> AppSettings:
        return self._settings

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

    def campaign_folder_exists(self, name: str) -> bool:
        """Preflight check for `create_campaign`/`rename_campaign` -- would `name` collide with a stray orphan folder?"""
        return named_entity_folder_exists(paths.campaigns_root(self._cwd), name)

    def delete_orphan_campaign_folder(self, name: str) -> None:
        """Delete a stray campaign folder the user already confirmed clearing, so `create_campaign`/`rename_campaign` can proceed."""
        delete_named_entity_folder(paths.campaigns_root(self._cwd), name)

    # Players

    def create_player(self, player: Player) -> Player:
        with Session(self._engine) as session:
            result = players.create_player(session, player, paths.players_root(self._cwd))
            session.commit()
            session.refresh(result)
            return result

    def player_folder_exists(self, name: str) -> bool:
        """Preflight check for `create_player`/`rename_player` -- would `name` collide with a stray orphan folder?"""
        return named_entity_folder_exists(paths.players_root(self._cwd), name)

    def delete_orphan_player_folder(self, name: str) -> None:
        """Delete a stray player folder the user already confirmed clearing, so `create_player`/`rename_player` can proceed."""
        delete_named_entity_folder(paths.players_root(self._cwd), name)

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

    def list_voice_clips(self, player_id: uuid.UUID) -> list[clips.VoiceClip]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            return clips.list_voice_clips(paths.player_folder(self._cwd, player.name))

    def delete_voice_clip(self, player_id: uuid.UUID, filename: str, on_progress: Callable[[int, int], None] | None = None) -> Player:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result = clips.delete_voice_clip(
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
            result = clips.recompute_centroid(
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
            result, deleted_filenames = clips.cleanup_voice_clips(
                session, player_id, folder, self._embed_clip, on_progress, outliers.min_sample_similarity, outliers.min_samples
            )
            session.commit()
            session.refresh(result)
            return result, deleted_filenames

    def validate_import_source(self, source_dir: Path) -> None:
        clips.validate_import_source(source_dir)

    def find_prior_import_clips(self, player_id: uuid.UUID, source_dir: Path) -> list[Path]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            return clips.find_prior_import_clips(folder, source_dir)

    def import_voice_clips(
        self,
        player_id: uuid.UUID,
        source_dir: Path,
        on_progress: Callable[[int, int], None] | None = None,
        *,
        should_clean_audio: bool = False,
    ) -> tuple[Player, clips.ImportResult]:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result, import_result = clips.import_voice_clips(
                session,
                player_id,
                player.name,
                source_dir,
                folder,
                self._embed_clip,
                on_progress,
                outliers.min_sample_similarity,
                outliers.min_samples,
                should_clean_audio=should_clean_audio,
                normalize_volume=self._settings.audio_cleaning.normalize_volume,
            )
            session.commit()
            session.refresh(result)
            return result, import_result

    def embedding_factory(self) -> EmbeddingFactory:
        if self._embedding_factory is None:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._embedding_factory = EmbeddingFactory(device=device)
        return self._embedding_factory

    def _embed_clip(self, path: Path) -> Embedding:
        return self.embedding_factory().extract(path)

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
            sessions.seed_attendance_from_previous_session_or_roster(session, campaign_id, result.id)
            session.commit()
            session.refresh(result)
            return result

    def session_folder_would_collide(self, campaign_id: uuid.UUID) -> bool:
        """Preflight check for `create_session` -- does a stray orphan folder already occupy the next session slot?

        Unlike `player_folder_exists`/`campaign_folder_exists`, the colliding
        name (a zero-padded sequence number, e.g. "001") is never something
        the user typed or sees -- it's computed the same way `create_session`
        itself computes it (`sessions.next_sequence_number`), so both agree
        on which on-disk slot is about to be used.
        """
        with Session(self._engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            next_sequence = sessions.next_sequence_number(session, campaign_id)
            return named_entity_folder_exists(paths.campaign_folder(self._cwd, campaign.name), f"{next_sequence:03d}")

    def delete_colliding_session_folder(self, campaign_id: uuid.UUID) -> None:
        """Delete the stray session folder the user already confirmed clearing, so `create_session` can proceed."""
        with Session(self._engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            next_sequence = sessions.next_sequence_number(session, campaign_id)
            delete_named_entity_folder(paths.campaign_folder(self._cwd, campaign.name), f"{next_sequence:03d}")

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

    def session_folder(self, session_id: uuid.UUID) -> Path:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return self._session_folder(session, game_session)

    def session_artifacts(self, session_id: uuid.UUID) -> dict[paths.ArtifactName, bool]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return artifacts.session_artifacts(self._session_folder(session, game_session))

    def exportable_artifacts(self, session_id: uuid.UUID) -> list[paths.ArtifactName]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return artifacts.exportable_artifacts(self._session_folder(session, game_session))

    def can_export_artifacts(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return artifacts.can_export_artifacts(self._session_folder(session, game_session))

    def export_artifact(self, session_id: uuid.UUID, artifact_name: paths.ArtifactName, destination: Path) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            artifacts.export_artifact(self._session_folder(session, game_session), artifact_name, destination)

    def session_player_centroids(self, session_id: uuid.UUID) -> dict[str, Embedding]:
        """Attending players' voice centroids, keyed by player name -- `transcribe_audio`'s speaker-ID input."""
        with Session(self._engine) as session:
            centroids: dict[str, Embedding] = {}
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                if player is not None and player.centroid_embedding is not None:
                    centroids[player.name] = Embedding.model_validate(json.loads(player.centroid_embedding))
            return centroids

    def session_player_roles(self, session_id: uuid.UUID) -> dict[str, str]:
        """Attending players' first (alphabetically) role name that session, keyed by player name.

        `transcribe_audio`'s role-transcript input.
        """
        with Session(self._engine) as session:
            role_names: dict[str, str] = {}
            for attendee in sessions.list_attendance(session, session_id):
                if attendee.roles:
                    role_names[attendee.player_name] = attendee.roles[0]
            return role_names

    def validate_import_audio_source(self, source_path: Path) -> None:
        import_audio.validate_import_source(source_path)

    def audio_import_extensions(self) -> frozenset[str]:
        return paths.AUDIO_EXTENSIONS

    def can_generate_summary(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return processing.can_generate_summary(self._session_folder(session, game_session))

    def generate_summary(self, session_id: uuid.UUID) -> None:
        """Generate and atomically replace a session's Markdown summary."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            transcript_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT_ROLES_TEXT].filename
            if not transcript_path.is_file():
                raise ValueError("Transcribe the session first.")

            entries = sorted(glossary.list_glossary_entries(session, game_session.campaign_id), key=lambda entry: entry.term.casefold())
            prompt_glossary = [
                generate_summary_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in entries
            ]
            transcript = transcript_path.read_text(encoding="utf-8")

        with widelog.wide_event(op="generate_summary", session_id=str(session_id), glossary_entry_count=len(prompt_glossary)):
            summary = asyncio.run(generate_summary_pipeline.generate_summary(transcript, prompt_glossary, self._settings.llm_model))
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.SUMMARY].filename
            temp_target = target.with_name(f".{target.stem}.tmp{target.suffix}")
            try:
                temp_target.write_text(summary, encoding="utf-8")
                temp_target.replace(target)
            except Exception:
                temp_target.unlink(missing_ok=True)
                raise

    def can_transcribe_audio(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcribe_audio.can_transcribe_audio(session, session_id, self._session_folder(session, game_session))

    # Speaker review -- see `.documentation/speaker_review_screen.md`.

    def extract_review_clips(self, session_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.extract_review_clips(self._session_folder(session, game_session), on_progress)

    def discard_review_clips(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            transcript_review.discard_review_clips(self._session_folder(session, game_session))

    def save_transcript(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            transcript.save(session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT].filename)

    def count_adjusted_utterances(self, session_id: uuid.UUID) -> int:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.count_adjusted_utterances(self._session_folder(session, game_session))

    def generate_benchmark_transcript(self, session_id: uuid.UUID) -> transcript_review.BenchmarkTranscriptResult:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.generate_benchmark_transcript(self._session_folder(session, game_session))

    def list_attendance(self, session_id: uuid.UUID) -> list[sessions.Attendee]:
        with Session(self._engine) as session:
            return sessions.list_attendance(session, session_id)

    def add_attendance(self, session_id: uuid.UUID, player_id: uuid.UUID) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            import_audio.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.add_attendance(session, game_session.campaign_id, session_id, player_id)
            session.commit()
            return result

    def add_attendance_with_roles(self, session_id: uuid.UUID, player_id: uuid.UUID, roles: list[str]) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            import_audio.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.add_attendance_with_roles(session, game_session.campaign_id, session_id, player_id, roles)
            session.commit()
            return result

    def set_attendance_player(self, session_id: uuid.UUID, attendance_id: uuid.UUID, player_id: uuid.UUID) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            import_audio.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.set_attendance_player(session, game_session.campaign_id, attendance_id, player_id)
            session.commit()
            return result

    def remove_attendance(self, session_id: uuid.UUID, attendance_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            import_audio.invalidate_downstream(self._session_folder(session, game_session))
            sessions.remove_attendance(session, attendance_id)
            session.commit()

    def set_attendance_roles(self, session_id: uuid.UUID, attendance_id: uuid.UUID, roles: list[str]) -> sessions.Attendee:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            import_audio.invalidate_downstream(self._session_folder(session, game_session))
            result = sessions.set_attendance_roles(session, attendance_id, roles)
            session.commit()
            return result

    def enhance_players_from_session(
        self, session_id: uuid.UUID, on_progress: players_from_session.OnProgress | None = None
    ) -> players_from_session.EnhanceResult:
        """Players List's "From Session" (S): pull high-confidence voice clips out of a transcribed session."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)

            player_folders: dict[uuid.UUID, Path] = {}
            for attendee in sessions.list_attendance(session, session_id):
                player = players.get_player(session, attendee.player_id)
                player_folders[attendee.player_id] = paths.player_folder(self._cwd, player.name)

            result = players_from_session.enhance_players_from_session(
                session,
                session_id,
                session_folder,
                campaign.name,
                game_session.name,
                player_folders,
                self._embed_clip,
                self._settings.enhance_voices,
                self._settings.remove_outliers,
                on_progress,
            )
            session.commit()
            return result

    # Import players from audio (Players List's "From Audio", F)

    def import_players_from_audio_transcribe(
        self,
        source_audio_path: Path,
        cleaned_audio_path: Path,
        speaker_count: int | None,
        on_progress: player_import_from_audio.OnProgress | None = None,
        *,
        should_clean_audio: bool = True,
    ) -> Transcript:
        return player_import_from_audio.transcribe_audio_file(
            source_audio_path,
            cleaned_audio_path,
            self._settings.session_audio_import.normalize_volume,
            self._settings.transcription_and_diarization,
            speaker_count,
            on_progress,
            should_clean_audio=should_clean_audio,
        )

    def import_players_from_audio_propose(
        self,
        cleaned_audio_path: Path,
        clip_dir: Path,
        transcript: Transcript,
        candidates: list[player_import_from_audio.SpeakerCandidate],
        on_progress: player_import_from_audio.OnProgress | None = None,
    ) -> player_import_from_audio.ProposeResult:
        with Session(self._engine) as session:
            existing_centroids: dict[uuid.UUID, tuple[str, Embedding]] = {}
            for player in players.list_players(session):
                if player.centroid_embedding is not None:
                    existing_centroids[player.id] = (player.name, Embedding.model_validate(json.loads(player.centroid_embedding)))

        return player_import_from_audio.propose_attendees(
            cleaned_audio_path,
            clip_dir,
            transcript,
            candidates,
            existing_centroids,
            self._embed_clip,
            self._propose_speakers,
            self._settings.speaker_identification.similarity_margin_threshold,
            self._settings.enhance_voices,
            on_progress,
        )

    def _propose_speakers(
        self, utterance_texts: list[tuple[str, str]], candidates: list[player_import_from_audio.SpeakerCandidate]
    ) -> list[player_import_from_audio.SpeakerGuess]:
        with widelog.wide_event(op="propose_speakers", speaker_count=len(utterance_texts)) as log:
            template_data = player_import_from_audio.SpeakerProposalPromptData(
                speakers=[{"speaker_id": speaker_id, "transcript": text} for speaker_id, text in utterance_texts],
                candidates=[{"name": candidate.name, "role": ", ".join(candidate.roles)} for candidate in candidates],
            )
            raw = asyncio.run(
                call_llm_with_prompt(
                    PromptName.PROPOSE_SPEAKERS,
                    template_data,
                    self._settings.llm_model,
                    response_model=player_import_from_audio.SpeakerGuesses,
                )
            )
            guesses = player_import_from_audio.SpeakerGuesses.model_validate_json(raw).speakers
            log.set(guess_count=len(guesses))
            return guesses

    def import_players_from_audio_build(
        self,
        source_audio_path: Path,
        speaker_clips: Mapping[str, Sequence[player_import_from_audio.SpeakerUtteranceClip]],
        speaker_centroids: dict[str, Embedding],
        pending: list[player_import_from_audio.PendingResolution],
        on_progress: player_import_from_audio.OnProgress | None = None,
    ) -> player_import_from_audio.ImportFromAudioResult:
        with Session(self._engine) as session:
            player_folders: dict[uuid.UUID, Path] = {}
            resolved: list[player_import_from_audio.ResolvedSpeaker] = []
            for item in pending:
                if item.player_id is None:
                    player = players.create_player(session, Player(name=item.player_name), paths.players_root(self._cwd))
                else:
                    player = players.get_player(session, item.player_id)
                player_folders[player.id] = paths.player_folder(self._cwd, player.name)
                resolved.append(
                    player_import_from_audio.ResolvedSpeaker(speaker_id=item.speaker_id, player_id=player.id, player_name=player.name)
                )

            result = player_import_from_audio.build_players_from_audio(
                session,
                source_audio_path,
                speaker_clips,
                speaker_centroids,
                resolved,
                player_folders,
                self._embed_clip,
                self._settings.enhance_voices,
                self._settings.remove_outliers,
                on_progress,
            )
            session.commit()
            return result
