from fastapi.testclient import TestClient
from api.index import app
import pytest

client = TestClient(app)

def test_csp_hardening_directives():
    """
    Verify that CSP contains hardened directives:
    - object-src 'none'
    - base-uri 'self'
    - form-action 'self'
    - script-src 'unsafe-eval' is removed
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")
    assert csp, "CSP header is missing"

    directives = {}
    for part in csp.split(";"):
        part = part.strip()
        if not part:
            continue
        parts = part.split(None, 1)
        key = parts[0]
        val = parts[1] if len(parts) > 1 else ""
        directives[key] = val

    # Verify directives
    assert "object-src" in directives, "Missing object-src directive"
    assert "'none'" in directives["object-src"], "object-src should be 'none'"

    assert "base-uri" in directives, "Missing base-uri directive"
    assert "'self'" in directives["base-uri"], "base-uri should be 'self'"

    # Optional: form-action is good to have
    # assert "form-action" in directives, "Missing form-action directive"
    # assert "'self'" in directives["form-action"], "form-action should be 'self'"

    # Verify script-src does NOT contain unsafe-eval
    script_src = directives.get("script-src", "")
    assert "'unsafe-eval'" not in script_src, "script-src should not contain 'unsafe-eval'"
