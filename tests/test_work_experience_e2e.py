# tests/test_work_experience_e2e.py
import time

import pytest
from starlette.testclient import TestClient
from main import db

# Get a direct handle to the database for assertions
experience_table = db.t.work_experience

@pytest.fixture(autouse=True)
def cleanup_db_after_test(authenticated_client: TestClient):
    """A fixture to clean up test data after each test in this file."""
    yield
    # This code runs after the test is complete
    print("\n--- Cleaning up test work experience ---")
    for attempt in range(5):
        try:
            experience_table.delete_where("object_address = ?", ["999 E2E Test Lane"])
            break
        except Exception as exc:
            if attempt == 4:
                raise
            time.sleep(0.1)


def test_add_and_verify_work_experience(authenticated_client: TestClient):
    """
    Tests the full end-to-end flow:
    1. POST a new work experience.
    2. Assert the immediate response looks correct.
    3. Directly query the database to verify the record was created correctly.
    """
    form_data = {
        "associated_activity": "Üldehituslik ehitamine",
        "role": "E2E Test Role",
        "contract_type": "ATV",
        "start_date": "2024-01",
        "work_description": "End-to-end test submission.",
        "object_address": "999 E2E Test Lane", # Unique address for easy querying
        "company_name": "Pytest LLC",
        "permit_required": "on",
    }

    # --- 1. POST the new work experience ---
    response = authenticated_client.post("/app/workex/save", data=form_data)

    # --- 2. Assert the immediate response ---
    assert response.status_code == 200

    # --- 3. Verify directly in the database ---
    # FIX: Correct the fastlite query syntax.
    # The `where` clause and parameters are positional arguments.
    for attempt in range(5):
        try:
            saved_records = experience_table("object_address = ?", ["999 E2E Test Lane"])
            break
        except Exception as exc:
            if attempt == 4:
                raise
            time.sleep(0.1)

    # Assert that exactly one record was found
    assert len(saved_records) == 1
    
    saved_record = saved_records[0]

    # Assert that the data in the database matches what we submitted
    assert saved_record['role'] == "E2E Test Role"
    assert saved_record['user_email'] == "test_user@example.com" # From conftest
    assert saved_record['contract_type'] == "ATV"