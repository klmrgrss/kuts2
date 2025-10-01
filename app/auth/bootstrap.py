"""Utility helpers for bootstrapping default accounts.

This module centralises the logic that creates or updates evaluator and
applicant accounts that should always exist in the system.  It is designed to
run during application start-up as well as from ad-hoc scripts such as
``promote_user.py``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional

from fastlite import NotFoundError

from auth.utils import get_password_hash


@dataclass
class DefaultUser:
    """Represents a user that should exist in the database."""

    email: str
    password: Optional[str]
    role: str = "applicant"
    full_name: Optional[str] = None
    birthday: Optional[str] = None


def ensure_default_users(db) -> None:
    """Ensure that pre-defined accounts exist in the database.

    The function reads configuration from environment variables and then
    creates or updates the accounts accordingly.  It is intentionally tolerant
    so that providing no configuration simply results in a no-op.
    """

    users_to_ensure = _load_default_users_from_env()
    if not users_to_ensure:
        print("--- Default user bootstrap: nothing to do ---")
        return

    force_reset = _is_truthy(os.getenv("DEFAULT_USERS_FORCE_RESET", "true"))
    default_birthday = os.getenv("DEFAULT_USERS_DEFAULT_BIRTHDAY", "1900-01-01")

    users_table = db.t.users

    for user in users_to_ensure:
        email = user.email.strip().lower()
        role = user.role or "applicant"
        full_name = user.full_name or email.split("@")[0]
        birthday = user.birthday or default_birthday

        hashed_password = (
            get_password_hash(user.password) if user.password else None
        )

        try:
            existing = users_table[email]
            updates = {}

            if existing.get("role") != role:
                updates["role"] = role

            if hashed_password and (
                force_reset or not existing.get("hashed_password")
            ):
                updates["hashed_password"] = hashed_password

            if full_name and not existing.get("full_name"):
                updates["full_name"] = full_name

            if birthday and not existing.get("birthday"):
                updates["birthday"] = birthday

            if updates:
                users_table.update(updates, pk_values=email)
                print(
                    f"--- Default user bootstrap: updated existing user '{email}' ({', '.join(updates.keys())}) ---"
                )
            else:
                print(
                    f"--- Default user bootstrap: user '{email}' already configured ---"
                )

        except NotFoundError:
            if not hashed_password:
                print(
                    f"--- Default user bootstrap: skipping '{email}' because no password was provided ---"
                )
                continue

            new_user = {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "birthday": birthday,
                "role": role,
            }
            users_table.insert(new_user, pk="email")
            print(
                f"--- Default user bootstrap: created user '{email}' with role '{role}' ---"
            )


def _load_default_users_from_env() -> List[DefaultUser]:
    """Load ``DefaultUser`` definitions from the environment.

    The primary configuration surface is ``DEFAULT_USERS`` which accepts either
    JSON or a simple ``email|password|role`` newline/comma separated format.
    For backwards compatibility we also honour ``EVALUATOR_EMAILS`` and
    ``DEFAULT_EVALUATOR_PASSWORD``.
    """

    configured_users: List[DefaultUser] = []

    raw = os.getenv("DEFAULT_USERS")
    if raw:
        raw = raw.strip()
        if raw:
            parsed = _parse_default_users(raw)
            configured_users.extend(parsed)

    if configured_users:
        return configured_users

    legacy_emails = os.getenv("EVALUATOR_EMAILS")
    if legacy_emails:
        password = os.getenv("DEFAULT_EVALUATOR_PASSWORD", "Password123!")
        for email in _split_entries(legacy_emails):
            configured_users.append(
                DefaultUser(email=email, password=password, role="evaluator")
            )

    return configured_users


def _parse_default_users(raw: str) -> List[DefaultUser]:
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        index = 0
        parsed_objects = []
        raw_length = len(raw)

        while index < raw_length:
            while index < raw_length and raw[index] in " \t\r\n;":
                index += 1

            if index >= raw_length:
                break

            if raw[index] != "{":
                parsed_objects = []
                break

            try:
                obj, next_index = decoder.raw_decode(raw, index)
            except json.JSONDecodeError:
                parsed_objects = []
                break

            parsed_objects.append(obj)
            index = next_index

        if parsed_objects:
            loaded = parsed_objects
        else:
            if "{" in raw:
                print(
                    "--- Default user bootstrap: no valid JSON objects found in DEFAULT_USERS ---"
                )
            return _parse_simple_default_users(raw)

    if isinstance(loaded, dict):
        loaded = [loaded]

    users: List[DefaultUser] = []
    for entry in loaded or []:
        if not isinstance(entry, dict):
            continue
        email = entry.get("email")
        password = entry.get("password")
        role = entry.get("role", "applicant")
        full_name = entry.get("full_name")
        birthday = entry.get("birthday")
        if email:
            users.append(
                DefaultUser(
                    email=email,
                    password=password,
                    role=role,
                    full_name=full_name,
                    birthday=birthday,
                )
            )
    return users


def _parse_simple_default_users(raw: str) -> List[DefaultUser]:
    users: List[DefaultUser] = []
    for entry in _split_entries(raw):
        if entry.strip().startswith("{"):
            continue
        delimiter = "|" if "|" in entry else ":"
        parts = [part.strip() for part in entry.split(delimiter) if part.strip()]
        if len(parts) < 2:
            continue
        email, password = parts[0], parts[1]
        role = parts[2] if len(parts) > 2 else "applicant"
        users.append(DefaultUser(email=email, password=password, role=role))
    return users


def _split_entries(raw: str) -> Iterable[str]:
    for chunk in raw.replace(";", "\n").replace(",", "\n").splitlines():
        chunk = chunk.strip()
        if chunk:
            yield chunk


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}

