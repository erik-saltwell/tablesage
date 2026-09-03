from __future__ import annotations

from pydantic import BaseModel, Field, PositiveInt

from .type_aliases import ScribeLanguageCode, ScribeModelId


class RemoveOutliersSettings(BaseModel, frozen=True):
    min_sample_similarity: float = Field(default=0.6, gt=0, le=1)
    min_samples: PositiveInt = 5


class SpeakerIdentificationDurationOverrideSettings(BaseModel, frozen=True):
    min_seconds: float = Field(default=1.0, gt=0)
    similarity_margin_threshold: float = Field(default=0.04, ge=0, le=2)


class ShortUtteranceWideningSettings(BaseModel, frozen=True):
    enabled: bool = True
    max_original_duration_seconds: float = Field(default=0.75, gt=0)
    target_duration_seconds: float = Field(default=1.0, gt=0)
    max_neighbor_gap_seconds: float = Field(default=2.0, ge=0)


class ClusterPropagationSettings(BaseModel, frozen=True):
    enabled: bool = True
    evidence_min_duration_seconds: float = Field(default=0.5, gt=0)
    max_utterance_duration_seconds: float = Field(default=0.5, gt=0)
    cluster_margin_threshold: float = Field(default=0.0, ge=0, le=2)
    contradiction_veto_margin_threshold: float = Field(default=0.02, ge=0, le=2)


class SpeakerIdentificationSettings(BaseModel, frozen=True):
    # Experiment #7's robust rule uses this base bar for utterances shorter than the duration
    # override, then the override's lower bar once enough audio evidence is available.
    similarity_margin_threshold: float = Field(default=0.1, ge=0, le=2)
    duration_override: SpeakerIdentificationDurationOverrideSettings = Field(default_factory=SpeakerIdentificationDurationOverrideSettings)
    short_utterance_widening: ShortUtteranceWideningSettings = Field(default_factory=ShortUtteranceWideningSettings)
    cluster_propagation: ClusterPropagationSettings = Field(default_factory=ClusterPropagationSettings)
    # "From Audio" compares a whole diarized-speaker centroid, not one duration-varying utterance.
    # Keep its pre-experiment threshold independent from the duration-conditioned production rule.
    existing_player_match_similarity_margin_threshold: float = Field(default=0.08, ge=0, le=2)
    log_diagnostics: bool = False
    # When False, an utterance is never left UNASSIGNED_SPEAKER just because its best-vs-runner-up
    # similarity margin fell below similarity_margin_threshold -- the best match is taken
    # regardless of confidence. Utterances too short to embed at all are unaffected: they're
    # still assigned UNASSIGNED_SPEAKER either way, since there's no embedding-based judgment to
    # skip there in the first place.
    allow_unassigned: bool = True


class AudioCleaningSettings(BaseModel, frozen=True):
    normalize_volume: bool = False


class SessionAudioImportSettings(BaseModel, frozen=True):
    normalize_volume: bool = False


class TranscriptionAndDiarizationSettings(BaseModel, frozen=True):
    timeout: PositiveInt = 7200
    language_code: ScribeLanguageCode = "eng"
    tag_audio_events: bool = False
    model_id: ScribeModelId = "scribe_v2"


class EnhanceVoicesSettings(BaseModel, frozen=True):
    min_margin_for_voice_sample: float = 0.15
    min_clip_seconds: float = 1.0
    max_clip_seconds: float = 8.0
    # A hard technical floor, not a quality filter: WeSpeaker's fbank feature extraction needs at
    # least ~125ms of audio to compute a window at all and remains weak just above that, so clips
    # shorter than this crash or embed poorly regardless of confidence. Unlike min_clip_seconds/
    # max_clip_seconds (which only ever apply to the unreviewed machine-transcript path), this
    # applies to a completed Manual Review's assigned utterances too -- the one path that
    # otherwise applies no duration filtering at all. See `MIN_UTTERANCE_DURATION_SECONDS` in
    # `tablesage_tools.speakers` for the same floor's rationale in the speaker-ID path.
    min_embeddable_clip_seconds: float = Field(default=0.15, gt=0)


class RemoveBackchannelsSettings(BaseModel, frozen=True):
    # Shared candidate-detection threshold: an utterance longer than this many words is never
    # considered a backchannel candidate, regardless of wordlist match. Used both by the
    # pre-review pass (Transcribe) and the post-review pass (Clean Transcript's role-transcript
    # step).
    max_words: PositiveInt = 3
    # The following three apply only to the pre-review pass (Transcribe), which is the only one
    # that makes an LLM call -- the post-review pass is a purely mechanical unassigned-speaker
    # filter with no LLM involved.
    #
    # Candidates needing an "is the previous utterance a question?" judgment are split into
    # batches of this size rather than sent as one call -- a large session can propose hundreds of
    # candidates, and one big call is what caused a real production timeout (`candidate_count=569`
    # in a single call, `litellm.Timeout` at 600s, nothing removed).
    batch_size: PositiveInt = 50
    # How many batches run concurrently. Sequential batching would trade "one call that might time
    # out" for "many calls that reliably take longer in total" -- concurrency keeps overall wait
    # roughly similar to (or better than) the old single call.
    max_concurrent_batches: PositiveInt = 4
    # Timeout (seconds) per batch (not per whole pass) -- a batch is a small fraction of the old
    # worst-case candidate count, so it doesn't need anywhere near as long as one giant call did.
    question_check_timeout: PositiveInt = 120


class AppSettings(BaseModel, frozen=True):
    audio_cleaning: AudioCleaningSettings = Field(default_factory=AudioCleaningSettings)
    transcription_and_diarization: TranscriptionAndDiarizationSettings = Field(default_factory=TranscriptionAndDiarizationSettings)
    speaker_identification: SpeakerIdentificationSettings = Field(default_factory=SpeakerIdentificationSettings)
    remove_outliers: RemoveOutliersSettings = Field(default_factory=RemoveOutliersSettings)
    enhance_voices: EnhanceVoicesSettings = Field(default_factory=EnhanceVoicesSettings)
    remove_backchannels: RemoveBackchannelsSettings = Field(default_factory=RemoveBackchannelsSettings)
    llm_model: str = "anthropic/claude-sonnet-4-5"
    llm_model_lite: str = "anthropic/claude-haiku-4-5"
    llm_model_high: str = "anthropic/claude-fable-5"
    clean_clips_on_import: bool = False
    session_audio_import: SessionAudioImportSettings = Field(default_factory=SessionAudioImportSettings)
