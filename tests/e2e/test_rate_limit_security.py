
import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts, RATE_LIMIT
from unittest.mock import patch

client = TestClient(app)

def test_rate_limit_ip_spoofing():
    """
    Test that the rate limiter correctly identifies the client IP from X-Forwarded-For
    and is not fooled by spoofed IPs at the beginning of the header.
    We simulate a scenario where the load balancer appends the real IP to the end.
    """
    # Reset rate limit state
    request_counts.clear()

    real_ip = "203.0.113.1"

    # We'll set a low limit for testing
    test_limit = 2

    with patch("api.index.RATE_LIMIT", test_limit):
        # 1. First request - Spoofed IP 1
        headers1 = {"X-Forwarded-For": f"1.2.3.4, {real_ip}"}
        response = client.get("/api/health", headers=headers1)
        assert response.status_code == 200

        # 2. Second request - Spoofed IP 2
        # If vulnerable, this counts as a new user (1.2.3.5)
        # If secure, this counts as the same user (203.0.113.1)
        headers2 = {"X-Forwarded-For": f"1.2.3.5, {real_ip}"}
        response = client.get("/api/health", headers=headers2)
        assert response.status_code == 200

        # 3. Third request - Spoofed IP 3
        # Should be blocked if we are correctly identifying the user by the last IP
        headers3 = {"X-Forwarded-For": f"1.2.3.6, {real_ip}"}
        response = client.get("/api/health", headers=headers3)

        # If vulnerable, this will be 200 (bypass)
        # If secure, this will be 429 (blocked)
        if response.status_code == 200:
            pytest.fail("Vulnerability confirmed: Rate limit bypassed by rotating first IP in X-Forwarded-For")

        assert response.status_code == 429
