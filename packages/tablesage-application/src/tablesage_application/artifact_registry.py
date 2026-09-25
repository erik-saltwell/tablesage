from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .processing_stages import SessionProcessingStageID


class ArtifactName(Enum):
    """Every artifact a session folder can hold and the identity used by the build graph."""

    INPUT_AUDIO = "input_audio"
    NEW_SPEAKER_ASSIGNMENTS = "new_speaker_assignments"
    CLEANED_TRANSCRIPT = "cleaned_transcript"
    NAME_CORRECTED_TRANSCRIPT = "name_corrected_transcript"
    REVIEWED_NEW_SPEAKER_ASSIGNMENTS = "reviewed_new_speaker_assignments"
    SEEDED_VOICE_SAMPLES = "seeded_voice_samples"
    IDENTIFIED_TRANSCRIPT = "identified_transcript"
    EXTRACTED_GLOSSARY_TERMS = "extracted_glossary_terms"
    SPELLCHECKED_TRANSCRIPT = "spellchecked_transcript"
    LEDGER = "ledger"
    SCENE_BREAKDOWN = "scene_breakdown"
    SUMMARY = "summary"
    TRANSCRIPT = "transcript"
    TRANSCRIPT_TEXT = "transcript_text"
    REVIEWED_TRANSCRIPT = "reviewed_transcript"
    ROLE_TRANSCRIPT = "role_transcript"
    TRANSCRIPT_SECTIONS = "transcript_sections"
    PLAYER_INTRODUCTIONS = "player_introductions"
    RECAP_SUMMARY = "recap_summary"


class ArtifactCategory(Enum):
    """How an artifact is produced, retained for grouping and destructive Clean Session behavior.

    IMPORTED artifacts are sources rather than derivatives. FROM_AUDIO
    artifacts are derived (directly or transitively) from the input audio. FROM_TRANSCRIPT
    artifacts are derived from the current transcript. FROM_LOG artifacts are derived from
    Ledger or Scene Breakdown outputs.
    """

    IMPORTED = "imported"
    FROM_AUDIO = "from_audio"
    FROM_TRANSCRIPT = "from_transcript"
    FROM_LOG = "from_log"


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    category: ArtifactCategory
    should_show_in_ui: bool
    display_name: str
    stage: SessionProcessingStageID
    companion_filenames: tuple[str, ...] = ()


# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table.
#
# Order here is pipeline order, and drives both the indicator panel's layout
# and `should_show_in_ui`'s filtering -- entries stay in this order whether
# or not they're shown.
LEDGER_PAIR_MARKER = ".ledger-generation-incomplete"
SUMMARY_INPUTS_FILENAME = ".summary-inputs.json"

