# tests/test_2applicants.py
import pytest
from starlette.testclient import TestClient
import time
import json
import base64
from itsdangerous import Signer

from app.controllers.evaluator import EvaluatorController
from app.logic.helpers import calculate_total_experience_years
from datetime import date
from main import db, SESSION_SECRET_KEY
from auth.roles import APPLICANT
from auth.utils import get_password_hash
from fastlite import NotFoundError

# Get a direct handle to the database for setup and assertions
users_table = db.t.users
qualifications_table = db.t.applied_qualifications
experience_table = db.t.work_experience
documents_table = db.t.documents


def _safe_delete(table, clause, params):
    for attempt in range(5):
        try:
            table.delete_where(clause, params)
            return
        except Exception as exc:
            if attempt == 4:
                print(f"--- ERROR [cleanup]: {exc} ---")
                raise
            time.sleep(0.1)


def _fetch_experience(email):
    for attempt in range(5):
        try:
            return experience_table("user_email = ?", [email])
        except Exception as exc:
            if attempt == 4:
                raise
            time.sleep(0.1)

def _setup_test_applicant(client: TestClient, email: str, full_name: str):
    """Helper to create a user and set up an authenticated session."""
    # --- Cleanup from previous runs ---
    _safe_delete(users_table, "email = ?", [email])
    _safe_delete(qualifications_table, "user_email = ?", [email])
    _safe_delete(experience_table, "user_email = ?", [email])
    _safe_delete(documents_table, "user_email = ?", [email])

    # --- Setup ---
    users_table.insert({
        "email": email, "hashed_password": get_password_hash("password123"), "full_name": full_name,
        "birthday": "1990-01-01", "role": APPLICANT, "national_id_number": f"test-{full_name.split()[0]}"
    }, pk='email')

    session_data = {"authenticated": True, "user_email": email, "role": APPLICANT}
    signer = Signer(SESSION_SECRET_KEY)
    signed_data = signer.sign(base64.b64encode(json.dumps(session_data).encode("utf-8")))
    client.cookies.set("session", signed_data.decode("utf-8"))

    # Add qualifications to make work experience tab available
    client.post("/app/kutsed/submit", data={"qual_1_0": "on"})


@pytest.fixture
def successful_applicant_client(client: TestClient):
    """
    Creates, authenticates, and sets up a 'successful' applicant.
    This fixture yields the authenticated client and then cleans up the user's data.
    """
    email = "successful.applicant@example.com"
    _setup_test_applicant(client, email, "Success Applicant")

    yield client # The test runs here

    # --- Teardown ---
    print(f"\n--- Cleaning up data for {email} ---")
    _safe_delete(users_table, "email = ?", [email])
    _safe_delete(qualifications_table, "user_email = ?", [email])
    _safe_delete(experience_table, "user_email = ?", [email])
    _safe_delete(documents_table, "user_email = ?", [email])


@pytest.fixture
def overlapping_applicant_client(client: TestClient):
    """
    Creates, authenticates, and sets up an applicant with overlapping experience.
    """
    email = "overlapping.applicant@example.com"
    _setup_test_applicant(client, email, "Overlapping Applicant")

    yield client

    # --- Teardown ---
    print(f"\n--- Cleaning up data for {email} ---")
    _safe_delete(users_table, "email = ?", [email])
    _safe_delete(qualifications_table, "user_email = ?", [email])
    _safe_delete(experience_table, "user_email = ?", [email])


def test_successful_applicant_scenario(successful_applicant_client: TestClient):
    """
    Tests a full scenario for an applicant who should meet the criteria.
    1. Submits multiple, non-overlapping work experiences.
    2. Has required documents (simulated by direct DB insertion).
    3. Final validation logic confirms eligibility.
    """
    email = "successful.applicant@example.com"
    client = successful_applicant_client

    # --- 1. Submit non-overlapping work experiences ---
    exp1 = {
        "associated_activity": "Üldehituslik ehitamine", "role": "Project Manager",
        "start_date": "2020-01", "end_date": "2021-12", # 2 years
        "object_address": "Success St 1"
    }
    exp2 = {
        "associated_activity": "Üldehituslik ehitamine", "role": "Site Manager",
        "start_date": "2022-01", "end_date": "2023-12", # 2 years
        "object_address": "Success St 2"
    }
    client.post("/app/workex/save", data=exp1)
    response = client.post("/app/workex/save", data=exp2)

    assert response.status_code == 200

    saved_addresses = {row["object_address"] for row in _fetch_experience(email)}
    assert {"Success St 1", "Success St 2"}.issubset(saved_addresses)

    # --- 2. Simulate document uploads ---
    # We insert directly to bypass complex GCS mocking for this scenario test
    documents_table.insert({
        "user_email": email, "document_type": "education",
        "original_filename": "diploma.pdf", "storage_identifier": "fake/path/diploma.pdf"
    })
    documents_table.insert({
        "user_email": email, "document_type": "training",
        "original_filename": "training.pdf", "storage_identifier": "fake/path/training.pdf"
    })

    # --- 3. Run validation logic and assert success ---
    # We instantiate the controller to get access to the validation engine
    evaluator_controller = EvaluatorController(db)
    applicant_data_for_validation = evaluator_controller._get_applicant_data_for_validation(email)

    # Assert that the total experience is calculated correctly (4 years)
    assert applicant_data_for_validation.work_experience_years == 4.0

    # Validate against the rules for "Ehituse tööjuht, tase 5"
    validation_results = evaluator_controller.validation_engine.validate(
        applicant_data_for_validation,
        "toojuht_tase_5"
    )

    # Check if any of the eligibility packages were met
    is_eligible = any(res['is_met'] for res in validation_results['results'])

    # This applicant (4 years experience, prior L4, training) should meet Variant 1
    assert is_eligible, "Applicant should have been found eligible but was not."
    assert validation_results['results'][0]['is_met'] == True # Specifically check Variant 1


def test_unsuccessful_applicant_overlapping_experience(overlapping_applicant_client: TestClient):
    """
    Tests a scenario for an applicant with overlapping job experience.
    The core assertion is that the `calculate_total_experience_years` helper
    correctly merges the periods and doesn't simply add them up.
    """
    client = overlapping_applicant_client
    email = "overlapping.applicant@example.com"

    # --- 1. Submit overlapping work experiences ---
    # Total unique period should be Jan 2020 to Dec 2022 = 3 years.
    # A naive sum would be 2 + 2 = 4 years.
    exp1 = {
        "associated_activity": "Üldehituslik ehitamine", "role": "Manager A",
        "start_date": "2020-01", "end_date": "2021-12", # 2 years
        "object_address": "Overlap St 1"
    }
    exp2 = {
        "associated_activity": "Üldehituslik ehitamine", "role": "Manager B",
        "start_date": "2021-01", "end_date": "2022-12", # 2 years
        "object_address": "Overlap St 2"
    }
    client.post("/app/workex/save", data=exp1)
    client.post("/app/workex/save", data=exp2)
    
    # --- 2. Verify the calculated total experience ---
    # We use the helper function directly to test the core logic
    periods = [
        (date(2020, 1, 1), date(2021, 12, 31)),
        (date(2021, 1, 1), date(2022, 12, 31))
    ]
    
    calculated_years = calculate_total_experience_years(periods)
    
    # Assert that the overlapping period was handled correctly
    assert calculated_years == 3.0
    assert calculated_years != 4.0