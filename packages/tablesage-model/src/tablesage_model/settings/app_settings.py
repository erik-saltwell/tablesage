class EnhanceVoicesSettings(BaseModel, frozen=True):
    min_margin_for_voice_sample: float = 0.15
    min_clip_seconds: float = 1.0
    max_clip_seconds: float = 8.0
