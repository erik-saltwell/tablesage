from __future__ import annotations

import asyncio
import functools
import json
import math
import shutil
import uuid
from collections.abc import Callable, Collection, Mapping, Sequence
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, Concatenate, ParamSpec, TypeVar, cast

import widelog
import yaml
from pydantic import TypeAdapter
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

from . import campaign_corrections, campaign_recap, opportunities, paths, players_from_session, previously_on, processing_steps
from ._fs import delete_named_entity_folder, named_entity_folder_exists
from .entities import campaigns, glossary, players, sessions
from .entities import session_processing as session_processing_entities
from .llm import PromptName, system_prompt_path
from .player_archive import PlayerArchiveResult
from .session_pipeline import artifact_graph as artifact_graph_pipeline
from .session_pipeline import artifacts, import_audio, processing, processing_state, transcribe_audio, transcript_review
from .session_pipeline import clean_transcript as clean_transcript_pipeline
from .session_pipeline import extract_glossary as extract_glossary_pipeline
from .session_pipeline import find_voice_matches as find_voice_matches_pipeline
from .session_pipeline import generate_ledger as generate_ledger_pipeline
from .session_pipeline import generate_player_introductions as player_introductions_pipeline
from .session_pipeline import generate_recap_summary as recap_summary_pipeline
from .session_pipeline import generate_summary as generate_summary_pipeline
from .session_pipeline import isolate_new_speakers as isolate_new_speakers_pipeline
from .session_pipeline import legacy_import as legacy_import_pipeline
from .session_pipeline import name_corrections as name_corrections_pipeline
from .session_pipeline import review_new_speaker_assignments as review_new_speaker_assignments_pipeline
from .session_pipeline import seed_voice_samples as seed_voice_samples_pipeline
from .session_pipeline import session_processing as session_processing_pipeline
from .session_pipeline import suggest_spelling_corrections as suggest_spelling_corrections_pipeline
from .session_pipeline import transcript_edits as transcript_edits_pipeline
from .session_pipeline import transcript_sections as transcript_sections_pipeline
from .session_pipeline.atomic_files import atomic_write
from .session_pipeline.remove_backchannels import remove_backchannels
from .session_pipeline.scene_breakdown import load_current_scene_breakdown, persist_ledger_pair
from .voice_clips import clips

_REVIEW_TRANSCRIPT_STEP = "review_transcript"


def _normalized_glossary_proposals(
    proposals: Sequence[extract_glossary_pipeline.GlossaryProposal],
) -> list[extract_glossary_pipeline.GlossaryProposal]:
    """Reviewed glossary proposals with whitespace trimmed; a blank term is an error."""
    normalized: list[extract_glossary_pipeline.GlossaryProposal] = []
    for proposal in proposals:
        term = proposal.term.strip()
        if not term:
            raise ValueError("Glossary terms cannot be blank.")
        description = proposal.description.strip() if proposal.description else None
        normalized.append(extract_glossary_pipeline.GlossaryProposal(term=term, description=description or None))
    return normalized


def _corrections_value(corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]) -> list[dict[str, object]]:
    return [
        {"from_text": correction.from_text, "to_text": correction.to_text, "case_sensitive": correction.case_sensitive}
        for correction in corrections
    ]


def _suggestions_value(suggestions: Sequence[suggest_spelling_corrections_pipeline.SpellingSuggestion]) -> list[dict[str, object]]:
    return [
        {
            "from_text": suggestion.from_text,
            "to_text": suggestion.to_text,
            "case_sensitive": suggestion.case_sensitive,
            "occurrence_count": suggestion.occurrence_count,
            "removed": suggestion.removed,
        }
        for suggestion in suggestions
    ]


def _suggestions_from(value: object, key: str) -> list[suggest_spelling_corrections_pipeline.SpellingSuggestion]:
    items: list[dict[str, Any]] = cast("dict[str, Any]", value).get(key, []) if isinstance(value, dict) else []
    return [
        suggest_spelling_corrections_pipeline.SpellingSuggestion(
            from_text=item["from_text"],
            to_text=item["to_text"],
            case_sensitive=bool(item.get("case_sensitive", False)),
            occurrence_count=int(item.get("occurrence_count", 0)),
            removed=bool(item.get("removed", False)),
        )
        for item in items
    ]


_P = ParamSpec("_P")
_R = TypeVar("_R")


def _completes(
    *names: paths.ArtifactName,
) -> Callable[[Callable[Concatenate[Application, uuid.UUID, _P], _R]], Callable[Concatenate[Application, uuid.UUID, _P], _R]]:
    """Mark a producer method: once it returns, record its build steps complete (see `Application._record_completion`).
    A producer that raises records nothing, so its step stays incomplete."""

    def decorate(method: Callable[Concatenate[Application, uuid.UUID, _P], _R]) -> Callable[Concatenate[Application, uuid.UUID, _P], _R]:
        @functools.wraps(method)
        def wrapper(self: Application, session_id: uuid.UUID, /, *args: _P.args, **kwargs: _P.kwargs) -> _R:
            self._invalidate_transcript_review_for(session_id, *names)
            result = method(self, session_id, *args, **kwargs)
            self._record_completion(session_id, *names)
            return result

        return wrapper

    return decorate


