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

        # Should have cleared
        assert len(request_counts) <= 10
        assert len(request_counts) > 0

    print("Memory leak safeguard passed.")

    # 3. Test IP Extraction from X-Forwarded-For
    request_counts.clear()
    request_log.clear()

    req = MockRequest(client_host="127.0.0.1", x_forwarded_for="203.0.113.1, 10.0.0.1")
    await rate_limit_middleware(req, mock_call_next)

    assert "203.0.113.1" in request_counts
    assert "127.0.0.1" not in request_counts
    print("X-Forwarded-For passed.")

def test_memory_leak_fix():
    asyncio.run(_run_test_logic())

if __name__ == "__main__":
    test_memory_leak_fix()
