from pydantic import BaseModel, field_validator


class SummarizeRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def url_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("URL must not be empty")
        return v.strip()


class VideoMetadata(BaseModel):
    video_id: str
    title: str | None = None
    channel_name: str | None = None
    duration_seconds: int | None = None
    thumbnail_url: str | None = None


class SummarizeResponse(BaseModel):
    summary: str
    metadata: VideoMetadata | None = None


class ErrorResponse(BaseModel):
    error: str
    message: str
    details: str | None = None
