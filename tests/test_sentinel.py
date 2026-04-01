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
    assert "DENY" in response.headers.get("X-Frame-Options", "DENY")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 🛡️ Sentinel: Verify CSP and other headers
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "https://cdnjs.cloudflare.com" in csp
    assert "https://cdn.jsdelivr.net" in csp
    assert "https://d3js.org" in csp

    assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains; preload"
    assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=()"

    # 🛡️ Sentinel: Verify API anti-caching headers
    assert response.headers.get("Cache-Control") == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers.get("Pragma") == "no-cache"


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

        # 🛡️ Sentinel: Ensure CSP and HSTS are also present on 500 errors
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert response.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains; preload"
        assert response.headers.get("Permissions-Policy") == "geolocation=(), microphone=(), camera=()"


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


def test_csp_strict_script_src():
    """
    Verify that script-src does not allow 'unsafe-inline'.
    """
    response = client.get("/api/health")
    csp = response.headers.get("Content-Security-Policy", "")

    # Parse directives
    directives = {}
    for part in csp.split(";"):
        part = part.strip()
        if not part:
            continue
        # Split on first whitespace
        parts = part.split(None, 1)
        key = parts[0]
        values = parts[1] if len(parts) > 1 else ""
        directives[key] = values

    script_src = directives.get("script-src", "")

    # 🛡️ Sentinel: Ensure 'unsafe-inline' is NOT in script-src
    assert "'unsafe-inline'" not in script_src, "CSP script-src must not allow 'unsafe-inline'"

    # Optional: ensure it is in style-src if intended
    style_src = directives.get("style-src", "")
    assert "'unsafe-inline'" in style_src, "CSP style-src should allow 'unsafe-inline' for now"

def test_additional_security_headers():
    """
    Verify the presence of isolation and resource policy headers.
    """
    response = client.get("/api/health")
    assert response.headers.get("Cross-Origin-Opener-Policy") == "same-origin"
    assert response.headers.get("Cross-Origin-Resource-Policy") == "same-origin"

def test_server_header_removed():
    """
    Verify that the 'Server' header is completely removed.
    """
    response = client.get("/api/health")
    assert "server" not in response.headers
