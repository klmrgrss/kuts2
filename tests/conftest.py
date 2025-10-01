# tests/conftest.py
import pytest
from starlette.testclient import TestClient
import sys
import os

# --- The Workaround ---
# Manually add the 'app' directory to the system path
# so that pytest can find modules like 'controllers' and 'ui'
app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app'))
sys.path.insert(0, app_path)
# --- End Workaround ---

from main import app # Now we can import 'main' directly

@pytest.fixture(scope="session")
def client():
    """
    A pytest fixture that provides a basic TestClient instance for our application.
    """
    with TestClient(app) as client:
        yield client

@pytest.fixture(scope="session")
def authenticated_client(client):
    """
    Provides an authenticated TestClient.
    Registers a dummy user and logs them in, then yields the client.
    """
    # Ensure the user exists (register if not)
    register_data = {
        "email": "test_user@example.com",
        "password": "test_password",
        "confirm_password": "test_password",
        "full_name": "Test User",
        "birthday": "2000-01-01"
    }
    # Attempt to register. If user already exists, the app will return an error,
    # but the login will still work.
    client.post("/register", data=register_data)

    # Log in the dummy user
    login_data = {
        "email": "test_user@example.com",
        "password": "test_password"
    }
    # Perform the login. The TestClient will automatically manage the session cookie.
    client.post("/login", data=login_data)
    client.get("/dashboard")

    # --- NEW: Select some qualifications for the test user ---
    # This data needs to match the expected format for /app/kutsed/submit
    # Based on app/ui/qualification_form.py and controllers/qualifications.py
    # It seems to expect form data like 'qual_SECTIONID_ITEMINDEX=on'
    qualification_data = {
        "qual_1_0": "on", # Assuming section 1, first item is a valid qualification
        # Add other required form fields if any for /app/kutsed/submit
    }
    # Submit qualifications for the authenticated client
    client.post("/app/kutsed/submit", data=qualification_data)
    # --- END NEW ---

    yield client # Yield the client, which is now authenticated