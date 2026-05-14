from __future__ import annotations

from enum import StrEnum


class ProvenanceType(StrEnum):
    INFERRED = "inferred"
    SESSION_ENHANCEMENT = "session_enhancement"
    IMPORT = "import"
