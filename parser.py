import json
import pandas as pd
from datetime import datetime
from pathlib import Path


raw_folder = Path("data/raw")

snapshot_files = list(raw_folder.glob("blinkit_snapshot_*.json"))

if not snapshot_files:
    raise FileNotFoundError("No Blinkit snapshot found in data/raw")

latest_snapshot = max(snapshot_files, key=lambda file: file.stat().st_mtime)

print("Reading:", latest_snapshot)

with open(latest_snapshot, "r", encoding="utf-8") as file:
    data = json.load(file)


products = []

snippets = data["response"]["snippets"]
scrape_timestamp = datetime.now()
for snippet in snippets:

    tracking = snippet.get("tracking", {})
    common = tracking.get("common_attributes", {})

    product = {

        "product_id": common.get("product_id"),

        "product_name": common.get("name"),

        "brand": common.get("brand"),

        "price": common.get("price"),

        "mrp": common.get("mrp"),

        "rating": common.get("rating"),

        "inventory": common.get("inventory"),

        "product_position": common.get("product_position"),

        "widget_position": common.get("widget_position"),
        "variant": snippet.get("data", {}).get("variant", {}).get("text"),
        "is_sold_out": snippet.get("data", {}).get("is_sold_out"),
        "merchant_type": snippet.get("data", {}).get("merchant_type"),
        "product_state": snippet.get("data", {}).get("product_state"),

        "product_display_name": snippet.get("data", {}).get("display_name", {}).get("text"),

        "currency": common.get("currency"),

        "ptype": common.get("ptype"),

        "quantity": common.get("quantity"),

        "state": common.get("state"),
        "scrape_timestamp": scrape_timestamp
    }

    products.append(product)


df = pd.DataFrame(products)

filename = scrape_timestamp.strftime("products_%Y-%m-%d_%H-%M-%S.csv")

df.to_csv(
    f"data/processed/{filename}",
    index=False
)

print(f"Processed data saved to: {filename}")

print("Processed data saved successfully.")

print(df.info())
print(df.head())