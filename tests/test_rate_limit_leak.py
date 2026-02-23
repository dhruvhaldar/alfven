import time
import asyncio
from unittest.mock import MagicMock, patch
import api.index
from api.index import rate_limit_middleware, request_counts, request_log

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

async def _run_test_logic():
    print("\n--- Starting Memory Leak Fix Verification ---")

    # Reset state
    request_counts.clear()
    request_log.clear()

    # Patch MAX_IPS to a small number for testing
    # We need to patch where it is used. api.index.MAX_IPS
    with patch("api.index.MAX_IPS", 50):
        # 1. Fill up to limit
        for i in range(50):
            req = MockRequest(client_host=f"10.0.0.{i}")
            await rate_limit_middleware(req, mock_call_next)

        assert len(request_counts) == 50

        # 2. Add more requests to trigger cleanup and overflow
        for i in range(50, 60):
            req = MockRequest(client_host=f"10.0.0.{i}")
            await rate_limit_middleware(req, mock_call_next)

        # Should NOT have cleared everything (security fix), but should be capped near limit
        # Old behavior: cleared to 0 (vulnerability).
        # New behavior: Maintains size around MAX_IPS (LRU eviction).
        assert len(request_counts) >= 50
        assert len(request_counts) <= 52  # Allow small buffer for current request

    print("Memory leak safeguard passed (LRU verified).")

    # 3. Test IP Extraction from X-Forwarded-For
    # 🛡️ Sentinel: Updated to verify we IGNORE X-Forwarded-For to prevent spoofing.
    # We rely on request.client.host which should be populated by the ASGI server.
    request_counts.clear()
    request_log.clear()

    req = MockRequest(client_host="127.0.0.1", x_forwarded_for="203.0.113.1, 10.0.0.1")
    await rate_limit_middleware(req, mock_call_next)

    # We should track 127.0.0.1 (actual client), NOT the spoofed header IP
    assert "127.0.0.1" in request_counts
    assert "10.0.0.1" not in request_counts
    print("X-Forwarded-For Ignore Check passed.")

    # 4. Test request_log Capping (DoS Prevention)
    print("\n--- Testing request_log Capping ---")
    request_counts.clear()
    request_log.clear()

    # Reduce MAX_LOG_SIZE to a small number
    with patch("api.index.MAX_LOG_SIZE", 5):
        # Add 6 requests (limit 5)
        for i in range(6):
            req = MockRequest(client_host=f"10.0.0.{i}")
            await rate_limit_middleware(req, mock_call_next)

        # request_log should be capped at 5
        assert len(request_log) == 5
        # The oldest (10.0.0.0) should have been popped from log
        # But it should still be in request_counts (unless expired)
        # Since time hasn't advanced much, it should be there
        assert "10.0.0.0" in request_counts

        # Verify that per-user cleanup still works (redundant check)
        # We simulate expiration manually for 10.0.0.0
        # By moving time forward past WINDOW_SIZE (61s)

        # We patch time.monotonic to ensure expiration
        with patch("time.monotonic", return_value=1000.0):
             # Initial request
             req = MockRequest(client_host="10.0.0.99")
             await rate_limit_middleware(req, mock_call_next)

        # Force eviction from log by adding other requests (limit is 5)
        # Use time close to initial so they don't expire
        with patch("time.monotonic", return_value=1000.1):
            for i in range(10):
                 req = MockRequest(client_host=f"10.1.0.{i}")
                 await rate_limit_middleware(req, mock_call_next)

        # Now 10.0.0.99 is definitely not in request_log (size 5)
        # But it is in request_counts

        # Make another request with 10.0.0.99 after expiration
        with patch("time.monotonic", return_value=1000.0 + 61.0):
             req = MockRequest(client_host="10.0.0.99")
             await rate_limit_middleware(req, mock_call_next)

        # If cleanup worked, count should be 1 (new request only)
        # If failed, count would be 2 (old + new)
        assert len(request_counts["10.0.0.99"]) == 1

    print("request_log Capping and Redundant Cleanup passed.")

def test_memory_leak_fix():
    asyncio.run(_run_test_logic())

if __name__ == "__main__":
    test_memory_leak_fix()
