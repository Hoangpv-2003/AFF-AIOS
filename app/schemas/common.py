"""Common API schemas."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)
    trace_id: str
    retryable: bool = False


class IdempotencyMeta(BaseModel):
    key: str
    replayed: bool = False


class TraceRef(BaseModel):
    trace_id: str
