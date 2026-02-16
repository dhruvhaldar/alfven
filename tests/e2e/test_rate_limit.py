from fastapi.testclient import TestClient
from unittest.mock import patch
import api.index
from api.index import app
import pytest

client = TestClient(app, raise_server_exceptions=False)

def test_rate_limiting():
    # Patch the RATE_LIMIT to a small number
    # We patch it on the api.index module directly
    with patch("api.index.RATE_LIMIT", 5):
        # Clear previous counts for "testclient" (default host for TestClient)
        # We need to access the request_counts dict from api.index
        # If request_counts is not yet defined (before implementation), this will fail,
        # which is expected for TDD.
        if hasattr(api.index, "request_counts"):
            api.index.request_counts.clear()

        # Make 5 allowed requests
        for i in range(5):
            response = client.get("/api/health")
            assert response.status_code == 200, f"Request {i+1} failed"

        # 6th request should fail
        response = client.get("/api/health")
        assert response.status_code == 429
        assert response.json()["detail"] == "Too many requests"
