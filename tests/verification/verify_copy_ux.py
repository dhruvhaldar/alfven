from playwright.sync_api import sync_playwright
import time
import subprocess
import os
import sys

def run():
    # Start server
    print("Starting server...")
    server = subprocess.Popen(["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(5) # Wait for server start

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            context = browser.new_context()
            context.grant_permissions(['clipboard-read', 'clipboard-write'])

            page = context.new_page()

            try:
                print("Navigating to http://localhost:8000")
                page.goto("http://localhost:8000")

                # Wait for Magnetosphere result to load
                print("Waiting for calculation...")

                # Wait for standoff-display to contain "Re" (result unit)
                page.wait_for_selector("#standoff-display:not([aria-busy='true'])", timeout=10000)

                display = page.locator("#standoff-display")
                initial_text = display.inner_text().strip()
                print(f"Result value: {initial_text}")

                if "Re" not in initial_text:
                     if "Error" in initial_text:
                         raise Exception("Calculation failed.")
                     else:
                         time.sleep(2)
                         initial_text = display.inner_text().strip()
                         if "Re" not in initial_text:
                             raise Exception(f"Unexpected result format: {initial_text}")

                # Test Copy Interaction
                print("Clicking to copy...")
                display.click()

                # Check visual feedback (class 'copied')
                print("Checking for 'copied' class...")
                start = time.time()
                found = False
                while time.time() - start < 2:
                    classes = display.get_attribute("class")
                    if classes and "copied" in classes:
                        found = True
                        break
                    time.sleep(0.1)

                if not found:
                     raise Exception("Class 'copied' not found on element.")
                print("Visual feedback confirmed: 'copied' class added.")

                # Check title update
                title = display.get_attribute("title")
                if title != "Copied!":
                    raise Exception(f"Title not updated. Got: {title}")
                print("Title updated to 'Copied!'.")

                # Wait for reset (2s + buffer)
                time.sleep(2.5)

                # Verify reset
                title_reset = display.get_attribute("title")
                if title_reset == "Copied!":
                     raise Exception("Title did not reset.")
                print("Title reset successfully.")

                print("✅ Copy UX Verification Passed!")

            except Exception as e:
                print(f"❌ Error: {e}")
                # Take screenshot for debugging
                page.screenshot(path="copy_ux_failure.png")
                raise e
            finally:
                browser.close()
    finally:
        server.terminate()
        server.wait()

if __name__ == "__main__":
    run()
