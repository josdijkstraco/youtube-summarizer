from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    url: str
    length_percent: int = Field(default=25, ge=10, le=50)

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("URL must not be empty")
        return v.strip()

    @field_validator("length_percent")
    @classmethod
    def length_percent_must_be_multiple_of_5(cls, v: int) -> int:
        if v % 5 != 0:
            raise ValueError("length_percent must be a multiple of 5")
        return v


class VideoMetadata(BaseModel):
    video_id: str
    title: str | None = None
    channel_name: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None


class ClearExample(BaseModel):
    scenario: str
    why_wrong: str


class Fallacy(BaseModel):
    timestamp: str | None = None
    quote: str
    fallacy_name: str
    category: str
    severity: str
    explanation: str
    clear_example: ClearExample


class FallacySummary(BaseModel):
    total_fallacies: int
    high_severity: int
    medium_severity: int
    low_severity: int
    primary_tactics: list[str]


class FallacyAnalysisResult(BaseModel):
    summary: FallacySummary
    fallacies: list[Fallacy]


class SummarizeResponse(BaseModel):
    summary: str
    metadata: VideoMetadata | None = None
    fallacy_analysis: FallacyAnalysisResult | None = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: str | None = None
