import pytest
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_no_input_reflection():
    """
    Test that malicious input is not reflected in validation error messages.
    """
    # Trigger a 422 error by passing a string instead of a float
    response = client.get("/api/plasma/larmor?T_ev=script_injection_attempt&B=1")
    assert response.status_code == 422

    data = response.json()
    errors = data.get("detail", [])

    for error in errors:
        assert "input" not in error, "Security Vulnerability: Input was reflected in validation error!"
        assert "url" not in error, "Security Vulnerability: URL was reflected in validation error!"
