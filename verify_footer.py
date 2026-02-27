from playwright.sync_api import Page, expect, sync_playwright
import time

def verify_footer_link(page: Page):
    # Navigate to the home page
    page.goto("http://localhost:8000")

    # Locate the GitHub link in the footer
    # Using specific attributes to ensure we are targeting the correct element we modified
    footer_link = page.locator("footer a.glass-link")

    # Assertions
    expect(footer_link).to_be_visible()
    expect(footer_link).to_have_attribute("href", "https://github.com/dhruvhaldar/alfven")
    expect(footer_link).to_have_attribute("target", "_blank")
    expect(footer_link).to_have_attribute("rel", "noopener noreferrer")
    expect(footer_link).to_have_attribute("aria-label", "GitHub repository (opens in a new tab)")

    # Check CSS styles (computed)
    # The color should be #4df (rgb(68, 221, 255))
    color = footer_link.evaluate("element => getComputedStyle(element).color")
    assert color == "rgb(68, 221, 255)", f"Expected color rgb(68, 221, 255), got {color}"

    # Hover state verification is tricky in static screenshots but we can try to trigger it
    footer_link.hover()

    # Take a screenshot of the footer area
    footer = page.locator("footer")
    footer.screenshot(path="verification_footer.png")
    print("Screenshot saved to verification_footer.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_footer_link(page)
        except Exception as e:
            print(f"Verification failed: {e}")
        finally:
            browser.close()
