from __future__ import annotations

import asyncio
import json
import math
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import cast

import widelog
import yaml
from sqlmodel import Session
from tablesage_model import setup
from tablesage_model.model import (
    Campaign,
    GlossaryEntry,
    Player,
)
from tablesage_model.model import Session as GameSession
from tablesage_model.player_names import validate_player_name
from tablesage_model.settings import AppSettings
from tablesage_tools.embeddings import Embedding, EmbeddingFactory
from tablesage_tools.model import Transcript
from tablesage_tools.speakers import UNASSIGNED_SPEAKER

from . import campaign_recap, opportunities, paths, players_from_session, previously_on
from ._fs import delete_named_entity_folder, named_entity_folder_exists
from .entities import campaigns, glossary, players, sessions
from .entities import session_processing as session_processing_entities
from .llm import PromptName, system_prompt_path
from .player_archive import PlayerArchiveResult
from .session_pipeline import artifact_graph as artifact_graph_pipeline
from .session_pipeline import artifacts, import_audio, processing, transcribe_audio, transcript_review
from .session_pipeline import clean_transcript as clean_transcript_pipeline
from .session_pipeline import extract_glossary as extract_glossary_pipeline
from .session_pipeline import generate_ledger as generate_ledger_pipeline
from .session_pipeline import generate_player_introductions as player_introductions_pipeline
from .session_pipeline import generate_recap_summary as recap_summary_pipeline
from .session_pipeline import generate_summary as generate_summary_pipeline
from .session_pipeline import isolate_new_speakers as isolate_new_speakers_pipeline
from .session_pipeline import name_corrections as name_corrections_pipeline
from .session_pipeline import review_new_speaker_assignments as review_new_speaker_assignments_pipeline
from .session_pipeline import seed_voice_samples as seed_voice_samples_pipeline
from .session_pipeline import session_processing as session_processing_pipeline
from .session_pipeline import suggest_spelling_corrections as suggest_spelling_corrections_pipeline
from .session_pipeline import transcript_sections as transcript_sections_pipeline
from .session_pipeline.atomic_files import atomic_write
from .session_pipeline.remove_backchannels import remove_backchannels
from .session_pipeline.scene_breakdown import load_current_scene_breakdown, persist_ledger_pair
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

    def apply_settings(self, settings: AppSettings) -> None:
        """Replace the snapshot used for subsequent operations."""
        self._settings = settings

    def require_credentials(self, *roles: str, transcription: bool = False) -> None:
        from tablesage_tools.credentials import require_credential

        if transcription:
            require_credential("elevenlabs", self._settings.transcription_and_diarization.model_id)
        for role in roles:
            model = getattr(self._settings, role)
            require_credential(model.partition("/")[0], model)

    def verify_setup(self, on_progress: Callable[[str], None] | None = None) -> str | None:
        """Settings' Save check: test every configured LLM, then download any missing local audio models.

        Returns a user-facing failure message, or `None` once every model responded and the local
        models are present. Downloads only start after all model tests pass.
        """
        from tablesage_tools.credentials import test_connection
        from tablesage_tools.local_models import missing_local_models

        from .configuration import MODEL_FIELDS

        settings = self._settings
        for model in dict.fromkeys(getattr(settings, field) for field in MODEL_FIELDS):
            if on_progress is not None:
                on_progress(f"Testing {model}…")
            result = asyncio.run(test_connection(model.partition("/")[0], [model], settings.connection_test_timeout))
            if not result.ok:
                return f"{model}: {result.message}"
        for local_model in missing_local_models():
            if on_progress is not None:
                on_progress(f"Downloading {local_model.name} model…")
            local_model.download()
        return None

    # Campaigns

    def previously_on_history(self, campaign_id: uuid.UUID) -> previously_on.CampaignHistory:
        """Validate every Session and take an in-memory snapshot without generating artifacts."""
        with Session(self._engine) as session:
            campaign = campaigns.get_campaign(session, campaign_id)
            game_sessions = sorted(sessions.list_sessions(session, campaign_id), key=lambda item: item.sequence_number)
            if not game_sessions:
                raise ValueError("This Campaign has no Sessions. Create Sessions and run Regenerate All Outputs first.")
            graph = self._artifact_graph(session, campaign_id)
            history: list[previously_on.CampaignSession] = []
            problems: list[str] = []
            for game_session in game_sessions:
                folder = self._session_folder(session, game_session)
                ref = artifact_graph_pipeline.ArtifactRef(folder, paths.ArtifactName.SCENE_BREAKDOWN)
                try:
                    status = graph.status(ref)
                    if status is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
                        raise ValueError(f"Scene Breakdown is {status.value} or its generation is incomplete")
                    breakdown = load_current_scene_breakdown(folder)
                    if breakdown.session_id != game_session.id:
                        raise ValueError("Scene Breakdown belongs to a different Session")
                    history.append(previously_on.CampaignSession(sequence_number=game_session.sequence_number, breakdown=breakdown))
                except (ValueError, OSError) as exc:
                    problems.append(f"Session {game_session.sequence_number:03d} — {game_session.name}: {exc}")
            if problems:
                raise ValueError(
                    "Every Session needs a current, valid, complete Scene Breakdown.\n\n"
                    + "\n".join(problems)
                    + "\n\nRun Regenerate All Outputs from Campaign detail, then try again."
                )
            return previously_on.CampaignHistory(
                campaign_name=campaign.name,
                sessions=tuple(history),
                glossary=tuple(
                    previously_on.GlossaryEntry(term=entry.term, description=entry.description)
                    for entry in sorted(glossary.list_glossary_entries(session, campaign_id), key=lambda item: item.term.casefold())
                ),
            )

    def create_campaign_scene_recap(self, campaign_id: uuid.UUID) -> campaign_recap.CampaignSceneRecap:
        """Create a chronological Campaign recap from every current Scene Breakdown."""
        history = self.previously_on_history(campaign_id)
        return campaign_recap.create_campaign_scene_recap(campaign_id, history)

    def previously_on_ingredients(self, history: previously_on.CampaignHistory) -> previously_on.Ingredients:
        with widelog.wide_event(op="previously_on_ingredients", session_count=len(history.sessions)):
            return asyncio.run(
                previously_on.generate_ingredients(history, self._settings.llm_model_high, self._settings.previously_on.ingredient_timeout)
            )

    def generate_opportunities(self, campaign_id: uuid.UUID, prompt: str) -> opportunities.OpportunityResult:
        if not prompt.strip():
            raise ValueError("Describe what might happen next Session first.")
        recap = self.create_campaign_scene_recap(campaign_id)
        with widelog.wide_event(op="generate_opportunities", scene_count=len(recap.scenes)):
            return asyncio.run(opportunities.generate(recap, prompt, self._settings.llm_model_high, self._settings.opportunities_timeout))

    def save_opportunities(self, result: opportunities.OpportunityResult, destination: Path, *, overwrite: bool = False) -> None:
        destination = self.previously_on_destination(destination)
        opportunities.save(result, destination, overwrite=overwrite)

    def previously_on_scout(self, data: previously_on.ScoutInput) -> previously_on.ScoutResult:
        with widelog.wide_event(op="previously_on_scout", session_count=len(data.history.sessions)):
            return asyncio.run(previously_on.scout_scenes(data, self._settings.llm_model_high, self._settings.previously_on.scout_timeout))

    def previously_on_destination(self, destination: Path) -> Path:
        destination = destination.expanduser().resolve()
        if destination.suffix.lower() != ".md":
            raise ValueError("Choose a Markdown file with a .md extension.")
        if destination.is_relative_to(paths.campaigns_root(self._cwd).resolve()):
            raise ValueError("Save the recap outside managed Campaign data.")
        if not destination.parent.is_dir() or destination.is_dir():
            raise ValueError("Choose a file in an existing directory.")
        return destination

    def export_previously_on(self, data: previously_on.EditorInput, destination: Path, *, overwrite: bool = False) -> None:
        destination = self.previously_on_destination(destination)
        if not data.selected_scenes:
            raise ValueError("Select at least one Scene before exporting.")
        with widelog.wide_event(op="export_previously_on", scene_count=len(data.selected_scenes)):
            asyncio.run(
                previously_on.write_recap(
                    data, destination, self._settings.llm_model_high, self._settings.previously_on.editor_timeout, overwrite=overwrite
                )
            )

    def export_campaign(self, campaign_id: uuid.UUID, destination: Path) -> None:
        from .campaign_archive import export_campaign

        export_campaign(self._db_path, paths.campaigns_root(self._cwd), campaign_id, destination)

    def import_campaign(self, source: Path) -> uuid.UUID:
        from .campaign_archive import import_campaign

        return import_campaign(self._db_path, paths.campaigns_root(self._cwd), source)

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
        validate_player_name(name)
        return named_entity_folder_exists(paths.players_root(self._cwd), name)

    def delete_orphan_player_folder(self, name: str) -> None:
        """Delete a stray player folder the user already confirmed clearing, so `create_player`/`rename_player` can proceed."""
        validate_player_name(name)
        delete_named_entity_folder(paths.players_root(self._cwd), name)

    def import_players(self, source: Path, on_progress: Callable[[int, int], None] | None = None) -> PlayerArchiveResult:
        from .player_archive import import_players

        return import_players(
            self._engine, paths.players_root(self._cwd), source, self._embed_clip, self._settings.remove_outliers, on_progress
        )

    def export_players(self, destination: Path) -> None:
        from .player_archive import export_players

        export_players(paths.players_root(self._cwd), [player.name for player in self.list_players()], destination)

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

    def can_delete_player(self, player_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            return players.can_delete_player(session, player_id)

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
            self._embedding_factory = EmbeddingFactory()
        return self._embedding_factory

    def _embed_clip(self, path: Path) -> Embedding:
        return self.embedding_factory().extract(path)

    # Glossary

    def create_glossary_entry(self, entry: GlossaryEntry) -> GlossaryEntry:
        with Session(self._engine) as session:
            result = glossary.create_glossary_entry(session, entry)
            campaign = campaigns.get_campaign(session, entry.campaign_id)
            campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(result)
            return result

    def list_glossary_entries(self, campaign_id: uuid.UUID) -> list[GlossaryEntry]:
        with Session(self._engine) as session:
            return glossary.list_glossary_entries(session, campaign_id)

    def update_glossary_entry(self, campaign_id: uuid.UUID, entry_id: uuid.UUID, term: str, description: str | None) -> GlossaryEntry:
        with Session(self._engine) as session:
            result = glossary.update_glossary_entry(session, campaign_id, entry_id, term, description)
            campaign = campaigns.get_campaign(session, campaign_id)
            campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(result)
            return result

    def delete_glossary_entry(self, campaign_id: uuid.UUID, entry_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            glossary.delete_glossary_entry(session, campaign_id, entry_id)
            campaign = campaigns.get_campaign(session, campaign_id)
            campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()

    def import_legacy_glossary(self, campaign_id: uuid.UUID, source_path: Path) -> int:
        """Import new terms from a pre-campaign ``settings.yaml`` glossary.

        Existing campaign terms, including their descriptions, are deliberately
        left unchanged. Duplicate terms within the legacy file are imported only
        once as well.
        """
        if source_path.suffix.lower() != ".yaml":
            raise ValueError("Please choose a YAML (.yaml) settings file.")

        try:
            source = yaml.safe_load(source_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise ValueError(f"Could not read '{source_path}': {exc.strerror or exc}") from exc
        except yaml.YAMLError as exc:
            raise ValueError(f"Could not parse '{source_path}' as YAML: {exc}") from exc

        if not isinstance(source, Mapping):
            raise ValueError("Legacy settings must contain a top-level mapping.")
        campaign_info = source.get("campaign_info")
        if not isinstance(campaign_info, Mapping):
            raise ValueError("Legacy settings must contain a 'campaign_info' mapping.")
        legacy_entries = campaign_info.get("glossary")
        if not isinstance(legacy_entries, list):
            raise ValueError("Legacy settings must contain a 'campaign_info.glossary' list.")

        entries: list[tuple[str, str | None]] = []
        for index, legacy_entry in enumerate(legacy_entries, start=1):
            if not isinstance(legacy_entry, Mapping):
                raise ValueError(f"Glossary entry {index} must be a mapping.")
            entry_mapping = cast(Mapping[object, object], legacy_entry)
            term = entry_mapping.get("term")
            description = entry_mapping.get("description")
            if not isinstance(term, str) or not (term := term.strip()):
                raise ValueError(f"Glossary entry {index} must have a non-blank 'term'.")
            if description is not None and not isinstance(description, str):
                raise ValueError(f"Glossary entry {index} has a non-text 'description'.")
            entries.append((term, description.strip() or None if isinstance(description, str) else None))

        with Session(self._engine) as session:
            existing_terms = {entry.term for entry in glossary.list_glossary_entries(session, campaign_id)}
            imported_count = 0
            for term, description in entries:
                if term in existing_terms:
                    continue
                glossary.create_glossary_entry(session, GlossaryEntry(campaign_id=campaign_id, term=term, description=description))
                existing_terms.add(term)
                imported_count += 1
            if imported_count:
                campaign = campaigns.get_campaign(session, campaign_id)
                campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()
            return imported_count

    def can_extract_glossary(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return extract_glossary_pipeline.can_extract_glossary(self._session_folder(session, game_session))

    def extract_glossary(self, session_id: uuid.UUID) -> list[extract_glossary_pipeline.GlossaryProposal]:
        """Propose new glossary entries from a Session's Role Transcript."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = extract_glossary_pipeline.can_extract_glossary(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot extract glossary terms.")

            attendees = tuple(
                extract_glossary_pipeline.AttendeePromptEntry(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sessions.list_attendance(session, session_id)
            )
            entries = sorted(glossary.list_glossary_entries(session, game_session.campaign_id), key=lambda entry: entry.term.casefold())
            prompt_glossary = tuple(
                extract_glossary_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in entries
            )
            transcript = clean_transcript_pipeline.render_role_transcript_text(session_folder)

        with widelog.wide_event(
            op="extract_glossary",
            session_id=str(session_id),
            attendee_count=len(attendees),
            existing_glossary_count=len(prompt_glossary),
        ) as log:
            proposals = asyncio.run(
                extract_glossary_pipeline.extract_glossary(transcript, attendees, prompt_glossary, self._settings.llm_model)
            )
            filtered = extract_glossary_pipeline.filter_existing_terms(proposals, [entry.term for entry in prompt_glossary])
            log.set(proposal_count=len(proposals), filtered_proposal_count=len(filtered))
            return sorted(filtered, key=lambda proposal: proposal.term.casefold())

    def complete_glossary_extraction(
        self, session_id: uuid.UUID, proposals: Sequence[extract_glossary_pipeline.GlossaryProposal]
    ) -> extract_glossary_pipeline.GlossaryCommitResult:
        """Atomically add unique reviewed proposals to the Session's campaign glossary."""
        normalized_proposals: list[extract_glossary_pipeline.GlossaryProposal] = []
        for proposal in proposals:
            term = proposal.term.strip()
            if not term:
                raise ValueError("Glossary terms cannot be blank.")
            description = proposal.description.strip() if proposal.description else None
            normalized_proposals.append(extract_glossary_pipeline.GlossaryProposal(term=term, description=description or None))

        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            existing = glossary.list_glossary_entries(session, game_session.campaign_id)
            seen = {extract_glossary_pipeline.normalize_term(entry.term) for entry in existing}
            accepted: list[GlossaryEntry] = []
            skipped_count = 0
            for proposal in normalized_proposals:
                normalized_term = extract_glossary_pipeline.normalize_term(proposal.term)
                if normalized_term in seen:
                    skipped_count += 1
                    continue
                seen.add(normalized_term)
                accepted.append(
                    GlossaryEntry(
                        campaign_id=game_session.campaign_id,
                        term=proposal.term,
                        description=proposal.description,
                    )
                )

            session.add_all(accepted)
            if accepted:
                campaign = campaigns.get_campaign(session, game_session.campaign_id)
                campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()

        return extract_glossary_pipeline.GlossaryCommitResult(added_count=len(accepted), skipped_duplicate_count=skipped_count)

    # Sessions

    def create_session(self, campaign_id: uuid.UUID, name: str, session_date: date | None = None) -> GameSession:
        with Session(self._engine) as session:
            campaign = session.get(Campaign, campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            result = sessions.create_session(session, campaign_id, name, session_date, paths.campaign_folder(self._cwd, campaign.name))
            sessions.seed_attendance_from_previous_session(session, campaign_id, result.id)
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

    @staticmethod
    def _summary_previous_session_id(session_folder: Path) -> uuid.UUID | None:
        """Return the recap source recorded when this Summary was generated, if available."""
        try:
            previous_session_id = json.loads((session_folder / paths.SUMMARY_INPUTS_FILENAME).read_text(encoding="utf-8")).get(
                "previous_session_id"
            )
            return uuid.UUID(previous_session_id) if isinstance(previous_session_id, str) else None
        except (OSError, json.JSONDecodeError, ValueError):
            return None

    def _artifact_graph(self, session: Session, campaign_id: uuid.UUID) -> artifact_graph_pipeline.ArtifactGraph:
        def prompt_input(name: PromptName) -> artifact_graph_pipeline.SystemPromptInput:
            return artifact_graph_pipeline.SystemPromptInput(system_prompt_path(name))

        game_sessions = sessions.list_sessions(session, campaign_id)
        sessions_by_id = {game_session.id: game_session for game_session in game_sessions}
        steps: list[artifact_graph_pipeline.BuildStep] = []
        interrupted: set[artifact_graph_pipeline.ArtifactRef] = set()
        # Each Summary: its own reference, its fixed dependencies, and the previous Session's folder (if any).
        summaries: list[tuple[artifact_graph_pipeline.ArtifactRef, list[artifact_graph_pipeline.Dependency], Path | None]] = []

        for game_session in game_sessions:
            folder = self._session_folder(session, game_session)

            def ref(name: paths.ArtifactName, folder: Path = folder) -> artifact_graph_pipeline.ArtifactRef:
                return artifact_graph_pipeline.ArtifactRef(folder, name)

            steps.extend(
                (
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.TRANSCRIPT,
                        (ref(paths.ArtifactName.TRANSCRIPT), ref(paths.ArtifactName.TRANSCRIPT_TEXT)),
                        (ref(paths.ArtifactName.INPUT_AUDIO),),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.CLEANED_TRANSCRIPT,
                        (ref(paths.ArtifactName.CLEANED_TRANSCRIPT),),
                        (
                            ref(paths.ArtifactName.TRANSCRIPT),
                            prompt_input(PromptName.CLASSIFY_BACKCHANNELS),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT,
                        (ref(paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT),),
                        (
                            ref(paths.ArtifactName.CLEANED_TRANSCRIPT),
                            prompt_input(PromptName.SUGGEST_NAME_CORRECTIONS),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS,
                        (ref(paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS),),
                        (
                            ref(paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT),
                            prompt_input(PromptName.ISOLATE_NEW_SPEAKERS),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS,
                        (ref(paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS),),
                        (ref(paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS),),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.SEEDED_VOICE_SAMPLES,
                        (ref(paths.ArtifactName.SEEDED_VOICE_SAMPLES),),
                        (ref(paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS),),
                    ),
                    # Identification also reads returning players' centroids from the database; changing
                    # those is not tracked here (see the session-processing-flow work item).
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.IDENTIFIED_TRANSCRIPT,
                        (ref(paths.ArtifactName.IDENTIFIED_TRANSCRIPT),),
                        (
                            ref(paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT),
                            ref(paths.ArtifactName.SEEDED_VOICE_SAMPLES),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.SPELLCHECKED_TRANSCRIPT,
                        (ref(paths.ArtifactName.SPELLCHECKED_TRANSCRIPT),),
                        (
                            ref(paths.ArtifactName.IDENTIFIED_TRANSCRIPT),
                            prompt_input(PromptName.SUGGEST_SPELLING_CORRECTIONS),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.REVIEWED_TRANSCRIPT,
                        (ref(paths.ArtifactName.REVIEWED_TRANSCRIPT),),
                        (ref(paths.ArtifactName.SPELLCHECKED_TRANSCRIPT),),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.ROLE_TRANSCRIPT,
                        (ref(paths.ArtifactName.ROLE_TRANSCRIPT),),
                        (ref(paths.ArtifactName.REVIEWED_TRANSCRIPT),),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.TRANSCRIPT_SECTIONS,
                        (ref(paths.ArtifactName.TRANSCRIPT_SECTIONS),),
                        (
                            ref(paths.ArtifactName.ROLE_TRANSCRIPT),
                            prompt_input(PromptName.SECTION_TRANSCRIPT),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.LEDGER,
                        (
                            ref(paths.ArtifactName.LEDGER),
                            artifact_graph_pipeline.FileRef(folder / generate_ledger_pipeline.LEDGER_MARKDOWN_FILENAME),
                            ref(paths.ArtifactName.SCENE_BREAKDOWN),
                        ),
                        (
                            ref(paths.ArtifactName.ROLE_TRANSCRIPT),
                            ref(paths.ArtifactName.TRANSCRIPT_SECTIONS),
                            prompt_input(PromptName.GENERATE_LEDGER),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.PLAYER_INTRODUCTIONS,
                        (ref(paths.ArtifactName.PLAYER_INTRODUCTIONS),),
                        (
                            ref(paths.ArtifactName.ROLE_TRANSCRIPT),
                            ref(paths.ArtifactName.TRANSCRIPT_SECTIONS),
                            prompt_input(PromptName.GENERATE_PLAYER_INTRODUCTIONS),
                        ),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.RECAP_SUMMARY,
                        (ref(paths.ArtifactName.RECAP_SUMMARY),),
                        (
                            ref(paths.ArtifactName.SCENE_BREAKDOWN),
                            prompt_input(PromptName.GENERATE_RECAP_SUMMARY),
                        ),
                    ),
                )
            )
            summary_dependencies: list[artifact_graph_pipeline.Dependency] = [
                ref(paths.ArtifactName.LEDGER),
                ref(paths.ArtifactName.PLAYER_INTRODUCTIONS),
                prompt_input(PromptName.SUMMARIZE_SESSION),
            ]
            # The Session the Summary recorded as previous; before its first generation, the one it will use.
            if (folder / paths.SUMMARY_INPUTS_FILENAME).exists():
                previous_session_id = self._summary_previous_session_id(folder)
                previous_session = sessions_by_id.get(previous_session_id) if previous_session_id is not None else None
            else:
                previous_session = sessions.find_prior_session(session, campaign_id, game_session.session_date)
            previous_folder = self._session_folder(session, previous_session) if previous_session is not None else None
            summaries.append((ref(paths.ArtifactName.SUMMARY), summary_dependencies, previous_folder))
            if (folder / paths.LEDGER_PAIR_MARKER).exists():
                interrupted.update((ref(paths.ArtifactName.LEDGER), ref(paths.ArtifactName.SCENE_BREAKDOWN)))

        # A Summary depends on the previous Session's recap only while that Session can be regenerated (its
        # reviewed transcript is current). Otherwise the Summary carries a placeholder and can still be current;
        # once the previous Session is reviewed, the dependency returns and the Summary goes out of date.
        # Reviewed transcripts never depend on Summaries, so a graph without them answers that safely.
        without_summaries = artifact_graph_pipeline.ArtifactGraph(tuple(steps), interrupted=frozenset(interrupted))
        for summary, summary_dependencies, previous_folder in summaries:
            if previous_folder is not None and self._previous_session_regenerable(without_summaries, previous_folder):
                summary_dependencies.append(artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.RECAP_SUMMARY))
            steps.append(artifact_graph_pipeline.BuildStep(paths.ArtifactName.SUMMARY, (summary,), tuple(summary_dependencies)))

        return artifact_graph_pipeline.ArtifactGraph(tuple(steps), interrupted=frozenset(interrupted))

    @staticmethod
    def _previous_session_regenerable(graph: artifact_graph_pipeline.ArtifactGraph, previous_folder: Path) -> bool:
        """Whether a previous Session's outputs can be rebuilt: generation needs its reviewed transcript current."""
        reviewed = artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.REVIEWED_TRANSCRIPT)
        return graph.status(reviewed) is artifact_graph_pipeline.ArtifactStatus.CURRENT

    def session_artifact_states(self, session_id: uuid.UUID) -> dict[paths.ArtifactName, artifact_graph_pipeline.ArtifactStatus]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            graph = self._artifact_graph(session, game_session.campaign_id)
            return graph.session_statuses(self._session_folder(session, game_session))

    def _first_current(self, session: Session, game_session: GameSession, *names: paths.ArtifactName) -> paths.ArtifactName | None:
        graph = self._artifact_graph(session, game_session.campaign_id)
        folder = self._session_folder(session, game_session)
        for name in names:
            if graph.status(artifact_graph_pipeline.ArtifactRef(folder, name)) is artifact_graph_pipeline.ArtifactStatus.CURRENT:
                return name
        return None

    def _current_transcript_source(self, session: Session, game_session: GameSession) -> paths.ArtifactName:
        """Players List "From Session"'s source: the completed review, else the identified transcript, else the machine one."""
        source = self._first_current(
            session,
            game_session,
            paths.ArtifactName.REVIEWED_TRANSCRIPT,
            paths.ArtifactName.IDENTIFIED_TRANSCRIPT,
            paths.ArtifactName.TRANSCRIPT,
        )
        if source is None:
            raise ValueError("No current transcript is available. Transcribe the session again before continuing.")
        return source

    def _review_source(self, session: Session, game_session: GameSession) -> paths.ArtifactName:
        """Review Transcript's starting point: a still-current completed review, else the spellchecked transcript."""
        source = self._first_current(
            session, game_session, paths.ArtifactName.REVIEWED_TRANSCRIPT, paths.ArtifactName.SPELLCHECKED_TRANSCRIPT
        )
        if source is None:
            raise ValueError("The spellchecked transcript isn't current. Run Spellcheck Against Glossary first.")
        return source

    def generation_plan(
        self,
        session_id: uuid.UUID,
        *,
        force: paths.ArtifactName | None = None,
        rebuild_prior_sessions: bool = True,
    ) -> tuple[artifact_graph_pipeline.GenerationTask, ...]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            graph = self._artifact_graph(session, game_session.campaign_id)
            campaign_sessions = sessions.list_sessions(session, game_session.campaign_id)
            folder_by_id = {item.id: self._session_folder(session, item) for item in campaign_sessions}
            session_id_by_folder = {folder: item_id for item_id, folder in folder_by_id.items()}

            if force is not None and force not in artifact_graph_pipeline.GENERATION_DEPENDENCIES:
                raise ValueError(f"{paths.ARTIFACTS[force].display_name} cannot be regenerated from this screen.")

            requested = set(artifact_graph_pipeline.GENERATION_ORDER) if force is None else {force}
            forced: set[paths.ArtifactName] = set()
            if force is not None:
                forced.add(force)
                changed = True
                while changed:
                    changed = False
                    for candidate, candidate_dependencies in artifact_graph_pipeline.GENERATION_DEPENDENCIES.items():
                        if candidate not in requested and candidate_dependencies & requested:
                            requested.add(candidate)
                            forced.add(candidate)
                            changed = True

            plan: list[artifact_graph_pipeline.GenerationTask] = []
            scheduled: set[tuple[uuid.UUID, paths.ArtifactName]] = set()

            def ensure(target_session_id: uuid.UUID, name: paths.ArtifactName, *, is_forced: bool = False) -> None:
                key = (target_session_id, name)
                if key in scheduled:
                    return
                target = artifact_graph_pipeline.ArtifactRef(folder_by_id[target_session_id], name)
                step = graph.step_for(target)
                if step is None:
                    raise ValueError(f"No build step produces {paths.ARTIFACTS[name].display_name}.")
                needs_build = is_forced or graph.status(target) is not artifact_graph_pipeline.ArtifactStatus.CURRENT
                if not needs_build:
                    return

                for dependency in step.dependencies:
                    if not isinstance(dependency, artifact_graph_pipeline.ArtifactRef):
                        continue
                    dependency_status = graph.status(dependency)
                    if dependency_status is artifact_graph_pipeline.ArtifactStatus.CURRENT:
                        continue
                    dependency_step = graph.step_for(dependency)
                    if dependency_step is None or dependency_step.name not in artifact_graph_pipeline.GENERATION_DEPENDENCIES:
                        raise ValueError(
                            f"{paths.ARTIFACTS[dependency.name].display_name} must be current before outputs can be generated."
                        )
                    dependency_session_id = session_id_by_folder[dependency.session_folder]
                    if dependency_session_id != session_id and not rebuild_prior_sessions:
                        continue
                    ensure(dependency_session_id, dependency_step.name)

                scheduled.add(key)
                plan.append(artifact_graph_pipeline.GenerationTask(target_session_id, name))

            for name in artifact_graph_pipeline.GENERATION_ORDER:
                if name in requested:
                    ensure(session_id, name, is_forced=name in forced)
            return tuple(plan)

    def generate_outputs(
        self,
        session_id: uuid.UUID,
        *,
        force: paths.ArtifactName | None = None,
        rebuild_prior_sessions: bool = True,
        on_stage: Callable[[artifact_graph_pipeline.GenerationTask, int, int], None] | None = None,
        on_clean_progress: Callable[[clean_transcript_pipeline.Stage, int, int], None] | None = None,
    ) -> tuple[artifact_graph_pipeline.GenerationTask, ...]:
        """Run a session's missing or stale output phases in dependency order."""
        plan = (
            self.generation_plan(session_id, force=force)
            if rebuild_prior_sessions
            else self.generation_plan(session_id, force=force, rebuild_prior_sessions=False)
        )
        phases: dict[paths.ArtifactName, Callable[[uuid.UUID], object]] = {
            paths.ArtifactName.ROLE_TRANSCRIPT: lambda task_session_id: self.clean_transcript(
                task_session_id, on_progress=on_clean_progress
            ),
            paths.ArtifactName.TRANSCRIPT_SECTIONS: self.generate_transcript_sections,
            paths.ArtifactName.LEDGER: self.generate_ledger,
            paths.ArtifactName.PLAYER_INTRODUCTIONS: self.generate_player_introductions,
            paths.ArtifactName.RECAP_SUMMARY: self.generate_recap_summary,
            paths.ArtifactName.SUMMARY: lambda task_session_id: self.generate_summary(
                task_session_id,
                omit_stale_prior_recap=not rebuild_prior_sessions,
            ),
        }
        for completed, task in enumerate(plan):
            if on_stage is not None:
                on_stage(task, completed, len(plan))
            try:
                phases[task.artifact_name](task.session_id)
            except Exception as exc:
                label = artifact_graph_pipeline.GENERATION_LABELS[task.artifact_name]
                raise RuntimeError(f"{label} generation failed: {exc}") from exc
        return plan

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

    def export_ledger_markdown(self, session_id: uuid.UUID, destination: Path) -> None:
        """Render the canonical Ledger on demand and export its human-readable Markdown view."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
        ledger_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.LEDGER].filename
        markdown_path = session_folder / generate_ledger_pipeline.LEDGER_MARKDOWN_FILENAME
        markdown_path.write_text(generate_ledger_pipeline.Ledger.load(ledger_path).to_markdown(), encoding="utf-8")
        shutil.copyfile(markdown_path, destination)

    def session_player_centroids(self, session_id: uuid.UUID) -> dict[str, Embedding]:
        """Attending players' voice centroids, keyed by player name -- `transcribe_audio`'s speaker-ID input."""
        with Session(self._engine) as session:
            centroids: dict[str, Embedding] = {}
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                if player is not None:
                    embedding = self._usable_player_embedding(player)
                    if embedding is not None:
                        centroids[player.name] = embedding
            return centroids

    def new_players(self, session_id: uuid.UUID) -> list[isolate_new_speakers_pipeline.NewPlayer]:
        """This Session's new players -- attendees with no usable voice centroid -- computed live from the database.

        Deliberately not persisted or part of artifact staleness: changing attendance or voice
        profiles after the new-player steps ran does not invalidate them.
        """
        with Session(self._engine) as session:
            new_players: list[isolate_new_speakers_pipeline.NewPlayer] = []
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                assert player is not None
                if self._usable_player_embedding(player) is None:
                    new_players.append(isolate_new_speakers_pipeline.NewPlayer(attendee.player_id, attendee.player_name, attendee.roles))
            return new_players

    def session_processing_blockers(self, session_id: uuid.UUID) -> list[paths.ProcessingBlocker]:
        """Errors that stop a Process Session step, and every step after it, from running."""
        blockers: list[paths.ProcessingBlocker] = []
        if not self.list_attendance(session_id):
            blockers.append(
                paths.ProcessingBlocker(
                    paths.SessionProcessingStageID.IMPORTING_AUDIO,
                    "This Session has no attendees. Add them on Session Detail.",
                )
            )
        return blockers

    @staticmethod
    def _usable_player_embedding(player: Player, expected_dimension: int | None = None) -> Embedding | None:
        """Validate a stored centroid before using it as identification evidence.

        Profiles do not identify their embedding backend, so the caller can provide an expected
        dimension when it is known.
        """
        if player.centroid_embedding is None or player.sample_count <= 0:
            return None
        try:
            embedding = Embedding.model_validate(json.loads(player.centroid_embedding))
        except (json.JSONDecodeError, ValueError, TypeError):
            return None
        dimension = len(embedding)
        if dimension == 0 or player.embedding_dimension != dimension:
            return None
        if expected_dimension is not None and dimension != expected_dimension:
            return None
        if not all(math.isfinite(value) for value in embedding.root):
            return None
        magnitude_squared = sum(value * value for value in embedding.root)
        return embedding if magnitude_squared > 0 else None

    def session_player_roles(self, session_id: uuid.UUID) -> dict[str, str]:
        """Attending players' first (alphabetically) role name that session, keyed by player name.

        Used by Ledger generation's role-name rendering step.
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

    def import_and_transcribe_audio(
        self,
        session_id: uuid.UUID,
        source_path: Path,
        *,
        should_clean_audio: bool,
        on_progress: transcribe_audio.OnProgress | None = None,
    ) -> transcribe_audio.TranscriptionResult:
        """Atomically replace input audio, invalidate an incompatible draft, and transcribe it.

        The input-audio replacement remains atomic inside the import pipeline. Only after that
        replacement succeeds do we clear a saved review draft, because its source can no longer
        match. A subsequent transcription failure leaves the newly imported audio available for
        an explicit retry.
        """
        self.validate_import_audio_source(source_path)
        session_folder = self.session_folder(session_id)
        import_audio.import_audio(
            source_path,
            session_folder,
            self._settings.session_audio_import.normalize_volume,
            should_clean_audio=should_clean_audio,
        )
        self.discard_review_draft(session_id)
        return self.transcribe_session_audio(session_id, on_progress=on_progress)

    def import_session_audio(self, session_id: uuid.UUID, source_path: Path, *, should_clean_audio: bool) -> None:
        """Replace input audio; the artifact graph marks everything derived from the old audio stale."""
        self.validate_import_audio_source(source_path)
        import_audio.import_audio(
            source_path,
            self.session_folder(session_id),
            self._settings.session_audio_import.normalize_volume,
            should_clean_audio=should_clean_audio,
        )

    def create_transcript(self, session_id: uuid.UUID, *, on_progress: transcribe_audio.OnProgress | None = None) -> int:
        """Process Session's Create Transcript step; returns the utterance count."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = transcribe_audio.can_transcribe_audio(session, session_id, session_folder)
            if not enabled:
                raise RuntimeError(reason or "Cannot transcribe audio.")
            attendee_count = len(sessions.list_attendance(session, session_id))
        return transcribe_audio.create_transcript(
            session_folder, attendee_count, self._settings.transcription_and_diarization, on_progress=on_progress
        )

    def remove_bad_utterances(self, session_id: uuid.UUID, *, on_progress: Callable[[int, int], None] | None = None) -> int:
        """Process Session's Remove Bad Utterances step: `transcript.json` minus backchannels, written as
        `cleaned_transcript.json`. Returns the number of utterances removed."""
        session_folder = self.session_folder(session_id)
        transcript = Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT].filename)
        settings = self._settings.remove_backchannels
        cleaned = asyncio.run(
            remove_backchannels(
                transcript,
                settings.max_words,
                self._settings.llm_model_lite,
                settings.question_check_timeout,
                settings.batch_size,
                settings.max_concurrent_batches,
                on_progress=on_progress,
            )
        )
        cleaned.save(session_folder / paths.ARTIFACTS[paths.ArtifactName.CLEANED_TRANSCRIPT].filename)
        return len(transcript.utterances) - len(cleaned.utterances)

    def _named_players(self, session_id: uuid.UUID) -> list[name_corrections_pipeline.NamedPlayer]:
        return [
            name_corrections_pipeline.NamedPlayer(attendee.player_name, attendee.roles) for attendee in self.list_attendance(session_id)
        ]

    def suggest_name_corrections(
        self, session_id: uuid.UUID
    ) -> tuple[Transcript, list[suggest_spelling_corrections_pipeline.SpellingSuggestion]]:
        """Process Session's Review Name Corrections step: the cleaned transcript and the LLM's proposed
        corrections to every attendee's player and character names. Raises when the LLM call fails."""
        session_folder = self.session_folder(session_id)
        transcript = name_corrections_pipeline.load_source(session_folder)
        players = self._named_players(session_id)
        with widelog.wide_event(
            op="suggest_name_corrections", session_id=str(session_id), player_count=len(players), utterance_count=len(transcript.utterances)
        ) as log:
            suggestions = asyncio.run(
                name_corrections_pipeline.suggest_name_corrections(
                    transcript, players, self._settings.llm_model, float(self._settings.name_corrections.timeout)
                )
            )
            log.set(suggestion_count=len(suggestions))
        return transcript, suggestions

    def save_name_corrections(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> tuple[bool, int]:
        """Write the name-corrected transcript from the reviewed corrections; return whether it was written
        and how many occurrences were replaced."""
        states = self.session_artifact_states(session_id)
        return name_corrections_pipeline.save_corrected(
            self.session_folder(session_id),
            corrections,
            saved_is_current=states[paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT] is artifact_graph_pipeline.ArtifactStatus.CURRENT,
        )

    def isolate_new_speakers(
        self, session_id: uuid.UUID, *, on_progress: isolate_new_speakers_pipeline.OnProgress | None = None
    ) -> isolate_new_speakers_pipeline.NewSpeakerAssignments:
        """Process Session's Isolate New Speakers step: high-confidence utterances for each new player."""
        session_folder = self.session_folder(session_id)
        bootstrap = self._settings.speaker_bootstrap
        isolation = self._settings.isolate_new_speakers
        outliers = self._settings.remove_outliers
        return isolate_new_speakers_pipeline.isolate_new_speakers(
            session_folder,
            self.new_players(session_id),
            isolate_new_speakers_pipeline.IsolationSettings(
                model=self._settings.llm_model,
                timeout=float(bootstrap.evidence_timeout),
                max_attempts=bootstrap.evidence_max_attempts,
                min_speech_seconds=isolation.min_speech_seconds,
                min_total_speech_seconds=bootstrap.min_total_speech_seconds,
                target_total_speech_seconds=bootstrap.target_total_speech_seconds,
                fallback_short_clip_seconds=isolation.fallback_short_clip_seconds,
                fallback_max_speech_seconds=isolation.fallback_max_speech_seconds,
                min_seed_speech_seconds=isolation.min_seed_speech_seconds,
                outlier_min_sample_similarity=outliers.min_sample_similarity,
                outlier_min_samples=outliers.min_samples,
            ),
            self._embed_clip,
            on_progress=on_progress,
        )

    def _current_new_speaker_review(
        self, session_id: uuid.UUID
    ) -> review_new_speaker_assignments_pipeline.ReviewedNewSpeakerAssignments | None:
        """The saved reviewed assignments, but only while the artifact graph says they are current."""
        states = self.session_artifact_states(session_id)
        if states[paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS] is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
            return None
        return review_new_speaker_assignments_pipeline.load_reviewed(self.session_folder(session_id))

    def new_speaker_assignment_review(self, session_id: uuid.UUID) -> review_new_speaker_assignments_pipeline.ReviewData:
        """Process Session's Review New Speaker Assignments step: each new player's proposed utterances,
        with earlier removals when a current review exists."""
        session_folder = self.session_folder(session_id)
        return review_new_speaker_assignments_pipeline.review_data(
            session_folder,
            review_new_speaker_assignments_pipeline.load_proposals(session_folder),
            self._current_new_speaker_review(session_id),
        )

    def extract_new_speaker_review_clips(
        self, session_id: uuid.UUID, indices: Sequence[int], on_progress: Callable[[int, int], None] | None = None
    ) -> None:
        review_new_speaker_assignments_pipeline.extract_clips(self.session_folder(session_id), indices, on_progress)

    def new_speaker_review_clip(self, session_id: uuid.UUID, utterance_index: int) -> Path:
        return review_new_speaker_assignments_pipeline.clip_path(self.session_folder(session_id), utterance_index)

    def discard_new_speaker_review_clips(self, session_id: uuid.UUID) -> None:
        review_new_speaker_assignments_pipeline.discard_clips(self.session_folder(session_id))

    def confirm_new_speaker_assignment_review(self, session_id: uuid.UUID, kept: Mapping[uuid.UUID, Sequence[int]]) -> bool:
        """Save the kept utterances; return whether the file was written (it is not when a current review matches)."""
        session_folder = self.session_folder(session_id)
        return review_new_speaker_assignments_pipeline.save_review(
            session_folder,
            review_new_speaker_assignments_pipeline.load_proposals(session_folder),
            kept,
            self._current_new_speaker_review(session_id),
        )

    def new_player_steps_skipped(self, session_id: uuid.UUID) -> bool:
        """Whether Process Session shows the new-player steps as not needed.

        Once Isolate New Speakers has run (and is current), its output decides: the steps were needed
        when it found new players to isolate. Before that, the live new-player list decides. This keeps
        a Session whose new players were just seeded -- and so are no longer new -- showing those steps
        as done rather than skipped.
        """
        states = self.session_artifact_states(session_id)
        if states[paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS] is artifact_graph_pipeline.ArtifactStatus.CURRENT:
            try:
                proposals = review_new_speaker_assignments_pipeline.load_proposals(self.session_folder(session_id))
            except (OSError, ValueError):
                return not self.new_players(session_id)
            return not proposals.players
        return not self.new_players(session_id)

    def seed_player_voice_samples(
        self, session_id: uuid.UUID, *, on_progress: seed_voice_samples_pipeline.OnProgress | None = None
    ) -> seed_voice_samples_pipeline.SeededVoiceSamples:
        """Process Session's Seed Player Voice Samples step: cut each reviewed new player's kept utterances into
        clips in their folder, recompute their centroids, then write the receipt."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)
            reviewed = review_new_speaker_assignments_pipeline.load_reviewed(session_folder)
            if reviewed is None:
                raise ValueError("The reviewed new speaker assignments are missing or unreadable.")
            targets: list[seed_voice_samples_pipeline.SeedTarget] = []
            for assignment in reviewed.players:
                player = players.get_player(session, assignment.player_id)
                targets.append(
                    seed_voice_samples_pipeline.SeedTarget(
                        assignment.player_id, player.name, paths.player_folder(self._cwd, player.name), assignment.utterance_indices
                    )
                )
            outliers = self._settings.remove_outliers
            receipt = seed_voice_samples_pipeline.seed_voice_samples(
                session,
                session_id,
                session_folder,
                campaign.name,
                game_session.name,
                targets,
                self._embed_clip,
                self._settings.enhance_voices.min_embeddable_clip_seconds,
                outliers.min_sample_similarity,
                outliers.min_samples,
                on_progress,
            )
            session.commit()
        # Written last: the receipt marks the step complete only once clips and centroids are saved.
        seed_voice_samples_pipeline.save_receipt(session_folder, receipt)
        return receipt

    def identify_session_speakers(self, session_id: uuid.UUID, *, on_progress: transcribe_audio.OnProgress | None = None) -> Transcript:
        """Process Session's Identify Speakers step: label each utterance of the name-corrected transcript with the
        attendee whose voice centroid it matches, or leave it unassigned, and write the identified transcript."""
        session_folder = self.session_folder(session_id)
        transcript = Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
        centroids = self.session_player_centroids(session_id)
        with widelog.wide_event(
            op="identify_session_speakers",
            session_id=str(session_id),
            reference_count=len(centroids),
            utterance_count=len(transcript.utterances),
        ) as log:
            identified = transcribe_audio.identify_raw_transcript(
                session_folder,
                transcript,
                centroids,
                self.embedding_factory(),
                self._settings.speaker_identification,
                on_progress=on_progress,
            )
            if len(identified.utterances) != len(transcript.utterances):
                raise ValueError("Speaker identification changed the number of utterances.")
            log.set(unassigned_count=sum(1 for utterance in identified.utterances if utterance.speaker == UNASSIGNED_SPEAKER))
        atomic_write(
            session_folder / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename,
            identified.model_dump_json(indent=2).encode("utf-8"),
        )
        return identified

    def suggest_glossary_spelling_corrections(
        self, session_id: uuid.UUID
    ) -> tuple[Transcript, list[suggest_spelling_corrections_pipeline.SpellingSuggestion]]:
        """Process Session's Spellcheck Against Glossary step: the identified transcript and the LLM's proposed
        corrections against the campaign glossary and attendees. Raises when the LLM call fails, so the
        failure lands in Process Session's error list instead of silently skipping the check."""
        session_folder = self.session_folder(session_id)
        transcript = Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename)
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            attendee_names = [attendee.player_name for attendee in sessions.list_attendance(session, session_id)]
            glossary_terms = [entry.term for entry in glossary.list_glossary_entries(session, game_session.campaign_id)]
        if not attendee_names and not glossary_terms:
            return transcript, []
        with widelog.wide_event(
            op="suggest_glossary_spelling_corrections", session_id=str(session_id), glossary_count=len(glossary_terms)
        ) as log:
            proposals = asyncio.run(
                suggest_spelling_corrections_pipeline.suggest_spelling_corrections(
                    transcript, glossary_terms, attendee_names, self._settings.llm_model
                )
            )
            suggestions = suggest_spelling_corrections_pipeline.filter_and_dedupe_suggestions(proposals, transcript)
            log.set(proposal_count=len(proposals), suggestion_count=len(suggestions))
        return transcript, suggestions

    def save_glossary_spelling_corrections(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> tuple[bool, int]:
        """Write the spellchecked transcript from the reviewed corrections; return whether it was written and how
        many occurrences were replaced."""
        session_folder = self.session_folder(session_id)
        states = self.session_artifact_states(session_id)
        return suggest_spelling_corrections_pipeline.save_corrected_transcript(
            Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename),
            session_folder / paths.ARTIFACTS[paths.ArtifactName.SPELLCHECKED_TRANSCRIPT].filename,
            corrections,
            whole_words=False,
            saved_is_current=states[paths.ArtifactName.SPELLCHECKED_TRANSCRIPT] is artifact_graph_pipeline.ArtifactStatus.CURRENT,
        )

    def complete_processing_step_automatically(self, session_id: uuid.UUID, stage: paths.SessionProcessingStageID) -> bool:
        """Complete a manual step without its screen when it has nothing to review; return whether it did.

        With no new players, Review Name Corrections writes the cleaned transcript unchanged, and
        Review New Speaker Assignments (whose input is then empty) writes an empty review.
        """
        if stage is paths.SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS:
            if self.new_players(session_id):
                return False
            self.save_name_corrections(session_id, ())
            return True
        if stage is not paths.SessionProcessingStageID.REVIEWING_NEW_SPEAKER_ASSIGNMENTS:
            return False
        proposals = review_new_speaker_assignments_pipeline.load_proposals(self.session_folder(session_id))
        if proposals.players:
            return False
        self.confirm_new_speaker_assignment_review(session_id, {})
        return True

    def transcribe_session_audio(
        self,
        session_id: uuid.UUID,
        *,
        on_progress: transcribe_audio.OnProgress | None = None,
    ) -> transcribe_audio.TranscriptionResult:
        """Transcribe the currently imported audio using deployed application settings."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = transcribe_audio.can_transcribe_audio(session, session_id, session_folder)
            if not enabled:
                raise RuntimeError(reason or "Cannot transcribe audio.")

        return transcribe_audio.transcribe_audio(
            session_folder,
            self.session_player_centroids(session_id),
            self.embedding_factory(),
            self._settings.transcription_and_diarization,
            self._settings.speaker_identification,
            self._settings.remove_backchannels,
            self._settings.llm_model_lite,
            on_progress=on_progress,
        )

    def can_clean_session(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return processing.can_clean_session(self._session_folder(session, game_session))

    def clean_session(self, session_id: uuid.UUID) -> None:
        """Delete every artifact for this session, including the raw input audio.

        Backs Session Detail's Clean Session (`C`) action, always behind a confirmation since
        it's destructive and, unlike every other invalidation in this screen, not a side effect of
        some other edit -- it's the whole point of pressing the binding.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            session_processing_entities.delete_state(session, session_id)
            session.commit()
        session_processing_pipeline.discard_review_draft(session_folder)
        artifacts.delete_all_artifacts(session_folder)
        # The retired bootstrap workflow kept its working documents here; they are disposable.
        shutil.rmtree(session_folder / "processing", ignore_errors=True)

    def clean_transcript(
        self,
        session_id: uuid.UUID,
        on_progress: Callable[[clean_transcript_pipeline.Stage, int, int], None] | None = None,
    ) -> clean_transcript_pipeline.CleanTranscriptResult:
        """Process Session's Assign Roles To Players step (also a generation task): drop leftover unassigned
        backchannels from the completed review and replace player names with character names, writing
        `role_transcript.json`."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = clean_transcript_pipeline.can_clean_transcript(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot clean transcript.")

        role_names = self.session_player_roles(session_id)
        return clean_transcript_pipeline.clean_transcript(
            session_folder,
            self._settings.remove_backchannels.max_words,
            role_names,
            on_progress=on_progress,
        )

    def can_generate_ledger(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return generate_ledger_pipeline.can_generate_ledger(self._session_folder(session, game_session))

    def can_generate_transcript_sections(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_sections_pipeline.can_generate_transcript_sections(self._session_folder(session, game_session))

    def generate_transcript_sections(self, session_id: uuid.UUID) -> transcript_sections_pipeline.TranscriptSections:
        """Classify and persist the opening sections of a Session's Role Transcript."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = transcript_sections_pipeline.can_generate_transcript_sections(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot section transcript.")
            attendees = tuple(
                transcript_sections_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sessions.list_attendance(session, session_id)
            )
            role_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.ROLE_TRANSCRIPT].filename
            role_transcript = transcript_sections_pipeline.RoleTranscript.load(role_path)

        with widelog.wide_event(
            op="generate_session_transcript_sections",
            session_id=str(session_id),
            session_folder=str(session_folder),
            attendee_count=len(attendees),
            role_transcript_utterance_count=len(role_transcript.utterances),
        ) as log:
            generated = asyncio.run(
                transcript_sections_pipeline.generate_transcript_sections(
                    role_transcript,
                    attendees,
                    self._settings.llm_model_high,
                )
            )
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT_SECTIONS].filename
            result = transcript_sections_pipeline.persist_transcript_sections(generated, role_path, target)
            if result.starting_context_range is None:
                raise transcript_sections_pipeline.TranscriptSectionsValidationError(
                    "Transcript sectioning found no usable starting situation; downstream generation cannot continue."
                )
            log.set(
                artifact_path=str(target),
                recap_range=result.recap_range.model_dump() if result.recap_range is not None else None,
                introduction_range=result.introduction_range.model_dump() if result.introduction_range is not None else None,
                starting_context_range=result.starting_context_range.model_dump(),
                session_start_index=result.session_start_index,
                failed=False,
            )
            return result

    def generate_ledger(self, session_id: uuid.UUID) -> None:
        """Generate and replace a Session's matched Ledger and Scene Breakdown artifacts."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = generate_ledger_pipeline.can_generate_ledger(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot generate Ledger.")

            attendees = sessions.list_attendance(session, session_id)
            known_roles = tuple(sorted({role for attendee in attendees for role in attendee.roles}))
            ledger_attendees = tuple(
                generate_ledger_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sorted(attendees, key=lambda attendee: attendee.player_name.casefold())
            )
            glossary_entries = sorted(
                glossary.list_glossary_entries(session, game_session.campaign_id), key=lambda entry: entry.term.casefold()
            )
            ledger_glossary = tuple(
                generate_ledger_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in glossary_entries
            )
            role_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.ROLE_TRANSCRIPT].filename
            sections_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT_SECTIONS].filename
            role_transcript = transcript_sections_pipeline.RoleTranscript.load(role_path)
            transcript_sections = transcript_sections_pipeline.load_current_transcript_sections(role_path, sections_path)
            routed_transcript = transcript_sections_pipeline.route_transcript(role_transcript, transcript_sections)
            session_name = game_session.name

        with widelog.wide_event(
            op="generate_session_ledger",
            session_id=str(session_id),
            session_folder=str(session_folder),
            known_role_count=len(known_roles),
            glossary_count=len(ledger_glossary),
            starting_context_utterance_count=len(routed_transcript.starting_context),
            session_utterance_count=len(routed_transcript.session),
        ) as log:
            generated = asyncio.run(
                generate_ledger_pipeline.generate_ledger(
                    routed_transcript.starting_context,
                    routed_transcript.session,
                    known_roles,
                    ledger_attendees,
                    ledger_glossary,
                    self._settings.llm_model_high,
                )
            )
            ledger = generate_ledger_pipeline.Ledger(
                version=4,
                session_id=session_id,
                session_name=session_name,
                attendees=ledger_attendees,
                starting_situation=generated.starting_situation,
                utterances=generated.ledger.utterances,
            )
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.LEDGER].filename
            markdown_target = session_folder / generate_ledger_pipeline.LEDGER_MARKDOWN_FILENAME
            breakdown = persist_ledger_pair(ledger, generated.scene_breakdown, session_folder)
            log.set(
                ledger_utterance_count=len(ledger.utterances),
                scene_count=len(breakdown.scenes),
                ledger_json_path=str(target),
                ledger_markdown_path=str(markdown_target),
                scene_breakdown_path=str(session_folder / paths.ARTIFACTS[paths.ArtifactName.SCENE_BREAKDOWN].filename),
                failed=False,
            )

    def can_generate_player_introductions(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return player_introductions_pipeline.can_generate_player_introductions(self._session_folder(session, game_session))

    def generate_player_introductions(self, session_id: uuid.UUID) -> player_introductions_pipeline.PlayerIntroductions:
        """Generate and atomically persist explicitly introduced attendee characters."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)
            enabled, reason = player_introductions_pipeline.can_generate_player_introductions(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot generate Player Introductions.")

            role_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.ROLE_TRANSCRIPT].filename
            sections_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT_SECTIONS].filename
            role_transcript = transcript_sections_pipeline.RoleTranscript.load(role_path)
            transcript_sections = transcript_sections_pipeline.load_current_transcript_sections(role_path, sections_path)
            introduction_transcript = transcript_sections_pipeline.slice_introduction_transcript(role_transcript, transcript_sections)
            prompt_attendees = tuple(
                player_introductions_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sessions.list_attendance(session, session_id)
            )
            prompt_glossary = tuple(
                player_introductions_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description)
                for entry in glossary.list_glossary_entries(session, game_session.campaign_id)
            )
            campaign_name = campaign.name
            game_system = campaign.game_system
            session_date = game_session.session_date.isoformat() if game_session.session_date else None

        with widelog.wide_event(
            op="generate_session_player_introductions",
            session_id=str(session_id),
            session_folder=str(session_folder),
            attendee_count=len(prompt_attendees),
            glossary_entry_count=len(prompt_glossary),
            introduction_range_present=introduction_transcript is not None,
            introduction_utterance_count=len(introduction_transcript or ()),
        ) as log:
            generated = asyncio.run(
                player_introductions_pipeline.generate_player_introductions(
                    introduction_transcript,
                    prompt_attendees,
                    prompt_glossary,
                    campaign_name,
                    session_date,
                    game_system,
                    self._settings.llm_model_high,
                )
            )
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.PLAYER_INTRODUCTIONS].filename
            result = player_introductions_pipeline.persist_player_introductions(generated, session_id, target)
            log.set(
                introduction_count=len(result.introductions),
                artifact_path=str(target),
                failed=False,
            )
            return result

    def can_generate_recap_summary(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return recap_summary_pipeline.can_generate_recap_summary(self._session_folder(session, game_session))

    def generate_recap_summary(self, session_id: uuid.UUID) -> str:
        """Generate and atomically persist a compact recap from the current Scene Breakdown."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)
            enabled, reason = recap_summary_pipeline.can_generate_recap_summary(session_folder)
            if not enabled:
                raise ValueError(reason or "Cannot generate Recap Summary.")

            entries = sorted(
                glossary.list_glossary_entries(session, game_session.campaign_id),
                key=lambda entry: entry.term.casefold(),
            )
            prompt_glossary = tuple(
                recap_summary_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in entries
            )
            attendees = sessions.list_attendance(session, session_id)
            prompt_attendees = tuple(
                recap_summary_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sorted(attendees, key=lambda attendee: attendee.player_name.casefold())
            )
            breakdown = load_current_scene_breakdown(session_folder)
            if breakdown.session_id != session_id:
                raise ValueError("Scene Breakdown belongs to a different Session.")
            breakdown_text = breakdown.model_dump_json(indent=2)
            campaign_name = campaign.name
            session_date = game_session.session_date.isoformat() if game_session.session_date else None
            game_system = campaign.game_system

        with widelog.wide_event(
            op="generate_recap_summary",
            session_id=str(session_id),
            session_folder=str(session_folder),
            attendee_count=len(prompt_attendees),
            glossary_entry_count=len(prompt_glossary),
            scene_breakdown_chars=len(breakdown_text),
        ) as log:
            recap = asyncio.run(
                recap_summary_pipeline.generate_recap_summary(
                    breakdown_text,
                    prompt_attendees,
                    prompt_glossary,
                    campaign_name,
                    session_date,
                    game_system,
                    self._settings.llm_model_high,
                )
            )
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.RECAP_SUMMARY].filename
            recap_summary_pipeline.persist_recap_summary(recap, target)
            log.set(recap_chars=len(recap), artifact_path=str(target), failed=False)
            return recap

    def can_generate_summary(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            previous_session = sessions.find_prior_session(session, game_session.campaign_id, game_session.session_date)
            previous_folder = self._session_folder(session, previous_session) if previous_session is not None else None
            return processing.can_generate_summary(self._session_folder(session, game_session), previous_folder)

    def generate_summary(self, session_id: uuid.UUID, *, omit_stale_prior_recap: bool = False) -> None:
        """Generate and atomically replace a session's Markdown summary from its Ledger."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)
            previous_session = sessions.find_prior_session(session, game_session.campaign_id, game_session.session_date)
            previous_folder = self._session_folder(session, previous_session) if previous_session is not None else None
            graph = self._artifact_graph(session, game_session.campaign_id)
            previous_recap_is_current = previous_folder is None or (
                graph.status(artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.RECAP_SUMMARY))
                is artifact_graph_pipeline.ArtifactStatus.CURRENT
            )
            # A previous Session that can't be regenerated contributes whatever recap it already has, or the
            # placeholder when it has none, without asking. One the caller chose not to rebuild ("Current Only")
            # gets the placeholder.
            previous_recap_path = (
                previous_folder / paths.ARTIFACTS[paths.ArtifactName.RECAP_SUMMARY].filename if previous_folder is not None else None
            )
            previous_unregenerable = previous_folder is not None and not self._previous_session_regenerable(graph, previous_folder)
            omit_previous_recap = previous_recap_path is not None and (
                (previous_unregenerable and not previous_recap_path.is_file())
                or (not previous_unregenerable and omit_stale_prior_recap and not previous_recap_is_current)
            )
            required_previous_folder = None if omit_previous_recap or previous_unregenerable else previous_folder
            enabled, reason = processing.can_generate_summary(session_folder, required_previous_folder)
            if not enabled:
                raise ValueError(reason or "Cannot generate summary.")

            entries = sorted(glossary.list_glossary_entries(session, game_session.campaign_id), key=lambda entry: entry.term.casefold())
            prompt_glossary = [
                generate_summary_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in entries
            ]
            attendees = sessions.list_attendance(session, session_id)
            prompt_attendees = tuple(
                generate_summary_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sorted(attendees, key=lambda attendee: attendee.player_name.casefold())
            )
            introduction_attendees = tuple(
                player_introductions_pipeline.Attendee(player_name=attendee.player_name, roles=attendee.roles) for attendee in attendees
            )
            ledger_text = (session_folder / paths.ARTIFACTS[paths.ArtifactName.LEDGER].filename).read_text(encoding="utf-8")
            campaign_name = campaign.name
            session_date = game_session.session_date.isoformat() if game_session.session_date else None
            game_system = campaign.game_system

        with widelog.wide_event(
            op="generate_summary",
            session_id=str(session_id),
            session_folder=str(session_folder),
            previous_session_id=str(previous_session.id) if previous_session is not None else None,
            has_previous_session=previous_session is not None,
            attendee_count=len(prompt_attendees),
            glossary_entry_count=len(prompt_glossary),
            ledger_chars=len(ledger_text),
        ) as log:
            summary = asyncio.run(
                generate_summary_pipeline.generate_summary(
                    ledger_text,
                    prompt_attendees,
                    prompt_glossary,
                    campaign_name,
                    session_date,
                    game_system,
                    self._settings.llm_model_high,
                )
            )
            introductions_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.PLAYER_INTRODUCTIONS].filename
            recap = (
                generate_summary_pipeline.RECAP_UNAVAILABLE_PLACEHOLDER
                if omit_previous_recap
                else previous_recap_path.read_text(encoding="utf-8")
                if previous_recap_path is not None
                else None
            )
            introductions = player_introductions_pipeline.PlayerIntroductions.load(introductions_path)
            if introductions.session_id != session_id:
                raise generate_summary_pipeline.SummaryCompositionError("Player Introductions belong to a different Session.")
            player_introductions_pipeline.validate_player_introductions(introductions, introduction_attendees)
            composed_summary = generate_summary_pipeline.compose_summary(summary, recap, introductions.to_markdown())
            target = session_folder / paths.ARTIFACTS[paths.ArtifactName.SUMMARY].filename
            inputs_target = session_folder / paths.SUMMARY_INPUTS_FILENAME
            temp_target = target.with_name(f".{target.stem}.tmp{target.suffix}")
            temp_inputs_target = inputs_target.with_name(".summary-inputs.tmp.json")
            summary_replaced = False
            try:
                temp_target.write_text(composed_summary, encoding="utf-8")
                temp_inputs_target.write_text(
                    json.dumps({"previous_session_id": str(previous_session.id) if previous_session is not None else None}) + "\n",
                    encoding="utf-8",
                )
                temp_target.replace(target)
                summary_replaced = True
                temp_inputs_target.replace(inputs_target)
            except Exception:
                temp_target.unlink(missing_ok=True)
                temp_inputs_target.unlink(missing_ok=True)
                if summary_replaced:
                    inputs_target.unlink(missing_ok=True)
                raise
            log.set(
                summary_template_chars=len(summary),
                recap_chars=len(recap) if recap is not None else 0,
                introduction_count=len(introductions.introductions),
                composed_summary_chars=len(composed_summary),
                artifact_path=str(target),
                failed=False,
            )

    def can_transcribe_audio(self, session_id: uuid.UUID) -> tuple[bool, str | None]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcribe_audio.can_transcribe_audio(session, session_id, self._session_folder(session, game_session))

    # Session processing state and transcript-review drafts.

    def save_review_draft(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        """Atomically save noncanonical review work and then record its current source fingerprint.

        The file is written first. If recording metadata fails, the resulting orphan file is
        ignored because no database record points to it; it can never be consumed by generation.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            source = self._review_source(session, game_session)
            source_path = session_folder / paths.ARTIFACTS[source].filename
            source_modified_ns = source_path.stat().st_mtime_ns

        session_processing_pipeline.save_review_draft(session_folder, transcript)

        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            session_processing_entities.set_draft_source(session, session_id, source.value, source_modified_ns)
            session.commit()

    def load_review_draft(self, session_id: uuid.UUID) -> Transcript | None:
        """Return a draft only when its database fingerprint still matches a current source.

        Filesystem artifacts decide whether a draft is valid. Missing or mismatched state is
        repaired by clearing the database pointer; any unreferenced draft file is deliberately
        ignored rather than promoted to a reviewed transcript.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            state = session_processing_entities.get_state(session, session_id)
            if state is None or state.draft_source_artifact is None or state.draft_source_modified_ns is None:
                return None

            try:
                source = paths.ArtifactName(state.draft_source_artifact)
            except ValueError:
                session_processing_entities.clear_draft_source(session, session_id)
                session.commit()
                return None

            session_folder = self._session_folder(session, game_session)
            graph = self._artifact_graph(session, game_session.campaign_id)
            source_ref = artifact_graph_pipeline.ArtifactRef(session_folder, source)
            is_current = graph.status(source_ref) is artifact_graph_pipeline.ArtifactStatus.CURRENT
            source_path = source_ref.path
            fingerprint_matches = source_path.is_file() and source_path.stat().st_mtime_ns == state.draft_source_modified_ns
            if not is_current or not fingerprint_matches:
                session_processing_entities.clear_draft_source(session, session_id)
                session.commit()
                return None

        try:
            draft = session_processing_pipeline.load_review_draft(session_folder)
        except Exception:
            self.discard_review_draft(session_id)
            return None
        if draft is not None:
            return draft

        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            session_processing_entities.clear_draft_source(session, session_id)
            session.commit()
        return None

    def discard_review_draft(self, session_id: uuid.UUID) -> None:
        """Clear the draft pointer before best-effort removal of its working-copy file."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            session_processing_entities.clear_draft_source(session, session_id)
            session.commit()
        session_processing_pipeline.discard_review_draft(session_folder)

    def clear_session_processing_state(self, session_id: uuid.UUID) -> None:
        """Remove a Session's Process-flow metadata and noncanonical transcript draft."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            session_processing_entities.delete_state(session, session_id)
            session.commit()
        session_processing_pipeline.discard_review_draft(session_folder)

    # Manual review.

    def extract_review_clips(self, session_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.extract_review_clips(
                self._session_folder(session, game_session), on_progress, source=self._review_source(session, game_session)
            )

    def discard_review_clips(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            transcript_review.discard_review_clips(self._session_folder(session, game_session))

    def save_reviewed_transcript(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            transcript_review.save_reviewed_transcript(session_folder, transcript)

    def count_adjusted_utterances(self, session_id: uuid.UUID) -> int:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.count_adjusted_utterances(self._session_folder(session, game_session))

    def list_attendance(self, session_id: uuid.UUID) -> list[sessions.Attendee]:
        with Session(self._engine) as session:
            return sessions.list_attendance(session, session_id)

    def add_attendance(self, session_id: uuid.UUID, player_id: uuid.UUID) -> sessions.Attendee:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            result = sessions.add_attendance(session, session_id, player_id)
            sessions.touch_attendance(session, session_id)
            session.commit()
            return result

    def add_attendance_with_roles(self, session_id: uuid.UUID, player_id: uuid.UUID, roles: list[str]) -> sessions.Attendee:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            result = sessions.add_attendance_with_roles(session, session_id, player_id, roles)
            sessions.touch_attendance(session, session_id)
            session.commit()
            return result

    def set_attendance_player(self, session_id: uuid.UUID, attendance_id: uuid.UUID, player_id: uuid.UUID) -> sessions.Attendee:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            result = sessions.set_attendance_player(session, attendance_id, player_id)
            sessions.touch_attendance(session, session_id)
            session.commit()
            return result

    def remove_attendance(self, session_id: uuid.UUID, attendance_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            sessions.remove_attendance(session, attendance_id)
            sessions.touch_attendance(session, session_id)
            session.commit()

    def set_attendance_roles(self, session_id: uuid.UUID, attendance_id: uuid.UUID, roles: list[str]) -> sessions.Attendee:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            result = sessions.set_attendance_roles(session, attendance_id, roles)
            sessions.touch_attendance(session, session_id)
            session.commit()
            return result

    def enhance_players_from_session(
        self, session_id: uuid.UUID, on_progress: players_from_session.OnProgress | None = None
    ) -> players_from_session.EnhanceResult:
        """Players List's "From Session" (S): pull voice clips out of a transcribed session."""
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
                source=self._current_transcript_source(session, game_session),
            )
            session.commit()
            return result
