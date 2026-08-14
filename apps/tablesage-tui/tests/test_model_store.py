from __future__ import annotations

from datetime import date

import pytest
from tablesage_model.model import Session, SessionSet
from tablesage_model.model.campaign.session_set import SessionName
from tablesage_tui.viewmodel import model_store
from tablesage_tui.viewmodel.model_store import ModelStore


def _session(slug: str, session_date: date) -> Session:
    return Session(session_date=session_date, name=slug.replace("-", " ").title(), slug=slug, audio_filename="session.wav", attendees={})


def test_get_last_session_for_campaign_loads_most_recent_session(monkeypatch: pytest.MonkeyPatch) -> None:
    sessions = {
        "early": _session("early", date(2026, 1, 1)),
        "latest": _session("latest", date(2026, 3, 1)),
    }

    monkeypatch.setattr(
        model_store,
        "load_session_set",
        lambda _campaign_slug: SessionSet(
            sessions=(
                SessionName(slug="early", name="Early", session_date=date(2026, 1, 1)),
                SessionName(slug="latest", name="Latest", session_date=date(2026, 3, 1)),
            )
        ),
    )
    monkeypatch.setattr(model_store, "load_session", lambda _campaign_slug, session_slug: sessions[session_slug])

    assert ModelStore().get_last_session_for_campaign("iron-pact") == sessions["latest"]


def test_get_last_session_for_campaign_raises_when_campaign_has_no_sessions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(model_store, "load_session_set", lambda _campaign_slug: SessionSet(sessions=()))

    with pytest.raises(LookupError, match="has no sessions"):
        ModelStore().get_last_session_for_campaign("iron-pact")
