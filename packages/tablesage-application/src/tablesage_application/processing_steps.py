"""Session processing's steps: one ordered list of manual and automatic processing steps.

A manual step shows a screen other than a progress dialog and records only a decision (a processing-state
section). An automatic step runs behind a progress dialog and produces documents or results. A step is
complete when every artifact it produces is current (see `artifact_graph`); the Approve Prior-Session Rebuild
step, which produces no artifact, is complete when its saved approval covers the current rebuild plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .artifact_registry import ArtifactName


class StepKind(StrEnum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"


class StepVisibility(StrEnum):
    """When Process Session draws a manual step's row. Display only: the coordinator never reads it."""

    ALWAYS = "always"
    # Only when the Session has new players (before Isolate New Speakers runs, the attendee list decides; after,
    # its recorded proposals do).
    NEW_PLAYERS = "new_players"
    # Only when generating this Session's outputs would rebuild earlier Sessions.
    PRIOR_REBUILD = "prior_rebuild"


class StepID(StrEnum):
    IMPORT_AUDIO = "import_audio"
    IMPORT_AUDIO_FILE = "import_audio_file"
    CREATE_TRANSCRIPT = "create_transcript"
    REMOVE_BACKCHANNELS = "remove_backchannels"
    SUGGEST_NAME_CORRECTIONS = "suggest_name_corrections"
    REVIEW_NAME_CORRECTIONS = "review_name_corrections"
    APPLY_NAME_CORRECTIONS = "apply_name_corrections"
    ISOLATE_NEW_SPEAKERS = "isolate_new_speakers"
    REVIEW_NEW_SPEAKER_ASSIGNMENTS = "review_new_speaker_assignments"
    SEED_VOICE_SAMPLES = "seed_voice_samples"
    IDENTIFY_SPEAKERS = "identify_speakers"
    SUGGEST_GLOSSARY_TERMS = "suggest_glossary_terms"
    REVIEW_GLOSSARY_TERMS = "review_glossary_terms"
    ADD_GLOSSARY_ENTRIES = "add_glossary_entries"
    SUGGEST_SPELLING_CORRECTIONS = "suggest_spelling_corrections"
    REVIEW_SPELLING_CORRECTIONS = "review_spelling_corrections"
    APPLY_SPELLING_CORRECTIONS = "apply_spelling_corrections"
    REVIEW_TRANSCRIPT = "review_transcript"
    APPLY_TRANSCRIPT_REVIEW = "apply_transcript_review"
    ASSIGN_ROLES = "assign_roles"
    APPROVE_PRIOR_REBUILD = "approve_prior_rebuild"
    GENERATE_ARTIFACTS = "generate_artifacts"
    IMPROVE_VOICE_PROFILES = "improve_voice_profiles"
    ENHANCE_VOICE_PROFILES = "enhance_voice_profiles"


@dataclass(frozen=True)
class ProcessingStep:
    id: StepID
    kind: StepKind
    label: str
    outputs: tuple[ArtifactName, ...]
    visibility: StepVisibility = StepVisibility.ALWAYS
    # Credentials a run including this step needs, checked before that run starts.
    llm_roles: tuple[str, ...] = ()
    needs_transcription: bool = False

    @property
    def is_manual(self) -> bool:
        return self.kind is StepKind.MANUAL


_M = StepKind.MANUAL
_A = StepKind.AUTOMATIC

