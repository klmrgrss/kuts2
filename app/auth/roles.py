"""Role vocabulary and helper utilities for RBAC."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

APPLICANT: str = 'applicant'
EVALUATOR: str = 'evaluator'
ADMIN: str = 'admin'

ALL_ROLES: Tuple[str, ...] = (APPLICANT, EVALUATOR, ADMIN)


def normalize_role(value: str | None, default: str = APPLICANT) -> str:
    """Normalise arbitrary role values to the canonical vocabulary."""
    if not value:
        return default
    lowered = value.strip().lower()
    if lowered in ALL_ROLES:
        return lowered
    return default


def is_applicant(role: str | None) -> bool:
    role = normalize_role(role)
    return role == APPLICANT


def is_evaluator(role: str | None) -> bool:
    role = normalize_role(role)
    return role in (EVALUATOR, ADMIN)


def is_admin(role: str | None) -> bool:
    role = normalize_role(role)
    return role == ADMIN


@dataclass(frozen=True)
class RoleLabels:
    """Human-friendly labels for rendering navigation and UI copy."""

    applicant: str = 'Taotleja'
    evaluator: str = 'Hindaja'
    admin: str = 'Administraator'


ROLE_LABELS = RoleLabels()


def allowed_roles(*roles: str) -> Tuple[str, ...]:
    """Validate a declaration of allowed roles and return the tuple."""
    normalised = tuple(normalize_role(role, default="") for role in roles)
    for role in normalised:
        if role not in ALL_ROLES:
            raise ValueError(f"Unknown role '{role}' declared in guard")
    return normalised


def describe_roles(roles: Iterable[str]) -> str:
    """Return a comma-separated description for debugging/logging."""
    return ', '.join(sorted({normalize_role(role) for role in roles}))
