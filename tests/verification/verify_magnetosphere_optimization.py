from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            print("Loading page...")
            page.goto("http://localhost:8000")

            # Wait for initial SVG
            try:
                page.wait_for_selector("#magnetosphere-viz svg", timeout=5000)
                print("Initial SVG found.")
            except:
                print("Initial SVG NOT found (timeout).")
                return

            # Inject attribute to mark the SVG element
            print("Injecting test attribute...")
            page.evaluate("document.querySelector('#magnetosphere-viz svg').setAttribute('data-test-id', 'original')")

            # Change input to trigger update
            print("Changing input value...")

            # Wait for API response (debounced 300ms)
            try:
                with page.expect_response(lambda response: "standoff" in response.url and response.status == 200, timeout=5000):
                    page.fill("#sw-density-num", "10")
                print("API response received.")
            except Exception as e:
                print(f"API wait timed out: {e}")

            # Allow some time for DOM update after API returns
            time.sleep(0.5)

            # Check if SVG still has the attribute
            print("Checking SVG persistence...")
            is_original = page.evaluate("document.querySelector('#magnetosphere-viz svg') && document.querySelector('#magnetosphere-viz svg').getAttribute('data-test-id') === 'original'")

            if is_original:
                print("RESULT: Optimization DETECTED (SVG was reused)")
            else:
                print("RESULT: Optimization NOT DETECTED (SVG was recreated)")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
