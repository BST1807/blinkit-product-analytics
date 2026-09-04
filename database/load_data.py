import os
from dotenv import load_dotenv
import pandas as pd
import mysql.connector
import glob

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Find the latest processed CSV
files = glob.glob("data/processed/products_*.csv")

if not files:
    raise FileNotFoundError("No processed CSV file found.")

latest_file = max(files, key=os.path.getmtime)

print(f"Reading: {latest_file}")

df = pd.read_csv(latest_file)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")

# Convert NaN values to None for MySQL
df = df.where(pd.notnull(df), None)

# Connect to MySQL
conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

cursor = conn.cursor()

# Insert data
columns = ", ".join(df.columns)
placeholders = ", ".join(["%s"] * len(df.columns))

query = f"""
INSERT INTO products ({columns})
VALUES ({placeholders})
ON DUPLICATE KEY UPDATE
    product_name = VALUES(product_name),
    brand = VALUES(brand),
    price = VALUES(price),
    mrp = VALUES(mrp),
    rating = VALUES(rating),
    inventory = VALUES(inventory),
    product_position = VALUES(product_position),
    widget_position = VALUES(widget_position),
    variant = VALUES(variant),
    is_sold_out = VALUES(is_sold_out),
    merchant_type = VALUES(merchant_type),
    product_state = VALUES(product_state),
    product_display_name = VALUES(product_display_name),
    currency = VALUES(currency),
    ptype = VALUES(ptype),
    quantity = VALUES(quantity),
    state = VALUES(state),
    scrape_timestamp = VALUES(scrape_timestamp)
"""

for _, row in df.iterrows():
    cursor.execute(query, tuple(row))

conn.commit()

print("Data loaded/updated successfully into MySQL.")

cursor.close()
conn.close()