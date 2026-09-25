from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum


class SessionProcessingStageID(IntEnum):
    IMPORTING_AUDIO = 20
    CREATING_TRANSCRIPTION = 30
    REMOVE_BACKCHANNELS = 40
    REVIEWING_NAME_CORRECTIONS = 45
    ISOLATING_NEW_SPEAKERS = 50
    REVIEWING_NEW_SPEAKER_ASSIGNMENTS = 60
    SEEDING_PLAYER_VOICE_SAMPLES = 70
    IDENTIFYING_SPEAKERS = 75
    EXTRACTING_GLOSSARY_TERMS = 78
    SPELLCHECKING_GLOSSARY = 80
    REVIEWING_TRANSCRIPT = 90
    ASSIGN_ROLES_TO_SPEAKERS = 100
    GENERATING_ARTIFACTS = 110


@dataclass(frozen=True, order=True)
class SessionProcessingStage:
    id: SessionProcessingStageID
    action: str = field(compare=False)
    binding: str | None = field(compare=False, default=None)
    # Credentials the step needs, checked before a processing run that includes it starts.
    llm_roles: tuple[str, ...] = field(compare=False, default=())
    needs_transcription: bool = field(compare=False, default=False)

    @property
    def has_manual_processing(self) -> bool:
        return self.binding is not None


_stages: list[SessionProcessingStage] = [
    SessionProcessingStage(id=SessionProcessingStageID.IMPORTING_AUDIO, action="Import Audio", binding="1"),
    SessionProcessingStage(id=SessionProcessingStageID.CREATING_TRANSCRIPTION, action="Create Transcript", needs_transcription=True),
    SessionProcessingStage(id=SessionProcessingStageID.REMOVE_BACKCHANNELS, action="Remove Bad Utterances", llm_roles=("llm_model_lite",)),
    SessionProcessingStage(
        id=SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS, action="Review Name Corrections", binding="2", llm_roles=("llm_model",)
    ),
    SessionProcessingStage(id=SessionProcessingStageID.ISOLATING_NEW_SPEAKERS, action="Isolate New Speakers", llm_roles=("llm_model",)),
    SessionProcessingStage(
        id=SessionProcessingStageID.REVIEWING_NEW_SPEAKER_ASSIGNMENTS, action="Review New Speaker Assignments", binding="3"
    ),
    SessionProcessingStage(id=SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES, action="Seed Player Voice Samples"),
    SessionProcessingStage(id=SessionProcessingStageID.IDENTIFYING_SPEAKERS, action="Identify Speakers"),
    SessionProcessingStage(
        id=SessionProcessingStageID.EXTRACTING_GLOSSARY_TERMS, action="Extract Glossary Terms", binding="4", llm_roles=("llm_model",)
    ),
    SessionProcessingStage(
        id=SessionProcessingStageID.SPELLCHECKING_GLOSSARY, action="Spellcheck Against Glossary", binding="5", llm_roles=("llm_model",)
    ),
    SessionProcessingStage(id=SessionProcessingStageID.REVIEWING_TRANSCRIPT, action="Review Transcript", binding="6"),
    SessionProcessingStage(id=SessionProcessingStageID.ASSIGN_ROLES_TO_SPEAKERS, action="Assign Roles To Players"),
    SessionProcessingStage(
        id=SessionProcessingStageID.GENERATING_ARTIFACTS, action="Generate Artifacts", binding="7", llm_roles=("llm_model_high",)
    ),
]


def get_processing_stages() -> list[SessionProcessingStage]:
    return sorted(_stages)


# Steps that only matter when the Session has new players (attendees with no usable voice profile).
# With none, Process Session shows them as skipped; continuing still completes each with an empty or
# unchanged output, so every downstream artifact exists.
NEW_PLAYER_STAGES: frozenset[SessionProcessingStageID] = frozenset(
    {
        SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS,
        SessionProcessingStageID.ISOLATING_NEW_SPEAKERS,
        SessionProcessingStageID.REVIEWING_NEW_SPEAKER_ASSIGNMENTS,
        SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES,
    }
)


@dataclass(frozen=True)
class ProcessingBlocker:
    """An error that prevents a step, and every step after it, from running."""

    stage: SessionProcessingStageID
    message: str
