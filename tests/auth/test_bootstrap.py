import importlib
import json

import pytest

from auth.utils import verify_password, get_password_hash


@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    for key in [
        "DEFAULT_USERS",
        "DEFAULT_USERS_FORCE_RESET",
        "DEFAULT_USERS_DEFAULT_BIRTHDAY",
        "EVALUATOR_EMAILS",
        "DEFAULT_EVALUATOR_PASSWORD",
        "DATABASE_FILE_PATH",
    ]:
        monkeypatch.delenv(key, raising=False)

    db_path = tmp_path / "test_app.db"
    monkeypatch.setenv("DATABASE_FILE_PATH", str(db_path))

    import app.database as database_module

    importlib.reload(database_module)
    db = database_module.setup_database()
    try:
        yield db
    finally:
        monkeypatch.delenv("DATABASE_FILE_PATH", raising=False)
        importlib.reload(database_module)


def test_default_users_created(monkeypatch, isolated_db):
    db = isolated_db

    config = [
        {"email": "evaluator@example.com", "password": "Secret123!", "role": "evaluator"},
        {"email": "applicant@example.com", "password": "Secret456!"},
    ]
    monkeypatch.setenv("DEFAULT_USERS", json.dumps(config))

    from auth.bootstrap import ensure_default_users

    ensure_default_users(db)

    users = db.t.users
    evaluator = users["evaluator@example.com"]
    applicant = users["applicant@example.com"]

    assert evaluator["role"] == "evaluator"
    assert verify_password("Secret123!", evaluator["hashed_password"])
    assert applicant["role"] == "applicant"
    assert verify_password("Secret456!", applicant["hashed_password"])

def test_default_users_do_not_override_password_when_disabled(monkeypatch, isolated_db):
    db = isolated_db

    existing_password = get_password_hash("OldSecret!1")
    db.t.users.insert(
        {
            "email": "existing@example.com",
            "hashed_password": existing_password,
            "full_name": "Existing",
            "birthday": "1990-01-01",
            "role": "applicant",
        },
        pk="email",
    )

    monkeypatch.setenv("DEFAULT_USERS_FORCE_RESET", "false")
    monkeypatch.setenv(
        "DEFAULT_USERS",
        json.dumps([
            {"email": "existing@example.com", "password": "NewPassword!2", "role": "evaluator"}
        ]),
    )

    from auth.bootstrap import ensure_default_users

    ensure_default_users(db)

    user = db.t.users["existing@example.com"]
    # Role should be updated but password must remain the same
    assert user["role"] == "evaluator"
    assert verify_password("OldSecret!1", user["hashed_password"])
    assert not verify_password("NewPassword!2", user["hashed_password"])


def test_newline_separated_json_users(monkeypatch, isolated_db):
    db = isolated_db

    raw = "\n".join(
        [
            '{"email": "first@example.com", "password": "FirstPass!1", "role": "evaluator"}',
            '{"email": "second@example.com", "password": "SecondPass!2"}',
        ]
    )

    monkeypatch.setenv("DEFAULT_USERS", raw)

    from auth.bootstrap import ensure_default_users

    ensure_default_users(db)

    users = db.t.users
    first = users["first@example.com"]
    second = users["second@example.com"]

    assert first["role"] == "evaluator"
    assert second["role"] == "applicant"
    assert verify_password("FirstPass!1", first["hashed_password"])
    assert verify_password("SecondPass!2", second["hashed_password"])


def test_comma_separated_json_users(monkeypatch, isolated_db):
    db = isolated_db

    raw = ",".join(
        [
            '{"email": "comma1@example.com", "password": "CommaPass!1", "role": "evaluator"}',
            '{"email": "comma2@example.com", "password": "CommaPass!2", "role": "applicant"}',
        ]
    )

    monkeypatch.setenv("DEFAULT_USERS", raw)

    from auth.bootstrap import ensure_default_users

    ensure_default_users(db)

    users = db.t.users
    first = users["comma1@example.com"]
    second = users["comma2@example.com"]

    assert first["role"] == "evaluator"
    assert second["role"] == "applicant"
    assert verify_password("CommaPass!1", first["hashed_password"])
    assert verify_password("CommaPass!2", second["hashed_password"])


def test_admin_seed_created_when_missing(isolated_db):
    from auth.bootstrap import ensure_default_users

    ensure_default_users(isolated_db)

    admin_row = isolated_db.execute(
        "SELECT email, role, hashed_password FROM users WHERE role = 'admin'"
    ).fetchone()

    assert admin_row is not None
    email, role, hashed_password = admin_row
    assert email
    assert hashed_password
