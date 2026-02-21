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
    print("\n--- Starting Rate Limiter Bypass Reproduction ---")

    # Reset state
    request_counts.clear()
    request_log.clear()

    # Patch MAX_IPS to a small number
    with patch("api.index.MAX_IPS", 5):
        # 1. Fill up to limit with 5 distinct IPs
        # These will be IPs 10.0.0.0 to 10.0.0.4
        for i in range(5):
            req = MockRequest(client_host=f"10.0.0.{i}")
            await rate_limit_middleware(req, mock_call_next)

        # Verify initial state
        assert len(request_counts) == 5, f"Expected 5 IPs, got {len(request_counts)}"
        assert "10.0.0.0" in request_counts
        assert "10.0.0.4" in request_counts

        # 2. Add one more IP (10.0.0.5)
        # This should trigger eviction of the oldest (LRU) one (10.0.0.0)
        # But NOT clear everything
        req = MockRequest(client_host="10.0.0.5")
        await rate_limit_middleware(req, mock_call_next)

        # 3. Assert LRU behavior
        print(f"Current request_counts size: {len(request_counts)}")
        print(f"Current IPs: {list(request_counts.keys())}")

        # Vulnerability Check: If it cleared, size would be 1 (only 10.0.0.5)
        # Fix Check: Size should be 5 (10.0.0.1 - 10.0.0.5)

        # We expect the fix to maintain MAX_IPS items
        assert len(request_counts) == 5, f"Expected 5 IPs after eviction, got {len(request_counts)}"

        # We expect the oldest IP (10.0.0.0) to be gone (LRU eviction)
        assert "10.0.0.0" not in request_counts, "Oldest IP 10.0.0.0 should have been evicted"

        # We expect the newest IP (10.0.0.5) to be present
        assert "10.0.0.5" in request_counts, "Newest IP 10.0.0.5 should be present"

        # We expect intermediate IPs to be preserved
        assert "10.0.0.1" in request_counts, "Intermediate IP 10.0.0.1 should be preserved"
        assert "10.0.0.4" in request_counts, "Intermediate IP 10.0.0.4 should be preserved"

    print("Rate Limiter LRU Eviction passed.")

def test_rate_limit_bypass():
    asyncio.run(_run_test_logic())

if __name__ == "__main__":
    test_rate_limit_bypass()
