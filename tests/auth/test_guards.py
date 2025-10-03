import pytest

from auth.roles import allowed_roles


def test_dashboard_requires_auth(client):
    client.get("/logout")
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_applicant_cannot_access_evaluator(authenticated_client):
    response = authenticated_client.get("/evaluator/d", follow_redirects=False)
    assert response.status_code == 403


def test_admin_can_access_evaluator(client):
    client.get("/logout")
    login_data = {"email": "admin@example.com", "password": "ChangeMe123!"}
    login_response = client.post("/login", data=login_data, follow_redirects=False)
    assert login_response.status_code in (303, 200)
    client.get("/dashboard")
    response = client.get("/evaluator/d", follow_redirects=False)
    assert response.status_code != 403
    client.get("/logout")


def test_allowed_roles_rejects_unknown_role():
    with pytest.raises(ValueError):
        allowed_roles("unknown-role")
