"""
database/load_data.py
Dual-Mode Database Ingestion Engine for Blinkit Product Analytics.

Loads validated, transformed product data into:
1. MySQL (Primary enterprise DBMS via localhost:3306)
2. SQLite (Portable, zero-config local database fallback at database/blinkit.db)

Data Model:
- dim_categories: Category & Subcategory Master
- dim_products: Master Catalog Dimension (Upserted)
- fact_product_snapshots: Time-Aware Snapshot Telemetry (Appended)
- products: Consolidated latest product state table for standard SQL queries
"""

import os
import glob
import sqlite3
import logging
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("DBLoader")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SQLITE_PATH = BASE_DIR / "database" / "blinkit.db"

# Category Dimension Seed Data
CATEGORIES_SEED = [
    (1, "Dairy, Bread & Eggs", 11, "Milk & Cream"),
    (1, "Dairy, Bread & Eggs", 12, "Bread & Bakery"),
    (2, "Snacks & Munchies", 21, "Chips & Crisps"),
    (2, "Snacks & Munchies", 22, "Biscuits & Cookies"),
    (3, "Cold Drinks & Juices", 31, "Soft Drinks & Sodas"),
    (3, "Cold Drinks & Juices", 32, "Juices & Fruit Drinks")
]


def get_mysql_connection():
    """Attempts connection to local MySQL server."""
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "pass"),
            database=os.getenv("MYSQL_DATABASE", "blinkit")
        )
        logger.info("Successfully connected to MySQL server.")
        return conn
    except Exception as e:
        logger.warning(f"MySQL connection unavailable ({e}). Falling back to SQLite.")
        return None


def get_sqlite_connection():
    """Initializes and returns SQLite database connection."""
    conn = sqlite3.connect(SQLITE_PATH)
    logger.info(f"Connected to local SQLite database: {SQLITE_PATH}")
    return conn


