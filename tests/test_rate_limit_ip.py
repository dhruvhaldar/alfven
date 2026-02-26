import pytest
from fastapi.testclient import TestClient
from api.index import app
import os
from unittest.mock import patch

client = TestClient(app)

def test_get_client_ip_logic():
    """
    Unit test for the get_client_ip function to be added.
    """
    from api.index import get_client_ip
    from fastapi import Request
    from unittest.mock import Mock

    # Mock Request
    req = Mock(spec=Request)
    req.client.host = "1.2.3.4"
    req.headers = {}

    # Case 1: Default behavior (no env var)
    with patch.dict(os.environ, {}, clear=True):
        assert get_client_ip(req) == "1.2.3.4"

        # Even with header, it should be ignored
        req.headers = {"X-Forwarded-For": "5.6.7.8"}
        assert get_client_ip(req) == "1.2.3.4"

    # Case 2: VERCEL env var set
    with patch.dict(os.environ, {"VERCEL": "1"}):
        # Header present
        req.headers = {"X-Forwarded-For": "5.6.7.8, 9.9.9.9"}
        assert get_client_ip(req) == "5.6.7.8"

        # Header missing (fallback)
        req.headers = {}
        assert get_client_ip(req) == "1.2.3.4"
