"""Authentication endpoints."""

from __future__ import annotations

import secrets
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

# Simple in-memory users for local/offline flow verification.
_USERS: Dict[str, str] = {
    "admin": "admin123",
    "operator": "operator123",
}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    expected_password = _USERS.get(payload.username)
    if expected_password is None or expected_password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = f"dev-{payload.username}-{secrets.token_hex(16)}"
    return LoginResponse(access_token=token)