def init_sqlite_schema(conn):
    """Creates tables in SQLite if they don't exist."""
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS dim_categories (
        category_id INTEGER,
        category_name TEXT,
        subcategory_id INTEGER,
        subcategory_name TEXT,
        PRIMARY KEY (category_id, subcategory_id)
    );

    CREATE TABLE IF NOT EXISTS dim_products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        brand TEXT,
        category TEXT,
        subcategory TEXT,
        ptype TEXT,
        variant TEXT,
        mrp REAL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS fact_product_snapshots (
        snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id TEXT,
        snapshot_time TEXT,
        price REAL,
        mrp REAL,
        discount_amount REAL,
        discount_percentage REAL,
        price_tier TEXT,
        inventory INTEGER,
        is_sold_out INTEGER,
        stock_status TEXT,
        rating REAL,
        product_position INTEGER,
        widget_position INTEGER,
        merchant_type TEXT,
        FOREIGN KEY (product_id) REFERENCES dim_products(product_id)
    );

    CREATE TABLE IF NOT EXISTS products (
        product_id TEXT PRIMARY KEY,
        product_name TEXT,
        brand TEXT,
        category TEXT,
        subcategory TEXT,
        price REAL,
        mrp REAL,
        discount_percentage REAL,
        rating REAL,
        inventory INTEGER,
        product_position INTEGER,
        widget_position INTEGER,
        variant TEXT,
        is_sold_out INTEGER,
        merchant_type TEXT,
        product_state TEXT,
        product_display_name TEXT,
        currency TEXT,
        ptype TEXT,
        quantity INTEGER,
        state TEXT,
        scrape_timestamp TEXT
    );
    """)
    conn.commit()

    # Ensure SQLite products table has category, subcategory, discount_percentage and unique index
    cursor.execute("PRAGMA table_info(products)")
    existing_sqlite_cols = [r[1].lower() for r in cursor.fetchall()]
    if "category" not in existing_sqlite_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN category TEXT")
    if "subcategory" not in existing_sqlite_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN subcategory TEXT")
    if "discount_percentage" not in existing_sqlite_cols:
        cursor.execute("ALTER TABLE products ADD COLUMN discount_percentage REAL")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_id ON products(product_id)")
    conn.commit()


def init_mysql_schema(conn):
    """Executes schema.sql statements on MySQL and alters existing tables if needed."""
    cursor = conn.cursor()
    schema_path = BASE_DIR / "database" / "schema.sql"
    if schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            sql_statements = f.read().split(";")
            for stmt in sql_statements:
                stmt_clean = stmt.strip()
                if stmt_clean:
                    try:
                        cursor.execute(stmt_clean)
                    except Exception as err:
                        logger.debug(f"MySQL Schema notice: {err}")
        conn.commit()

    # Ensure existing products table has category, subcategory, discount_percentage
    try:
        cursor.execute("DESCRIBE products")
        existing_cols = [r[0].lower() for r in cursor.fetchall()]
        if "category" not in existing_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN category VARCHAR(100) AFTER brand")
        if "subcategory" not in existing_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN subcategory VARCHAR(100) AFTER category")
        if "discount_percentage" not in existing_cols:
            cursor.execute("ALTER TABLE products ADD COLUMN discount_percentage DECIMAL(5,2) AFTER mrp")
        conn.commit()
    except Exception as err:
        logger.debug(f"Column check notice: {err}")

    cursor.close()


def seed_categories(mysql_conn, sqlite_conn):
    """Seeds dim_categories in both databases."""
    if mysql_conn:
        cur = mysql_conn.cursor()
        for row in CATEGORIES_SEED:
            cur.execute("""
                INSERT INTO dim_categories (category_id, category_name, subcategory_id, subcategory_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE subcategory_name = VALUES(subcategory_name)
            """, row)
        mysql_conn.commit()
        cur.close()

    if sqlite_conn:
        cur = sqlite_conn.cursor()
        for row in CATEGORIES_SEED:
            cur.execute("""
                INSERT OR REPLACE INTO dim_categories (category_id, category_name, subcategory_id, subcategory_name)
                VALUES (?, ?, ?, ?)
            """, row)
        sqlite_conn.commit()


def load_dataframe_to_db(df, mysql_conn=None, sqlite_conn=None):
    """
    Ingests a processed DataFrame into both MySQL and SQLite.
    Updates dim_products, appends fact_product_snapshots, and refreshes products table.
    """
    if df.empty:
        return

    # Standardize snapshot timestamp column
    time_col = "snapshot_time" if "snapshot_time" in df.columns else ("scrape_timestamp" if "scrape_timestamp" in df.columns else None)
    if time_col and pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df["snapshot_time_str"] = df[time_col].dt.strftime("%Y-%m-%d %H:%M:%S")
    elif time_col:
        df["snapshot_time_str"] = df[time_col].astype(str)
    else:
        df["snapshot_time_str"] = "2026-10-22 12:00:00"

    # Ensure required columns exist with sensible defaults if missing in older CSVs
    defaults = {
        "category": "Dairy, Bread & Eggs",
        "subcategory": "Milk & Cream",
        "ptype": "Milk",
        "variant": "Standard",
        "mrp": df["price"] if "price" in df.columns else 0.0,
        "discount_amount": 0.0,
        "discount_percentage": 0.0,
        "price_tier": "Mid-Range",
        "rating": 4.5,
        "inventory": 20,
        "is_sold_out": False,
        "stock_status": "In Stock",
        "product_position": 1,
        "widget_position": 1,
        "merchant_type": "express",
        "state": "available"
    }
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val

    # 1. Update dim_products (Master Catalog)
    dim_cols = ["product_id", "product_name", "brand", "category", "subcategory", "ptype", "variant", "mrp"]
    dim_df = df[dim_cols].drop_duplicates(subset=["product_id"])

    # 2. Ingest into MySQL if available
    if mysql_conn:
        cur = mysql_conn.cursor()
        
        # Upsert dim_products
        for _, r in dim_df.iterrows():
            cur.execute("""
                INSERT INTO dim_products (product_id, product_name, brand, category, subcategory, ptype, variant, mrp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    product_name = VALUES(product_name),
                    brand = VALUES(brand),
                    category = VALUES(category),
                    subcategory = VALUES(subcategory),
                    ptype = VALUES(ptype),
                    variant = VALUES(variant),
                    mrp = VALUES(mrp),
                    updated_at = CURRENT_TIMESTAMP
            """, tuple(r))

        # Insert fact_product_snapshots
        fact_cols = ["product_id", "snapshot_time_str", "price", "mrp", "discount_amount", "discount_percentage",
                     "price_tier", "inventory", "is_sold_out", "stock_status", "rating", "product_position",
                     "widget_position", "merchant_type"]
        fact_data = [tuple(x) for x in df[fact_cols].values]
        cur.executemany("""
            INSERT INTO fact_product_snapshots 
            (product_id, snapshot_time, price, mrp, discount_amount, discount_percentage, price_tier,
             inventory, is_sold_out, stock_status, rating, product_position, widget_position, merchant_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, fact_data)

        # Refresh products compatibility table (latest snapshot state)
        for _, r in df.iterrows():
            cur.execute("""
                INSERT INTO products 
                (product_id, product_name, brand, category, subcategory, price, mrp, discount_percentage, rating,
                 inventory, product_position, widget_position, variant, is_sold_out, merchant_type, product_state,
                 product_display_name, currency, ptype, quantity, state, scrape_timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'INR', %s, 1, %s, %s)
                ON DUPLICATE KEY UPDATE
                    product_name = VALUES(product_name),
                    brand = VALUES(brand),
                    category = VALUES(category),
                    subcategory = VALUES(subcategory),
                    price = VALUES(price),
                    mrp = VALUES(mrp),
                    discount_percentage = VALUES(discount_percentage),
                    rating = VALUES(rating),
                    inventory = VALUES(inventory),
                    variant = VALUES(variant),
                    is_sold_out = VALUES(is_sold_out),
                    state = VALUES(state),
                    scrape_timestamp = VALUES(scrape_timestamp)
            """, (
                r["product_id"], r["product_name"], r["brand"], r["category"], r["subcategory"],
                r["price"], r["mrp"], r["discount_percentage"], r["rating"], r["inventory"],
                r["product_position"], r["widget_position"], r["variant"], int(r["is_sold_out"]),
                r["merchant_type"], r["state"], r["product_name"], r["ptype"], r["state"], r["snapshot_time_str"]
            ))

        mysql_conn.commit()
        cur.close()
        logger.info(f"Loaded {len(df)} records into MySQL.")

    # 3. Ingest into SQLite
    if sqlite_conn:
        cur = sqlite_conn.cursor()
        
        # Upsert dim_products in SQLite
        for _, r in dim_df.iterrows():
            cur.execute("""
                INSERT INTO dim_products (product_id, product_name, brand, category, subcategory, ptype, variant, mrp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    product_name = excluded.product_name,
                    brand = excluded.brand,
                    category = excluded.category,
                    subcategory = excluded.subcategory,
                    ptype = excluded.ptype,
                    variant = excluded.variant,
                    mrp = excluded.mrp,
                    updated_at = CURRENT_TIMESTAMP
            """, tuple(r))

        # Insert fact_product_snapshots
        fact_cols = ["product_id", "snapshot_time_str", "price", "mrp", "discount_amount", "discount_percentage",
                     "price_tier", "inventory", "is_sold_out", "stock_status", "rating", "product_position",
                     "widget_position", "merchant_type"]
        fact_data = [tuple(x) for x in df[fact_cols].values]
        cur.executemany("""
            INSERT INTO fact_product_snapshots 
            (product_id, snapshot_time, price, mrp, discount_amount, discount_percentage, price_tier,
             inventory, is_sold_out, stock_status, rating, product_position, widget_position, merchant_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fact_data)

        # Refresh products compatibility table
        for _, r in df.iterrows():
            cur.execute("""
                INSERT INTO products 
                (product_id, product_name, brand, category, subcategory, price, mrp, discount_percentage, rating,
                 inventory, product_position, widget_position, variant, is_sold_out, merchant_type, product_state,
                 product_display_name, currency, ptype, quantity, state, scrape_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'INR', ?, 1, ?, ?)
                ON CONFLICT(product_id) DO UPDATE SET
                    product_name = excluded.product_name,
                    brand = excluded.brand,
                    category = excluded.category,
                    subcategory = excluded.subcategory,
                    price = excluded.price,
                    mrp = excluded.mrp,
                    discount_percentage = excluded.discount_percentage,
                    rating = excluded.rating,
                    inventory = excluded.inventory,
                    variant = excluded.variant,
                    is_sold_out = excluded.is_sold_out,
                    state = excluded.state,
                    scrape_timestamp = excluded.scrape_timestamp
            """, (
                r["product_id"], r["product_name"], r["brand"], r["category"], r["subcategory"],
                r["price"], r["mrp"], r["discount_percentage"], r["rating"], r["inventory"],
                r["product_position"], r["widget_position"], r["variant"], int(r["is_sold_out"]),
                r["merchant_type"], r["state"], r["product_name"], r["ptype"], r["state"], r["snapshot_time_str"]
            ))

        sqlite_conn.commit()
        logger.info(f"Loaded {len(df)} records into SQLite ({SQLITE_PATH}).")


def load_all_processed_data():
    """Finds all processed CSV files and ingests them into MySQL and SQLite."""
    csv_files = sorted(glob.glob(str(BASE_DIR / "data" / "processed" / "products_*.csv")))
    if not csv_files:
        logger.warning("No processed products_*.csv files found in data/processed/.")
        return

    mysql_conn = get_mysql_connection()
    sqlite_conn = get_sqlite_connection()

    if mysql_conn:
        init_mysql_schema(mysql_conn)
    if sqlite_conn:
        init_sqlite_schema(sqlite_conn)

    seed_categories(mysql_conn, sqlite_conn)

    total_loaded = 0
    for csv_file in csv_files:
        logger.info(f"Ingesting: {csv_file}")
        df = pd.read_csv(csv_file)
        load_dataframe_to_db(df, mysql_conn=mysql_conn, sqlite_conn=sqlite_conn)
        total_loaded += len(df)

    if mysql_conn:
        mysql_conn.close()
    if sqlite_conn:
        sqlite_conn.close()

    logger.info(f"Dual-Mode ingestion finished. Total snapshot rows processed: {total_loaded}")


if __name__ == "__main__":
    load_all_processed_data()