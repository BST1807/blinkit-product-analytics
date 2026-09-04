import json

filename = "data/raw/blinkit_snapshot_2026-08-10_20-20-27.json"

with open(filename, "r", encoding="utf-8") as file:
    data = json.load(file)

snippets = data["response"]["snippets"]

product_ids = []

for snippet in snippets:

    common = (
        snippet
        .get("tracking", {})
        .get("common_attributes", {})
    )

    product_id = common.get("product_id")

    if product_id:
        product_ids.append(product_id)

print("Total products:", len(product_ids))
print("Unique products:", len(set(product_ids)))

print("\nProduct IDs:")
print(product_ids)