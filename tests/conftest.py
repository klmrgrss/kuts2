# tests/conftest.py
import pytest
from starlette.testclient import TestClient
import sys
import os
import json
import base64
from itsdangerous import Signer
from fastlite import NotFoundError

# --- The Workaround ---
# Manually add the 'app' directory to the system path
# so that pytest can find modules like 'controllers' and 'ui'
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, app_path)
# --- End Workaround ---

from main import app, db, SESSION_SECRET_KEY
from auth.utils import get_password_hash
from auth.roles import APPLICANT, ADMIN

@pytest.fixture(scope="session")
def client():
    """
    A pytest fixture that provides a basic TestClient instance for our application.
    """
    with TestClient(app) as client:
        yield client

def _create_auth_client(base_client: TestClient, email: str, role: str, full_name: str) -> TestClient:
    """Helper factory to create a user and return an authenticated client."""
    # 1. Ensure user exists in the database
    try:
        db.t.users.delete(email)
    except NotFoundError:
        pass  # User didn't exist, which is fine

    db.t.users.insert({
        "email": email,
        "hashed_password": get_password_hash("test_password"),
        "full_name": full_name,
        "birthday": "2000-01-01",
        "role": role,
        "national_id_number": f"_test_{email.split('@')[0]}"
    }, pk='email')

    # 2. Create and sign the session data
    session_data = {
        "authenticated": True,
        "user_email": email,
        "role": role
    }
    signer = Signer(SESSION_SECRET_KEY)
    # Starlette's SessionMiddleware b64-encodes the JSON before signing
    signed_data = signer.sign(base64.b64encode(json.dumps(session_data).encode("utf-8")))

    # 3. Set the cookie on the client
    base_client.cookies.clear()
    base_client.cookies.set("session", signed_data.decode("utf-8"))
    
    return base_client

@pytest.fixture
def authenticated_client(client: TestClient):
    """Provides an authenticated TestClient with an 'applicant' role."""
    email = "test_user@example.com"
    _create_auth_client(client, email, APPLICANT, "Test Applicant")
    
    # Select some qualifications for the test user
    client.post("/app/kutsed/submit", data={"qual_1_0": "on"})

    yield client
    
    # Teardown
    try:
        db.t.users.delete(email)
    except NotFoundError:
        pass

@pytest.fixture
def admin_client(client: TestClient):
    """Provides an authenticated TestClient with an 'admin' role."""
    email = "test_admin@example.com"
    _create_auth_client(client, email, ADMIN, "Test Admin")

    yield client

    # Teardown
    try:
        db.t.users.delete(email)
    except NotFoundError:
        pass