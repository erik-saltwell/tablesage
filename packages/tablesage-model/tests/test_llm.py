from __future__ import annotations

import pytest
from tablesage_model import _paths
from tablesage_model._settings import AppSettings
from tablesage_model._tools.llm import summary as llm_summary
from tablesage_model._tools.llm.summary import generate_summary
from tablesage_model.io import load_summary
from tablesage_model.model.campaign import GlossaryEntry
from tablesage_model.model.transcription import Discourse, Utterance, Word
from tablesage_model.protocols import NullPhasedProgressSink, PhasedProgressEvent


def _make_discourse(text: str = "The party met the lich-king at the gate.") -> Discourse:
    words = tuple(Word(text=tok, start=float(i), end=float(i) + 0.5, speaker="ada") for i, tok in enumerate(text.split()))
    return Discourse(utterances=(Utterance.from_words(words),))


@pytest.mark.anyio
async def test_generate_summary_prompt_contains_every_utterance_text(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    async def fake_call_llm(prompt: str, model: str) -> str:
        captured["prompt"] = prompt
        return "# fake summary"

    monkeypatch.setattr(llm_summary, "_call_llm", fake_call_llm)

    utterance_text = "The party met the lich-king at the gate."
    discourse = _make_discourse(utterance_text)

    await generate_summary(discourse, glossary=(), model="claude-test")

    assert utterance_text in captured["prompt"]


@pytest.mark.anyio
async def test_generate_summary_prompt_contains_every_glossary_entry_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    async def fake_call_llm(prompt: str, model: str) -> str:
        captured["prompt"] = prompt
        return "# fake summary"

    monkeypatch.setattr(llm_summary, "_call_llm", fake_call_llm)

    glossary = (
        GlossaryEntry(term="Quarl", description="A lich-king who rules the Iron Pact"),
        GlossaryEntry(term="Iron Pact", description="A coalition of undead nobles"),
    )

    await generate_summary(_make_discourse(), glossary, model="claude-test")

    prompt = captured["prompt"]
    assert "Quarl" in prompt
    assert "A lich-king who rules the Iron Pact" in prompt
    assert "Iron Pact" in prompt
    assert "A coalition of undead nobles" in prompt


@pytest.mark.anyio
async def test_generate_summary_action_writes_summary_markdown_to_disk(monkeypatch: pytest.MonkeyPatch) -> None:
    body = "# Session One\n\nThe party met **Quarl** at the gate."

    async def fake_tool_generate_summary(discourse: Discourse, glossary: tuple[GlossaryEntry, ...], model: str) -> str:
        return body

    import sys

    import tablesage_model._actions.transcription.generate_summary  # noqa: F401  (load submodule)

    action_mod = sys.modules["tablesage_model._actions.transcription.generate_summary"]
    monkeypatch.setattr(action_mod, "_tool_generate_summary", fake_tool_generate_summary)

    _paths.ensure_dir(_paths.session_dir("sable-crown", "session-one"))

    await action_mod.generate_summary(
        campaign_slug="sable-crown",
        session_slug="session-one",
        app_settings=AppSettings(),
        glossary=(GlossaryEntry(term="Quarl", description=""),),
        discourse=_make_discourse(),
        sink=NullPhasedProgressSink(),
    )

    summary = load_summary("sable-crown", "session-one")
    assert summary.markdown == body


class _CapturingSink:
    def __init__(self) -> None:
        self.events: list[PhasedProgressEvent] = []

    async def publish(self, event: PhasedProgressEvent) -> None:
        self.events.append(event)


@pytest.mark.anyio
async def test_generate_summary_action_emits_a_progress_event(monkeypatch: pytest.MonkeyPatch) -> None:
    import sys

    import tablesage_model._actions.transcription.generate_summary  # noqa: F401

    async def fake_tool_generate_summary(discourse: Discourse, glossary: tuple[GlossaryEntry, ...], model: str) -> str:
        return "body"

    action_mod = sys.modules["tablesage_model._actions.transcription.generate_summary"]
    monkeypatch.setattr(action_mod, "_tool_generate_summary", fake_tool_generate_summary)
    _paths.ensure_dir(_paths.session_dir("sable-crown", "session-one"))

    sink = _CapturingSink()
    await action_mod.generate_summary(
        campaign_slug="sable-crown",
        session_slug="session-one",
        app_settings=AppSettings(),
        glossary=(),
        discourse=_make_discourse(),
        sink=sink,
    )

    assert any(e.source == "generate_summary" for e in sink.events)
