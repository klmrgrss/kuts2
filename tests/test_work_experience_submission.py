# tests/test_work_experience_submission.py
import pytest
from starlette.testclient import TestClient

# The 'authenticated_client' fixture is automatically provided by tests/conftest.py

def test_submit_new_work_experience_v2(authenticated_client: TestClient):
    """
    Tests submitting a new work experience form with valid data using the V2 endpoint.
    """
    # Define all the form fields and their values as a dictionary.
    # This must match the fields in the V2 form.
    form_data = {
        "associated_activity": "Üldehituslik ehitamine",
        "role": "Test Role",
        "contract_type": "PTV",
        "start_date": "2023-01",
        "end_date": "2024-06",
        "work_keywords": "Testing, Pytest",
        "work_description": "A work experience entry created by an automated test.",
        "object_address": "123 Test Street",
        "object_purpose": "Testing Facility",
        "ehr_code": "TEST123456",
        "permit_required": "on",
        "company_name": "Test Inc.",
        "company_code": "12345678",
        "company_contact": "Test Contact",
        "company_email": "contact@testinc.com",
        "company_phone": "555-0101",
        "client_name": "Test Client",
        "client_code": "87654321",
        "client_contact": "Client Contact",
        "client_email": "contact@client.com",
        "client_phone": "555-0102",
    }

    # Simulate a POST request to the new V2 submission endpoint
    response = authenticated_client.post("/app/workex/save", data=form_data)

    # Assert that the request was successful (HTTP 200 OK)
    assert response.status_code == 200

    # The new controller method re-renders the entire tab.
    # A good assertion is to check for a key element that should be present on that page.
    # For example, we can check for the title of the page or a specific form element.
    # Let's check for the newly created entry's address in the response text.
    assert '123 Test Street' in response.text
    
    # We can also assert that the response is a full HTML fragment for the tab,
    # for instance by checking for the main container ID.
    assert 'id="work-experience-form-v2-container"' in response.text

    # And we can assert that the OLD response fragment is NOT present
    assert 'id="add-button-container"' not in response.text