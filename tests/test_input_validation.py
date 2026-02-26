import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_rate_limit():
    request_counts.clear()

def test_magnetosphere_standoff_infinite_validation():
    """
    Test that extremely small density/velocity values are rejected with 422.
    """
    try:
        response = client.get("/api/magnetosphere/standoff?density=1e-300&velocity=1e-10")
        assert response.status_code == 422
    except ValueError:
        pytest.fail("Endpoint crashed with ValueError instead of returning 422")

def test_larmor_radius_infinite_validation():
    """
    Test that extremely small B field is rejected with 422.
    """
    try:
        response = client.get("/api/plasma/larmor?T_ev=10&B=1e-300")
        assert response.status_code == 422
    except ValueError:
        pytest.fail("Endpoint crashed with ValueError instead of returning 422")

def test_aurora_power_infinite_validation():
    """
    Test that large inputs are rejected with 422.
    """
    payload = {
        "E_field": 1e300,
        "sigma_P": 1e300,
        "area": 1e300
    }
    try:
        response = client.post("/api/aurora/power", json=payload)
        assert response.status_code == 422
    except ValueError:
        pytest.fail("Endpoint crashed with ValueError instead of returning 422")
