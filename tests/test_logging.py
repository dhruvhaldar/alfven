import logging
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.index import app, request_counts

client = TestClient(app, raise_server_exceptions=False)

def test_exception_logging(caplog):
    """
    Verify that unhandled exceptions are logged with ERROR level and include traceback.
    """
    request_counts.clear()

    # Configure the logger to capture logs
    logger = logging.getLogger("alfven")
    logger.setLevel(logging.ERROR)

    # Use caplog to capture logs from "alfven" logger
    caplog.set_level(logging.ERROR, logger="alfven")

    with patch("api.index.PlasmaState") as mock_plasma:
        # Simulate an exception in the business logic
        mock_plasma.side_effect = Exception("Test Security Exception")

        # Call an endpoint that uses PlasmaState
        response = client.get("/api/plasma/debye?n=1&T_ev=1")

        # Verify 500 response (user sees this)
        assert response.status_code == 500
        assert response.json() == {"detail": "Internal Server Error"}

        # Verify log record (admin sees this)
        # Check that we captured at least one error log
        assert len(caplog.records) > 0

        # Check the content of the log
        last_record = caplog.records[-1]
        assert last_record.levelname == "ERROR"
        assert "Unhandled exception" in last_record.message
        assert "Test Security Exception" in last_record.message

        # Verify traceback is included (exc_info=True populates exc_text or exc_info)
        assert last_record.exc_info is not None
