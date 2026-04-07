import subprocess
import time
import pytest
from playwright.sync_api import Page

@pytest.fixture(scope="session", autouse=True)
def start_server():
    server = subprocess.Popen(
        ["uvicorn", "api.index:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    time.sleep(3)  # Wait for server to start
    yield
    server.terminate()
    server.wait()

def test_sunspot_optimization(page: Page):
    page.goto("http://127.0.0.1:8000")

    page.wait_for_selector("#sunspot-temp:not([aria-busy='true'])", timeout=10000)

    # Trigger first calculate to cache the value 0.5
    with page.expect_response(lambda response: "sunspot" in response.url and response.status == 200, timeout=5000):
        page.fill("#sunspot-ratio-num", "0.5")

    time.sleep(1) # wait for cache

    # Trigger it again. It should NOT show Calculating...
    page.fill("#sunspot-ratio-num", "0.5")

    # We should immediately see the result, not the loading spinner
    is_loading = page.evaluate("document.querySelector('#sunspot-temp').innerText.includes('Calculating')")
    assert not is_loading, "Sunspot should not show loading state for cached values due to DOM thrashing prevention"
