from playwright.sync_api import sync_playwright
import time
import threading

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Intercept and delay request to capture loading state
        def handle_route(route):
            if "ionosphere/profile" in route.request.url:
                print("Route intercepted! Delaying...")
                # Delay continue in a separate thread
                t = threading.Timer(2.0, lambda: route.continue_())
                t.start()
            else:
                route.continue_()

        page.route("**/*", handle_route)

        try:
            page.goto("http://localhost:8000")
            page.wait_for_selector("#day-night-val")

            # Initial Screenshot
            page.screenshot(path="tests/verification/ionosphere_initial.png")
            print("Captured initial state.")

            # Toggle
            print("Clicking toggle...")
            page.click(".glass-toggle-slider")

            # Should be "Updating..." now
            # Wait a bit for UI update but before response returns (2s delay)
            time.sleep(0.5)

            # Verify "Updating..." text
            val = page.text_content("#day-night-val")
            print(f"Intermediate value: {val}")

            if "Updating" in val:
                print("Loading state confirmed.")
            else:
                print(f"WARNING: Loading state not found. Value: {val}")

            # Screenshot Loading
            page.screenshot(path="tests/verification/ionosphere_loading.png")
            print("Captured loading state.")

            # Wait for completion (2s delay + some buffer)
            time.sleep(2.5)

            val_final = page.text_content("#day-night-val")
            print(f"Final value: {val_final}")

            # Screenshot Final
            page.screenshot(path="tests/verification/ionosphere_final.png")
            print("Captured final state.")

        except Exception as e:
            print(f"Error: {e}")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    run()
