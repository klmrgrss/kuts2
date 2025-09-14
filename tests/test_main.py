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
