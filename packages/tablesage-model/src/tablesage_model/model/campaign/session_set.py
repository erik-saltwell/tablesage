from __future__ import annotations

from pydantic import BaseModel

from ..._utils import StrippedNonBlankStr


# SessionName is an intentional lightweight index entry — it intentionally omits the
# full Session fields so the display name can be updated independently of session data.
class SessionName(BaseModel, frozen=True):
    slug: StrippedNonBlankStr
    name: StrippedNonBlankStr


class SessionSet(BaseModel, frozen=True):
    sessions: tuple[SessionName, ...]
