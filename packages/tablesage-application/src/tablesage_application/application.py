from __future__ import annotations

import asyncio
import hashlib
import json
import math
import shutil
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, date, datetime
from pathlib import Path
from typing import cast

import widelog
import yaml
from pydantic import BaseModel
from sqlmodel import Session
from tablesage_model import setup
from tablesage_model.model import (
    Campaign,
    GlossaryEntry,
    Player,
    SessionBootstrapRun,
    SessionProcessingPhase,
    SessionProcessingState,
)
from tablesage_model.model import Session as GameSession
from tablesage_model.player_names import validate_player_name
from tablesage_model.settings import AppSettings
from tablesage_tools.audio import extract_clip
from tablesage_tools.embeddings import (
    BootstrapCandidate,
    BootstrapSelectionConfig,
    Embedding,
    EmbeddingFactory,
    find_bootstrap_collisions,
    select_bootstrap_candidates,
)
from tablesage_tools.model import Transcript

from . import campaign_recap, opportunities, paths, player_import_from_audio, players_from_session, previously_on
from ._fs import delete_named_entity_folder, named_entity_folder_exists
from .entities import campaigns, glossary, players, sessions
from .entities import session_bootstrap as session_bootstrap_entities
from .entities import session_processing as session_processing_entities
from .llm import PromptName, call_llm_with_prompt, system_prompt_path
from .player_archive import PlayerArchiveResult
from .session_pipeline import artifact_graph as artifact_graph_pipeline
from .session_pipeline import artifacts, import_audio, processing, transcribe_audio, transcript_review
from .session_pipeline import bootstrap_speakers as bootstrap_speakers_pipeline
from .session_pipeline import bootstrap_workflow as bootstrap_workflow_pipeline
from .session_pipeline import clean_transcript as clean_transcript_pipeline
from .session_pipeline import extract_glossary as extract_glossary_pipeline
from .session_pipeline import generate_ledger as generate_ledger_pipeline
from .session_pipeline import generate_player_introductions as player_introductions_pipeline
from .session_pipeline import generate_recap_summary as recap_summary_pipeline
from .session_pipeline import generate_summary as generate_summary_pipeline
from .session_pipeline import isolate_new_speakers as isolate_new_speakers_pipeline
from .session_pipeline import name_corrections as name_corrections_pipeline
from .session_pipeline import review_new_speaker_assignments as review_new_speaker_assignments_pipeline
from .session_pipeline import session_processing as session_processing_pipeline
from .session_pipeline import suggest_spelling_corrections as suggest_spelling_corrections_pipeline
from .session_pipeline import transcript_sections as transcript_sections_pipeline
from .session_pipeline.remove_backchannels import remove_backchannels
from .session_pipeline.scene_breakdown import load_current_scene_breakdown, persist_ledger_pair
from .voice_clips import clips


