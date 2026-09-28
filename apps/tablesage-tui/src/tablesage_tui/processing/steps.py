"""Every processing step, written as a linear async function over a `StepContext`.

Automatic steps run their work behind the run's progress dialog. Manual steps show one screen (or prompt) and save
only its decision; Cancel returns the cancel outcome, which ends the run. A manual step whose suggestions are empty
completes on its own with an empty decision, without opening its screen. See the processing-step-architecture work
item for the rules these follow.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

from tablesage_application.paths import ArtifactName
from tablesage_application.players_from_session import Stage as EnhanceStage
from tablesage_application.processing_steps import StepID
from tablesage_application.session_pipeline import clean_transcript, transcribe_audio
from tablesage_application.session_pipeline.artifact_graph import GENERATION_LABELS, GenerationTask
from tablesage_application.session_pipeline.extract_glossary import GlossaryProposal
from tablesage_application.session_pipeline.suggest_spelling_corrections import SpellingSuggestion
from textual_fspicker import Filters

from ..dialogs.file_picker import FileOpen
from .coordinator import StepContext, StepFunction, StepResult
from .drafts import DraftSlot

_TRANSCRIBE_LABELS = {
    transcribe_audio.Stage.TRANSCRIBING: "Transcribing (this may take a while)…",
    transcribe_audio.Stage.PUNCTUATING: "Punctuating…",
    transcribe_audio.Stage.IDENTIFYING_SPEAKERS: "Identifying speakers…",
}
_CLEAN_LABELS = {
    clean_transcript.Stage.REMOVING_BACKCHANNELS: "Removing leftover backchannels…",
    clean_transcript.Stage.ASSIGNING_ROLES: "Assigning roles…",
}
_ENHANCE_LABELS = {
    EnhanceStage.EXTRACTING: "Extracting voice clips…",
    EnhanceStage.RECOMPUTING_CENTROIDS: "Recomputing centroids…",
}


def _draft(ctx: StepContext, step_id: StepID, basis: ArtifactName) -> DraftSlot:
    return DraftSlot(ctx.application, ctx.session_id, step_id.value, basis)


def _suggestions(value: Any) -> list[SpellingSuggestion]:
    return [
        SpellingSuggestion(
            from_text=item["from_text"],
            to_text=item["to_text"],
            case_sensitive=bool(item.get("case_sensitive", False)),
            occurrence_count=int(item.get("occurrence_count", 0)),
            removed=bool(item.get("removed", False)),
        )
        for item in value or []
    ]


# Import Audio


async def import_audio(ctx: StepContext) -> StepResult:
    """Choose the file and whether to clean it; the import itself is the next (automatic) step."""
    application = ctx.application
    # Checked before the picker, so a missing key never costs minutes of audio cleaning.
    application.require_credentials("llm_model_lite", transcription=True)
    audio_filter = Filters(("Audio", lambda path: path.suffix.lower() in application.audio_import_extensions()))
    location = Path.home()
    while True:
        source_path = await ctx.show(FileOpen(title="Import Audio", location=location, filters=audio_filter))
        if source_path is None:
            return StepResult.cancel()
        try:
            application.validate_import_audio_source(source_path)
        except ValueError as exc:
            ctx.notify(str(exc), severity="error")
            location = source_path.parent
            continue
        clean_audio = True
        if source_path.suffix.lower() == ".wav":
            answer = await ctx.confirm(
                title="Clean Audio?", prompt="Run this .wav through noise-cleaning before import? Skip if it's already been cleaned."
            )
            if answer is None:
                return StepResult.cancel()
            clean_audio = answer
        await ctx.call(functools.partial(application.save_import_request, ctx.session_id, source_path, clean_audio=clean_audio))
        return StepResult.success()


async def import_audio_file(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Importing audio (cleaning can take a few minutes)…", lambda: ctx.application.import_requested_audio(ctx.session_id)
    )
    return StepResult.success()


async def create_transcript(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Transcribing (this may take a while)…",
        lambda: ctx.application.create_transcript(
            ctx.session_id, on_progress=lambda stage, completed, total: ctx.progress(_TRANSCRIBE_LABELS[stage], completed, total)
        ),
    )
    return StepResult.success()


async def remove_backchannels(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Removing backchannels…",
        lambda: ctx.application.remove_bad_utterances(
            ctx.session_id, on_progress=lambda completed, total: ctx.progress("Removing backchannels…", completed, total)
        ),
    )
    return StepResult.success()


# Review Name Corrections: suggest, review, apply


async def suggest_name_corrections(ctx: StepContext) -> StepResult:
    await ctx.background("Finding misheard names…", lambda: ctx.application.propose_name_corrections(ctx.session_id))
    return StepResult.success()


async def _review_corrections(
    ctx: StepContext,
    *,
    step_id: StepID,
    suggestions_artifact: ArtifactName,
    title: str,
    hint: str,
    whole_words: bool,
    load: Any,
    propose: Any,
    save: Any,
) -> StepResult:
    """Shared by Review Name Corrections and Spellcheck Against Glossary."""
    from ..screens.corrections_step import CorrectionsStepScreen

    application = ctx.application
    if await ctx.call(lambda: application.is_imported_placeholder(ctx.session_id, suggestions_artifact)):
        await ctx.background("Finding suggestions…", lambda: propose(ctx.session_id))
    transcript, suggestions, decided = await ctx.call(lambda: load(ctx.session_id))
    if not suggestions and not decided:
        await ctx.call(lambda: save(ctx.session_id, ()))
        return StepResult.success()
    draft = _draft(ctx, step_id, suggestions_artifact)
    saved_draft = await ctx.call(draft.load)
    rows = _suggestions(saved_draft) if saved_draft is not None else (decided if decided is not None else suggestions)
    corrections = await ctx.show(
        CorrectionsStepScreen(
            title=title,
            hint=hint,
            transcript=transcript,
            suggestions=rows,
            whole_words=whole_words,
            draft=draft,
            soft_remove=step_id is StepID.REVIEW_SPELLING_CORRECTIONS,
        )
    )
    if corrections is None:
        return StepResult.cancel()
    await ctx.call(lambda: save(ctx.session_id, corrections))
    await ctx.call(draft.discard)
    return StepResult.success()


async def review_name_corrections(ctx: StepContext) -> StepResult:
    application = ctx.application
    return await _review_corrections(
        ctx,
        step_id=StepID.REVIEW_NAME_CORRECTIONS,
        suggestions_artifact=ArtifactName.NAME_CORRECTION_SUGGESTIONS,
        title="Name Corrections",
        hint="Keep only corrections to names that were misheard; they apply to every later step.",
        whole_words=True,
        load=application.name_correction_review,
        propose=application.propose_name_corrections,
        save=application.save_name_correction_decisions,
    )


def _replaced(occurrences: int) -> StepResult:
    if not occurrences:
        return StepResult.success()
    return StepResult.success(f"Replaced {occurrences} occurrence{'' if occurrences == 1 else 's'}.")


async def apply_name_corrections(ctx: StepContext) -> StepResult:
    return _replaced(await ctx.background("Applying name corrections…", lambda: ctx.application.apply_name_corrections(ctx.session_id)))


# New speakers


async def isolate_new_speakers(ctx: StepContext) -> StepResult:
    await ctx.background("Isolating new speakers…", lambda: ctx.application.isolate_new_speakers(ctx.session_id, on_progress=ctx.progress))
    return StepResult.success()


async def review_new_speaker_assignments(ctx: StepContext) -> StepResult:
    from ..screens.new_speaker_assignments import NewSpeakerAssignmentsScreen

    application = ctx.application
    proposals = await ctx.call(lambda: application.new_speaker_proposals(ctx.session_id))
    if not proposals.players:
        await ctx.call(lambda: application.confirm_new_speaker_assignment_review(ctx.session_id, {}))
        return StepResult.success()
    draft = _draft(ctx, StepID.REVIEW_NEW_SPEAKER_ASSIGNMENTS, ArtifactName.NEW_SPEAKER_ASSIGNMENTS)
    result = await ctx.show(NewSpeakerAssignmentsScreen(ctx.session_id, draft=draft))
    if result is None:
        return StepResult.cancel()
    kept, rejected = result
    await ctx.call(lambda: application.confirm_new_speaker_assignment_review(ctx.session_id, kept, rejected))
    await ctx.call(draft.discard)
    return StepResult.success()


async def seed_voice_samples(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Cutting voice clips…", lambda: ctx.application.seed_player_voice_samples(ctx.session_id, on_progress=ctx.progress)
    )
    return StepResult.success()


async def identify_speakers(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Identifying speakers…",
        lambda: ctx.application.identify_session_speakers(
            ctx.session_id, on_progress=lambda stage, completed, total: ctx.progress(_TRANSCRIBE_LABELS[stage], completed, total)
        ),
    )
    return StepResult.success()


# Extract Glossary Terms: suggest, review, add


async def suggest_glossary_terms(ctx: StepContext) -> StepResult:
    await ctx.background("Extracting glossary terms…", lambda: ctx.application.propose_glossary_terms(ctx.session_id))
    return StepResult.success()


async def review_glossary_terms(ctx: StepContext) -> StepResult:
    from ..screens.glossary_review import GlossaryReviewScreen

    application = ctx.application
    if await ctx.call(lambda: application.is_imported_placeholder(ctx.session_id, ArtifactName.GLOSSARY_SUGGESTIONS)):
        await ctx.background("Extracting glossary terms…", lambda: application.propose_glossary_terms(ctx.session_id))
    proposals, decided = await ctx.call(lambda: application.glossary_term_review(ctx.session_id))
    if not proposals and not decided:
        await ctx.call(lambda: application.save_glossary_decisions(ctx.session_id, ()))
        return StepResult.success()
    draft = _draft(ctx, StepID.REVIEW_GLOSSARY_TERMS, ArtifactName.GLOSSARY_SUGGESTIONS)
    saved_draft = await ctx.call(draft.load)
    rows = (
        [GlossaryProposal.model_validate(item) for item in saved_draft]
        if saved_draft is not None
        else (decided if decided is not None else proposals)
    )
    reviewed = await ctx.show(GlossaryReviewScreen(ctx.session_id, rows, section="process session · extract glossary terms", draft=draft))
    if reviewed is None:
        return StepResult.cancel()
    await ctx.call(lambda: application.save_glossary_decisions(ctx.session_id, reviewed))
    await ctx.call(draft.discard)
    return StepResult.success()


async def add_glossary_entries(ctx: StepContext) -> StepResult:
    result = await ctx.background("Adding glossary entries…", lambda: ctx.application.add_glossary_entries(ctx.session_id))
    if not result.added_count:
        return StepResult.success()
    added_word = "entry" if result.added_count == 1 else "entries"
    message = f"Added {result.added_count} glossary {added_word}."
    if result.skipped_duplicate_count:
        duplicate_word = "duplicate" if result.skipped_duplicate_count == 1 else "duplicates"
        message += f" Skipped {result.skipped_duplicate_count} {duplicate_word}."
    return StepResult.success(message)


# Spellcheck Against Glossary: suggest, review, apply


async def suggest_spelling_corrections(ctx: StepContext) -> StepResult:
    await ctx.background("Finding misspelled glossary terms…", lambda: ctx.application.propose_spelling_corrections(ctx.session_id))
    return StepResult.success()


async def review_spelling_corrections(ctx: StepContext) -> StepResult:
    application = ctx.application
    return await _review_corrections(
        ctx,
        step_id=StepID.REVIEW_SPELLING_CORRECTIONS,
        suggestions_artifact=ArtifactName.SPELLING_SUGGESTIONS,
        title="Spellcheck Against Glossary",
        hint="Keep only corrections to glossary terms and names that were misspelled.",
        whole_words=False,
        load=application.spelling_review,
        propose=application.propose_spelling_corrections,
        save=application.save_spelling_decisions,
    )


async def apply_spelling_corrections(ctx: StepContext) -> StepResult:
    return _replaced(
        await ctx.background("Applying spelling corrections…", lambda: ctx.application.apply_spelling_corrections(ctx.session_id))
    )


# Review Transcript


async def review_transcript(ctx: StepContext) -> StepResult:
    from ..screens.speaker_review import ManualReviewScreen

    reviewed = await ctx.show(ManualReviewScreen(ctx.session_id))
    if reviewed is None:
        return StepResult.cancel()
    await ctx.call(lambda: ctx.application.save_transcript_review(ctx.session_id, reviewed))
    return StepResult.success()


async def apply_transcript_review(ctx: StepContext) -> StepResult:
    await ctx.background("Saving the reviewed transcript…", lambda: ctx.application.apply_transcript_review(ctx.session_id))
    return StepResult.success()


async def assign_roles(ctx: StepContext) -> StepResult:
    await ctx.background(
        "Assigning roles…",
        lambda: ctx.application.clean_transcript(
            ctx.session_id, on_progress=lambda stage, completed, total: ctx.progress(_CLEAN_LABELS[stage], completed, total)
        ),
    )
    return StepResult.success()


# Generate Artifacts


async def approve_prior_rebuild(ctx: StepContext) -> StepResult:
    application = ctx.application
    tasks = await ctx.call(lambda: application.prior_rebuild_tasks(ctx.session_id))
    if tasks:
        session_count = len({task.session_id for task in tasks})
        phase_label = "phase" if len(tasks) == 1 else "phases"
        session_label = "Session" if session_count == 1 else "Sessions"
        answer = await ctx.confirm(
            title="Prior Sessions Are Out of Date",
            prompt=(
                f"Generating this Session's outputs requires rebuilding {len(tasks)} output {phase_label} in {session_count} "
                f"prior {session_label}.\n\nRegenerate Prior rebuilds them first, then this Session. Cancel does nothing."
            ),
            show_cancel=False,
            no_label="Cancel",
            yes_label="Regenerate Prior",
        )
        if not answer:
            return StepResult.cancel()
    await ctx.call(lambda: application.approve_prior_rebuild(ctx.session_id, tasks))
    return StepResult.success()


async def generate_artifacts(ctx: StepContext) -> StepResult:
    force = ctx.facts.pop("force", None)

    def on_stage(task: GenerationTask, _completed: int, _total: int) -> None:
        ctx.progress(f"Generating {GENERATION_LABELS[task.artifact_name]}…")

    tasks = await ctx.background(
        "Generating outputs…",
        lambda: ctx.application.generate_outputs(
            ctx.session_id,
            force=force,
            on_stage=on_stage,
            on_clean_progress=lambda stage, completed, total: ctx.progress(_CLEAN_LABELS[stage], completed, total),
        ),
    )
    if not tasks:
        return StepResult.success()
    return StepResult.success(f"Generated {len(tasks)} output{'' if len(tasks) == 1 else 's'}.")


# Improve Player Voice Profiles


async def improve_voice_profiles(ctx: StepContext) -> StepResult:
    answer = await ctx.confirm(
        title="Improve Player Voice Profiles",
        prompt=(
            "Add voice samples from this Session to your players' voice profiles? This helps TableSage "
            "recognize them in future Sessions.\n\n"
            "Only do this if you've carefully reviewed the transcript's speaker assignments -- "
            "mislabeled lines will teach TableSage the wrong voice for a player."
        ),
        show_cancel=False,
        no_label="Not Now",
        yes_label="Add Samples",
    )
    if answer is None:
        return StepResult.cancel()
    await ctx.call(lambda: ctx.application.save_voice_profile_decision(ctx.session_id, accepted=answer))
    if not answer:
        return StepResult.success("You can add this Session's voice samples later with From Session on the Players screen.")
    return StepResult.success()


async def enhance_voice_profiles(ctx: StepContext) -> StepResult:
    result = await ctx.background(
        "Adding voice samples…",
        lambda: ctx.application.enhance_voice_profiles(
            ctx.session_id, on_progress=lambda stage, completed, total: ctx.progress(_ENHANCE_LABELS[stage], completed, total)
        ),
    )
    if result is None:
        return StepResult.success()
    return StepResult.success(f"Enhanced {result.enhanced_player_count} player(s) with {result.clip_count} clip(s) total.")


STEP_FUNCTIONS: dict[StepID, StepFunction] = {
    StepID.IMPORT_AUDIO: import_audio,
    StepID.IMPORT_AUDIO_FILE: import_audio_file,
    StepID.CREATE_TRANSCRIPT: create_transcript,
    StepID.REMOVE_BACKCHANNELS: remove_backchannels,
    StepID.SUGGEST_NAME_CORRECTIONS: suggest_name_corrections,
    StepID.REVIEW_NAME_CORRECTIONS: review_name_corrections,
    StepID.APPLY_NAME_CORRECTIONS: apply_name_corrections,
    StepID.ISOLATE_NEW_SPEAKERS: isolate_new_speakers,
    StepID.REVIEW_NEW_SPEAKER_ASSIGNMENTS: review_new_speaker_assignments,
    StepID.SEED_VOICE_SAMPLES: seed_voice_samples,
    StepID.IDENTIFY_SPEAKERS: identify_speakers,
    StepID.SUGGEST_GLOSSARY_TERMS: suggest_glossary_terms,
    StepID.REVIEW_GLOSSARY_TERMS: review_glossary_terms,
    StepID.ADD_GLOSSARY_ENTRIES: add_glossary_entries,
    StepID.SUGGEST_SPELLING_CORRECTIONS: suggest_spelling_corrections,
    StepID.REVIEW_SPELLING_CORRECTIONS: review_spelling_corrections,
    StepID.APPLY_SPELLING_CORRECTIONS: apply_spelling_corrections,
    StepID.REVIEW_TRANSCRIPT: review_transcript,
    StepID.APPLY_TRANSCRIPT_REVIEW: apply_transcript_review,
    StepID.ASSIGN_ROLES: assign_roles,
    StepID.APPROVE_PRIOR_REBUILD: approve_prior_rebuild,
    StepID.GENERATE_ARTIFACTS: generate_artifacts,
    StepID.IMPROVE_VOICE_PROFILES: improve_voice_profiles,
    StepID.ENHANCE_VOICE_PROFILES: enhance_voice_profiles,
}
