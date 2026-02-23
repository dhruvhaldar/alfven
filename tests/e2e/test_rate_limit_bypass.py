
import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts
from unittest.mock import patch

client = TestClient(app)

def test_rate_limit_bypass_mitigation():
    """
    Verify that the rate limiter ignores the X-Forwarded-For header to prevent spoofing
    when not configured with a trusted proxy.

    In this test, all requests come from the same underlying client (TestClient),
    so rate limiting should kick in regardless of the X-Forwarded-For header values.
    """
    # Reset rate limit state
    request_counts.clear()

    # Set a low limit for testing
    test_limit = 2

    with patch("api.index.RATE_LIMIT", test_limit):
        # 1. Request 1 - Spoofed IP A
        response = client.get("/api/health", headers={"X-Forwarded-For": "1.1.1.1"})
        assert response.status_code == 200

        # 2. Request 2 - Spoofed IP B
        response = client.get("/api/health", headers={"X-Forwarded-For": "2.2.2.2"})
        assert response.status_code == 200

        # 3. Request 3 - Spoofed IP C
        # Should be blocked because we ignore the header and see the real client IP (which is shared)
        response = client.get("/api/health", headers={"X-Forwarded-For": "3.3.3.3"})

        # We expect 429 Too Many Requests
        assert response.status_code == 429
