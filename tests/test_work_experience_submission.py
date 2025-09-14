# tests/test_work_experience_submission.py
import pytest
from starlette.testclient import TestClient

# The 'client' fixture is automatically provided by tests/conftest.py

def test_submit_new_work_experience(authenticated_client: TestClient):
    """
    Tests submitting a new work experience form with valid data.
    """
    # Define all the form fields and their values as a dictionary
    # Make sure to include all required fields!
    form_data = {
        "associated_activity": "Üldehituslik ehitamine", # Example activity
        "role": "Projektijuht",
        "contract_type": "PTV",
        "start_date": "2023-01",
        "end_date": "2024-06",
        "work_keywords": "Vundamenditööd, Betoonitööd",
        "work_description": "Eramu ehitus nullist võtmed kätte lahendusena.",
        "company_name": "Test Ehitus OÜ",
        "company_code": "12345678",
        "company_contact": "Jaan Tamm",
        "company_email": "jaan.tamm@test.ee",
        "company_phone": "+37255512345",
        "object_address": "Näidis tn 1, Tallinn",
        "object_purpose": "Elamu",
        "ehr_code": "123456789",
        "permit_required": "on", # Checkbox value
        "client_name": "Mati Maasikas",
        "client_code": "87654321",
        "client_contact": "Mari Maasikas",
        "client_email": "mari.maasikas@example.com",
        "client_phone": "+37255598765",
    }

    # Simulate a POST request to the form's submission endpoint
    response = authenticated_client.post("/app/tookogemus/save", data=form_data)

    assert response.status_code == 200

    # Assert that the response contains some expected HTMX fragments
    # Check for the presence of the 'add-button-container' which indicates the form was cleared and button shown.
    assert 'id="add-button-container"' in response.text
    assert 'hx-swap-oob="outerHTML"' in response.text # Confirm it's an OOB swap

    # Assert that the form-error-message is NOT present
    assert 'id="form-error-message"' not in response.text
