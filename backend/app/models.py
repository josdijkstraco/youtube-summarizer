from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


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


class FallacyAnalysisRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("URL must not be empty")
        return v.strip()


class Highlight(BaseModel):
    start: int
    end: int


class HighlightRequest(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    @model_validator(mode='after')
    def end_after_start(self) -> 'HighlightRequest':
        if self.end <= self.start:
            raise ValueError('end must be greater than start')
        return self


class SummaryStats(BaseModel):
    chars_in: int
    chars_out: int
    total_tokens: int
    generation_seconds: float


class SummarizeResponse(BaseModel):
    summary: str
    transcript: str
    metadata: VideoMetadata | None = None
    storage_warning: bool = False
    stats: SummaryStats | None = None
    highlights: list[Highlight] = []


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: str | None = None


class VideoRecord(BaseModel):
    id: int
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    transcript: str
    fallacy_analysis: FallacyAnalysisResult | None = None
    highlights: list[Highlight] = []
    created_at: datetime


class HistoryItem(BaseModel):
    video_id: str
    title: str | None
    thumbnail_url: str | None
    summary: str
    has_fallacy_analysis: bool = False
    created_at: datetime


class HistoryResponse(BaseModel):
    items: list[HistoryItem]
