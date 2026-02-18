import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import api.index
from api.index import app

# Set raise_server_exceptions=False to allow the app's exception handler to catch the error
client = TestClient(app, raise_server_exceptions=False)

def test_exception_logging():
    """
    Verify that 500 errors are logged to help identify security issues.
    """
    # Check if logger exists first (Validation that feature is missing/present)
    if not hasattr(api.index, "logger"):
        pytest.fail("Logger 'logger' not found in api.index. Fix: Initialize logging.")

    # Mock an endpoint dependency to trigger 500
    with patch("api.index.PlasmaState") as mock_plasma:
        mock_plasma.side_effect = Exception("Test Critical Failure")

        # Patch the logger in api.index
        with patch("api.index.logger") as mock_logger:
            client.get("/api/plasma/debye?n=1&T_ev=1")

            # Verify error was logged
            assert mock_logger.error.called
            args, _ = mock_logger.error.call_args
            assert "Internal Server Error" in args[0]

def test_csp_hardening():
    """
    Verify strict CSP directives to prevent object injection and form hijacking.
    """
    response = client.get("/api/health")
    csp = response.headers.get("Content-Security-Policy", "")

    print(f"CSP: {csp}")

    assert "object-src 'none'" in csp, "Missing object-src 'none'"
    assert "base-uri 'self'" in csp, "Missing base-uri 'self'"
    assert "form-action 'self'" in csp, "Missing form-action 'self'"
