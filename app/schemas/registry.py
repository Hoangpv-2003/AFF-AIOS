"""Registry transition schemas."""

from typing import Optional

from pydantic import BaseModel


class RegistryTransitionEvent(BaseModel):
    skill_id: str
    from_state: str
    to_state: str
    reason: Optional[str] = None


class RegistryTransitionError(BaseModel):
    code: str
    message: str
