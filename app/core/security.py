"""Security abstractions for authentication and authorization."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class AuthContext:
    subject: str
    roles: list[str]


class TokenValidator(Protocol):
    def validate(self, token: str) -> AuthContext:
        ...


def resolve_roles(context: AuthContext) -> set[str]:
    return set(context.roles)

