import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts
from unittest.mock import patch

client = TestClient(app)

def test_ip_memory_leak():
    request_counts.clear()

    # 1MB string
    large_string = "A" * 1_000_000

    with patch("api.index.IS_VERCEL", True):
        response = client.get("/api/health", headers={"X-Forwarded-For": large_string})
        assert response.status_code == 200

        # Check if the large string is in the dict
        assert large_string not in request_counts

        # Check if the truncated string is in the dict
        truncated_string = large_string[:45]
        assert truncated_string in request_counts

if __name__ == "__main__":
    pytest.main(["-v", "tests/e2e/test_ip_memory_leak.py"])