PROCESSING_STEPS: tuple[ProcessingStep, ...] = (
    ProcessingStep(StepID.IMPORT_AUDIO, _M, "Import Audio", (ArtifactName.IMPORT_REQUEST,)),
    ProcessingStep(StepID.IMPORT_AUDIO_FILE, _A, "Import Audio File", (ArtifactName.INPUT_AUDIO, ArtifactName.NORMALIZED_REVIEW_AUDIO)),
    ProcessingStep(
        StepID.CREATE_TRANSCRIPT,
        _A,
        "Create Transcript",
        (ArtifactName.TRANSCRIPT, ArtifactName.TRANSCRIPT_TEXT),
        needs_transcription=True,
    ),
    ProcessingStep(
        StepID.REMOVE_BACKCHANNELS, _A, "Remove Bad Utterances", (ArtifactName.CLEANED_TRANSCRIPT,), llm_roles=("llm_model_lite",)
    ),
    ProcessingStep(
        StepID.SUGGEST_NAME_CORRECTIONS,
        _A,
        "Suggest Name Corrections",
        (ArtifactName.NAME_CORRECTION_SUGGESTIONS,),
        visibility=StepVisibility.NEW_PLAYERS,
        llm_roles=("llm_model",),
    ),
    ProcessingStep(
        StepID.REVIEW_NAME_CORRECTIONS,
        _M,
        "Review Name Corrections",
        (ArtifactName.NAME_CORRECTION_DECISIONS,),
        visibility=StepVisibility.NEW_PLAYERS,
    ),
    ProcessingStep(
        StepID.APPLY_NAME_CORRECTIONS,
        _A,
        "Apply Name Corrections",
        (ArtifactName.NAME_CORRECTED_TRANSCRIPT,),
        visibility=StepVisibility.NEW_PLAYERS,
    ),
    ProcessingStep(
        StepID.ISOLATE_NEW_SPEAKERS,
        _A,
        "Isolate New Speakers",
        (ArtifactName.NEW_SPEAKER_ASSIGNMENTS,),
        visibility=StepVisibility.NEW_PLAYERS,
        llm_roles=("llm_model",),
    ),
    ProcessingStep(
        StepID.REVIEW_NEW_SPEAKER_ASSIGNMENTS,
        _M,
        "Review New Speaker Assignments",
        (ArtifactName.REVIEWED_NEW_SPEAKER_ASSIGNMENTS,),
        visibility=StepVisibility.NEW_PLAYERS,
    ),
    ProcessingStep(
        StepID.SEED_VOICE_SAMPLES,
        _A,
        "Seed Player Voice Samples",
        (ArtifactName.SEEDED_VOICE_SAMPLES,),
        visibility=StepVisibility.NEW_PLAYERS,
    ),
    ProcessingStep(StepID.IDENTIFY_SPEAKERS, _A, "Identify Speakers", (ArtifactName.IDENTIFIED_TRANSCRIPT,)),
    ProcessingStep(
        StepID.SUGGEST_GLOSSARY_TERMS, _A, "Suggest Glossary Terms", (ArtifactName.GLOSSARY_SUGGESTIONS,), llm_roles=("llm_model",)
    ),
    ProcessingStep(StepID.REVIEW_GLOSSARY_TERMS, _M, "Extract Glossary Terms", (ArtifactName.GLOSSARY_DECISIONS,)),
    ProcessingStep(StepID.ADD_GLOSSARY_ENTRIES, _A, "Add Glossary Entries", (ArtifactName.EXTRACTED_GLOSSARY_TERMS,)),
    ProcessingStep(
        StepID.SUGGEST_SPELLING_CORRECTIONS,
        _A,
        "Suggest Spelling Corrections",
        (ArtifactName.SPELLING_SUGGESTIONS,),
        llm_roles=("llm_model",),
    ),
    ProcessingStep(StepID.REVIEW_SPELLING_CORRECTIONS, _M, "Spellcheck Against Glossary", (ArtifactName.SPELLING_DECISIONS,)),
    ProcessingStep(StepID.APPLY_SPELLING_CORRECTIONS, _A, "Apply Spelling Corrections", (ArtifactName.SPELLCHECKED_TRANSCRIPT,)),
    ProcessingStep(StepID.REVIEW_TRANSCRIPT, _M, "Review Transcript", (ArtifactName.TRANSCRIPT_REVIEW_EDITS,)),
    ProcessingStep(StepID.APPLY_TRANSCRIPT_REVIEW, _A, "Apply Transcript Review", (ArtifactName.REVIEWED_TRANSCRIPT,)),
    ProcessingStep(StepID.ASSIGN_ROLES, _A, "Assign Roles To Players", (ArtifactName.ROLE_TRANSCRIPT,)),
    ProcessingStep(StepID.APPROVE_PRIOR_REBUILD, _M, "Rebuild Prior Sessions", (), visibility=StepVisibility.PRIOR_REBUILD),
    ProcessingStep(
        StepID.GENERATE_ARTIFACTS,
        _A,
        "Generate Artifacts",
        (
            ArtifactName.TRANSCRIPT_SECTIONS,
            ArtifactName.LEDGER,
            ArtifactName.SCENE_BREAKDOWN,
            ArtifactName.PLAYER_INTRODUCTIONS,
            ArtifactName.RECAP_SUMMARY,
            ArtifactName.SUMMARY,
        ),
        llm_roles=("llm_model_high",),
    ),
    ProcessingStep(StepID.IMPROVE_VOICE_PROFILES, _M, "Improve Player Voice Profiles", (ArtifactName.VOICE_PROFILE_DECISION,)),
    ProcessingStep(StepID.ENHANCE_VOICE_PROFILES, _A, "Enhance Voice Profiles", (ArtifactName.VOICE_PROFILE_ENHANCEMENT,)),
)

STEPS_BY_ID: dict[StepID, ProcessingStep] = {step.id: step for step in PROCESSING_STEPS}

# The processing-state section holding the approved prior-Session rebuild plan (not a build artifact).
PRIOR_REBUILD_APPROVAL_SECTION = "prior_rebuild_approval"


def step_producing(name: ArtifactName) -> ProcessingStep | None:
    return next((step for step in PROCESSING_STEPS if name in step.outputs), None)


def next_manual_step(step_id: StepID) -> ProcessingStep | None:
    """The manual step an automatic step leads to -- the row that shows its progress and failures."""
    index = [step.id for step in PROCESSING_STEPS].index(step_id)
    return next((step for step in PROCESSING_STEPS[index:] if step.is_manual), None)


@dataclass(frozen=True)
class ProcessingBlocker:
    """An error that prevents a step, and every step after it, from running."""

    step: StepID
    message: str


@dataclass(frozen=True)
class StepState:
    step: ProcessingStep
    complete: bool
    # Process Session draws the row (manual steps only).
    visible: bool
    # Complete with an empty decision: its row notes there was nothing to review.
    nothing_to_review: bool = False
    failure: str | None = None


@dataclass(frozen=True)
class ProcessingOverview:
    """Everything Process Session and the coordinator need about a Session's processing, computed at once."""

    steps: tuple[StepState, ...]
    new_players: tuple[str, ...]
    # Conditions that stop processing entirely (e.g. no attendees); Continue shows the first.
    blockers: tuple[str, ...]

    def state(self, step_id: StepID) -> StepState:
        return next(state for state in self.steps if state.step.id == step_id)

    @property
    def next_step(self) -> ProcessingStep | None:
        """The first incomplete step, where Continue starts."""
        return next((state.step for state in self.steps if not state.complete), None)
