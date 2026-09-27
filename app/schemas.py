"""Strict request/response contracts shared with Hazma and Analytics."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .utils import normalize_text


class StrictModel(BaseModel):
    """Reject extra keys, coercion, and non-finite numeric values."""

    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class EducationItem(StrictModel):
    """A documented qualification; unknown details are represented as null."""

    degree: str | None = Field(max_length=300)
    institution: str | None = Field(max_length=300)
    graduation_year: int | None = Field(ge=1900, le=2200)


class ResumeSchema(StrictModel):
    """Extracted facts. All keys are required; nullable fields may be null."""

    candidate_name: str | None = Field(max_length=300)
    email: str | None = Field(max_length=320)
    skills: list[Annotated[str, Field(min_length=1, max_length=150)]] = Field(max_length=200)
    experience_years: float = Field(ge=0, le=100)
    education: list[EducationItem] = Field(max_length=30)
    summary: str = Field(max_length=3000)


class EmbeddingRequest(StrictModel):
    """A sentence or short paragraph; overlong token sequences are rejected."""

    text: str = Field(min_length=1, max_length=12000)

    @field_validator("text")
    @classmethod
    def clean_text(cls, value: str) -> str:
        """Reject inputs that become empty after Unicode normalization."""
        value = normalize_text(value)
        if not value:
            raise ValueError("text must contain visible characters")
        return value


class EmbeddingResponse(StrictModel):
    """A normalized, finite 384-dimensional vector for pgvector vector(384)."""

    embedding: list[float] = Field(min_length=384, max_length=384)
    dimensions: Literal[384] = 384


class ErrorDetail(StrictModel):
    """Stable machine-readable failure code and safe human-readable message."""

    code: str
    message: str


class ErrorResponse(StrictModel):
    """Consistent failure envelope; never includes resume text or model output."""

    error: ErrorDetail
