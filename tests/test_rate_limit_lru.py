import time
import asyncio
from unittest.mock import MagicMock, patch
import api.index
from api.index import rate_limit_middleware, request_counts

# Create a mock request
class MockRequest:
    def __init__(self, client_host, x_forwarded_for=None):
        self.client = MagicMock()
        self.client.host = client_host
        self.headers = {}
        if x_forwarded_for:
            self.headers["X-Forwarded-For"] = x_forwarded_for

async def mock_call_next(request):
    return "ok"

async def _run_test_lru_behavior():
    print("\n--- Starting Rate Limit LRU Eviction Test ---")

    # Reset state
    request_counts.clear()

    # Patch MAX_IPS to a small number for testing
    TEST_MAX_IPS = 10

    # Use a base time
    BASE_TIME = 1000.0

    with patch("api.index.MAX_IPS", TEST_MAX_IPS):
        # 1. Fill up to limit with IPs 0..9
        # Use timestamps very close to each other so they don't expire (window is 60s)
        for i in range(TEST_MAX_IPS):
            req = MockRequest(client_host=f"10.0.0.{i}")
            # Timestamps: 1000.0, 1000.1, ... 1000.9
            with patch("time.monotonic", return_value=BASE_TIME + i * 0.1):
                await rate_limit_middleware(req, mock_call_next)

        assert len(request_counts) == TEST_MAX_IPS

        # 2. Add one more IP (11th, id=10)
        # New logic: Evicts before adding if full.
        # So 10.0.0.0 (oldest) should be evicted immediately.
        req = MockRequest(client_host=f"10.0.0.{TEST_MAX_IPS}")
        with patch("time.monotonic", return_value=BASE_TIME + TEST_MAX_IPS * 0.1):
            await rate_limit_middleware(req, mock_call_next)

        # Size should still be TEST_MAX_IPS
        assert len(request_counts) == TEST_MAX_IPS

        # Verify eviction happened immediately
        assert "10.0.0.0" not in request_counts, "Oldest IP should be evicted immediately when full"
        assert f"10.0.0.{TEST_MAX_IPS}" in request_counts

        # 3. Add 12th IP
        req = MockRequest(client_host=f"10.0.0.{TEST_MAX_IPS+1}")
        with patch("time.monotonic", return_value=BASE_TIME + (TEST_MAX_IPS + 1) * 0.1):
            await rate_limit_middleware(req, mock_call_next)

        assert len(request_counts) == TEST_MAX_IPS
        assert "10.0.0.1" not in request_counts
        assert f"10.0.0.{TEST_MAX_IPS+1}" in request_counts

    print("Rate Limit LRU Eviction Test Passed.")

def test_rate_limit_lru():
    asyncio.run(_run_test_lru_behavior())

if __name__ == "__main__":
    test_rate_limit_lru()
