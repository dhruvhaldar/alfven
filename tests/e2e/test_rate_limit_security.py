
import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts, RATE_LIMIT
from unittest.mock import patch

client = TestClient(app)

def test_rate_limit_ip_spoofing():
    """
    Test that the rate limiter ignores the X-Forwarded-For header by default,
    preventing spoofing attempts.

    The application relies on the ASGI server (Uvicorn) to populate request.client.host
    correctly. In this test environment, request.client.host is constant ("testclient"),
    so all requests are treated as coming from the same user, regardless of headers.
    """
    # Reset rate limit state
    request_counts.clear()

    # We'll set a low limit for testing
    test_limit = 2

    with patch("api.index.RATE_LIMIT", test_limit):
        # 1. First request - Spoofed IP 1
        headers1 = {"X-Forwarded-For": "1.2.3.4, 203.0.113.1"}
        response = client.get("/api/health", headers=headers1)
        assert response.status_code == 200

        # 2. Second request - Spoofed IP 2
        # Even with different headers, the underlying client is the same
        headers2 = {"X-Forwarded-For": "1.2.3.5, 203.0.113.1"}
        response = client.get("/api/health", headers=headers2)
        assert response.status_code == 200

        # 3. Third request - Spoofed IP 3
        # Should be blocked because the limit is 2 per user (based on client.host)
        headers3 = {"X-Forwarded-For": "1.2.3.6, 203.0.113.1"}
        response = client.get("/api/health", headers=headers3)

        # If vulnerable (trusting header), this would be 200 (bypass)
        # If secure (ignoring header), this will be 429 (blocked)
        if response.status_code == 200:
            pytest.fail("Vulnerability confirmed: Rate limit bypassed by rotating X-Forwarded-For")

        assert response.status_code == 429
