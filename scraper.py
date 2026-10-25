"""
scraper.py
Modular Blinkit Scraper utilizing Playwright for browser automation & network interception,
and BeautifulSoup for HTML parsing and DOM metadata extraction.

Supports multi-category and multi-subcategory crawling:
- Dairy, Bread & Eggs (Milk & Cream, Bread & Bakery)
- Snacks & Munchies (Chips & Crisps, Biscuits & Cookies)
- Cold Drinks & Juices (Soft Drinks & Sodas, Juices & Fruit Drinks)
"""

import os
import json
import argparse
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

CATEGORIES = [
    {
        "name": "Dairy, Bread & Eggs",
        "url_slug": "cn/dairy-bread-eggs/cid/14",
        "subcategories": ["Milk", "Bread & Pav"]
    },
    {
        "name": "Snacks & Munchies",
        "url_slug": "cn/chips-crisps/cid/1237",
        "subcategories": ["Chips & Crisps", "Biscuits & Cookies"]
    },
    {
        "name": "Cold Drinks & Juices",
        "url_slug": "cn/cold-drinks-juices/cid/332",
        "subcategories": ["Soft Drinks", "Fruit Juices"]
    }
]


def parse_html_product_card(html_content, category_name="", subcategory_name=""):
    """
    Uses BeautifulSoup to parse product card DOM snippets for badges,
    titles, prices, discounts, and pack sizes.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    products = []

    cards = soup.select("[data-test-id='product-card'], div[class*='Product__Updated']") or soup.find_all("div", class_=lambda c: c and "product" in c.lower())

    for card in cards:
        name_el = card.find(class_=lambda c: c and ("title" in c.lower() or "name" in c.lower()))
        price_el = card.find(class_=lambda c: c and "price" in c.lower())
        mrp_el = card.find(class_=lambda c: c and "mrp" in c.lower())
        badge_el = card.find(class_=lambda c: c and ("badge" in c.lower() or "tag" in c.lower()))
        variant_el = card.find(class_=lambda c: c and ("variant" in c.lower() or "unit" in c.lower()))

        name = name_el.get_text(strip=True) if name_el else None
        if not name:
            continue

        products.append({
            "name": name,
            "price": price_el.get_text(strip=True) if price_el else None,
            "mrp": mrp_el.get_text(strip=True) if mrp_el else None,
            "badge": badge_el.get_text(strip=True) if badge_el else None,
            "variant": variant_el.get_text(strip=True) if variant_el else None,
            "category": category_name,
            "subcategory": subcategory_name
        })

    return products


def scrape_blinkit(headless=True, max_scrolls=8):
    """
    Launches Playwright, navigates across categories, intercepts API responses,
    and captures HTML DOM cards parsed with BeautifulSoup.
    """
    os.makedirs("data/raw", exist_ok=True)
    all_snippets = []

    def handle_response(response):
        if "listing_widgets" not in response.url and "layout" not in response.url:
            return

        try:
            data = response.json()
        except Exception:
            return

        snippets = data.get("response", {}).get("snippets", [])
        for snippet in snippets:
            common = snippet.get("tracking", {}).get("common_attributes", {})
            if common.get("product_id") and snippet not in all_snippets:
                all_snippets.append(snippet)

    print("Launching Chromium browser for scraping...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.on("response", handle_response)

        try:
            print("Navigating to Blinkit...")
            page.goto("https://blinkit.com", timeout=30000)
            page.wait_for_timeout(4000)

            for cat in CATEGORIES:
                cat_name = cat["name"]
                print(f"\n--- Scraping Category: {cat_name} ---")
                try:
                    category_button = page.get_by_text(cat_name).first
                    if category_button:
                        category_button.click(timeout=5000)
                        page.wait_for_timeout(4000)
                except Exception as e:
                    print(f"Could not click category {cat_name}: {e}. Trying direct URL...")
                    page.goto(f"https://blinkit.com/{cat['url_slug']}", timeout=20000)
                    page.wait_for_timeout(4000)

                # Trigger pagination with smooth scrolling
                for scroll_idx in range(max_scrolls):
                    page.mouse.wheel(0, 1200)
                    page.wait_for_timeout(1500)

                # Parse current DOM HTML with BeautifulSoup
                html = page.content()
                dom_products = parse_html_product_card(html, category_name=cat_name)
                print(f"BeautifulSoup parsed {len(dom_products)} product cards from DOM.")
                print(f"Total API snippets captured so far: {len(all_snippets)}")

        except Exception as err:
            print(f"Scraper encountered network/browser notice: {err}")
        finally:
            browser.close()

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_filename = f"data/raw/blinkit_snapshot_{timestamp}.json"

    result = {
        "scrape_timestamp": datetime.now().isoformat(),
        "product_count": len(all_snippets),
        "response": {
            "snippets": all_snippets
        }
    }

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    print(f"\nSaved raw snapshot to {output_filename} ({len(all_snippets)} SKUs).")
    return output_filename


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blinkit Multi-Category Scraper")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--scrolls", type=int, default=6, help="Number of scrolls per category")
    args = parser.parse_args()

    scrape_blinkit(headless=args.headless, max_scrolls=args.scrolls)
