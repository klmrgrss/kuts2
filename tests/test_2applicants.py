import pytest
from starlette.testclient import TestClient
from app.database import setup_database
from app.controllers.evaluator import EvaluatorController
from app.logic.helpers import calculate_total_experience_years
from datetime import date

# Get a direct handle to the database for setup and assertions
db = setup_database()
users_table = db.t.users
qualifications_table = db.t.applied_qualifications
experience_table = db.t.work_experience
documents_table = db.t.documents

@pytest.fixture
def successful_applicant_client(client: TestClient):
    """
    Creates, authenticates, and sets up a 'successful' applicant.
    This fixture yields the authenticated client and then cleans up the user's data.
    """
    email = "successful.applicant@example.com"
    
    # --- Setup ---
    client.post("/register", data={
        "email": email, "password": "password123", "confirm_password": "password123",
        "full_name": "Success Applicant", "birthday": "1990-05-15"
    })
    client.post("/login", data={"email": email, "password": "password123"})
    
    # Add qualifications to make work experience tab available
    client.post("/app/kutsed/submit", data={"qual_1_0": "on"})

    yield client # The test runs here

    # --- Teardown ---
    print(f"\n--- Cleaning up data for {email} ---")
    users_table.delete_where("email = ?", [email])
    qualifications_table.delete_where("user_email = ?", [email])
    experience_table.delete_where("user_email = ?", [email])
    documents_table.delete_where("user_email = ?", [email])


@pytest.fixture
def overlapping_applicant_client(client: TestClient):
    """
    Creates, authenticates, and sets up an applicant with overlapping experience.
    """
    email = "overlapping.applicant@example.com"
    
    # --- Setup ---
    client.post("/register", data={
        "email": email, "password": "password123", "confirm_password": "password123",
        "full_name": "Overlapping Applicant", "birthday": "1985-10-20"
    })
    client.post("/login", data={"email": email, "password": "password123"})
    client.post("/app/kutsed/submit", data={"qual_1_0": "on"})


    yield client

    # --- Teardown ---
    print(f"\n--- Cleaning up data for {email} ---")
    users_table.delete_where("email = ?", [email])
    qualifications_table.delete_where("user_email = ?", [email])
    experience_table.delete_where("user_email = ?", [email])


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
    assert "Success St 1" in response.text
    assert "Success St 2" in response.text

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
