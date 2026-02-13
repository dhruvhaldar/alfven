from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app, raise_server_exceptions=False)

def test_ionosphere_profile_steps_limit():
    """Test that requests with steps > 2000 are rejected."""
    payload = {
        "layers": [{"h0": 300, "H": 50, "n_max": 1e12}],
        "min_h": 60,
        "max_h": 600,
        "steps": 2001 # Exceeds limit
    }
    response = client.post("/api/ionosphere/profile", json=payload)
    assert response.status_code == 422
    # Pydantic v2 error format
    errors = response.json()["detail"]
    found = False
    for error in errors:
        if error["loc"] == ["body", "steps"] and "less than or equal to 2000" in error["msg"]:
            found = True
            break
    assert found, f"Expected error about steps limit, got: {response.json()}"

def test_ionosphere_profile_layers_limit():
    """Test that requests with too many layers are rejected."""
    payload = {
        "layers": [{"h0": 300, "H": 50, "n_max": 1e12}] * 21, # Exceeds limit
        "min_h": 60,
        "max_h": 600,
        "steps": 100
    }
    response = client.post("/api/ionosphere/profile", json=payload)
    assert response.status_code == 422
    # Custom validator error
    errors = response.json()["detail"]
    found = False
    for error in errors:
        if error["loc"] == ["body", "layers"] and "Too many layers (max 20)" in error["msg"]:
            found = True
            break
    assert found, f"Expected error about layers limit, got: {response.json()}"

def test_ionosphere_profile_valid():
    """Test that valid requests are accepted."""
    payload = {
        "layers": [{"h0": 300, "H": 50, "n_max": 1e12}] * 20, # Max allowed
        "min_h": 60,
        "max_h": 600,
        "steps": 2000 # Max allowed
    }
    response = client.post("/api/ionosphere/profile", json=payload)
    assert response.status_code == 200
