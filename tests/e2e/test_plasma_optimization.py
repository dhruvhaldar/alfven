from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_plasma_parameters_endpoint():
    """
    Test that the batched endpoint returns correct values for both Debye Length and Plasma Frequency.
    """
    n = 1e6
    T_ev = 10

    # Call the new endpoint
    response = client.get(f"/api/plasma/parameters?n={n}&T_ev={T_ev}")

    # Expect 200 OK
    assert response.status_code == 200
    data = response.json()

    # Check keys exist
    assert "debye_length" in data
    assert "plasma_frequency" in data

    # Verify values against individual endpoints
    resp_debye = client.get(f"/api/plasma/debye?n={n}&T_ev={T_ev}")
    assert resp_debye.status_code == 200
    expected_debye = resp_debye.json()["debye_length"]

    resp_freq = client.get(f"/api/plasma/frequency?n={n}")
    assert resp_freq.status_code == 200
    expected_freq = resp_freq.json()["plasma_frequency"]

    # Assert equality (floating point comparison)
    assert abs(data["debye_length"] - expected_debye) < 1e-9
    assert abs(data["plasma_frequency"] - expected_freq) < 1e-9

def test_plasma_parameters_invalid_input():
    """
    Test invalid input handling for the new endpoint.
    """
    # Negative n
    response = client.get("/api/plasma/parameters?n=-1&T_ev=10")
    assert response.status_code == 422

    # Negative T_ev
    response = client.get("/api/plasma/parameters?n=1e6&T_ev=-5")
    assert response.status_code == 422
