import time
import asyncio
import pytest
from unittest.mock import MagicMock, patch
import api.index
from api.index import rate_limit_middleware, request_counts, RATE_LIMIT

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
    print("\n--- Starting Token Bucket Rate Limit Verification ---")

    # Reset state
    request_counts.clear()

    # Patch MAX_IPS to a small number for testing
    TEST_MAX_IPS = 50
    with patch("api.index.MAX_IPS", TEST_MAX_IPS):
        # 1. Fill up to limit
        for i in range(TEST_MAX_IPS):
            req = MockRequest(client_host=f"10.0.0.{i}")
            # Ensure different timestamps if needed, but monotonic handles it
            await rate_limit_middleware(req, mock_call_next)

        assert len(request_counts) == TEST_MAX_IPS
        print("Filled up to MAX_IPS.")

        # 2. Add more requests to trigger LRU eviction
        # Adding 10 more IPs
        for i in range(TEST_MAX_IPS, TEST_MAX_IPS + 10):
            req = MockRequest(client_host=f"10.0.0.{i}")
            await rate_limit_middleware(req, mock_call_next)

        # Size should be maintained at MAX_IPS
        # The code checks `len >= MAX_IPS` -> evict -> add.
        # So size should be exactly MAX_IPS.
        assert len(request_counts) == TEST_MAX_IPS
        print("Memory leak safeguard passed (LRU size maintained).")

        # Verify oldest IPs were evicted
        assert "10.0.0.0" not in request_counts
        assert f"10.0.0.{TEST_MAX_IPS+9}" in request_counts
        print("LRU eviction verified.")

    # 3. Test IP Extraction from X-Forwarded-For (Security)
    request_counts.clear()
    req = MockRequest(client_host="127.0.0.1", x_forwarded_for="203.0.113.1, 10.0.0.1")
    await rate_limit_middleware(req, mock_call_next)

    assert "127.0.0.1" in request_counts
    assert "10.0.0.1" not in request_counts
    print("X-Forwarded-For Ignore Check passed.")

    # 4. Test Token Refill Logic
    print("\n--- Testing Token Refill ---")
    request_counts.clear()

    client_ip = "192.168.1.1"
    req = MockRequest(client_host=client_ip)

    # Initial request (consumes 1 token)
    # Patch time
    start_time = 1000.0
    with patch("time.monotonic", return_value=start_time):
        await rate_limit_middleware(req, mock_call_next)

    # Check tokens: RATE_LIMIT - 1
    # bucket is [tokens, last_update]
    assert request_counts[client_ip][0] == RATE_LIMIT - 1

    # Consume all tokens
    # We already consumed 1. Need to consume RATE_LIMIT - 1 more.
    with patch("time.monotonic", return_value=start_time):
        for _ in range(RATE_LIMIT - 1):
            res = await rate_limit_middleware(req, mock_call_next)
            assert res == "ok"

    # Now tokens should be 0 (or close to 0 due to float, but we started exact)
    # With start_time unchanged, no refill happened.
    assert request_counts[client_ip][0] == 0

    # Next request should fail (429)
    with patch("time.monotonic", return_value=start_time):
        resp = await rate_limit_middleware(req, mock_call_next)
        # Verify response is 429 JSONResponse
        assert resp.status_code == 429

    # Wait for 1 token refill
    # Rate = RATE_LIMIT / 60.
    # Time needed = 1 / Rate = 60 / RATE_LIMIT.
    # If RATE_LIMIT = 100, time = 0.6s.
    refill_time = 60.0 / RATE_LIMIT + 0.01 # slightly more

    with patch("time.monotonic", return_value=start_time + refill_time):
        resp = await rate_limit_middleware(req, mock_call_next)
        assert resp == "ok"
        # Tokens should be roughly 0 (refilled >1, consumed 1)
        # If we wait exactly for 1 token, we get 1.0xxxxx. Consume 1 -> 0.0xxxxx.
        assert request_counts[client_ip][0] >= 0

    print("Token Refill passed.")

import threading

def test_rate_limit_token_bucket():
    def run_in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run_test_logic())
        finally:
            loop.close()

    thread = threading.Thread(target=run_in_thread)
    thread.start()
    thread.join()

if __name__ == "__main__":
    test_rate_limit_token_bucket()
