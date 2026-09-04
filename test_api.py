from playwright.sync_api import sync_playwright
import json
from datetime import datetime


all_snippets = []


def handle_response(response):

    if "listing_widgets" not in response.url:
        return

    try:
        data = response.json()
    except Exception:
        return

    snippets = data.get("response", {}).get("snippets", [])

    product_snippets = []

    for snippet in snippets:

        common = (
            snippet
            .get("tracking", {})
            .get("common_attributes", {})
        )

        # Keep only snippets that actually represent products
        if common.get("product_id"):
            product_snippets.append(snippet)

    if product_snippets:

        all_snippets.extend(product_snippets)

        print("=" * 80)
        print("PRODUCT API RESPONSE")
        print("URL:", response.url)
        print("Products in this response:", len(product_snippets))
        print("Total products collected:", len(all_snippets))


with sync_playwright() as p:

    browser = p.chromium.launch(headless=False)

    page = browser.new_page()

    page.on("response", handle_response)

    page.goto("https://blinkit.com")

    page.wait_for_timeout(5000)

    page.get_by_text("Dairy, Bread & Eggs").click()

    page.wait_for_timeout(8000)

    print("Current URL:", page.url)

    # Scroll down repeatedly to trigger pagination
    for i in range(10):

        page.mouse.wheel(0, 1500)

        page.wait_for_timeout(2000)

        print("Scroll:", i + 1)
        print("Products collected so far:", len(all_snippets))

    # Save the complete category snapshot
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    output = {
        "scrape_timestamp": datetime.now().isoformat(),
        "product_count": len(all_snippets),
        "response": {
            "snippets": all_snippets
        }
    }

    filename = f"data/raw/blinkit_snapshot_{timestamp}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=4)

    print("=" * 80)
    print("FINAL PRODUCT COUNT:", len(all_snippets))
    print("RAW SNAPSHOT SAVED:", filename)

    input("Press Enter to close...")

    browser.close()