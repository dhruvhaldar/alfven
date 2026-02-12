from fastapi.testclient import TestClient
from unittest.mock import patch
from api.index import app

client = TestClient(app, raise_server_exceptions=False)

def test_api_security_invalid_inputs():
    # Test Debye Length with negative n
    response = client.get("/api/plasma/debye?n=-1&T_ev=10")
    assert response.status_code == 422

    # Test Debye Length with n=0
    response = client.get("/api/plasma/debye?n=0&T_ev=10")
    assert response.status_code == 422

    # Test Larmor Radius with B=0
    response = client.get("/api/plasma/larmor?T_ev=10&B=0")
    assert response.status_code == 422

    # Test Plasma Frequency with negative n
    response = client.get("/api/plasma/frequency?n=-1")
    assert response.status_code == 422

    # Test Parker Spiral with negative r
    response = client.get("/api/solar/parker?r=-1")
    assert response.status_code == 422

    # Test Magnetosphere Standoff with negative density
    response = client.get("/api/magnetosphere/standoff?density=-1&velocity=400&Bz=0")
    assert response.status_code == 422

def test_global_exception_handler():
    # Mock PlasmaState to raise an unexpected exception
    with patch("api.index.PlasmaState") as mock_plasma:
        mock_plasma.side_effect = Exception("Unexpected failure")

        # Call an endpoint that uses PlasmaState
        response = client.get("/api/plasma/debye?n=10&T_ev=10")

        # Verify it returns 500 and the generic error message
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}
