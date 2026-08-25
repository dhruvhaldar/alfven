import subprocess
import time
import threading
import re
import pytest
from playwright.sync_api import Page, expect

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

def test_page_loads_and_title(page: Page):
    page.goto("http://127.0.0.1:8000")
    expect(page).to_have_title(re.compile("Alfven"))
    expect(page.get_by_role("heading", name="Alfvén Speed")).to_be_visible()

def test_expanded_science_outputs(page: Page):
    page.goto("http://127.0.0.1:8000")

    expect(page.locator("#iono-peak-density")).not_to_have_text("-", timeout=10000)
    expect(page.locator("#iono-peak-altitude")).to_contain_text("km")
    expect(page.locator("#iono-tec")).to_contain_text("TECU")

    expect(page.locator("#res-larmor")).not_to_have_text("-", timeout=10000)
    expect(page.locator("#res-temp-k")).to_contain_text("K")
    expect(page.locator("#res-thermal-speed")).to_contain_text("km/s")
    expect(page.locator("#res-gyrofrequency")).to_contain_text("Hz")
    expect(page.locator("#res-plasma-state")).to_contain_text("plasma")

    expect(page.locator("#res-alfven-speed")).to_contain_text("km/s", timeout=10000)
    expect(page.locator("#res-alfven-mach")).not_to_have_text("-")

def test_starfield_renders_and_animates(page: Page):
    page.goto("http://127.0.0.1:8000")
    canvas = page.locator("#canvas-container canvas")
    expect(canvas).to_be_attached()

    first_frame = canvas.evaluate("element => element.toDataURL()")
    page.wait_for_timeout(500)
    second_frame = canvas.evaluate("element => element.toDataURL()")

    assert first_frame != second_frame
    assert page.locator("#canvas-container").evaluate(
        "element => getComputedStyle(element).zIndex"
    ) == "0"

def test_footer_link(page: Page):
    page.goto("http://127.0.0.1:8000")
    footer_link = page.locator('footer a.glass-link[href="https://github.com/dhruvhaldar/alfven"]')
    expect(footer_link).to_be_visible()
    expect(footer_link).to_have_attribute("href", "https://github.com/dhruvhaldar/alfven")
    expect(footer_link).to_have_attribute("target", "_blank")
    expect(footer_link).to_have_attribute("rel", "noopener noreferrer")
    expect(footer_link).to_have_attribute("aria-label", "GitHub repository (opens in a new tab)")

    color = footer_link.evaluate("element => getComputedStyle(element).color")
    assert color == "rgb(68, 221, 255)", f"Expected color rgb(68, 221, 255), got {color}"

def test_copy_ux(page: Page, context):
    context.grant_permissions(['clipboard-read', 'clipboard-write'])
    page.goto("http://127.0.0.1:8000")

    # Wait for Magnetosphere result to load
    page.wait_for_selector("#standoff-display:not([aria-busy='true'])", timeout=10000)

    display = page.locator("#standoff-display")
    initial_text = display.inner_text().strip()

    assert display.evaluate("element => getComputedStyle(element).display") == "flex"
    assert display.evaluate("element => getComputedStyle(element).gap") == "8px"
    assert display.evaluate(
        "element => getComputedStyle(element, '::after').position"
    ) == "static"
    assert display.evaluate("element => getComputedStyle(element).color") == "rgb(68, 221, 255)"

    if "Re" not in initial_text:
        time.sleep(2)
        initial_text = display.inner_text().strip()
        assert "Re" in initial_text, f"Unexpected result format: {initial_text}"

    display.click()

    expect(display).to_have_class(re.compile(r"copied"))
    expect(display).to_have_attribute("title", "Copied!")

    time.sleep(2.5)

    expect(display).not_to_have_attribute("title", "Copied!")

def test_ionosphere_ux(page: Page):
    def handle_route(route):
        if "ionosphere/profile" in route.request.url:
            import time
            time.sleep(2)
            route.continue_()
        else:
            route.continue_()

    page.route("**/*", handle_route)
    page.goto("http://127.0.0.1:8000")
    page.wait_for_selector("#day-night-val")

    page.click(".glass-toggle-slider")

    # Do not block the page thread when waiting for UI state
    # Use playwright expectations to poll the DOM state.
    expect(page.locator("#day-night-val")).to_contain_text("Updating")

    # Then wait for the update to complete
    expect(page.locator("#day-night-val")).not_to_contain_text("Updating", timeout=5000)

    # We must reset the route so it doesn't leak or hang
    page.unroute("**/*")

def test_ionosphere_optimization(page: Page):
    page.goto("http://127.0.0.1:8000")
    page.wait_for_selector("#iono-chart")

    page.wait_for_function("typeof chart !== 'undefined' && chart !== null")

    chart_id = page.evaluate("""() => {
        chart._test_id = 'original';
        return chart._test_id;
    }""")
    assert chart_id == 'original'

    page.click(".glass-toggle-slider")

    page.wait_for_function("""() => {
        const el = document.getElementById('day-night-val');
        return el && !el.innerText.includes('Updating');
    }""")

    new_chart_id = page.evaluate("() => chart._test_id")
    assert new_chart_id == 'original'

def test_magnetosphere_optimization(page: Page):
    page.goto("http://127.0.0.1:8000")

    page.wait_for_selector("#magnetosphere-viz svg", timeout=5000)

    page.evaluate("document.querySelector('#magnetosphere-viz svg').setAttribute('data-test-id', 'original')")

    with page.expect_response(lambda response: "standoff" in response.url and response.status == 200, timeout=5000):
        page.fill("#sw-density-num", "10")

    time.sleep(0.5)

    is_original = page.evaluate("document.querySelector('#magnetosphere-viz svg') && document.querySelector('#magnetosphere-viz svg').getAttribute('data-test-id') === 'original'")
    assert is_original
