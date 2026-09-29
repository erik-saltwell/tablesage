from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ArtifactName(Enum):
    """Every artifact a session folder can hold and the identity used by the build graph."""

    INPUT_AUDIO = "input_audio"
    NORMALIZED_REVIEW_AUDIO = "normalized_review_audio"
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
    # Sections of `processing_state.json` (see `ArtifactStorage.SECTION`).
    IMPORT_REQUEST = "import_request"
    NAME_CORRECTION_SUGGESTIONS = "name_correction_suggestions"
    NAME_CORRECTION_DECISIONS = "name_correction_decisions"
    GLOSSARY_SUGGESTIONS = "glossary_suggestions"
    GLOSSARY_DECISIONS = "glossary_decisions"
    SPELLING_SUGGESTIONS = "spelling_suggestions"
    SPELLING_DECISIONS = "spelling_decisions"
    TRANSCRIPT_REVIEW_EDITS = "transcript_review_edits"
    VOICE_PROFILE_DECISION = "voice_profile_decision"
    VOICE_PROFILE_ENHANCEMENT = "voice_profile_enhancement"


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


class ArtifactStorage(Enum):
    """Where an artifact lives. A FILE is a document a person reads or exports, or a tool outside the pipeline
    consumes. Everything else -- decisions, suggestions, receipts -- is a SECTION of the Session's
    `processing_state.json`; a SECTION's `filename`, when set, is only the legacy file it was imported from."""

    FILE = "file"
    SECTION = "section"


@dataclass(frozen=True)
class ArtifactSpec:
    filename: str
    category: ArtifactCategory
    should_show_in_ui: bool
    display_name: str
    companion_filenames: tuple[str, ...] = ()
    storage: ArtifactStorage = ArtifactStorage.FILE

    @property
    def is_file(self) -> bool:
        return self.storage is ArtifactStorage.FILE


def _section(display_name: str, legacy_filename: str = "") -> ArtifactSpec:
    return ArtifactSpec(
        legacy_filename,
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name=display_name,
        storage=ArtifactStorage.SECTION,
    )


# Fixed filenames within a session folder -- the filesystem is the only
# source of truth for artifact existence, there is no `session_artifact`
# table.
#
# Order here is pipeline order, and drives both the indicator panel's layout
# and `should_show_in_ui`'s filtering -- entries stay in this order whether
# or not they're shown.
LEDGER_PAIR_MARKER = ".ledger-generation-incomplete"
AUDIO_PAIR_MARKER = ".audio-import-incomplete"
SUMMARY_INPUTS_FILENAME = ".summary-inputs.json"