ARTIFACTS: dict[ArtifactName, ArtifactSpec] = {
    ArtifactName.INPUT_AUDIO: ArtifactSpec(
        "input_audio.wav",
        ArtifactCategory.IMPORTED,
        should_show_in_ui=True,
        display_name="Input Audio",
        stage=SessionProcessingStageID.IMPORTING_AUDIO,
    ),
    ArtifactName.TRANSCRIPT: ArtifactSpec(
        "transcript.json",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=False,
        display_name="Transcript (JSON)",
        stage=SessionProcessingStageID.CREATING_TRANSCRIPTION,
    ),
    ArtifactName.TRANSCRIPT_TEXT: ArtifactSpec(
        "transcript.md",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=True,
        display_name="Transcript",
        stage=SessionProcessingStageID.CREATING_TRANSCRIPTION,
    ),
    # A cleaned copy of the transcript with backchannels and other bad utterances removed.
    ArtifactName.CLEANED_TRANSCRIPT: ArtifactSpec(
        "cleaned_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Cleaned Transcript",
        stage=SessionProcessingStageID.REMOVE_BACKCHANNELS,
    ),
    # The cleaned transcript with reviewed player- and character-name corrections applied; the base
    # transcript for every later step. Same utterances as the cleaned transcript, so indices match.
    ArtifactName.NAME_CORRECTED_TRANSCRIPT: ArtifactSpec(
        "name_corrected_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Name-Corrected Transcript",
        stage=SessionProcessingStageID.REVIEWING_NAME_CORRECTIONS,
    ),
    # For each new speaker, the high-confidence utterances (indices into the name-corrected transcript), as first proposed.
    ArtifactName.NEW_SPEAKER_ASSIGNMENTS: ArtifactSpec(
        "new_speaker_assignments.json",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=False,
        display_name="New Speaker Assignments",
        stage=SessionProcessingStageID.ISOLATING_NEW_SPEAKERS,
    ),
    # The new-speaker assignments after human review.
    ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS: ArtifactSpec(
        "reviewed_new_speaker_assignments.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Reviewed New Speaker Assignments",
        stage=SessionProcessingStageID.REVIEWING_NEW_SPEAKER_ASSIGNMENTS,
    ),
    # Receipt of the voice clips seeded into each new player's folder from the reviewed assignments.
    # Seeding itself changes player folders and centroids; this file is the step's completion marker.
    ArtifactName.SEEDED_VOICE_SAMPLES: ArtifactSpec(
        "seeded_voice_samples.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Seeded Voice Samples",
        stage=SessionProcessingStageID.SEEDING_PLAYER_VOICE_SAMPLES,
    ),
    # The name-corrected transcript with each utterance's speaker identified by voice centroid (or
    # left unassigned). Same utterances as the name-corrected transcript.
    ArtifactName.IDENTIFIED_TRANSCRIPT: ArtifactSpec(
        "identified_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Identified Transcript",
        stage=SessionProcessingStageID.IDENTIFYING_SPEAKERS,
    ),
    # Receipt of the glossary entries the reviewed Extract Glossary Terms step added to the campaign.
    # The entries themselves live in the database, which the artifact graph can't see; this file is the
    # step's completion marker, so spellchecking reruns only when this Session's extraction adds terms.
    ArtifactName.EXTRACTED_GLOSSARY_TERMS: ArtifactSpec(
        "extracted_glossary_terms.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Extracted Glossary Terms",
        stage=SessionProcessingStageID.EXTRACTING_GLOSSARY_TERMS,
    ),
    # The transcript after glossary spellchecking replacements.
    ArtifactName.SPELLCHECKED_TRANSCRIPT: ArtifactSpec(
        "spellchecked_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Spellchecked Transcript",
        stage=SessionProcessingStageID.SPELLCHECKING_GLOSSARY,
    ),
    # A completed Manual Review. It is deliberately separate from the machine-produced
    # transcript and becomes stale whenever that source transcript is rebuilt or the audio
    # (or attendance that influences speaker identification) changes.
    ArtifactName.REVIEWED_TRANSCRIPT: ArtifactSpec(
        "transcript_reviewed.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Reviewed Transcript",
        stage=SessionProcessingStageID.REVIEWING_TRANSCRIPT,
    ),
    # Role-attributed transcript written by the Assign Roles step (see
    # `session_pipeline.clean_transcript`). Ledger generation reads this directly instead of
    # rendering its own role-attributed text.
    ArtifactName.ROLE_TRANSCRIPT: ArtifactSpec(
        "role_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Role Transcript",
        stage=SessionProcessingStageID.ASSIGN_ROLES_TO_SPEAKERS,
    ),
    ArtifactName.TRANSCRIPT_SECTIONS: ArtifactSpec(
        "transcript_sections.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Transcript Sections",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
    ),
    ArtifactName.LEDGER: ArtifactSpec(
        "ledger.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Ledger",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
        companion_filenames=("ledger.md",),
    ),
    ArtifactName.SCENE_BREAKDOWN: ArtifactSpec(
        "scene_breakdown.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Scene Breakdown",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
    ),
    ArtifactName.PLAYER_INTRODUCTIONS: ArtifactSpec(
        "player_introductions.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Player Introductions",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
    ),
    ArtifactName.RECAP_SUMMARY: ArtifactSpec(
        "recap_summary.md",
        ArtifactCategory.FROM_LOG,
        should_show_in_ui=True,
        display_name="Recap Summary",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
    ),
    ArtifactName.SUMMARY: ArtifactSpec(
        "summary.md",
        ArtifactCategory.FROM_LOG,
        should_show_in_ui=True,
        display_name="Summary",
        stage=SessionProcessingStageID.GENERATING_ARTIFACTS,
        companion_filenames=(SUMMARY_INPUTS_FILENAME,),
    ),
}


def artifacts_for_stage(stage: SessionProcessingStageID) -> list[ArtifactName]:
    """Every artifact produced by `stage`, in registry (pipeline) order."""
    return [name for name, spec in ARTIFACTS.items() if spec.stage == stage]
