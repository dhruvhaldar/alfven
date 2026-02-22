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

async def _run_test_lru_behavior():
    print("\n--- Starting Rate Limit LRU Eviction Test ---")

    # Reset state
    request_counts.clear()
    request_log.clear()

    # Patch MAX_IPS to a small number for testing
    TEST_MAX_IPS = 10

    # Use a base time
    BASE_TIME = 1000.0

    # We patch MAX_IPS where it is used. Since it is imported, we patch the module attribute?
    # In repro script, `with patch("api.index.MAX_IPS", TEST_MAX_IPS):` worked.

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
        # Timestamp: 1001.0 (still within window)
        # This expands the map to 11 (limit is 10, check happens *before* adding? No, *after* check but before add?)
        # Wait, check logic: `if len > MAX`: evict. THEN `dq = request_counts[ip]`.
        # So when 11th comes:
        # 1. `len` is 10. `10 > 10` False.
        # 2. Add 11th. `len` becomes 11.

        req = MockRequest(client_host=f"10.0.0.{TEST_MAX_IPS}")
        with patch("time.monotonic", return_value=BASE_TIME + TEST_MAX_IPS * 0.1):
            await rate_limit_middleware(req, mock_call_next)

        assert len(request_counts) == TEST_MAX_IPS + 1

        # 3. Add 12th IP (id=11)
        # Timestamp: 1001.1
        # This triggers `len > MAX_IPS` (11 > 10).
        # It should evict the oldest IP (10.0.0.0, time=1000.0)
        req = MockRequest(client_host=f"10.0.0.{TEST_MAX_IPS+1}")
        with patch("time.monotonic", return_value=BASE_TIME + (TEST_MAX_IPS + 1) * 0.1):
            await rate_limit_middleware(req, mock_call_next)

        # 4. Verify LRU Eviction
        # Size should be 11 (10 preserved + 1 new)
        # Evicted one (size 10) + Added new one (size 11)
        assert len(request_counts) == TEST_MAX_IPS + 1

        # Verify 10.0.0.0 (oldest) is gone
        assert "10.0.0.0" not in request_counts, "Oldest IP (10.0.0.0) should be evicted"

        # Verify 10.0.0.1 (second oldest) is still there
        assert "10.0.0.1" in request_counts, "Second oldest IP (10.0.0.1) should be preserved"

        # Verify newest is there
        assert f"10.0.0.{TEST_MAX_IPS+1}" in request_counts, "Newest IP should be present"

    print("Rate Limit LRU Eviction Test Passed.")

def test_rate_limit_lru():
    asyncio.run(_run_test_lru_behavior())

if __name__ == "__main__":
    test_rate_limit_lru()
