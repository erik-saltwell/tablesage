from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class QuestionCategory(StrEnum):
    FICTION_CHANGE = "fiction_change"
    RECAP = "recap"
    INTRODUCTION = "introduction"
    CORRECTION = "correction"


class CompletenessQuestion(StrictModel):
    id: str = Field(min_length=1)
    category: QuestionCategory
    question: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    enabled: bool = True

    @field_validator("id", "question", "evidence")
    @classmethod
    def _strip_text(cls, value: str) -> str:
        return value.strip()


class BundleFile(StrictModel):
    path: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class BundleManifest(StrictModel):
    format: str = "tablesage-prompt-evaluation"
    version: int = 1
    target: str = "ledger"
    campaign_name: str = Field(min_length=1)
    session_sequence: str = Field(pattern=r"^\d{3}$")
    session_uuid: str = Field(min_length=1)
    files: dict[str, BundleFile]


class GeneratedQuestion(StrictModel):
    category: QuestionCategory
    question: str = Field(min_length=1)
    evidence: str = Field(min_length=1)


class GeneratedQuestionList(StrictModel):
    questions: list[GeneratedQuestion]


class QuestionAnswer(StrictModel):
    id: str
    covered: bool
    covered_by_correction: bool = False
    rationale: str = ""


class QuestionAnswerList(StrictModel):
    answers: list[QuestionAnswer]


class ClaimVerdict(StrictModel):
    claim: str
    supported: bool
    evidence: str = ""
    rationale: str = ""


class ClaimVerdictList(StrictModel):
    verdicts: list[ClaimVerdict]


class ExclusionSeverity(StrEnum):
    MAJOR = "major"
    MODERATE = "moderate"
    MINOR = "minor"


class ExclusionViolation(StrictModel):
    entry: str
    severity: ExclusionSeverity
    rationale: str


class ExclusionViolationList(StrictModel):
    violations: list[ExclusionViolation]


class DuplicateGroup(StrictModel):
    entries: list[str] = Field(min_length=2)
    rationale: str


class DuplicateGroupList(StrictModel):
    groups: list[DuplicateGroup]