class Application:
    def __init__(self, cwd: Path | None = None, settings: AppSettings | None = None) -> None:
        self._cwd: Path = cwd if cwd is not None else Path.cwd()
        self._db_path: Path = setup.ensure_database(self._cwd)
        self._engine = setup.create_engine(self._db_path)
        self._embedding_factory: EmbeddingFactory | None = None
        # Find More's per-Session utterance embeddings, kept so only a Session's first search embeds the transcript.
        self._voice_match_embeddings: dict[uuid.UUID, find_voice_matches_pipeline.VoiceMatchEmbeddings] = {}
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
            # The upcoming Session may already exist before it is played; it has no history to read yet.
            latest_folder = self._session_folder(session, game_sessions[-1])
            if not artifacts.session_artifacts(latest_folder)[paths.ArtifactName.INPUT_AUDIO]:
                game_sessions = game_sessions[:-1]
                if not game_sessions:
                    raise ValueError("This Campaign has no recorded Sessions yet. Process a Session's recording first.")
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
                    "Every Session except an unrecorded upcoming one needs a current, valid, complete Scene Breakdown.\n\n"
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

    def recompute_voice_print(self, player_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> Player:
        with Session(self._engine) as session:
            player = players.get_player(session, player_id)
            folder = paths.player_folder(self._cwd, player.name)
            outliers = self._settings.remove_outliers
            result = clips.recompute_voice_print(
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

    def export_glossary(self, campaign_id: uuid.UUID, destination: Path) -> int:
        """Export portable terms and descriptions as a JSON array, without campaign or entry IDs."""
        with Session(self._engine) as session:
            campaigns.get_campaign(session, campaign_id)
            entries = sorted(glossary.list_glossary_entries(session, campaign_id), key=lambda entry: entry.term.casefold())
            payload = [{"term": entry.term, "description": entry.description} for entry in entries]
        atomic_write(destination, (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return len(payload)

    def import_glossary(self, campaign_id: uuid.UUID, source_path: Path) -> extract_glossary_pipeline.GlossaryCommitResult:
        """Atomically import JSON entries; existing definitions and the first occurrence of each new term win."""
        proposals = TypeAdapter(list[extract_glossary_pipeline.GlossaryProposal]).validate_json(source_path.read_bytes())
        with Session(self._engine) as session:
            campaign = campaigns.get_campaign(session, campaign_id)
            seen = {extract_glossary_pipeline.normalize_term(entry.term) for entry in glossary.list_glossary_entries(session, campaign_id)}
            added: list[extract_glossary_pipeline.GlossaryProposal] = []
            for proposal in proposals:
                normalized_term = extract_glossary_pipeline.normalize_term(proposal.term)
                if normalized_term in seen:
                    continue
                seen.add(normalized_term)
                session.add(GlossaryEntry(campaign_id=campaign_id, term=proposal.term, description=proposal.description))
                added.append(proposal)
            if added:
                campaign.glossary_updated_at = datetime.now(UTC)
            session.commit()
        return extract_glossary_pipeline.GlossaryCommitResult(
            added_count=len(added), skipped_duplicate_count=len(proposals) - len(added), added=tuple(added)
        )

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
        """Session Detail's Extract Glossary restarts Suggest Glossary Terms, which needs the identified transcript."""
        states = self.session_artifact_states(session_id)
        if states[paths.ArtifactName.IDENTIFIED_TRANSCRIPT] is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
            return False, "Process the Session through Identify Speakers first."
        return True, None

    def extract_glossary(self, session_id: uuid.UUID) -> list[extract_glossary_pipeline.GlossaryProposal]:
        """Session Detail's Extract Glossary: propose new glossary entries from a Session's Role Transcript."""
        with Session(self._engine) as session:
            session_folder = self._session_folder(session, sessions.get_session(session, session_id))
        enabled, reason = extract_glossary_pipeline.can_extract_glossary(session_folder)
        if not enabled:
            raise ValueError(reason or "Cannot extract glossary terms.")
        return self._propose_glossary_entries(
            session_id, clean_transcript_pipeline.render_role_transcript_text(session_folder), op="extract_glossary"
        )

    def suggest_glossary_terms(self, session_id: uuid.UUID) -> list[extract_glossary_pipeline.GlossaryProposal]:
        """Process Session's Extract Glossary Terms step: propose new glossary entries from the identified
        transcript, before it is spellchecked against the glossary. Raises when the LLM call fails, so the
        failure lands in Process Session's error list."""
        transcript = Transcript.load(self.session_folder(session_id) / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename)
        return self._propose_glossary_entries(
            session_id, extract_glossary_pipeline.render_transcript_text(transcript), op="suggest_glossary_terms"
        )

    def _propose_glossary_entries(
        self, session_id: uuid.UUID, transcript: str, *, op: str
    ) -> list[extract_glossary_pipeline.GlossaryProposal]:
        """Ask the LLM for glossary entries in `transcript`, dropping terms the campaign glossary already has."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            attendees = tuple(
                extract_glossary_pipeline.AttendeePromptEntry(player_name=attendee.player_name, roles=attendee.roles)
                for attendee in sessions.list_attendance(session, session_id)
            )
            entries = sorted(glossary.list_glossary_entries(session, game_session.campaign_id), key=lambda entry: entry.term.casefold())
            prompt_glossary = tuple(
                extract_glossary_pipeline.GlossaryPromptEntry(term=entry.term, description=entry.description) for entry in entries
            )

        with widelog.wide_event(
            op=op,
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
        normalized_proposals = _normalized_glossary_proposals(proposals)

        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            existing = glossary.list_glossary_entries(session, game_session.campaign_id)
            seen = {extract_glossary_pipeline.normalize_term(entry.term) for entry in existing}
            accepted: list[GlossaryEntry] = []
            added: list[extract_glossary_pipeline.GlossaryProposal] = []
            skipped_count = 0
            for proposal in normalized_proposals:
                normalized_term = extract_glossary_pipeline.normalize_term(proposal.term)
                if normalized_term in seen:
                    skipped_count += 1
                    continue
                seen.add(normalized_term)
                added.append(proposal)
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

        return extract_glossary_pipeline.GlossaryCommitResult(
            added_count=len(accepted), skipped_duplicate_count=skipped_count, added=tuple(added)
        )

    def propose_glossary_terms(self, session_id: uuid.UUID) -> list[extract_glossary_pipeline.GlossaryProposal]:
        """Suggest Glossary Terms: the LLM's new-term proposals from the identified transcript, saved for review."""
        proposals = self.suggest_glossary_terms(session_id)
        self._complete_section(
            session_id, paths.ArtifactName.GLOSSARY_SUGGESTIONS, {"proposals": [proposal.model_dump(mode="json") for proposal in proposals]}
        )
        return proposals

    def glossary_term_review(
        self, session_id: uuid.UUID
    ) -> tuple[list[extract_glossary_pipeline.GlossaryProposal], list[extract_glossary_pipeline.GlossaryProposal] | None]:
        """Extract Glossary Terms' review: the saved proposals, and the last saved decision (to reopen as left)."""
        suggestions = self._section(session_id, paths.ArtifactName.GLOSSARY_SUGGESTIONS) or {}
        decisions = self._section(session_id, paths.ArtifactName.GLOSSARY_DECISIONS)
        proposals = [extract_glossary_pipeline.GlossaryProposal.model_validate(item) for item in suggestions.get("proposals", [])]
        decided = (
            [extract_glossary_pipeline.GlossaryProposal.model_validate(item) for item in decisions.get("entries", [])]
            if isinstance(decisions, dict)
            else None
        )
        return proposals, decided

    def save_glossary_decisions(self, session_id: uuid.UUID, proposals: Sequence[extract_glossary_pipeline.GlossaryProposal]) -> None:
        """Extract Glossary Terms' decision: the reviewed entries to add to the campaign glossary."""
        entries = [proposal.model_dump(mode="json") for proposal in _normalized_glossary_proposals(proposals)]
        self._complete_section(session_id, paths.ArtifactName.GLOSSARY_DECISIONS, {"entries": entries})

    def add_glossary_entries(self, session_id: uuid.UUID) -> extract_glossary_pipeline.GlossaryCommitResult:
        """Add Glossary Entries: commit the decided entries to the campaign glossary (existing terms are skipped, so
        re-running is harmless), then record the receipt."""
        decisions = self._section(session_id, paths.ArtifactName.GLOSSARY_DECISIONS)
        if not isinstance(decisions, dict):
            raise ValueError("The glossary review hasn't been completed.")
        entries = [extract_glossary_pipeline.GlossaryProposal.model_validate(item) for item in decisions.get("entries", [])]
        result = self.complete_glossary_extraction(session_id, entries)
        self._complete_section(
            session_id, paths.ArtifactName.EXTRACTED_GLOSSARY_TERMS, {"entries": [entry.model_dump(mode="json") for entry in entries]}
        )
        return result

    def save_extracted_glossary_terms(
        self, session_id: uuid.UUID, proposals: Sequence[extract_glossary_pipeline.GlossaryProposal]
    ) -> extract_glossary_pipeline.GlossaryCommitResult:
        """Complete Extract Glossary Terms and commit it (decision, then Add Glossary Entries)."""
        self.save_glossary_decisions(session_id, proposals)
        return self.add_glossary_entries(session_id)

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

    def _artifact_graph(self, session: Session, campaign_id: uuid.UUID, *, legacy: bool = False) -> artifact_graph_pipeline.ArtifactGraph:
        """The campaign's build graph. Sessions not yet imported into `processing_state.json` are imported first
        (see `_import_legacy_sessions`); `legacy` builds the retired modification-time graph that import uses."""
        graph_type = artifact_graph_pipeline.LegacyArtifactGraph if legacy else artifact_graph_pipeline.ArtifactGraph

        prompt_input = self._prompt_input
        game_sessions = sessions.list_sessions(session, campaign_id)
        if not legacy:
            self._import_legacy_sessions(session, campaign_id, [self._session_folder(session, item) for item in game_sessions])
        sessions_by_id = {game_session.id: game_session for game_session in game_sessions}
        steps: list[artifact_graph_pipeline.BuildStep] = []
        interrupted: set[artifact_graph_pipeline.ArtifactRef] = set()
        # Each Summary: its own reference, its fixed dependencies, and the previous Session's folder (if any).
        summaries: list[tuple[artifact_graph_pipeline.ArtifactRef, list[artifact_graph_pipeline.Dependency], Path | None]] = []

        for game_session in game_sessions:
            folder = self._session_folder(session, game_session)

            def ref(name: paths.ArtifactName, folder: Path = folder) -> artifact_graph_pipeline.ArtifactRef:
                return artifact_graph_pipeline.ArtifactRef(folder, name)

            steps.extend(self._legacy_session_steps(folder) if legacy else self._session_steps(folder))
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
            if (folder / paths.AUDIO_PAIR_MARKER).exists():
                interrupted.update((ref(paths.ArtifactName.INPUT_AUDIO), ref(paths.ArtifactName.NORMALIZED_REVIEW_AUDIO)))

        # A Summary depends on the previous Session's recap only while that Session can be regenerated (its
        # reviewed transcript is current). Otherwise the Summary carries a placeholder and can still be current;
        # once the previous Session is reviewed, the dependency returns and the Summary goes out of date.
        # Reviewed transcripts never depend on Summaries, so a graph without them answers that safely.
        without_summaries = graph_type(tuple(steps), interrupted=frozenset(interrupted))
        for summary, summary_dependencies, previous_folder in summaries:
            if previous_folder is not None and self._previous_session_regenerable(without_summaries, previous_folder):
                summary_dependencies.append(artifact_graph_pipeline.ArtifactRef(previous_folder, paths.ArtifactName.RECAP_SUMMARY))
            steps.append(artifact_graph_pipeline.BuildStep(paths.ArtifactName.SUMMARY, (summary,), tuple(summary_dependencies)))

        return graph_type(tuple(steps), interrupted=frozenset(interrupted))

    @staticmethod
    def _prompt_input(name: PromptName) -> artifact_graph_pipeline.SystemPromptInput:
        return artifact_graph_pipeline.SystemPromptInput(system_prompt_path(name))

    @classmethod
    def _session_steps(cls, folder: Path) -> tuple[artifact_graph_pipeline.BuildStep, ...]:
        """A Session's build steps, apart from its Summary (see `_artifact_graph`). Each processing step's outputs
        are built by one of these; a manual step's decision section depends on the suggestions it reviews."""
        ref = functools.partial(artifact_graph_pipeline.ArtifactRef, folder)
        prompt_input = cls._prompt_input
        name = paths.ArtifactName
        step = artifact_graph_pipeline.BuildStep
        return (
            # Import Audio's decision has no inputs: it is whatever file was chosen last.
            step(name.IMPORT_REQUEST, (ref(name.IMPORT_REQUEST),), ()),
            step(name.INPUT_AUDIO, (ref(name.INPUT_AUDIO), ref(name.NORMALIZED_REVIEW_AUDIO)), (ref(name.IMPORT_REQUEST),)),
            step(name.TRANSCRIPT, (ref(name.TRANSCRIPT), ref(name.TRANSCRIPT_TEXT)), (ref(name.INPUT_AUDIO),)),
            step(
                name.CLEANED_TRANSCRIPT,
                (ref(name.CLEANED_TRANSCRIPT),),
                (ref(name.TRANSCRIPT), prompt_input(PromptName.CLASSIFY_BACKCHANNELS)),
            ),
            step(
                name.NAME_CORRECTION_SUGGESTIONS,
                (ref(name.NAME_CORRECTION_SUGGESTIONS),),
                (ref(name.CLEANED_TRANSCRIPT), prompt_input(PromptName.SUGGEST_NAME_CORRECTIONS)),
            ),
            step(name.NAME_CORRECTION_DECISIONS, (ref(name.NAME_CORRECTION_DECISIONS),), (ref(name.NAME_CORRECTION_SUGGESTIONS),)),
            step(
                name.NAME_CORRECTED_TRANSCRIPT,
                (ref(name.NAME_CORRECTED_TRANSCRIPT),),
                (ref(name.CLEANED_TRANSCRIPT), ref(name.NAME_CORRECTION_DECISIONS)),
            ),
            step(
                name.NEW_SPEAKER_ASSIGNMENTS,
                (ref(name.NEW_SPEAKER_ASSIGNMENTS),),
                (ref(name.NAME_CORRECTED_TRANSCRIPT), prompt_input(PromptName.ISOLATE_NEW_SPEAKERS)),
            ),
            step(
                name.REVIEWED_NEW_SPEAKER_ASSIGNMENTS,
                (ref(name.REVIEWED_NEW_SPEAKER_ASSIGNMENTS),),
                (ref(name.NEW_SPEAKER_ASSIGNMENTS), ref(name.NORMALIZED_REVIEW_AUDIO)),
            ),
            step(name.SEEDED_VOICE_SAMPLES, (ref(name.SEEDED_VOICE_SAMPLES),), (ref(name.REVIEWED_NEW_SPEAKER_ASSIGNMENTS),)),
            # Identification also reads returning players' voice voice prints from the database. Deliberately not a
            # dependency: enhancing a player's voice print from a later Session must not re-identify every earlier one.
            step(
                name.IDENTIFIED_TRANSCRIPT,
                (ref(name.IDENTIFIED_TRANSCRIPT),),
                (ref(name.NAME_CORRECTED_TRANSCRIPT), ref(name.SEEDED_VOICE_SAMPLES)),
            ),
            step(
                name.GLOSSARY_SUGGESTIONS,
                (ref(name.GLOSSARY_SUGGESTIONS),),
                (ref(name.IDENTIFIED_TRANSCRIPT), prompt_input(PromptName.EXTRACT_GLOSSARY)),
            ),
            step(name.GLOSSARY_DECISIONS, (ref(name.GLOSSARY_DECISIONS),), (ref(name.GLOSSARY_SUGGESTIONS),)),
            # The glossary itself (shared across the campaign's Sessions) is deliberately not a dependency: later
            # Sessions adding terms must not invalidate this one. Only this Session's receipt is.
            step(name.EXTRACTED_GLOSSARY_TERMS, (ref(name.EXTRACTED_GLOSSARY_TERMS),), (ref(name.GLOSSARY_DECISIONS),)),
            step(
                name.SPELLING_SUGGESTIONS,
                (ref(name.SPELLING_SUGGESTIONS),),
                (
                    ref(name.IDENTIFIED_TRANSCRIPT),
                    ref(name.EXTRACTED_GLOSSARY_TERMS),
                    prompt_input(PromptName.SUGGEST_SPELLING_CORRECTIONS),
                ),
            ),
            step(name.SPELLING_DECISIONS, (ref(name.SPELLING_DECISIONS),), (ref(name.SPELLING_SUGGESTIONS),)),
            step(
                name.SPELLCHECKED_TRANSCRIPT,
                (ref(name.SPELLCHECKED_TRANSCRIPT),),
                (ref(name.IDENTIFIED_TRANSCRIPT), ref(name.SPELLING_DECISIONS)),
            ),
            step(
                name.TRANSCRIPT_REVIEW_EDITS,
                (ref(name.TRANSCRIPT_REVIEW_EDITS),),
                (ref(name.SPELLCHECKED_TRANSCRIPT), ref(name.NORMALIZED_REVIEW_AUDIO)),
            ),
            step(
                name.REVIEWED_TRANSCRIPT,
                (ref(name.REVIEWED_TRANSCRIPT),),
                (ref(name.SPELLCHECKED_TRANSCRIPT), ref(name.TRANSCRIPT_REVIEW_EDITS)),
            ),
            step(name.ROLE_TRANSCRIPT, (ref(name.ROLE_TRANSCRIPT),), (ref(name.REVIEWED_TRANSCRIPT),)),
            step(
                name.TRANSCRIPT_SECTIONS,
                (ref(name.TRANSCRIPT_SECTIONS),),
                (ref(name.ROLE_TRANSCRIPT), prompt_input(PromptName.SECTION_TRANSCRIPT)),
            ),
            step(
                name.LEDGER,
                (
                    ref(name.LEDGER),
                    artifact_graph_pipeline.FileRef(folder / generate_ledger_pipeline.LEDGER_MARKDOWN_FILENAME),
                    ref(name.SCENE_BREAKDOWN),
                ),
                (ref(name.ROLE_TRANSCRIPT), ref(name.TRANSCRIPT_SECTIONS), prompt_input(PromptName.GENERATE_LEDGER)),
            ),
            step(
                name.PLAYER_INTRODUCTIONS,
                (ref(name.PLAYER_INTRODUCTIONS),),
                (ref(name.ROLE_TRANSCRIPT), ref(name.TRANSCRIPT_SECTIONS), prompt_input(PromptName.GENERATE_PLAYER_INTRODUCTIONS)),
            ),
            step(
                name.RECAP_SUMMARY, (ref(name.RECAP_SUMMARY),), (ref(name.SCENE_BREAKDOWN), prompt_input(PromptName.GENERATE_RECAP_SUMMARY))
            ),
            # The voice-print offer asks again only when the reviewed transcript -- where its clips come from -- changes.
            step(name.VOICE_PRINT_DECISION, (ref(name.VOICE_PRINT_DECISION),), (ref(name.REVIEWED_TRANSCRIPT),)),
            step(name.VOICE_PRINT_ENHANCEMENT, (ref(name.VOICE_PRINT_ENHANCEMENT),), (ref(name.VOICE_PRINT_DECISION),)),
        )

    @classmethod
    def _legacy_session_steps(cls, folder: Path) -> tuple[artifact_graph_pipeline.BuildStep, ...]:
        """The retired pre-`processing_state.json` build steps, kept only for the one-time legacy import."""
        prompt_input = cls._prompt_input

        def ref(name: paths.ArtifactName) -> artifact_graph_pipeline.ArtifactRef:
            return artifact_graph_pipeline.ArtifactRef(folder, name)

        return (
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
            # Identification also reads returning players' voice prints from the database; changing
            # those is not tracked here (see the session-processing-flow work item).
            artifact_graph_pipeline.BuildStep(
                paths.ArtifactName.IDENTIFIED_TRANSCRIPT,
                (ref(paths.ArtifactName.IDENTIFIED_TRANSCRIPT),),
                (
                    ref(paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT),
                    ref(paths.ArtifactName.SEEDED_VOICE_SAMPLES),
                ),
            ),
            # The glossary itself (shared across the campaign's Sessions) is deliberately not a dependency:
            # later Sessions adding terms must not invalidate this one. Only this Session's receipt is.
            artifact_graph_pipeline.BuildStep(
                paths.ArtifactName.EXTRACTED_GLOSSARY_TERMS,
                (ref(paths.ArtifactName.EXTRACTED_GLOSSARY_TERMS),),
                (
                    ref(paths.ArtifactName.IDENTIFIED_TRANSCRIPT),
                    prompt_input(PromptName.EXTRACT_GLOSSARY),
                ),
            ),
            artifact_graph_pipeline.BuildStep(
                paths.ArtifactName.SPELLCHECKED_TRANSCRIPT,
                (ref(paths.ArtifactName.SPELLCHECKED_TRANSCRIPT),),
                (
                    ref(paths.ArtifactName.IDENTIFIED_TRANSCRIPT),
                    ref(paths.ArtifactName.EXTRACTED_GLOSSARY_TERMS),
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

    def _import_legacy_sessions(self, session: Session, campaign_id: uuid.UUID, folders: Sequence[Path]) -> None:
        """Import Sessions processed before `processing_state.json` existed, once each.

        The retired modification-time graph decides what was current. Old receipt files become sections, steps
        that didn't exist then get placeholder sections wherever the work they precede was current (see
        `legacy_import`), and each build step standing for current work gets a completion record fingerprinting
        its inputs as they are now -- so exactly the work that was current stays current. This is the only place
        file modification times still decide anything. The replaced files move to the Session's `legacy/` folder.
        """
        pending = [folder for folder in folders if processing_state.needs_legacy_import(folder)]
        if not pending:
            return
        legacy_graph = self._artifact_graph(session, campaign_id, legacy=True)
        carried_by_folder: dict[Path, tuple[set[paths.ArtifactName], set[paths.ArtifactName]]] = {}
        for folder in pending:
            current = {
                name
                for name, spec in paths.ARTIFACTS.items()
                if spec.filename
                and legacy_graph.status(artifact_graph_pipeline.ArtifactRef(folder, name)) is artifact_graph_pipeline.ArtifactStatus.CURRENT
            }
            sections, carried = legacy_import_pipeline.build_sections(folder, current)

            def add_sections(state: processing_state.ProcessingState, sections: dict[str, object] = sections) -> None:
                state.sections.update(sections)
                state.legacy_imported_at = processing_state.now()

            processing_state.update(folder, add_sections, reason="legacy_import")
            carried_by_folder[folder] = (current, carried)

        # Every pending folder now has a state document, so this builds the current graph without importing again.
        graph = self._artifact_graph(session, campaign_id)
        for folder, (current, carried) in carried_by_folder.items():
            with widelog.wide_event(op="processing_state.legacy_import", session_folder=str(folder)) as log:
                records: dict[str, processing_state.CompletionRecord] = {}
                for step in graph.steps:
                    if step.folder != folder:
                        continue
                    outputs = [output for output in step.outputs if isinstance(output, artifact_graph_pipeline.ArtifactRef)]
                    if all(output.name in (carried if output.is_section else current) for output in outputs):
                        records[step.name.value] = processing_state.CompletionRecord(
                            completed_at=processing_state.now(), inputs=artifact_graph_pipeline.current_fingerprints(step, graph.state)
                        )

                def add_records(
                    state: processing_state.ProcessingState, records: dict[str, processing_state.CompletionRecord] = records
                ) -> None:
                    state.records.update(records)

                processing_state.update(folder, add_records, reason="legacy_import")
                moved = legacy_import_pipeline.move_retired_files(folder)
                log.set(
                    legacy_current=sorted(name.value for name in current),
                    imported=sorted(records),
                    placeholder_sections=sorted(name.value for name in carried),
                    moved_to_legacy=moved,
                )

    def _record_completion(self, session_id: uuid.UUID, *names: paths.ArtifactName) -> None:
        """Mark build steps complete: record each declared input's fingerprint as it is now. Producers call this
        after writing their outputs -- also when they left identical output unwritten."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            folder = self._session_folder(session, game_session)
            graph = self._artifact_graph(session, game_session.campaign_id)
        records: dict[str, processing_state.CompletionRecord] = {}
        for name in names:
            step = graph.step_for(artifact_graph_pipeline.ArtifactRef(folder, name))
            if step is None:
                raise ValueError(f"No build step produces {paths.ARTIFACTS[name].display_name}.")
            records[name.value] = processing_state.CompletionRecord(
                completed_at=processing_state.now(), inputs=artifact_graph_pipeline.current_fingerprints(step, graph.state)
            )

        def apply(state: processing_state.ProcessingState) -> None:
            state.records.update(records)

        processing_state.update(folder, apply, reason="step_completed")

    def _complete_section(self, session_id: uuid.UUID, name: paths.ArtifactName, value: object) -> None:
        """Save a section and record its build step complete, in one state write: a crash leaves neither or both."""
        if paths.ARTIFACTS[name].is_file:
            raise ValueError(f"{name.value} is a file artifact, not a section.")
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            folder = self._session_folder(session, game_session)
            graph = self._artifact_graph(session, game_session.campaign_id)
        step = graph.step_for(artifact_graph_pipeline.ArtifactRef(folder, name))
        if step is None:
            raise ValueError(f"No build step produces {paths.ARTIFACTS[name].display_name}.")
        record = processing_state.CompletionRecord(
            completed_at=processing_state.now(), inputs=artifact_graph_pipeline.current_fingerprints(step, graph.state)
        )
        self._invalidate_transcript_review_for(session_id, name)

        def apply(state: processing_state.ProcessingState) -> None:
            state.sections[name.value] = value
            state.records[name.value] = record

        processing_state.update(folder, apply, reason="step_completed")

    def _section(self, session_id: uuid.UUID, name: paths.ArtifactName) -> Any:
        """A section's saved value, or None when it has none."""
        return processing_state.load(self.session_folder(session_id)).sections.get(name.value)

    def is_imported_placeholder(self, session_id: uuid.UUID, name: paths.ArtifactName) -> bool:
        """Whether a section is a placeholder from importing a pre-`processing_state.json` Session (see `legacy_import`):
        its suggestions weren't kept, so reopening the step that reviews them re-runs the suggestion step first."""
        value = self._section(session_id, name)
        return isinstance(value, dict) and bool(value.get("legacy"))

    # Session processing steps (see `processing_steps`): the overview Process Session and the coordinator read,
    # restarts, failures, and the decisions that aren't reviews.

    def processing_overview(self, session_id: uuid.UUID) -> processing_steps.ProcessingOverview:
        """Every step's completion and display state, the new players, and anything blocking processing."""
        states = self.session_artifact_states(session_id)
        state = processing_state.load(self.session_folder(session_id))
        new_players = tuple(player.player_name for player in self.new_players(session_id))
        blockers = tuple(blocker.message for blocker in self.session_processing_blockers(session_id))

        def current(name: paths.ArtifactName) -> bool:
            return states[name] is artifact_graph_pipeline.ArtifactStatus.CURRENT

        # New-player rows: once Isolate New Speakers has run, its proposals decide (players seeded by this Session
        # are no longer new, but their rows stay); before that, the live attendee list does.
        proposals = state.sections.get(paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS.value)
        if current(paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS) and isinstance(proposals, dict):
            shows_new_players = bool(proposals.get("players"))
        else:
            shows_new_players = bool(new_players)

        step_states: list[processing_steps.StepState] = []
        predecessors_complete = True
        for step in processing_steps.PROCESSING_STEPS:
            if step.id is processing_steps.StepID.APPROVE_PRIOR_REBUILD:
                prior = self.prior_rebuild_tasks(session_id) if predecessors_complete else ()
                complete = predecessors_complete and self._prior_rebuild_approved(state, prior)
                visible = bool(prior)
            else:
                complete = all(current(name) for name in step.outputs)
                # Whether the step applies to this Session; Process Session decides whether to draw automatic ones.
                visible = step.visibility is processing_steps.StepVisibility.ALWAYS or (
                    step.visibility is processing_steps.StepVisibility.NEW_PLAYERS and shows_new_players
                )
            failure = state.failures.get(step.id.value)
            step_states.append(
                processing_steps.StepState(
                    step=step,
                    complete=complete,
                    visible=visible,
                    nothing_to_review=complete and self._reviewed_nothing(state, step.id),
                    failure=failure.message if failure is not None else None,
                )
            )
            predecessors_complete = predecessors_complete and complete
        return processing_steps.ProcessingOverview(steps=tuple(step_states), new_players=new_players, blockers=blockers)

    @staticmethod
    def _reviewed_nothing(state: processing_state.ProcessingState, step_id: processing_steps.StepID) -> bool:
        """Whether a manual step completed on its own because there was nothing to review (not an imported Session's
        placeholder, whose suggestions simply weren't kept)."""
        reviewed = {
            processing_steps.StepID.REVIEW_NAME_CORRECTIONS: (paths.ArtifactName.NAME_CORRECTION_SUGGESTIONS, "suggestions"),
            processing_steps.StepID.REVIEW_NEW_SPEAKER_ASSIGNMENTS: (paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS, "players"),
            processing_steps.StepID.REVIEW_GLOSSARY_TERMS: (paths.ArtifactName.GLOSSARY_SUGGESTIONS, "proposals"),
            processing_steps.StepID.REVIEW_SPELLING_CORRECTIONS: (paths.ArtifactName.SPELLING_SUGGESTIONS, "suggestions"),
        }.get(step_id)
        if reviewed is None:
            return False
        value = state.sections.get(reviewed[0].value)
        return isinstance(value, dict) and not value.get("legacy") and not value.get(reviewed[1])

    def prior_rebuild_tasks(self, session_id: uuid.UUID) -> tuple[artifact_graph_pipeline.GenerationTask, ...]:
        """The earlier Sessions' outputs that generating this Session's would rebuild; empty when none are stale."""
        try:
            plan = self.generation_plan(session_id)
        except ValueError:
            return ()
        return tuple(task for task in plan if task.session_id != session_id)

    @staticmethod
    def _task_value(tasks: Sequence[artifact_graph_pipeline.GenerationTask]) -> list[dict[str, str]]:
        return [{"session_id": str(task.session_id), "artifact": task.artifact_name.value} for task in tasks]

    def _prior_rebuild_approved(
        self, state: processing_state.ProcessingState, tasks: Sequence[artifact_graph_pipeline.GenerationTask]
    ) -> bool:
        """Approved when nothing needs rebuilding, or the saved approval covers exactly the current rebuild plan."""
        return not tasks or state.sections.get(processing_steps.PRIOR_REBUILD_APPROVAL_SECTION) == self._task_value(tasks)

    def approve_prior_rebuild(self, session_id: uuid.UUID, tasks: Sequence[artifact_graph_pipeline.GenerationTask]) -> None:
        """Rebuild Prior Sessions' decision: consent to rebuild exactly `tasks` before this Session's outputs."""
        value = self._task_value(tasks)

        def apply(state: processing_state.ProcessingState) -> None:
            state.sections[processing_steps.PRIOR_REBUILD_APPROVAL_SECTION] = value

        processing_state.update(self.session_folder(session_id), apply, reason="step_completed")

    def reopen_step(self, session_id: uuid.UUID, step_id: processing_steps.StepID) -> None:
        """Restart a step: mark its outputs incomplete, keeping their content (a manual step reopens as it was left).
        Completing it again with the same result preserves downstream content freshness, but upstream restarts
        permanently discard transcript-review work."""
        step = processing_steps.STEPS_BY_ID[step_id]
        self._invalidate_transcript_review_for(session_id, *step.outputs)

        def apply(state: processing_state.ProcessingState) -> None:
            for name in step.outputs:
                record = state.records.get(name.value)
                if record is not None:
                    state.records[name.value] = record.model_copy(update={"complete": False})
            if step_id is processing_steps.StepID.APPROVE_PRIOR_REBUILD:
                state.sections.pop(processing_steps.PRIOR_REBUILD_APPROVAL_SECTION, None)

        processing_state.update(self.session_folder(session_id), apply, reason=f"step_reopened:{step_id.value}")

    def reopen_artifact(self, session_id: uuid.UUID, name: paths.ArtifactName) -> None:
        """Mark one output incomplete, keeping its content, so the step producing it runs again (Regenerate Artifact)."""
        self._invalidate_transcript_review_for(session_id, name)

        def apply(state: processing_state.ProcessingState) -> None:
            record = state.records.get(name.value)
            if record is not None:
                state.records[name.value] = record.model_copy(update={"complete": False})

        processing_state.update(self.session_folder(session_id), apply, reason=f"artifact_reopened:{name.value}")

    def record_step_failure(self, session_id: uuid.UUID, step_id: processing_steps.StepID, message: str, run_id: str | None) -> None:
        """Keep a step's last failure for its row; informational only, never read for completion."""
        failure = processing_state.StepFailure(message=message, at=processing_state.now(), run_id=run_id)

        def apply(state: processing_state.ProcessingState) -> None:
            state.failures[step_id.value] = failure

        processing_state.update(self.session_folder(session_id), apply, reason="step_failed")

    def clear_step_failure(self, session_id: uuid.UUID, step_id: processing_steps.StepID) -> None:
        def apply(state: processing_state.ProcessingState) -> None:
            state.failures.pop(step_id.value, None)

        processing_state.update(self.session_folder(session_id), apply, reason="step_failure_cleared")

    def save_voice_print_decision(self, session_id: uuid.UUID, *, accepted: bool) -> None:
        """Improve Player Voice Prints' decision: whether to add this Session's voice clips to its players' voice samples."""
        self._complete_section(session_id, paths.ArtifactName.VOICE_PRINT_DECISION, {"accepted": accepted})

    def enhance_voice_prints(
        self, session_id: uuid.UUID, on_progress: players_from_session.OnProgress | None = None
    ) -> players_from_session.EnhanceResult | None:
        """Enhance Voice Prints: when the offer was accepted, add this Session's clips to its players' voice samples
        (replacing any this Session added before, so re-running is harmless); record the receipt either way."""
        decision = self._section(session_id, paths.ArtifactName.VOICE_PRINT_DECISION)
        accepted = isinstance(decision, dict) and bool(decision.get("accepted"))
        result = self.enhance_players_from_session(session_id, on_progress) if accepted else None
        self._complete_section(
            session_id,
            paths.ArtifactName.VOICE_PRINT_ENHANCEMENT,
            {
                "enhanced_player_count": result.enhanced_player_count if result is not None else 0,
                "clip_count": result.clip_count if result is not None else 0,
            },
        )
        return result

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

    def session_player_voice_prints(self, session_id: uuid.UUID) -> dict[str, Embedding]:
        """Attending players' voice voice prints, keyed by player name -- `transcribe_audio`'s speaker-ID input."""
        with Session(self._engine) as session:
            voice_prints: dict[str, Embedding] = {}
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                if player is not None:
                    embedding = self._usable_player_embedding(player)
                    if embedding is not None:
                        voice_prints[player.name] = embedding
            return voice_prints

    def new_players(self, session_id: uuid.UUID) -> list[isolate_new_speakers_pipeline.NewPlayer]:
        """This Session's new players -- attendees with no usable voice voice print -- computed live from the database.

        Deliberately not persisted or part of artifact staleness: changing attendance or voice
        prints after the new-player steps ran does not invalidate them.
        """
        with Session(self._engine) as session:
            new_players: list[isolate_new_speakers_pipeline.NewPlayer] = []
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                assert player is not None
                if self._usable_player_embedding(player) is None:
                    new_players.append(isolate_new_speakers_pipeline.NewPlayer(attendee.player_id, attendee.player_name, attendee.roles))
            return new_players

    def session_processing_blockers(self, session_id: uuid.UUID) -> list[processing_steps.ProcessingBlocker]:
        """Errors that stop a Process Session step, and every step after it, from running."""
        blockers: list[processing_steps.ProcessingBlocker] = []
        if not self.list_attendance(session_id):
            blockers.append(
                processing_steps.ProcessingBlocker(
                    processing_steps.StepID.IMPORT_AUDIO,
                    "This Session has no attendees. Add them on Session Detail.",
                )
            )
        return blockers

    @staticmethod
    def _usable_player_embedding(player: Player, expected_dimension: int | None = None) -> Embedding | None:
        """Validate a stored voice print before using it as identification evidence.

        Voice prints do not identify their embedding backend, so the caller can provide an expected
        dimension when it is known.
        """
        if player.voice_print_embedding is None or player.sample_count <= 0:
            return None
        try:
            embedding = Embedding.model_validate(json.loads(player.voice_print_embedding))
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
        self.import_session_audio(session_id, source_path, should_clean_audio=should_clean_audio)
        self.discard_review_draft(session_id)
        return self.transcribe_session_audio(session_id, on_progress=on_progress)

    def save_import_request(self, session_id: uuid.UUID, source_path: Path, *, clean_audio: bool) -> None:
        """Import Audio's decision: which file to import and whether to clean it."""
        self.validate_import_audio_source(source_path)
        self._complete_section(session_id, paths.ArtifactName.IMPORT_REQUEST, {"source_path": str(source_path), "clean_audio": clean_audio})

    @_completes(paths.ArtifactName.INPUT_AUDIO)
    def import_requested_audio(self, session_id: uuid.UUID) -> None:
        """Import Audio File: replace the input audio from the saved request; everything derived from the old audio
        goes stale."""
        request = self._section(session_id, paths.ArtifactName.IMPORT_REQUEST)
        if not isinstance(request, dict) or not request.get("source_path"):
            raise ValueError("No audio file has been chosen. Run Import Audio to choose one.")
        source_path = Path(request["source_path"])
        self.validate_import_audio_source(source_path)
        import_audio.import_audio(
            source_path,
            self.session_folder(session_id),
            self._settings.session_audio_import.normalize_volume,
            should_clean_audio=bool(request.get("clean_audio")),
            review_normalization=self._settings.session_audio_import.review_normalization,
        )

    def import_session_audio(self, session_id: uuid.UUID, source_path: Path, *, should_clean_audio: bool) -> None:
        """Replace input audio (Import Audio's decision, then its import); everything derived from the old audio goes stale."""
        self.save_import_request(session_id, source_path, clean_audio=should_clean_audio)
        self.import_requested_audio(session_id)

    @_completes(paths.ArtifactName.TRANSCRIPT)
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

    @_completes(paths.ArtifactName.CLEANED_TRANSCRIPT)
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

    def propose_name_corrections(self, session_id: uuid.UUID) -> list[suggest_spelling_corrections_pipeline.SpellingSuggestion]:
        """Suggest Name Corrections: the LLM's corrections to misheard player and character names, saved for review.
        Names are only reviewed for Sessions with new players, so without any this saves none and calls no LLM."""
        suggestions = self.suggest_name_corrections(session_id)[1] if self.new_players(session_id) else []
        self._complete_section(session_id, paths.ArtifactName.NAME_CORRECTION_SUGGESTIONS, {"suggestions": _suggestions_value(suggestions)})
        return suggestions

    def name_correction_review(
        self, session_id: uuid.UUID
    ) -> tuple[
        Transcript,
        list[suggest_spelling_corrections_pipeline.SpellingSuggestion],
        list[suggest_spelling_corrections_pipeline.SpellingSuggestion] | None,
    ]:
        """Review Name Corrections: the cleaned transcript, the saved suggestions, and the last saved decision."""
        transcript = name_corrections_pipeline.load_source(self.session_folder(session_id))
        decisions = self._section(session_id, paths.ArtifactName.NAME_CORRECTION_DECISIONS)
        return (
            transcript,
            _suggestions_from(self._section(session_id, paths.ArtifactName.NAME_CORRECTION_SUGGESTIONS), "suggestions"),
            _suggestions_from(decisions, "corrections") if decisions is not None else None,
        )

    def save_name_correction_decisions(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> None:
        self._complete_section(session_id, paths.ArtifactName.NAME_CORRECTION_DECISIONS, {"corrections": _corrections_value(corrections)})

    @_completes(paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT)
    def apply_name_corrections(self, session_id: uuid.UUID) -> int:
        """Write the name-corrected transcript from the saved decision; return how many occurrences were replaced."""
        decisions = self._section(session_id, paths.ArtifactName.NAME_CORRECTION_DECISIONS)
        if decisions is None:
            raise ValueError("The name corrections haven't been reviewed.")
        _written, occurrences = name_corrections_pipeline.save_corrected(
            self.session_folder(session_id), _suggestions_from(decisions, "corrections"), saved_is_current=False
        )
        return occurrences

    def save_name_corrections(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> tuple[bool, int]:
        """Complete Review Name Corrections and write the name-corrected transcript (decision, then apply)."""
        self.save_name_correction_decisions(session_id, corrections)
        return True, self.apply_name_corrections(session_id)

    def isolate_new_speakers(
        self, session_id: uuid.UUID, *, on_progress: isolate_new_speakers_pipeline.OnProgress | None = None
    ) -> isolate_new_speakers_pipeline.NewSpeakerAssignments:
        """Process Session's Isolate New Speakers step: high-confidence utterances for each new player, saved as the
        proposals Review New Speaker Assignments reviews."""
        session_folder = self.session_folder(session_id)
        bootstrap = self._settings.speaker_bootstrap
        isolation = self._settings.isolate_new_speakers
        outliers = self._settings.remove_outliers
        proposals = isolate_new_speakers_pipeline.isolate_new_speakers(
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
        self._complete_section(session_id, paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS, proposals.model_dump(mode="json"))
        return proposals

    def new_speaker_proposals(self, session_id: uuid.UUID) -> isolate_new_speakers_pipeline.NewSpeakerAssignments:
        value = self._section(session_id, paths.ArtifactName.NEW_SPEAKER_ASSIGNMENTS)
        if value is None:
            raise ValueError("New speakers haven't been isolated yet.")
        return isolate_new_speakers_pipeline.NewSpeakerAssignments.model_validate(value)

    def _current_new_speaker_review(
        self, session_id: uuid.UUID
    ) -> review_new_speaker_assignments_pipeline.ReviewedNewSpeakerAssignments | None:
        """The last saved review, to reopen the step as it was left."""
        value = self._section(session_id, paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS)
        return review_new_speaker_assignments_pipeline.ReviewedNewSpeakerAssignments.model_validate(value) if value is not None else None

    def draft_new_speaker_review(
        self, session_id: uuid.UUID, kept: Mapping[uuid.UUID, Sequence[int]], rejected: Mapping[uuid.UUID, Sequence[int]]
    ) -> dict[str, Any]:
        """Unfinished Review New Speaker Assignments work, in the saved review's shape, for a draft."""
        return review_new_speaker_assignments_pipeline.build_review(self.new_speaker_proposals(session_id), kept, rejected).model_dump(
            mode="json"
        )

    def new_speaker_assignment_review(
        self, session_id: uuid.UUID, draft: Mapping[str, Any] | None = None
    ) -> review_new_speaker_assignments_pipeline.ReviewData:
        """Process Session's Review New Speaker Assignments step: each new player's proposed utterances,
        with earlier removals when a current review exists."""
        session_folder = self.session_folder(session_id)
        return review_new_speaker_assignments_pipeline.review_data(
            session_folder,
            self.new_speaker_proposals(session_id),
            review_new_speaker_assignments_pipeline.ReviewedNewSpeakerAssignments.model_validate(draft)
            if draft is not None
            else self._current_new_speaker_review(session_id),
            self._settings.speaker_bootstrap.target_total_speech_seconds,
        )

    def extract_new_speaker_review_clips(
        self, session_id: uuid.UUID, indices: Sequence[int], on_progress: Callable[[int, int], None] | None = None
    ) -> None:
        review_new_speaker_assignments_pipeline.extract_clips(self.session_folder(session_id), indices, on_progress)

    def find_more_voice_matches(
        self,
        session_id: uuid.UUID,
        player_id: uuid.UUID,
        kept: Mapping[uuid.UUID, Collection[int]],
        listed: Collection[int],
        rejected: Collection[int],
        *,
        on_progress: find_voice_matches_pipeline.OnProgress | None = None,
    ) -> tuple[review_new_speaker_assignments_pipeline.ReviewUtterance, ...]:
        """Review New Speaker Assignments' Find More: the utterances that sound most like `player_id`'s kept ones,
        with their playback clips extracted. `kept` is every new player's current kept utterances, `listed`
        everything already in any new player's list, and `rejected` this player's removed Find More additions."""
        session_folder = self.session_folder(session_id)
        cache = self._voice_match_embeddings.get(session_id)
        if cache is None or not cache.is_current():
            cache = find_voice_matches_pipeline.VoiceMatchEmbeddings.load(session_folder)
            self._voice_match_embeddings[session_id] = cache
        with Session(self._engine) as session:
            known_voices: list[Embedding] = []
            for attendee in sessions.list_attendance(session, session_id):
                player = session.get(Player, attendee.player_id)
                # A new player seeded by an earlier run has a voice print now, but it must not compete with themselves.
                if player is not None and player.id not in kept:
                    embedding = self._usable_player_embedding(player)
                    if embedding is not None:
                        known_voices.append(embedding)
        added = find_voice_matches_pipeline.find_voice_matches(
            cache,
            find_voice_matches_pipeline.VoiceMatchRequest(
                player_id=player_id,
                kept=kept,
                listed=listed,
                rejected=rejected,
                known_voices=tuple(known_voices),
                min_speech_seconds=self._settings.isolate_new_speakers.find_more_min_speech_seconds,
                target_speech_seconds=self._settings.speaker_bootstrap.target_total_speech_seconds,
            ),
            self._embed_clip,
            on_progress,
        )
        review_new_speaker_assignments_pipeline.extract_more_clips(
            session_folder, added, None if on_progress is None else lambda done, total: on_progress("Preparing clips…", done, total)
        )
        return tuple(
            review_new_speaker_assignments_pipeline.review_utterance(cache.transcript, index, found_by_find_more=True) for index in added
        )

    def new_speaker_review_clip(self, session_id: uuid.UUID, utterance_index: int) -> Path:
        return review_new_speaker_assignments_pipeline.clip_path(self.session_folder(session_id), utterance_index)

    def discard_new_speaker_review_clips(self, session_id: uuid.UUID) -> None:
        review_new_speaker_assignments_pipeline.discard_clips(self.session_folder(session_id))

    def confirm_new_speaker_assignment_review(
        self,
        session_id: uuid.UUID,
        kept: Mapping[uuid.UUID, Sequence[int]],
        rejected: Mapping[uuid.UUID, Sequence[int]] | None = None,
    ) -> bool:
        """Review New Speaker Assignments' decision: the kept utterances and removed Find More additions."""
        reviewed = review_new_speaker_assignments_pipeline.build_review(self.new_speaker_proposals(session_id), kept, rejected)
        self._complete_section(session_id, paths.ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS, reviewed.model_dump(mode="json"))
        return True

    def seed_player_voice_samples(
        self, session_id: uuid.UUID, *, on_progress: seed_voice_samples_pipeline.OnProgress | None = None
    ) -> seed_voice_samples_pipeline.SeededVoiceSamples:
        """Process Session's Seed Player Voice Samples step: cut each reviewed new player's kept utterances into
        clips in their folder, recompute their voice prints, then write the receipt."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = session.get(Campaign, game_session.campaign_id)
            if campaign is None:
                raise ValueError("Campaign not found.")
            session_folder = self._session_folder(session, game_session)
            reviewed = self._current_new_speaker_review(session_id)
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
        # Recorded last: the receipt marks the step complete only once clips and voice prints are saved. Seeding replaces
        # this Session's earlier clips, so a crash before the receipt is repaired by running the step again.
        self._complete_section(session_id, paths.ArtifactName.SEEDED_VOICE_SAMPLES, receipt.model_dump(mode="json"))
        return receipt

    @_completes(paths.ArtifactName.IDENTIFIED_TRANSCRIPT)
    def identify_session_speakers(self, session_id: uuid.UUID, *, on_progress: transcribe_audio.OnProgress | None = None) -> Transcript:
        """Process Session's Identify Speakers step: label each utterance of the name-corrected transcript with the
        attendee whose voice voice print it matches, or leave it unassigned, and write the identified transcript."""
        session_folder = self.session_folder(session_id)
        transcript = Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.NAME_CORRECTED_TRANSCRIPT].filename)
        voice_prints = self.session_player_voice_prints(session_id)
        with widelog.wide_event(
            op="identify_session_speakers",
            session_id=str(session_id),
            reference_count=len(voice_prints),
            utterance_count=len(transcript.utterances),
        ) as log:
            identified = transcribe_audio.identify_raw_transcript(
                session_folder,
                transcript,
                voice_prints,
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
        folder, prior_folders = self._campaign_correction_location(session_id)
        remembered = campaign_corrections.load(folder, prior_folders)
        suggestions: list[suggest_spelling_corrections_pipeline.SpellingSuggestion] = []
        if attendee_names or glossary_terms:
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

        for mapping in remembered:
            occurrences = transcript_review.count_occurrences(transcript, mapping.from_text, mapping.case_sensitive)
            if occurrences:
                suggestions.append(
                    suggest_spelling_corrections_pipeline.SpellingSuggestion(
                        mapping.from_text, mapping.to_text, mapping.case_sensitive, occurrences
                    )
                )
        distinct = {
            (row.from_text if row.case_sensitive else row.from_text.casefold(), row.to_text, row.case_sensitive): row for row in suggestions
        }
        ordered = sorted(distinct.values(), key=lambda row: (row.from_text.casefold(), row.from_text, row.to_text, row.case_sensitive))
        seen_from: set[str] = set()
        combined: list[suggest_spelling_corrections_pipeline.SpellingSuggestion] = []
        for row in ordered:
            key = row.from_text.casefold()
            combined.append(
                suggest_spelling_corrections_pipeline.SpellingSuggestion(
                    row.from_text, row.to_text, row.case_sensitive, row.occurrence_count, key in seen_from
                )
            )
            seen_from.add(key)
        return transcript, combined

    def _campaign_correction_location(self, session_id: uuid.UUID) -> tuple[Path, list[Path]]:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            campaign = campaigns.get_campaign(session, game_session.campaign_id)
            prior = sorted(sessions.list_sessions(session, campaign.id), key=lambda item: item.sequence_number)
            return paths.campaign_folder(self._cwd, campaign.name), [
                paths.session_folder(self._cwd, campaign.name, item.sequence_number) for item in prior
            ]

    def propose_spelling_corrections(self, session_id: uuid.UUID) -> list[suggest_spelling_corrections_pipeline.SpellingSuggestion]:
        """Suggest Spelling Corrections: the LLM's corrections against the campaign glossary, saved for review."""
        _transcript, suggestions = self.suggest_glossary_spelling_corrections(session_id)
        self._complete_section(session_id, paths.ArtifactName.SPELLING_SUGGESTIONS, {"suggestions": _suggestions_value(suggestions)})
        return suggestions

    def spelling_review(
        self, session_id: uuid.UUID
    ) -> tuple[
        Transcript,
        list[suggest_spelling_corrections_pipeline.SpellingSuggestion],
        list[suggest_spelling_corrections_pipeline.SpellingSuggestion] | None,
    ]:
        """Spellcheck Against Glossary's review: the identified transcript, saved suggestions, and last decision."""
        transcript = Transcript.load(self.session_folder(session_id) / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename)
        decisions = self._section(session_id, paths.ArtifactName.SPELLING_DECISIONS)
        return (
            transcript,
            _suggestions_from(self._section(session_id, paths.ArtifactName.SPELLING_SUGGESTIONS), "suggestions"),
            _suggestions_from(decisions, "rows" if isinstance(decisions, dict) and "rows" in decisions else "corrections")
            if decisions is not None
            else None,
        )

    def save_spelling_decisions(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> None:
        folder, prior_folders = self._campaign_correction_location(session_id)
        remembered = campaign_corrections.load(folder, prior_folders)
        previous = self._section(session_id, paths.ArtifactName.SPELLING_DECISIONS)
        previous_rows = previous.get("rows", previous.get("corrections", [])) if isinstance(previous, dict) else []
        previous_active = {campaign_corrections.Mapping.from_dict(row) for row in previous_rows if not row.get("removed", False)}
        rows = [
            {**row, "removed": bool(getattr(correction, "removed", False))}
            for correction in corrections
            for row in [_corrections_value((correction,))[0]]
        ]
        current_active = {campaign_corrections.Mapping.from_dict(row) for row in rows if not row["removed"]}
        removed = previous_active - current_active
        if previous is None:
            proposed = {
                campaign_corrections.Mapping(row.from_text, row.to_text, row.case_sensitive)
                for row in _suggestions_from(self._section(session_id, paths.ArtifactName.SPELLING_SUGGESTIONS), "suggestions")
            }
            removed.update((proposed & remembered) - current_active)
            removed.update(campaign_corrections.Mapping.from_dict(row) for row in rows if row["removed"])
        self._complete_section(
            session_id,
            paths.ArtifactName.SPELLING_DECISIONS,
            {"rows": rows, "corrections": [row for row in rows if not row["removed"]]},
        )
        campaign_corrections.change(folder, prior_folders, add=current_active - previous_active, remove=removed)

    @_completes(paths.ArtifactName.SPELLCHECKED_TRANSCRIPT)
    def apply_spelling_corrections(self, session_id: uuid.UUID) -> int:
        """Write the spellchecked transcript from the saved decision; return how many occurrences were replaced."""
        decisions = self._section(session_id, paths.ArtifactName.SPELLING_DECISIONS)
        if decisions is None:
            raise ValueError("The spelling corrections haven't been reviewed.")
        session_folder = self.session_folder(session_id)
        _written, occurrences = suggest_spelling_corrections_pipeline.save_corrected_transcript(
            Transcript.load(session_folder / paths.ARTIFACTS[paths.ArtifactName.IDENTIFIED_TRANSCRIPT].filename),
            session_folder / paths.ARTIFACTS[paths.ArtifactName.SPELLCHECKED_TRANSCRIPT].filename,
            _suggestions_from(decisions, "corrections"),
            whole_words=False,
            saved_is_current=False,
        )
        return occurrences

    def save_glossary_spelling_corrections(
        self, session_id: uuid.UUID, corrections: Sequence[suggest_spelling_corrections_pipeline.Correction]
    ) -> tuple[bool, int]:
        """Complete Spellcheck Against Glossary and write the spellchecked transcript (decision, then apply)."""
        self.save_spelling_decisions(session_id, corrections)
        return True, self.apply_spelling_corrections(session_id)

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

        self._invalidate_transcript_review_for(session_id, paths.ArtifactName.TRANSCRIPT)
        return transcribe_audio.transcribe_audio(
            session_folder,
            self.session_player_voice_prints(session_id),
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
        processing_state.delete(session_folder)
        # The retired bootstrap workflow kept its working documents here; they are disposable.
        shutil.rmtree(session_folder / "processing", ignore_errors=True)

    @_completes(paths.ArtifactName.ROLE_TRANSCRIPT)
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

    @_completes(paths.ArtifactName.TRANSCRIPT_SECTIONS)
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
                    timeout=self._settings.generate_artifacts.timeout,
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

    @_completes(paths.ArtifactName.LEDGER)
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
                    timeout=self._settings.generate_artifacts.timeout,
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

    @_completes(paths.ArtifactName.PLAYER_INTRODUCTIONS)
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
                    timeout=self._settings.generate_artifacts.timeout,
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

    @_completes(paths.ArtifactName.RECAP_SUMMARY)
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
                    timeout=self._settings.generate_artifacts.timeout,
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

    @_completes(paths.ArtifactName.SUMMARY)
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
                    timeout=self._settings.generate_artifacts.timeout,
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

    # Manual-step drafts: uncompleted work a manual step saved on Cancel.

    def _draft_basis(self, session_id: uuid.UUID, basis: paths.ArtifactName) -> str | None:
        """The fingerprint of what a draft was made against; a draft is valid only while it still matches."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            folder = self._session_folder(session, game_session)
            graph = self._artifact_graph(session, game_session.campaign_id)
        ref = artifact_graph_pipeline.ArtifactRef(folder, basis)
        if graph.status(ref) is not artifact_graph_pipeline.ArtifactStatus.CURRENT:
            return None
        step = artifact_graph_pipeline.BuildStep(basis, (ref,), (ref,))
        fingerprints = artifact_graph_pipeline.current_fingerprints(step, graph.state)
        fingerprint = fingerprints.get(artifact_graph_pipeline.dependency_key(folder, ref))
        return fingerprint.sha256 if fingerprint is not None else None

    def save_step_draft(self, session_id: uuid.UUID, step_id: str, basis: paths.ArtifactName, value: object) -> None:
        """Save a manual step's uncompleted work, tied to `basis` (what the step reviews) as it is now."""
        fingerprint = self._draft_basis(session_id, basis)
        if fingerprint is None:
            raise ValueError(f"{paths.ARTIFACTS[basis].display_name} isn't current, so this work can't be saved as a draft.")

        def apply(state: processing_state.ProcessingState) -> None:
            state.drafts[step_id] = {"basis": basis.value, "basis_sha256": fingerprint, "value": value}

        processing_state.update(self.session_folder(session_id), apply, reason="draft_saved")

    def load_step_draft(self, session_id: uuid.UUID, step_id: str) -> Any:
        """A manual step's saved draft, or None when there is none or what it was made against has changed."""
        draft = processing_state.load(self.session_folder(session_id)).drafts.get(step_id)
        if not isinstance(draft, dict):
            return None
        try:
            basis = paths.ArtifactName(draft.get("basis"))
        except ValueError:
            return None
        if self._draft_basis(session_id, basis) != draft.get("basis_sha256"):
            return None
        return draft.get("value")

    def discard_step_draft(self, session_id: uuid.UUID, step_id: str) -> None:
        def apply(state: processing_state.ProcessingState) -> None:
            state.drafts.pop(step_id, None)

        processing_state.update(self.session_folder(session_id), apply, reason="draft_discarded")

    def save_review_draft(self, session_id: uuid.UUID, transcript: Transcript | transcript_review.ReviewDecision) -> None:
        """Review Transcript's draft: the reviewer's unfinished edits, as an edit list."""
        inputs = self._transcript_review_inputs(session_id)
        if inputs is None:
            raise ValueError("Transcript review inputs aren't current, so this work can't be saved as a draft.")
        decision = transcript if isinstance(transcript, transcript_review.ReviewDecision) else transcript_review.ReviewDecision(transcript)
        edits = transcript_edits_pipeline.diff(self.transcript_review_source(session_id), decision.transcript)
        value = {
            **edits.model_dump(mode="json"),
            "review_inputs": inputs,
            "removed_indices": list(decision.removed_indices),
            "find_replacements": [mapping.as_dict() for mapping in decision.find_replacements],
        }
        self.save_step_draft(session_id, _REVIEW_TRANSCRIPT_STEP, paths.ArtifactName.SPELLCHECKED_TRANSCRIPT, value)

    def load_review_draft(self, session_id: uuid.UUID) -> transcript_review.ReviewDecision | None:
        inputs = self._transcript_review_inputs(session_id)
        if inputs is None:
            return None
        value = self.load_step_draft(session_id, _REVIEW_TRANSCRIPT_STEP)
        if not isinstance(value, dict) or value.get("review_inputs") != inputs:
            if _REVIEW_TRANSCRIPT_STEP in processing_state.load(self.session_folder(session_id)).drafts:
                self.discard_review_draft(session_id)
            return None
        try:
            edits = transcript_edits_pipeline.TranscriptEdits.model_validate(value)
        except ValueError:
            return None
        return transcript_review.ReviewDecision(
            transcript_edits_pipeline.apply(self.transcript_review_source(session_id), edits),
            tuple(value.get("removed_indices", ())),
            tuple(campaign_corrections.Mapping.from_dict(row) for row in value.get("find_replacements", ())),
        )

    def discard_review_draft(self, session_id: uuid.UUID) -> None:
        self.discard_step_draft(session_id, _REVIEW_TRANSCRIPT_STEP)

    def clear_session_processing_state(self, session_id: uuid.UUID) -> None:
        """Remove a Session's retired Process-flow metadata and every manual-step draft."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            session_folder = self._session_folder(session, game_session)
            session_processing_entities.delete_state(session, session_id)
            session.commit()
        session_processing_pipeline.discard_review_draft(session_folder)

        def apply(state: processing_state.ProcessingState) -> None:
            state.drafts.clear()

        processing_state.update(session_folder, apply, reason="drafts_cleared")

    # Manual review.

    def extract_review_clips(self, session_id: uuid.UUID, on_progress: Callable[[int, int], None] | None = None) -> tuple[Transcript, Path]:
        """Review Transcript's source (the spellchecked transcript) with a playback clip per utterance."""
        return transcript_review.extract_review_clips(
            self.session_folder(session_id), on_progress, source=paths.ArtifactName.SPELLCHECKED_TRANSCRIPT
        )

    def discard_review_clips(self, session_id: uuid.UUID) -> None:
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            transcript_review.discard_review_clips(self._session_folder(session, game_session))

    def transcript_review_source(self, session_id: uuid.UUID) -> Transcript:
        """What Review Transcript edits: the spellchecked transcript."""
        return Transcript.load(self.session_folder(session_id) / paths.ARTIFACTS[paths.ArtifactName.SPELLCHECKED_TRANSCRIPT].filename)

    @staticmethod
    def _clear_transcript_review(state: processing_state.ProcessingState) -> None:
        """Discard incompatible review work; no later rebuild can make it valid again."""
        state.drafts.pop(_REVIEW_TRANSCRIPT_STEP, None)
        name = paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS.value
        state.sections.pop(name, None)
        state.records.pop(name, None)

    def _discard_transcript_review(self, session_id: uuid.UUID) -> None:
        folder = self.session_folder(session_id)
        state = processing_state.load(folder)
        name = paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS.value
        if _REVIEW_TRANSCRIPT_STEP in state.drafts or name in state.sections or name in state.records:
            processing_state.update(folder, self._clear_transcript_review, reason="transcript_review_invalidated")

    def _invalidate_transcript_review_for(self, session_id: uuid.UUID, *names: paths.ArtifactName) -> None:
        """Upstream restarts and producers invalidate review work even when they recreate identical content."""
        folder = self.session_folder(session_id)
        steps = self._session_steps(folder)
        producers = {
            output.name: step for step in steps for output in step.outputs if isinstance(output, artifact_graph_pipeline.ArtifactRef)
        }
        upstream: set[paths.ArtifactName] = set()

        def visit(name: paths.ArtifactName) -> None:
            step = producers.get(name)
            if step is None:
                return
            for dependency in step.dependencies:
                if isinstance(dependency, artifact_graph_pipeline.ArtifactRef) and dependency.name not in upstream:
                    upstream.add(dependency.name)
                    visit(dependency.name)

        visit(paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS)
        if upstream.intersection(names):
            self._discard_transcript_review(session_id)

    def _transcript_review_inputs(self, session_id: uuid.UUID) -> dict[str, str] | None:
        """Validate review dependencies, independently of the review's own reopened completion flag."""
        with Session(self._engine) as session:
            game_session = sessions.get_session(session, session_id)
            folder = self._session_folder(session, game_session)
            graph = self._artifact_graph(session, game_session.campaign_id)
        ref = artifact_graph_pipeline.ArtifactRef(folder, paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS)
        step = graph.step_for(ref)
        if step is None:
            self._discard_transcript_review(session_id)
            return None
        if any(
            graph.status(dependency) is not artifact_graph_pipeline.ArtifactStatus.CURRENT
            for dependency in step.dependencies
            if isinstance(dependency, artifact_graph_pipeline.ArtifactRef)
        ):
            self._discard_transcript_review(session_id)
            return None
        inputs = {key: fingerprint.sha256 for key, fingerprint in artifact_graph_pipeline.current_fingerprints(step, graph.state).items()}
        state = graph.state(folder)
        record = state.records.get(paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS.value)
        if paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS.value in state.sections and (
            record is None or any(record.inputs.get(key) is None or record.inputs[key].sha256 != value for key, value in inputs.items())
        ):
            self._discard_transcript_review(session_id)
        return inputs

    def saved_transcript_review(self, session_id: uuid.UUID) -> transcript_review.ReviewDecision | None:
        """The last completed review applied to the current source, to reopen the step as it was left."""
        if self._transcript_review_inputs(session_id) is None:
            return None
        value = self._section(session_id, paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS)
        if value is None:
            return None
        edits = transcript_edits_pipeline.TranscriptEdits.model_validate({"edits": value.get("edits", [])})
        return transcript_review.ReviewDecision(
            transcript_edits_pipeline.apply(self.transcript_review_source(session_id), edits),
            tuple(value.get("removed_indices", ())),
            tuple(campaign_corrections.Mapping.from_dict(row) for row in value.get("find_replacements", ())),
        )

    def save_transcript_review(self, session_id: uuid.UUID, transcript: Transcript | transcript_review.ReviewDecision) -> None:
        """Review Transcript's decision: the reviewer's edits to the spellchecked transcript."""
        if self._transcript_review_inputs(session_id) is None:
            raise ValueError("Transcript review inputs aren't current, so this review can't be completed.")
        decision = transcript if isinstance(transcript, transcript_review.ReviewDecision) else transcript_review.ReviewDecision(transcript)
        previous = self._section(session_id, paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS)
        old_replacements = (
            {campaign_corrections.Mapping.from_dict(row) for row in previous.get("find_replacements", ())}
            if isinstance(previous, dict)
            else set()
        )
        edits = transcript_edits_pipeline.diff(self.transcript_review_source(session_id), decision.transcript)
        value = {
            **edits.model_dump(mode="json"),
            "removed_indices": list(decision.removed_indices),
            "find_replacements": [mapping.as_dict() for mapping in decision.find_replacements],
        }
        self._complete_section(session_id, paths.ArtifactName.TRANSCRIPT_REVIEW_EDITS, value)
        new_replacements = set(decision.find_replacements) - old_replacements
        if new_replacements:
            folder, prior_folders = self._campaign_correction_location(session_id)
            campaign_corrections.change(folder, prior_folders, add=new_replacements)
        self.discard_review_draft(session_id)

    @_completes(paths.ArtifactName.REVIEWED_TRANSCRIPT)
    def apply_transcript_review(self, session_id: uuid.UUID) -> None:
        """Write `transcript_reviewed.json`: the spellchecked transcript with the saved review edits applied."""
        reviewed = self.saved_transcript_review(session_id)
        if reviewed is None:
            raise ValueError("The transcript review hasn't been completed.")
        transcript_review.save_reviewed_transcript(self.session_folder(session_id), reviewed.kept_transcript())

    def save_reviewed_transcript(self, session_id: uuid.UUID, transcript: Transcript | transcript_review.ReviewDecision) -> None:
        """Complete Review Transcript and write the reviewed transcript (decision, then apply)."""
        self.save_transcript_review(session_id, transcript)
        self.apply_transcript_review(session_id)

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
