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


def test_request_body_size_limit_content_length():
    """Test that requests with payload > 100KB are rejected with 413."""
    payload = {
        "layers": [{"h0": 300, "H": 50, "n_max": 1e12}],
        "min_h": 60,
        "max_h": 600,
        "steps": 100,
        # Add padding to exceed 100KB limit
        "padding": "A" * 105000
    }
    response = client.post("/api/ionosphere/profile", json=payload)
    assert response.status_code == 413
    assert response.json()["detail"] == "Payload Too Large"


def test_request_body_size_limit_chunked():
    """Test that chunked transfer encoding is blocked to prevent streaming DoS."""
    def generate_chunks():
        yield b'{"layers": [{"h0": 300, "H": 50, "n_max": 1e12}],'
        yield b'"min_h": 60, "max_h": 600, "steps": 100}'

    # By providing a generator, httpx will use Transfer-Encoding: chunked
    response = client.post("/api/ionosphere/profile", content=generate_chunks(), headers={"Content-Type": "application/json"})
    assert response.status_code == 411
    assert response.json()["detail"] == "Chunked encoding not supported"

def test_request_body_size_limit_get():
    """Test that GET requests with a large body are rejected."""
    payload = b"A" * 105000
    response = client.request("GET", "/api/health", content=payload)
    assert response.status_code == 413
    assert response.json()["detail"] == "Payload Too Large"
