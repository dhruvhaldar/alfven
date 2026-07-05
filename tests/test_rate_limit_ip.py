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
    req.scope = {"client": ["1.2.3.4", 12345]}

    # Case 1: Default behavior (no env var)
    with patch('api.index.IS_VERCEL', False):
        assert get_client_ip(req) == "1.2.3.4"

        # Even with header, it should be ignored
        req.headers = {"X-Forwarded-For": "5.6.7.8"}
        assert get_client_ip(req) == "1.2.3.4"

    # Case 2: VERCEL env var set
    with patch('api.index.IS_VERCEL', True):
        # Prefer x-vercel-forwarded-for over X-Forwarded-For
        req.headers = {
            "x-vercel-forwarded-for": "10.0.0.1",
            "X-Forwarded-For": "5.6.7.8, 9.9.9.9"
        }
        req.scope = {
            "headers": [
                (b"x-vercel-forwarded-for", b"10.0.0.1"),
                (b"x-forwarded-for", b"5.6.7.8, 9.9.9.9")
            ]
        }
        assert get_client_ip(req) == "10.0.0.1"

        # Fallback to right-most X-Forwarded-For if x-vercel-forwarded-for is absent
        req.headers = {"X-Forwarded-For": "5.6.7.8, 9.9.9.9"}
        req.scope = {
            "headers": [
                (b"x-forwarded-for", b"5.6.7.8, 9.9.9.9")
            ]
        }
        assert get_client_ip(req) == "9.9.9.9"

        # Header missing completely (fallback to connection IP)
        req.headers = {}
        req.scope = {"headers": [], "client": ["1.2.3.4", 12345]}
        assert get_client_ip(req) == "1.2.3.4"
