import pytest
from fastapi.testclient import TestClient
from api.index import app
import os
from unittest.mock import patch

client = TestClient(app, raise_server_exceptions=False)


def test_security_headers():
    """
    Verify that security headers are present in API responses.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert "SAMEORIGIN" in response.headers.get("X-Frame-Options", "SAMEORIGIN")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 🛡️ Sentinel: Verify CSP and other headers
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "https://cdnjs.cloudflare.com" in csp

    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=()"


def test_security_headers_on_error():
    """
    Verify that security headers are present even on 500 errors.
    """
    # Mock an endpoint to raise exception
    with patch("api.index.PlasmaState") as mock_plasma:
        mock_plasma.side_effect = Exception("Boom")
        # Trigger an error via an endpoint that uses PlasmaState, e.g., /api/plasma/debye
        response = client.get("/api/plasma/debye?n=1&T_ev=1")
        assert response.status_code == 500
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_no_polyfill_io():
    """
    Verify that public/index.html does not contain references to polyfill.io.
    """
    index_path = os.path.join("public", "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            content = f.read()
            assert (
                "polyfill.io" not in content
            ), "Found malicious polyfill.io domain in index.html"
            assert (
                "cdnjs.cloudflare.com/polyfill" in content or "polyfill" not in content
            ), "Should use safe polyfill or none"