@contextmanager
def _exclusive_finalization_lock(processing_folder: Path) -> Iterator[None]:
    """Serialize automatic profile publication without leaving a stale DB lock on a crash."""
    # A filesystem advisory lock is deliberately used instead of the persisted workflow
    # operation field: the OS releases it when a worker exits unexpectedly, which lets a
    # prepared contribution recover on the next Generate attempt.
    import fcntl

    processing_folder.mkdir(parents=True, exist_ok=True)
    lock_path = processing_folder / ".bootstrap-finalization.lock"
    with lock_path.open("a+b") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Bootstrap profile finalization is already running for this session.") from exc
        try:
            yield
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


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
                        paths.ArtifactName.SPEAKER_ENHANCED_TRANSCRIPT,
                        (ref(paths.ArtifactName.SPEAKER_ENHANCED_TRANSCRIPT),),
                        (ref(paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS),),
                    ),
                    artifact_graph_pipeline.BuildStep(
                        paths.ArtifactName.SPELLCHECKED_TRANSCRIPT,
                        (ref(paths.ArtifactName.SPELLCHECKED_TRANSCRIPT),),
                        (ref(paths.ArtifactName.SPEAKER_ENHANCED_TRANSCRIPT),),
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
            previous_session_id = self._summary_previous_session_id(folder)
            previous_session = sessions_by_id.get(previous_session_id) if previous_session_id is not None else None
            if previous_session is not None:
                previous_folder = self._session_folder(session, previous_session)
                summary_dependencies.append(artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.RECAP_SUMMARY))
            steps.append(
                artifact_graph_pipeline.BuildStep(
                    paths.ArtifactName.SUMMARY,
                    (ref(paths.ArtifactName.SUMMARY),),
                    tuple(summary_dependencies),
                )
            )
            if (folder / paths.LEDGER_PAIR_MARKER).exists():
                interrupted.update((ref(paths.ArtifactName.LEDGER), ref(paths.ArtifactName.SCENE_BREAKDOWN)))

        return artifact_graph_pipeline.ArtifactGraph(tuple(steps), interrupted=frozenset(interrupted))

    def session_artifact_states(self, session_id: uuid.UUID) -> dict[paths.ArtifactName, artifact_graph_pipeline.ArtifactStatus]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            graph = self._artifact_graph(session, game_session.campaign_id)
            return graph.session_statuses(self._session_folder(session, game_session))

    def _current_transcript_source(self, session: Session, game_session: GameSession) -> paths.ArtifactName:
        graph = self._artifact_graph(session, game_session.campaign_id)
        folder = self._session_folder(session, game_session)
        for name in (paths.ArtifactName.REVIEWED_TRANSCRIPT, paths.ArtifactName.TRANSCRIPT):
            if graph.status(artifact_graph_pipeline.ArtifactRef(folder, name)) is artifact_graph_pipeline.ArtifactStatus.CURRENT:
                return name
        raise ValueError("No current transcript is available. Transcribe the session again before continuing.")

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
        self.finalize_bootstrap_profiles(session_id)
        return plan

    def finalize_bootstrap_profiles(self, session_id: uuid.UUID) -> int:
        """Add reviewed-session clips for only the immutable bootstrap targets.

        This dispatcher is intentionally invoked after every successful output run, including
        an empty plan. Terminal receipts make the operation one-time; the player-screen
        enhancement operation remains the only path that can deliberately replace clips.
        """
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            return 0
        states = self.session_artifact_states(session_id)
        if states[paths.ArtifactName.REVIEWED_TRANSCRIPT] is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
            raise RuntimeError("Complete canonical transcript review before finalizing bootstrap profiles.")
        if any(states[name] is not artifact_graph_pipeline.ArtifactStatus.CURRENT for name in artifact_graph_pipeline.GENERATION_ORDER):
            raise RuntimeError("Generate all current output artifacts before finalizing bootstrap profiles.")
        target_ids = tuple(uuid.UUID(value) for value in json.loads(run.targets_json))
        if not target_ids:
            return 0
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = campaigns.get_campaign(session, game_session.campaign_id)
            session_folder = self._session_folder(session, game_session)
            reviewed_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.REVIEWED_TRANSCRIPT].filename
            reviewed_sha256 = hashlib.sha256(reviewed_path.read_bytes()).hexdigest()
            transcript = Transcript.load(reviewed_path)
            input_audio = session_folder / paths.ARTIFACTS[paths.ArtifactName.INPUT_AUDIO].filename
            committed = 0
            with _exclusive_finalization_lock(bootstrap_workflow_pipeline.processing_folder(session_folder)):
                for player_id in target_ids:
                    contribution = session_bootstrap_entities.get_or_create_contribution(
                        session, session_id=session_id, player_id=player_id, run_id=run.id
                    )
                    if contribution.state in {"committed", "no_usable_clips", "skipped_existing_profile"}:
                        continue
                    player = players.get_player(session, player_id)
                    if contribution.state != "prepared" and player.sample_count > 0:
                        session_bootstrap_entities.update_contribution(
                            session,
                            contribution,
                            state="skipped_existing_profile",
                            clip_count=0,
                            reviewed_transcript_sha256=reviewed_sha256,
                        )
                        continue
                    utterances = players_from_session.select_assigned_utterances(
                        transcript.utterances, player.name, self._settings.enhance_voices.min_embeddable_clip_seconds
                    )
                    if not utterances:
                        session_bootstrap_entities.update_contribution(
                            session,
                            contribution,
                            state="no_usable_clips",
                            clip_count=0,
                            reviewed_transcript_sha256=reviewed_sha256,
                        )
                        continue
                    player_folder = paths.player_folder(self._cwd, player.name)
                    player_folder.mkdir(parents=True, exist_ok=True)
                    session_hash = clips.hash8(str(session_id))
                    try:
                        stage_folder = bootstrap_workflow_pipeline.processing_folder(session_folder) / "finalization" / str(contribution.id)
                        manifest_path = stage_folder / "manifest.json"
                        if contribution.state == "prepared" and manifest_path.is_file():
                            manifest_data = manifest_path.read_bytes()
                            if contribution.staged_manifest_sha256 != hashlib.sha256(manifest_data).hexdigest():
                                raise RuntimeError("Prepared manifest digest does not match its receipt.")
                            manifest = json.loads(manifest_data)
                            if manifest.get("reviewed_sha256") != reviewed_sha256:
                                raise RuntimeError("Prepared clips belong to an earlier reviewed transcript.")
                        else:
                            stage_folder.mkdir(parents=True, exist_ok=True)
                            entries: list[dict[str, str]] = []
                            for utterance in utterances:
                                clip_identity = uuid.uuid5(
                                    uuid.NAMESPACE_URL, f"{session_id}:{player_id}:{utterance.start:.6f}:{utterance.end:.6f}"
                                ).hex
                                filename = (
                                    f"session-{clips.slugify(player.name)}-{clips.slugify(campaign.name)}-"
                                    f"{clips.slugify(game_session.name)}-{session_hash}-{clip_identity}.wav"
                                )
                                staged = stage_folder / filename
                                if not staged.is_file():
                                    asyncio.run(extract_clip(input_audio, staged, utterance.start, utterance.end))
                                entries.append({"filename": filename, "sha256": hashlib.sha256(staged.read_bytes()).hexdigest()})
                            manifest = {"reviewed_sha256": reviewed_sha256, "entries": entries}
                            manifest_data = json.dumps(manifest, sort_keys=True).encode("utf-8")
                            bootstrap_workflow_pipeline.atomic_write(manifest_path, manifest_data)
                            session_bootstrap_entities.update_contribution(
                                session,
                                contribution,
                                state="prepared",
                                clip_count=len(entries),
                                reviewed_transcript_sha256=reviewed_sha256,
                            )
                            contribution.staged_manifest_sha256 = hashlib.sha256(manifest_data).hexdigest()
                            session.add(contribution)
                            session.commit()
                        raw_entries = manifest.get("entries")
                        if not isinstance(raw_entries, list) or not raw_entries:
                            raise RuntimeError("Prepared manifest has no clip entries.")
                        entries = cast(list[dict[str, str]], raw_entries)
                        for entry in entries:
                            filename, digest = entry.get("filename"), entry.get("sha256")
                            if not isinstance(filename, str) or Path(filename).name != filename or not isinstance(digest, str):
                                raise RuntimeError("Prepared manifest contains an invalid clip entry.")
                            staged = stage_folder / filename
                            target = player_folder / filename
                            existing = target if target.is_file() else staged
                            if not existing.is_file() or hashlib.sha256(existing.read_bytes()).hexdigest() != digest:
                                raise RuntimeError(f"Prepared clip disagrees with manifest: {filename}")
                            if not target.is_file():
                                staged.replace(target)
                        clips.recompute_centroid(
                            session,
                            player_id,
                            player_folder,
                            self._embed_clip,
                            None,
                            self._settings.remove_outliers.min_sample_similarity,
                            self._settings.remove_outliers.min_samples,
                        )
                    except Exception as exc:
                        session_bootstrap_entities.update_contribution(
                            session,
                            contribution,
                            state="prepared",
                            clip_count=0,
                            reviewed_transcript_sha256=reviewed_sha256,
                            failure_message=str(exc),
                        )
                        session.commit()
                        raise RuntimeError(f"Could not finalize {player.name}'s bootstrap profile: {exc}") from exc
                    session_bootstrap_entities.update_contribution(
                        session,
                        contribution,
                        state="committed",
                        clip_count=len(entries),
                        reviewed_transcript_sha256=reviewed_sha256,
                    )
                    shutil.rmtree(stage_folder, ignore_errors=True)
                    committed += 1
                session.commit()
            return committed

    def bootstrap_finalization_pending(self, session_id: uuid.UUID) -> bool:
        """Whether Generate must remain actionable despite an empty artifact plan."""
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            return False
        targets = tuple(uuid.UUID(value) for value in json.loads(run.targets_json))
        with Session(self._engine) as session:
            for player_id in targets:
                contribution = session_bootstrap_entities.get_contribution(session, session_id, player_id)
                if contribution is None or contribution.state in {"pending", "prepared", "failed"}:
                    return True
        return False

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

        Legacy profiles do not identify their embedding backend, so the caller can provide an
        expected dimension when it is known. Valid legacy entries are marked as such in a
        bootstrap snapshot rather than being rewritten during a read-only eligibility check.
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

    def bootstrap_eligibility(
        self, session_id: uuid.UUID, *, expected_embedding_dimension: int | None = None
    ) -> bootstrap_workflow_pipeline.BootstrapEligibility:
        """Snapshot which attendees require bootstrapping without mutating profiles or state."""
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            attendees: list[bootstrap_workflow_pipeline.BootstrapAttendeeSnapshot] = []
            targets: list[uuid.UUID] = []
            references: list[bootstrap_workflow_pipeline.BootstrapReferenceSnapshot] = []
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                assert player is not None
                embedding = self._usable_player_embedding(player, expected_embedding_dimension)
                usable = embedding is not None
                attendees.append(
                    bootstrap_workflow_pipeline.BootstrapAttendeeSnapshot(
                        player_id=attendee.player_id,
                        player_name=attendee.player_name,
                        roles=attendee.roles,
                        usable_centroid=usable,
                    )
                )
                if usable:
                    assert embedding is not None
                    references.append(
                        bootstrap_workflow_pipeline.BootstrapReferenceSnapshot(
                            player_id=attendee.player_id,
                            player_name=attendee.player_name,
                            embedding=embedding.root,
                            embedding_dimension=len(embedding),
                            provenance="legacy",
                        )
                    )
                else:
                    targets.append(attendee.player_id)
            return bootstrap_workflow_pipeline.BootstrapEligibility(
                attendees=tuple(attendees), targets=tuple(targets), references=tuple(references)
            )

    def create_bootstrap_run(
        self,
        session_id: uuid.UUID,
        *,
        source_sha256: str,
        settings_fingerprint: str,
        prompt_fingerprint: str,
        embedding_model_id: str,
        expected_embedding_dimension: int | None = None,
    ) -> SessionBootstrapRun:
        """Create a durable bootstrap snapshot and its empty atomic workflow manifest.

        Callers supply fingerprints produced by the concrete transcription/prompt settings in
        later phases. This operation intentionally does not transcribe, identify, or alter any
        durable player profile.
        """
        eligibility = self.bootstrap_eligibility(session_id, expected_embedding_dimension=expected_embedding_dimension)
        attendees_json = self._fingerprint_payload(eligibility.attendees)
        references_json = self._fingerprint_payload(eligibility.references)
        targets_json = self._fingerprint_payload(eligibility.targets)
        attendee_fingerprint = hashlib.sha256(attendees_json.encode("utf-8")).hexdigest()
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            run = session_bootstrap_entities.create_run(
                session,
                session_id=session_id,
                source_sha256=source_sha256,
                attendee_fingerprint=attendee_fingerprint,
                settings_fingerprint=settings_fingerprint,
                prompt_fingerprint=prompt_fingerprint,
                embedding_model_id=embedding_model_id,
                targets_json=targets_json,
                attendees_json=attendees_json,
                references_json=references_json,
            )
            manifest = bootstrap_workflow_pipeline.BootstrapWorkflowManifest(run_id=run.id, source_sha256=source_sha256)
            manifest_sha256 = bootstrap_workflow_pipeline.write_manifest(self._session_folder(session, game_session), manifest)
            session_bootstrap_entities.publish_manifest(session, run, manifest_sha256, manifest.revision)
            session.commit()
            session.refresh(run)
            return run

    @staticmethod
    def _fingerprint_payload(payload: object) -> str:
        def normalize(value: object) -> object:
            if isinstance(value, BaseModel):
                return normalize(value.model_dump(mode="json"))
            if isinstance(value, dict):
                return {str(key): normalize(item) for key, item in value.items()}
            if isinstance(value, (list, tuple)):
                return [normalize(item) for item in value]
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

        return json.dumps(normalize(payload), sort_keys=True, separators=(",", ":"))

    def latest_bootstrap_run(self, session_id: uuid.UUID) -> SessionBootstrapRun | None:
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            return session_bootstrap_entities.latest_run(session, session_id)

    def bootstrap_run_matches_source(self, run_id: uuid.UUID, source_sha256: str) -> bool:
        """Check a persisted run before reusing any of its working documents."""
        with Session(self._engine) as session:
            run = session_bootstrap_entities.get_run(session, run_id)
            if run is None or run.source_sha256 != source_sha256:
                return False
            game_session = sessions.get_session(session, run.session_id)
            manifest = bootstrap_workflow_pipeline.load_manifest(self._session_folder(session, game_session))
            return bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, source_sha256)

    def begin_bootstrap_operation(self, run_id: uuid.UUID, operation: str) -> SessionBootstrapRun:
        """Acquire the persisted per-run guard used by later long-running bootstrap stages."""
        with Session(self._engine) as session:
            run = session_bootstrap_entities.get_run(session, run_id)
            if run is None:
                raise ValueError("Bootstrap run not found.")
            result = session_bootstrap_entities.begin_operation(session, run, operation)
            session.commit()
            session.refresh(result)
            return result

    def finish_bootstrap_operation(self, run_id: uuid.UUID, failure_message: str | None = None) -> SessionBootstrapRun:
        """Release a persisted per-run guard, optionally retaining a retryable failure message."""
        with Session(self._engine) as session:
            run = session_bootstrap_entities.get_run(session, run_id)
            if run is None:
                raise ValueError("Bootstrap run not found.")
            result = session_bootstrap_entities.finish_operation(session, run, failure_message)
            session.commit()
            session.refresh(result)
            return result

    def prepare_session_bootstrap(
        self, session_id: uuid.UUID, *, on_progress: transcribe_audio.OnProgress | None = None
    ) -> bootstrap_speakers_pipeline.BootstrapPreparationResult:
        """Persist raw diarization and cited identity evidence for bootstrap targets.

        This deliberately stops before canonical transcript publication. Phase 4's Process
        overview will route to candidate review after this operation; the existing Audio screen
        continues using `transcribe_session_audio` until then.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            enabled, reason = transcribe_audio.can_transcribe_audio(session, session_id, session_folder)
            if not enabled:
                raise RuntimeError(reason or "Cannot prepare session audio.")
            source_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.INPUT_AUDIO].filename
            source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()

        eligibility = self.bootstrap_eligibility(session_id)
        if not eligibility.targets:
            raw_transcript = transcribe_audio.transcribe_and_diarize_audio(
                session_folder, len(eligibility.attendees), self._settings.transcription_and_diarization, on_progress
            )
            return bootstrap_speakers_pipeline.BootstrapPreparationResult(
                run_id=None, raw_transcript=raw_transcript, evidence=bootstrap_speakers_pipeline.BootstrapEvidence(claims=())
            )

        run = self.latest_bootstrap_run(session_id)
        raw_document: bootstrap_speakers_pipeline.DiarizedBootstrapTranscript | None = None
        if run is not None and self.bootstrap_run_matches_source(run.id, source_sha256):
            raw_document = self._load_bootstrap_diarized_document(session_id, run)
        if raw_document is None:
            run = self.create_bootstrap_run(
                session_id,
                source_sha256=source_sha256,
                settings_fingerprint=self._fingerprint_payload(
                    {
                        "transcription_and_diarization": self._settings.transcription_and_diarization,
                        "speaker_bootstrap": self._settings.speaker_bootstrap,
                        "llm_model_lite": self._settings.llm_model_lite,
                    }
                ),
                prompt_fingerprint=self._prompt_sha256(PromptName.PROPOSE_BOOTSTRAP_EVIDENCE),
                embedding_model_id="legacy-unknown",
            )
            self.begin_bootstrap_operation(run.id, "preparing")
            try:
                raw_transcript = transcribe_audio.transcribe_and_diarize_audio(
                    session_folder, len(eligibility.attendees), self._settings.transcription_and_diarization, on_progress
                )
                raw_document = bootstrap_speakers_pipeline.DiarizedBootstrapTranscript(
                    run_id=run.id,
                    transcript=raw_transcript,
                    utterance_ids=tuple(
                        bootstrap_workflow_pipeline.SourceUtteranceId(run_id=run.id, original_index=index)
                        for index in range(len(raw_transcript.utterances))
                    ),
                )
                self._publish_bootstrap_document(session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.DIARIZED, raw_document)
            except Exception as exc:
                self.finish_bootstrap_operation(run.id, str(exc))
                raise
            self.finish_bootstrap_operation(run.id)

        assert run is not None
        assert raw_document is not None
        self.begin_bootstrap_operation(run.id, "preparing")
        try:
            targets = tuple(attendee for attendee in eligibility.attendees if attendee.player_id in eligibility.targets)
            evidence = asyncio.run(
                bootstrap_speakers_pipeline.propose_bootstrap_evidence(
                    raw_document, targets, self._settings.speaker_bootstrap, self._settings.llm_model_lite
                )
            )
            self._publish_bootstrap_document(session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.EVIDENCE, evidence)
        except Exception as exc:
            self.finish_bootstrap_operation(run.id, str(exc))
            raise
        self.finish_bootstrap_operation(run.id)
        self.set_session_processing_phase(session_id, SessionProcessingPhase.BOOTSTRAP_REVIEW)
        return bootstrap_speakers_pipeline.BootstrapPreparationResult(
            run_id=run.id, raw_transcript=raw_document.transcript, evidence=evidence
        )

    def _load_bootstrap_diarized_document(
        self, session_id: uuid.UUID, run: SessionBootstrapRun
    ) -> bootstrap_speakers_pipeline.DiarizedBootstrapTranscript | None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
        manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
        if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
            return None
        assert manifest is not None
        if (
            bootstrap_workflow_pipeline.document_status(manifest, bootstrap_workflow_pipeline.BootstrapDocumentName.DIARIZED)
            is not bootstrap_workflow_pipeline.BootstrapDocumentStatus.COMPLETE
        ):
            return None
        try:
            path = bootstrap_workflow_pipeline.document_path(session_folder, bootstrap_workflow_pipeline.BootstrapDocumentName.DIARIZED)
            return bootstrap_speakers_pipeline.DiarizedBootstrapTranscript.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def select_bootstrap_seed_clips(self, session_id: uuid.UUID) -> bootstrap_speakers_pipeline.BootstrapSelectionResult:
        """Create deterministic provisional centroids from persisted, cited raw utterances.

        This is deliberately separate from review approval: it produces an auditable proposed
        seed set for the Phase 4 candidate-review screen and never touches durable profiles.
        """
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            return bootstrap_speakers_pipeline.BootstrapSelectionResult(selections=(), collision_player_pairs=())
        raw = self._load_bootstrap_diarized_document(session_id, run)
        evidence = self._load_bootstrap_evidence_document(session_id, run)
        if raw is None or evidence is None:
            raise RuntimeError("Bootstrap diarization and evidence must be prepared before selecting seed clips.")
        review = self._load_bootstrap_candidate_review_document(session_id, run)
        if review is not None:
            evidence = review.evidence
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
        claims_by_player: dict[uuid.UUID, list[bootstrap_speakers_pipeline.BootstrapEvidenceClaim]] = {}
        for claim in evidence.claims:
            claims_by_player.setdefault(claim.player_id, []).append(claim)
        source_index = {source.value: source.original_index for source in raw.utterance_ids}
        candidates: list[tuple[BootstrapCandidate, bootstrap_workflow_pipeline.SourceUtteranceId]] = []
        for player_id, claims in claims_by_player.items():
            for claim in claims:
                exchange_id = ":".join(sorted(source.value for source in claim.evidence_utterance_ids))
                for source in claim.candidate_utterance_ids:
                    index = source_index[source.value]
                    utterance = raw.transcript.utterances[index]
                    duration = bootstrap_speakers_pipeline.speech_duration(utterance)
                    if duration < self._settings.speaker_bootstrap.min_speech_seconds:
                        continue
                    if bootstrap_speakers_pipeline.has_cross_speaker_overlap(raw.transcript, index):
                        continue
                    candidates.append((BootstrapCandidate(source.value, str(player_id), exchange_id, duration, Embedding(root=())), source))

        embedded = self._embed_bootstrap_candidates(session_folder, run, raw, candidates)
        references = {
            str(reference.player_id): Embedding(root=reference.embedding)
            for reference in bootstrap_workflow_pipeline.BootstrapEligibility.model_validate(
                {
                    "attendees": json.loads(run.attendees_json),
                    "targets": json.loads(run.targets_json),
                    "references": json.loads(run.references_json),
                }
            ).references
        }
        config = BootstrapSelectionConfig(
            min_clips=self._settings.speaker_bootstrap.min_clips,
            min_independent_exchanges=self._settings.speaker_bootstrap.min_independent_exchanges,
            min_total_speech_seconds=self._settings.speaker_bootstrap.min_total_speech_seconds,
            max_clips_per_exchange=self._settings.speaker_bootstrap.max_clips_per_exchange,
            pairwise_similarity_threshold=self._settings.speaker_bootstrap.pairwise_similarity_threshold,
            leave_one_out_similarity_threshold=self._settings.speaker_bootstrap.leave_one_out_similarity_threshold,
            competitor_margin=self._settings.speaker_bootstrap.competitor_margin,
        )
        selections = [select_bootstrap_candidates(str(player_id), embedded, references, config) for player_id in claims_by_player]
        collisions = find_bootstrap_collisions(selections, self._settings.speaker_bootstrap.collision_similarity_threshold)
        collided = {player_id for pair in collisions for player_id in pair}
        persisted = bootstrap_speakers_pipeline.BootstrapSelectionResult(
            selections=tuple(
                bootstrap_speakers_pipeline.BootstrapSeedSelection(
                    player_id=uuid.UUID(selection.player_id),
                    selected_utterance_ids=(
                        tuple(
                            source
                            for candidate, source in candidates
                            if candidate.player_id == selection.player_id and candidate.clip_id in selection.selected_clip_ids
                        )
                        if selection.player_id not in collided
                        else ()
                    ),
                    centroid=selection.centroid.root if selection.centroid is not None and selection.player_id not in collided else None,
                    diagnostics=tuple(
                        bootstrap_speakers_pipeline.BootstrapSeedDiagnostic(
                            utterance_id=next(
                                source
                                for candidate, source in candidates
                                if candidate.player_id == selection.player_id and candidate.clip_id == diagnostic.clip_id
                            ),
                            accepted=diagnostic.accepted and selection.player_id not in collided,
                            reason="provisional_profile_collision" if selection.player_id in collided else diagnostic.reason,
                            leave_one_out_similarity=diagnostic.leave_one_out_similarity,
                            competitor_similarity=diagnostic.competitor_similarity,
                            competitor_margin=diagnostic.competitor_margin,
                        )
                        for diagnostic in selection.diagnostics
                    ),
                    reason="provisional_profile_collision" if selection.player_id in collided else selection.reason,
                    independent_exchange_count=selection.independent_exchange_count,
                    total_speech_seconds=selection.total_speech_seconds,
                )
                for selection in selections
            ),
            collision_player_pairs=tuple((uuid.UUID(left), uuid.UUID(right)) for left, right in collisions),
        )
        self._publish_bootstrap_document(session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.SELECTION, persisted)
        return persisted

    def _load_bootstrap_evidence_document(
        self, session_id: uuid.UUID, run: SessionBootstrapRun
    ) -> bootstrap_speakers_pipeline.BootstrapEvidence | None:
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
        if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
            return None
        assert manifest is not None
        if (
            bootstrap_workflow_pipeline.document_status(manifest, bootstrap_workflow_pipeline.BootstrapDocumentName.EVIDENCE)
            is not bootstrap_workflow_pipeline.BootstrapDocumentStatus.COMPLETE
        ):
            return None
        try:
            evidence_path = bootstrap_workflow_pipeline.document_path(
                session_folder, bootstrap_workflow_pipeline.BootstrapDocumentName.EVIDENCE
            )
            return bootstrap_speakers_pipeline.BootstrapEvidence.model_validate_json(evidence_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _load_bootstrap_candidate_review_document(
        self, session_id: uuid.UUID, run: SessionBootstrapRun
    ) -> bootstrap_speakers_pipeline.BootstrapCandidateReview | None:
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
        if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
            return None
        assert manifest is not None
        if (
            bootstrap_workflow_pipeline.document_status(manifest, bootstrap_workflow_pipeline.BootstrapDocumentName.REVIEW)
            is not bootstrap_workflow_pipeline.BootstrapDocumentStatus.COMPLETE
        ):
            return None
        try:
            review_path = bootstrap_workflow_pipeline.document_path(
                session_folder, bootstrap_workflow_pipeline.BootstrapDocumentName.REVIEW
            )
            return bootstrap_speakers_pipeline.BootstrapCandidateReview.model_validate_json(review_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def identify_bootstrap_speakers(self, session_id: uuid.UUID) -> Transcript:
        """Identify from frozen established/provisional centroids, retaining abstentions."""
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            raise RuntimeError("Bootstrap preparation has not started for this session.")
        raw = self._load_bootstrap_diarized_document(session_id, run)
        selection = self._load_bootstrap_selection_document(session_id, run)
        if raw is None or selection is None:
            raise RuntimeError("Bootstrap seed selection must complete before speaker identification.")
        attendees = tuple(
            bootstrap_workflow_pipeline.BootstrapAttendeeSnapshot.model_validate(item) for item in json.loads(run.attendees_json)
        )
        names = {attendee.player_id: attendee.player_name for attendee in attendees}
        references = tuple(
            bootstrap_workflow_pipeline.BootstrapReferenceSnapshot.model_validate(item) for item in json.loads(run.references_json)
        )
        centroids = {reference.player_name: Embedding(root=reference.embedding) for reference in references}
        for seed in selection.selections:
            if seed.centroid is not None:
                centroids[names[seed.player_id]] = Embedding(root=seed.centroid)
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        identified = transcribe_audio.identify_raw_transcript(
            session_folder,
            raw.transcript,
            centroids,
            self.embedding_factory(),
            self._settings.speaker_identification,
            absolute_similarity_threshold=self._settings.speaker_bootstrap.incomplete_reference_absolute_similarity_threshold,
            force_abstention=True,
        )
        identified_document = bootstrap_speakers_pipeline.DiarizedBootstrapTranscript(
            run_id=run.id, transcript=identified, utterance_ids=raw.utterance_ids
        )
        self._publish_bootstrap_document(
            session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.IDENTIFICATION, identified_document
        )
        self.set_session_processing_phase(session_id, SessionProcessingPhase.NEW_SPEAKER_REVIEW)
        return identified

    def _load_bootstrap_selection_document(
        self, session_id: uuid.UUID, run: SessionBootstrapRun
    ) -> bootstrap_speakers_pipeline.BootstrapSelectionResult | None:
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
        if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
            return None
        assert manifest is not None
        if (
            bootstrap_workflow_pipeline.document_status(manifest, bootstrap_workflow_pipeline.BootstrapDocumentName.SELECTION)
            is not bootstrap_workflow_pipeline.BootstrapDocumentStatus.COMPLETE
        ):
            return None
        try:
            selection_path = bootstrap_workflow_pipeline.document_path(
                session_folder, bootstrap_workflow_pipeline.BootstrapDocumentName.SELECTION
            )
            return bootstrap_speakers_pipeline.BootstrapSelectionResult.model_validate_json(selection_path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _embed_bootstrap_candidates(
        self,
        session_folder: Path,
        run: SessionBootstrapRun,
        raw: bootstrap_speakers_pipeline.DiarizedBootstrapTranscript,
        candidates: Sequence[tuple[BootstrapCandidate, bootstrap_workflow_pipeline.SourceUtteranceId]],
    ) -> list[BootstrapCandidate]:
        """Extract cited spans once per stable ID and cache their embedding in a run-local file."""
        clip_folder = bootstrap_workflow_pipeline.processing_folder(session_folder) / "bootstrap-clips"
        clip_folder.mkdir(parents=True, exist_ok=True)
        audio_path = session_folder / paths.ARTIFACTS[paths.ArtifactName.INPUT_AUDIO].filename
        source_index = {source.value: source.original_index for source in raw.utterance_ids}
        cache_path = bootstrap_workflow_pipeline.processing_folder(session_folder) / "bootstrap-embedding-cache.json"
        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
        except (json.JSONDecodeError, OSError):
            cache = {}
        if not isinstance(cache, dict):
            cache = {}

        def cache_key(candidate: BootstrapCandidate) -> str:
            return f"{run.source_sha256}:{run.embedding_model_id}:{candidate.clip_id}"

        async def embed_one(candidate: BootstrapCandidate) -> BootstrapCandidate:
            cached = cache.get(cache_key(candidate))
            if isinstance(cached, list) and all(isinstance(value, (int, float)) for value in cached):
                return BootstrapCandidate(
                    candidate.clip_id,
                    candidate.player_id,
                    candidate.exchange_id,
                    candidate.speech_seconds,
                    Embedding(root=tuple(float(value) for value in cached)),
                )
            index = source_index[candidate.clip_id]
            utterance = raw.transcript.utterances[index]
            clip_path = clip_folder / f"{hashlib.sha256(candidate.clip_id.encode()).hexdigest()}.wav"
            if not clip_path.is_file():
                await extract_clip(audio_path, clip_path, utterance.start, utterance.end)
            embedding = await asyncio.to_thread(self._embed_clip, clip_path)
            cache[cache_key(candidate)] = list(embedding.root)
            return BootstrapCandidate(candidate.clip_id, candidate.player_id, candidate.exchange_id, candidate.speech_seconds, embedding)

        async def run_all() -> list[BootstrapCandidate]:
            semaphore = asyncio.Semaphore(self._settings.speaker_bootstrap.embedding_concurrency)

            async def limited(candidate: BootstrapCandidate) -> BootstrapCandidate:
                async with semaphore:
                    return await embed_one(candidate)

            return list(await asyncio.gather(*(limited(candidate) for candidate, _source in candidates)))

        result = asyncio.run(run_all())
        cache_path.write_text(json.dumps(cache, sort_keys=True, separators=(",", ":")), encoding="utf-8")
        return result

    def _publish_bootstrap_document(
        self,
        session_id: uuid.UUID,
        run: SessionBootstrapRun,
        name: bootstrap_workflow_pipeline.BootstrapDocumentName,
        payload: BaseModel,
    ) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            persisted_run = session_bootstrap_entities.get_run(session, run.id)
            if persisted_run is None:
                raise ValueError("Bootstrap run not found.")
            manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
            if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
                raise RuntimeError("Bootstrap workflow manifest does not match the current run.")
            assert manifest is not None
            record = bootstrap_workflow_pipeline.write_document(session_folder, name, payload)
            updated_manifest = bootstrap_workflow_pipeline.record_document(manifest, name, record)
            manifest_sha256 = bootstrap_workflow_pipeline.write_manifest(session_folder, updated_manifest)
            session_bootstrap_entities.publish_manifest(session, persisted_run, manifest_sha256, updated_manifest.revision)
            session.commit()

    @staticmethod
    def _prompt_sha256(prompt: PromptName) -> str:
        return hashlib.sha256(system_prompt_path(prompt).read_bytes()).hexdigest()

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
            self._settings.speaker_bootstrap.min_total_speech_seconds,
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

    def bootstrap_candidate_review_data(
        self, session_id: uuid.UUID
    ) -> tuple[bootstrap_speakers_pipeline.BootstrapEvidence, tuple[bootstrap_workflow_pipeline.BootstrapAttendeeSnapshot, ...]]:
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            raise RuntimeError("Bootstrap preparation has not started for this session.")
        evidence = self._load_bootstrap_evidence_document(session_id, run)
        if evidence is None:
            raise RuntimeError("Bootstrap evidence is not available.")
        attendees = tuple(
            bootstrap_workflow_pipeline.BootstrapAttendeeSnapshot.model_validate(item) for item in json.loads(run.attendees_json)
        )
        return evidence, tuple(attendee for attendee in attendees if attendee.player_id in set(json.loads(run.targets_json)))

    def complete_bootstrap_candidate_review(
        self, session_id: uuid.UUID, approved_claims: Sequence[bootstrap_speakers_pipeline.BootstrapEvidenceClaim]
    ) -> None:
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            raise RuntimeError("Bootstrap preparation has not started for this session.")
        review = bootstrap_speakers_pipeline.BootstrapCandidateReview(
            evidence=bootstrap_speakers_pipeline.BootstrapEvidence(claims=tuple(approved_claims))
        )
        self._publish_bootstrap_document(session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.REVIEW, review)
        self.select_bootstrap_seed_clips(session_id)
        self.identify_bootstrap_speakers(session_id)

    def bootstrap_identification_data(self, session_id: uuid.UUID) -> bootstrap_speakers_pipeline.DiarizedBootstrapTranscript:
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            raise RuntimeError("Bootstrap preparation has not started for this session.")
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        manifest = bootstrap_workflow_pipeline.load_manifest(session_folder)
        if not bootstrap_workflow_pipeline.manifest_matches(manifest, run.id, run.source_sha256):
            raise RuntimeError("Bootstrap identification is not current.")
        assert manifest is not None
        if (
            bootstrap_workflow_pipeline.document_status(manifest, bootstrap_workflow_pipeline.BootstrapDocumentName.IDENTIFICATION)
            is not bootstrap_workflow_pipeline.BootstrapDocumentStatus.COMPLETE
        ):
            raise RuntimeError("Identify all speakers before focused review.")
        path = bootstrap_workflow_pipeline.document_path(session_folder, bootstrap_workflow_pipeline.BootstrapDocumentName.IDENTIFICATION)
        return bootstrap_speakers_pipeline.DiarizedBootstrapTranscript.model_validate_json(path.read_text(encoding="utf-8"))

    def complete_new_speaker_review(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        """Persist focused unassignments, then expose the result to spelling/manual review."""
        run = self.latest_bootstrap_run(session_id)
        if run is None:
            raise RuntimeError("Bootstrap preparation has not started for this session.")
        identified = self.bootstrap_identification_data(session_id)
        reviewed = bootstrap_speakers_pipeline.DiarizedBootstrapTranscript(
            run_id=run.id, transcript=transcript, utterance_ids=identified.utterance_ids
        )
        self._publish_bootstrap_document(session_id, run, bootstrap_workflow_pipeline.BootstrapDocumentName.NEW_SPEAKER_REVIEW, reviewed)
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        transcript.save(session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT].filename)
        (session_folder / paths.ARTIFACTS[paths.ArtifactName.TRANSCRIPT_TEXT].filename).write_text(
            transcribe_audio._render_transcript_text(transcript), encoding="utf-8"
        )
        self.begin_spelling_review(session_id, transcript)

    def bootstrap_utterance_clip(self, session_id: uuid.UUID, source_id: bootstrap_workflow_pipeline.SourceUtteranceId) -> Path:
        """Return a disposable cached clip for bootstrap-review playback."""
        run = self.latest_bootstrap_run(session_id)
        if run is None or source_id.run_id != run.id:
            raise RuntimeError("Bootstrap utterance does not belong to this session.")
        raw = self._load_bootstrap_diarized_document(session_id, run)
        if raw is None or source_id.original_index >= len(raw.transcript.utterances):
            raise RuntimeError("Bootstrap utterance is unavailable.")
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        utterance = raw.transcript.utterances[source_id.original_index]
        clip_path = bootstrap_workflow_pipeline.processing_folder(session_folder) / "review-clips" / f"{source_id.original_index:04d}.wav"
        if not clip_path.is_file():
            asyncio.run(
                extract_clip(
                    session_folder / paths.ARTIFACTS[paths.ArtifactName.INPUT_AUDIO].filename,
                    clip_path,
                    utterance.start,
                    utterance.end,
                )
            )
        return clip_path

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
        # Workflow intermediates are disposable. Terminal contribution receipts live in the
        # database and deliberately survive Clean Session, so this cannot recreate clips later.
        shutil.rmtree(bootstrap_workflow_pipeline.processing_folder(session_folder), ignore_errors=True)

    def clean_transcript(
        self,
        session_id: uuid.UUID,
        on_progress: Callable[[clean_transcript_pipeline.Stage, int, int], None] | None = None,
    ) -> clean_transcript_pipeline.CleanTranscriptResult:
        """Remove backchannels from and assign roles to a session's preferred transcript, writing `role_transcript.json`."""
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
            previous_recap_is_current = previous_folder is None or (
                self._artifact_graph(session, game_session.campaign_id).status(
                    artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.RECAP_SUMMARY)
                )
                is artifact_graph_pipeline.ArtifactStatus.CURRENT
            )
            required_previous_folder = None if omit_stale_prior_recap and not previous_recap_is_current else previous_folder
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
                generate_summary_pipeline.STALE_RECAP_PLACEHOLDER
                if previous_folder is not None and omit_stale_prior_recap and not previous_recap_is_current
                else (previous_folder / paths.ARTIFACTS[paths.ArtifactName.RECAP_SUMMARY].filename).read_text(encoding="utf-8")
                if previous_folder is not None
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

    def session_processing_state(self, session_id: uuid.UUID) -> SessionProcessingState | None:
        """Return persisted navigation/error metadata without creating a record."""
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            return session_processing_entities.get_state(session, session_id)

    def set_session_processing_phase(self, session_id: uuid.UUID, phase: SessionProcessingPhase) -> SessionProcessingState:
        """Persist the stage the primary Process flow should reopen."""
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            state = session_processing_entities.set_phase(session, session_id, phase)
            session.commit()
            session.refresh(state)
            return state

    def record_session_processing_failure(
        self, session_id: uuid.UUID, phase: SessionProcessingPhase, message: str
    ) -> SessionProcessingState:
        """Persist a recoverable phase error and log only its Session and phase.

        The user-facing message remains in workflow state so the stage can explain what
        happened. It is deliberately excluded from the wide event because provider errors
        can include excerpts of transcript content.
        """
        with widelog.wide_event(
            op="session_processing_failure",
            session_id=str(session_id),
            processing_phase=phase.value,
            workflow_failed=True,
        ) as log:
            with Session(self._engine) as session:
                sessions.get_session(session, session_id)
                state = session_processing_entities.record_failure(session, session_id, phase, message)
                session.commit()
                session.refresh(state)
            log.set(failure_recorded=True)
            return state

    def clear_session_processing_failure(self, session_id: uuid.UUID) -> None:
        """Clear the saved Process-flow error while retaining its navigation state."""
        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            session_processing_entities.clear_failure(session, session_id)
            session.commit()

    def save_review_draft(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        """Atomically save noncanonical review work and then record its current source fingerprint.

        The file is written first. If recording metadata fails, the resulting orphan file is
        ignored because no database record points to it; it can never be consumed by generation.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            source = self._current_transcript_source(session, game_session)
            source_path = session_folder / paths.ARTIFACTS[source].filename
            source_modified_ns = source_path.stat().st_mtime_ns

        session_processing_pipeline.save_review_draft(session_folder, transcript)

        with Session(self._engine) as session:
            sessions.get_session(session, session_id)
            session_processing_entities.set_draft_source(session, session_id, source.value, source_modified_ns)
            session_processing_entities.set_phase(session, session_id, SessionProcessingPhase.TRANSCRIPT)
            session.commit()

    def begin_spelling_review(self, session_id: uuid.UUID, transcript: Transcript | None = None) -> Transcript:
        """Create or resume the noncanonical spelling checkpoint from a current transcript.

        A caller may provide a focused-review working copy; it is still tied to the current
        canonical machine transcript fingerprint so an audio/transcription replacement cannot
        later promote it into Manual Review or generation.
        """
        existing = self.load_spelling_review(session_id)
        if existing is not None:
            return existing
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            source = self._current_transcript_source(session, game_session)
            source_path = session_folder / paths.ARTIFACTS[source].filename
            source_modified_ns = source_path.stat().st_mtime_ns
            working_copy = transcript if transcript is not None else Transcript.load(source_path)
        session_processing_pipeline.save_spelling_review(
            session_folder,
            session_processing_pipeline.SpellingReview(
                source_artifact=source.value, source_modified_ns=source_modified_ns, transcript=working_copy
            ),
        )
        self.set_session_processing_phase(session_id, SessionProcessingPhase.SPELLING)
        return working_copy

    def save_spelling_review(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        """Save spelling corrections while retaining the original source fingerprint."""
        if self.load_spelling_review(session_id) is None:
            raise RuntimeError("Start spelling review before saving spelling corrections.")
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            source = self._current_transcript_source(session, game_session)
            source_modified_ns = (session_folder / paths.ARTIFACTS[source].filename).stat().st_mtime_ns
        session_processing_pipeline.save_spelling_review(
            session_folder,
            session_processing_pipeline.SpellingReview(
                source_artifact=source.value, source_modified_ns=source_modified_ns, transcript=transcript
            ),
        )
        self.set_session_processing_phase(session_id, SessionProcessingPhase.SPELLING)

    def load_spelling_review(self, session_id: uuid.UUID) -> Transcript | None:
        """Load spelling work only while the canonical source fingerprint remains current."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            try:
                review = session_processing_pipeline.load_spelling_review(session_folder)
            except Exception:
                review = None
            if review is None:
                return None
            try:
                source = paths.ArtifactName(review.source_artifact)
            except ValueError:
                session_processing_pipeline.discard_spelling_review(session_folder)
                return None
            source_path = session_folder / paths.ARTIFACTS[source].filename
            graph = self._artifact_graph(session, game_session.campaign_id)
            current = (
                graph.status(artifact_graph_pipeline.ArtifactRef(session_folder, source)) is artifact_graph_pipeline.ArtifactStatus.CURRENT
            )
            if not current or not source_path.is_file() or source_path.stat().st_mtime_ns != review.source_modified_ns:
                session_processing_pipeline.discard_spelling_review(session_folder)
                return None
            return review.transcript

    def complete_spelling_review(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        """Hand the spelling working copy to canonical review as its ordinary resumable draft."""
        self.save_review_draft(session_id, transcript)
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        session_processing_pipeline.discard_spelling_review(session_folder)

    def discard_spelling_review(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        session_processing_pipeline.discard_spelling_review(session_folder)

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
        session_processing_pipeline.discard_spelling_review(session_folder)

    def resolve_session_processing_phase(self, session_id: uuid.UUID) -> SessionProcessingPhase:
        """Choose a safe Process-flow destination, clamping stored navigation to valid artifacts."""
        states = self.session_artifact_states(session_id)
        state = self.session_processing_state(session_id)
        if state is not None:
            try:
                stored_phase = SessionProcessingPhase(state.phase)
            except ValueError:
                stored_phase = SessionProcessingPhase.AUDIO
            if stored_phase in (SessionProcessingPhase.BOOTSTRAP_REVIEW, SessionProcessingPhase.NEW_SPEAKER_REVIEW):
                return stored_phase
        if (
            states[paths.ArtifactName.INPUT_AUDIO] is not artifact_graph_pipeline.ArtifactStatus.CURRENT
            or states[paths.ArtifactName.TRANSCRIPT] is not artifact_graph_pipeline.ArtifactStatus.CURRENT
        ):
            return SessionProcessingPhase.AUDIO
        if self.load_spelling_review(session_id) is not None:
            return SessionProcessingPhase.SPELLING
        if self.load_review_draft(session_id) is not None:
            return SessionProcessingPhase.TRANSCRIPT
        if states[paths.ArtifactName.REVIEWED_TRANSCRIPT] is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
            return SessionProcessingPhase.TRANSCRIPT

        if state is None:
            return SessionProcessingPhase.OUTPUTS
        try:
            return SessionProcessingPhase(state.phase)
        except ValueError:
            return SessionProcessingPhase.OUTPUTS

    # Manual review.

    def extract_review_clips(self, session_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            return transcript_review.extract_review_clips(
                self._session_folder(session, game_session), on_progress, source=self._current_transcript_source(session, game_session)
            )

    def suggest_spelling_corrections(
        self, session_id: uuid.UUID, transcript: Transcript
    ) -> list[suggest_spelling_corrections_pipeline.SpellingSuggestion]:
        """Propose spelling corrections for *transcript* (Manual Review's working copy) against the campaign glossary and attendees.

        Fail-open on two independent fronts, both simply skipping to an empty result rather than
        raising: no glossary terms and no attendees (nothing to suggest against, so the LLM is
        never called), and any failure of the LLM call itself (timeout, error, malformed
        response) -- this is a convenience layer on top of an already-usable transcript, and
        Manual Review's entry point must never hard-fail because of it.
        """
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            attendee_names = [attendee.player_name for attendee in sessions.list_attendance(session, session_id)]
            glossary_terms = [entry.term for entry in glossary.list_glossary_entries(session, game_session.campaign_id)]

        if not attendee_names and not glossary_terms:
            return []

        with widelog.wide_event(op="suggest_spelling_corrections", session_id=str(session_id)) as log:
            try:
                proposals = asyncio.run(
                    suggest_spelling_corrections_pipeline.suggest_spelling_corrections(
                        transcript, glossary_terms, attendee_names, self._settings.llm_model
                    )
                )
            except Exception as exc:
                log.set(failed=True, error=str(exc), suggestion_count=0)
                return []

            suggestions = suggest_spelling_corrections_pipeline.filter_and_dedupe_suggestions(proposals, transcript)
            log.set(failed=False, proposal_count=len(proposals), suggestion_count=len(suggestions))
            return suggestions

    def discard_review_clips(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            transcript_review.discard_review_clips(self._session_folder(session, game_session))

    def save_reviewed_transcript(self, session_id: uuid.UUID, transcript: Transcript) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            transcript_review.save_reviewed_transcript(session_folder, transcript)
        # A completed canonical review supersedes any earlier spelling checkpoint. It is never
        # an input to generation on its own, so leaving it around would only offer stale work.
        session_processing_pipeline.discard_spelling_review(session_folder)

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
            self._settings.speaker_identification.existing_player_match_similarity_margin_threshold,
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
