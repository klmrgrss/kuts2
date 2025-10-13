# tests/auth/test_guards.py
import pytest

from auth.roles import allowed_roles


def test_dashboard_requires_auth(client):
    client.get("/logout")
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/" # Should redirect to landing page

def test_applicant_cannot_access_evaluator(authenticated_client):
    response = authenticated_client.get("/evaluator/d", follow_redirects=False)
    # Assert that an authorized but not permitted user gets a 403 Forbidden
    assert response.status_code == 403

def test_admin_can_access_evaluator(admin_client):
    # The admin client is already authenticated by the fixture
    response = admin_client.get("/evaluator/d", follow_redirects=False)
    # An admin should get a 200 OK, not a redirect
    assert response.status_code == 200
    admin_client.get("/logout")


def test_allowed_roles_rejects_unknown_role():
    with pytest.raises(ValueError):
        allowed_roles("unknown-role")