ARTIFACTS: dict[ArtifactName, ArtifactSpec] = {
    # The Import Audio step's decision: the chosen file and whether to clean it.
    ArtifactName.IMPORT_REQUEST: _section("Import Request"),
    ArtifactName.INPUT_AUDIO: ArtifactSpec(
        "input_audio.wav",
        ArtifactCategory.IMPORTED,
        should_show_in_ui=True,
        display_name="Input Audio",
    ),
    ArtifactName.NORMALIZED_REVIEW_AUDIO: ArtifactSpec(
        "normalized_review_audio.wav",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=False,
        display_name="Normalized Review Audio",
    ),
    ArtifactName.TRANSCRIPT: ArtifactSpec(
        "transcript.json",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=False,
        display_name="Transcript (JSON)",
    ),
    ArtifactName.TRANSCRIPT_TEXT: ArtifactSpec(
        "transcript.md",
        ArtifactCategory.FROM_AUDIO,
        should_show_in_ui=True,
        display_name="Transcript",
    ),
    # A cleaned copy of the transcript with backchannels and other bad utterances removed.
    ArtifactName.CLEANED_TRANSCRIPT: ArtifactSpec(
        "cleaned_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Cleaned Transcript",
    ),
    # The cleaned transcript with reviewed player- and character-name corrections applied; the base
    # transcript for every later step. Same utterances as the cleaned transcript, so indices match.
    ArtifactName.NAME_CORRECTION_SUGGESTIONS: _section("Name Correction Suggestions"),
    ArtifactName.NAME_CORRECTION_DECISIONS: _section("Name Correction Decisions"),
    ArtifactName.NAME_CORRECTED_TRANSCRIPT: ArtifactSpec(
        "name_corrected_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Name-Corrected Transcript",
    ),
    # For each new speaker, the high-confidence utterances (indices into the name-corrected transcript), as first proposed.
    ArtifactName.NEW_SPEAKER_ASSIGNMENTS: _section("New Speaker Assignments", legacy_filename="new_speaker_assignments.json"),
    # The new-speaker assignments after human review.
    ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS: _section(
        "Reviewed New Speaker Assignments",
        legacy_filename="reviewed_new_speaker_assignments.json",
    ),
    # Receipt of the voice clips seeded into each new player's folder from the reviewed assignments.
    # Seeding itself changes player folders and voice prints; this file is the step's completion marker.
    ArtifactName.SEEDED_VOICE_SAMPLES: _section("Seeded Voice Samples", legacy_filename="seeded_voice_samples.json"),
    # The name-corrected transcript with each utterance's speaker identified by voice voice print (or
    # left unassigned). Same utterances as the name-corrected transcript.
    ArtifactName.IDENTIFIED_TRANSCRIPT: ArtifactSpec(
        "identified_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Identified Transcript",
    ),
    # Receipt of the glossary entries the reviewed Extract Glossary Terms step added to the campaign.
    # The entries themselves live in the database, which the artifact graph can't see; this file is the
    # step's completion marker, so spellchecking reruns only when this Session's extraction adds terms.
    ArtifactName.GLOSSARY_SUGGESTIONS: _section("Glossary Suggestions"),
    ArtifactName.GLOSSARY_DECISIONS: _section("Glossary Decisions"),
    ArtifactName.EXTRACTED_GLOSSARY_TERMS: _section("Extracted Glossary Terms", legacy_filename="extracted_glossary_terms.json"),
    # The transcript after glossary spellchecking replacements.
    ArtifactName.SPELLING_SUGGESTIONS: _section("Spelling Suggestions"),
    ArtifactName.SPELLING_DECISIONS: _section("Spelling Decisions"),
    ArtifactName.SPELLCHECKED_TRANSCRIPT: ArtifactSpec(
        "spellchecked_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Spellchecked Transcript",
    ),
    # A completed Manual Review. It is deliberately separate from the machine-produced
    # transcript and becomes stale whenever that source transcript is rebuilt or the audio
    # (or attendance that influences speaker identification) changes.
    ArtifactName.TRANSCRIPT_REVIEW_EDITS: _section("Transcript Review Edits"),
    ArtifactName.REVIEWED_TRANSCRIPT: ArtifactSpec(
        "transcript_reviewed.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Reviewed Transcript",
    ),
    # Role-attributed transcript written by the Assign Roles step (see
    # `session_pipeline.clean_transcript`). Ledger generation reads this directly instead of
    # rendering its own role-attributed text.
    ArtifactName.ROLE_TRANSCRIPT: ArtifactSpec(
        "role_transcript.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Role Transcript",
    ),
    ArtifactName.TRANSCRIPT_SECTIONS: ArtifactSpec(
        "transcript_sections.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Transcript Sections",
    ),
    ArtifactName.LEDGER: ArtifactSpec(
        "ledger.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=True,
        display_name="Ledger",
        companion_filenames=("ledger.md",),
    ),
    ArtifactName.SCENE_BREAKDOWN: ArtifactSpec(
        "scene_breakdown.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Scene Breakdown",
    ),
    ArtifactName.PLAYER_INTRODUCTIONS: ArtifactSpec(
        "player_introductions.json",
        ArtifactCategory.FROM_TRANSCRIPT,
        should_show_in_ui=False,
        display_name="Player Introductions",
    ),
    ArtifactName.RECAP_SUMMARY: ArtifactSpec(
        "recap_summary.md",
        ArtifactCategory.FROM_LOG,
        should_show_in_ui=True,
        display_name="Recap Summary",
    ),
    ArtifactName.SUMMARY: ArtifactSpec(
        "summary.md",
        ArtifactCategory.FROM_LOG,
        should_show_in_ui=True,
        display_name="Summary",
        companion_filenames=(SUMMARY_INPUTS_FILENAME,),
    ),
    # The post-generation offer to add this Session's voice clips to its players' profiles, and its receipt.
    ArtifactName.VOICE_PROFILE_DECISION: _section("Voice Profile Decision"),
    ArtifactName.VOICE_PROFILE_ENHANCEMENT: _section("Voice Profile Enhancement"),
}


FILE_ARTIFACTS: tuple[ArtifactName, ...] = tuple(name for name, spec in ARTIFACTS.items() if spec.is_file)
