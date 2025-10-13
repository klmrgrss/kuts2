"""Regression tests for authentication middleware."""

import base64
import json

import pytest
from itsdangerous import Signer

from auth.roles import ADMIN, APPLICANT
from auth.utils import get_password_hash
from fastlite import NotFoundError
from main import SESSION_SECRET_KEY, db


def _legacy_session_cookie(payload: dict[str, object]) -> str:
    signer = Signer(SESSION_SECRET_KEY)
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8"))
    return signer.sign(encoded).decode("utf-8")


@pytest.fixture
def _cleanup_user():
    created_emails: list[str] = []

    yield created_emails

    for email in created_emails:
        try:
            db.t.users.delete(email)
        except NotFoundError:
            pass


def _provision_user(email: str, role: str, cleanup: list[str]) -> None:
    try:
        db.t.users.delete(email)
    except NotFoundError:
        pass

    db.t.users.insert(
        {
            "email": email,
            "hashed_password": get_password_hash("unused"),
            "full_name": "Legacy User",
            "birthday": "1990-01-01",
            "role": role,
            "national_id_number": f"legacy-{role}",
        },
        pk="email",
    )
    cleanup.append(email)


def test_legacy_cookie_allows_admin_access(client, _cleanup_user):
    client.cookies.clear()
    email = "legacy.admin@example.com"
    _provision_user(email, ADMIN, _cleanup_user)

    client.cookies.set(
        "session",
        _legacy_session_cookie({"authenticated": True, "user_email": email, "role": ADMIN}),
    )

    response = client.get("/evaluator/d", follow_redirects=False)
    assert response.status_code == 200


def test_legacy_cookie_preserves_role_checks(client, _cleanup_user):
    client.cookies.clear()
    email = "legacy.applicant@example.com"
    _provision_user(email, APPLICANT, _cleanup_user)

    client.cookies.set(
        "session",
        _legacy_session_cookie({"authenticated": True, "user_email": email, "role": APPLICANT}),
    )

    response = client.get("/evaluator/d", follow_redirects=False)
    assert response.status_code == 403
