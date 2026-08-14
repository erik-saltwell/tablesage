from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


# SessionName is an intentional lightweight index entry — it intentionally omits the
# full Session fields so the display name can be updated independently of session data.
# session_date is the one exception: it is an intrinsic, stable fact of a session (not a
# denormalized rollup), kept here so list-level views can compute first/last/count of
# sessions without opening every full session file.
class SessionName(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr
    session_date: date


class SessionSet(BaseModel, frozen=True):
    sessions: tuple[SessionName, ...]
