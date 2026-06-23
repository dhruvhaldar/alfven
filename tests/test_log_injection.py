import logging
import pytest
from fastapi.testclient import TestClient
from api.index import app, request_counts, RATE_LIMIT
from urllib.parse import quote

client = TestClient(app)

def test_log_injection(caplog):
    request_counts.clear()
    caplog.set_level(logging.WARNING, logger="alfven")

    # Exceed rate limit
    for _ in range(RATE_LIMIT + 10):
        client.get("/api/health")

    # Now this will be logged
    # We use quoting to mimic how a browser/client might encode it to bypass invalid URL checks
    malicious_path = "/api/health%0A2026-01-01%2012%3A00%3A00%20%5BCRITICAL%5D%20You%20have%20been%20hacked"
    response = client.get(malicious_path)
    assert response.status_code == 429

    # Check log output
    logs = [record.message for record in caplog.records]
    print("LOGS:", logs)

    for log in logs:
        if '\n' in log:
            pytest.fail("Log injection vulnerability: newline character found in logs")

if __name__ == "__main__":
    import pytest
    pytest.main(["-v", "tests/test_log_injection.py"])
