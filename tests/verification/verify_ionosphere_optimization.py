from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        try:
            page.goto("http://localhost:8000")
            page.wait_for_selector("#iono-chart")

            # Wait for chart to be initialized
            # We can check window.chart if it was exposed?
            # public/js/iono_profile.js uses `let chart;` in top level scope.
            # It is NOT on window.
            # So we cannot access it easily via page.evaluate("chart") IF it's not global.
            # But let's test if we can access it.

            # If `let chart` is in a script without type=module, in global scope...
            # Browsers treat top-level let/const in non-module scripts as global variables
            # but NOT properties of window.
            # page.evaluate() executes in the global scope. So `chart` should be visible.

            # Wait for chart to be defined
            page.wait_for_function("typeof chart !== 'undefined' && chart !== null")

            # Tag the original chart
            chart_id = page.evaluate("""() => {
                chart._test_id = 'original';
                return chart._test_id;
            }""")
            print(f"Original chart tagged: {chart_id}")

            # Toggle the switch
            print("Clicking toggle...")
            page.click(".glass-toggle-slider")

            # Wait for update to complete
            # The text changes to "Updating..." then back to "Day Mode" or "Night Mode"
            # We wait for it to NOT be "Updating..."
            page.wait_for_function("""() => {
                const el = document.getElementById('day-night-val');
                return el && !el.innerText.includes('Updating');
            }""")

            # Check if chart still has the tag
            new_chart_id = page.evaluate("""() => {
                return chart._test_id;
            }""")
            print(f"New chart tag: {new_chart_id}")

            if new_chart_id == 'original':
                print("SUCCESS: Chart instance was reused.")
            else:
                print("FAILURE: Chart instance was recreated (tag missing).")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    run()
