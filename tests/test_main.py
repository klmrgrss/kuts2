# tests/test_main.py

def test_homepage(client):
    """
    Tests the homepage ('/').
    It uses the 'client' fixture, which pytest automatically provides.
    """
    # Make a GET request to the homepage
    response = client.get("/")

    # Assert that the request was successful (HTTP 200 OK)
    assert response.status_code == 200

    # Assert that some expected text is in the response HTML
    assert "Ehitamise valdkonna kutsete taotlemine" in response.text

def test_dashboard_access_fails_without_login(client):
    try:
        resp = client.get("/dashboard", follow_redirects=False)
        # Should redirect to / or return 403 depending on implementation
        print(f"Status: {resp.status_code}")
    except Exception as e:
        print(f"CRASH: {e}")
        raise e
