from __future__ import annotations

from ..._settings import AppSettings
from ..._tools.llm.summary import generate_summary as _tool_generate_summary
from ...io import save_summary
from ...model.artifacts import Summary
from ...model.campaign import GlossaryEntry
from ...model.transcription import Discourse
from ...protocols import PhasedProgressEvent, PhasedProgressSink


async def generate_summary(
    campaign_slug: str,
    session_slug: str,
    app_settings: AppSettings,
    glossary: tuple[GlossaryEntry, ...],
    discourse: Discourse,
    sink: PhasedProgressSink,
) -> None:
    await sink.publish(PhasedProgressEvent(source="generate_summary", phase="generating summary"))
    markdown = await _tool_generate_summary(discourse, glossary, app_settings.llm_model)
    save_summary(campaign_slug, session_slug, Summary(markdown=markdown))
