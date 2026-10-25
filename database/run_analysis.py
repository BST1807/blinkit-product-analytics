"""
database/run_analysis.py
Executes analytical SQL queries from database/analysis.sql on either MySQL or SQLite,
printing structured analytical results to the console.
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def run_analytics():
    # Attempt MySQL first, fallback to SQLite
    use_mysql = False
    conn = None
    try:
        import mysql.connector
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "pass"),
            database=os.getenv("MYSQL_DATABASE", "blinkit")
        )
        use_mysql = True
        print("=== RUNNING ANALYTICS ON MYSQL SERVER (blinkit) ===")
    except Exception as e:
        print(f"MySQL unavailable ({e}). Running analytics on SQLite (database/blinkit.db)...")
        conn = sqlite3.connect(BASE_DIR / "database" / "blinkit.db")

    queries = {
        "1. Catalog Overview": """
            SELECT 
                COUNT(DISTINCT product_id) AS total_skus,
                COUNT(DISTINCT brand) AS total_brands,
                COUNT(DISTINCT category) AS total_categories,
                COUNT(DISTINCT subcategory) AS total_subcategories,
                ROUND(AVG(price), 2) AS catalog_avg_price,
                ROUND(AVG(discount_percentage), 2) AS catalog_avg_discount_pct
            FROM products;
        """,
        "2. Assortment & Average Metrics by Subcategory": """
            SELECT 
                category,
                subcategory,
                COUNT(*) AS total_skus,
                COUNT(DISTINCT brand) AS brand_count,
                ROUND(AVG(price), 2) AS avg_price,
                ROUND(AVG(rating), 2) AS avg_rating,
                ROUND(AVG(discount_percentage), 2) AS avg_discount_pct
            FROM products
            GROUP BY category, subcategory
            ORDER BY category, total_skus DESC;
        """,
        "3. Availability & Stock-Out Rates by Category": """
            SELECT 
                category,
                COUNT(*) AS total_products,
                SUM(CASE WHEN state = 'out_of_stock' OR is_sold_out = 1 THEN 1 ELSE 0 END) AS out_of_stock_count,
                ROUND(100.0 * SUM(CASE WHEN state = 'out_of_stock' OR is_sold_out = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) AS stock_out_rate_pct
            FROM products
            GROUP BY category
            ORDER BY stock_out_rate_pct DESC;
        """,
        "4. Chronic Recurring Stock-Out SKUs (Across Historical Snapshots)": """
            SELECT 
                p.product_name,
                p.brand,
                p.subcategory,
                COUNT(s.snapshot_id) AS snapshots_monitored,
                SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) AS oos_count,
                ROUND(100.0 * SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) / COUNT(s.snapshot_id), 1) AS oos_risk_pct
            FROM dim_products p
            JOIN fact_product_snapshots s ON p.product_id = s.product_id
            GROUP BY p.product_id, p.product_name, p.brand, p.subcategory
            HAVING oos_count >= 2
            ORDER BY oos_risk_pct DESC
            LIMIT 8;
        """,
        "5. Assortment Concentration: Herfindahl-Hirschman Index (HHI)": """
            WITH subcat_shares AS (
                SELECT 
                    category,
                    subcategory,
                    brand,
                    100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY subcategory) AS share_pct
                FROM products
                GROUP BY category, subcategory, brand
            )
            SELECT 
                subcategory,
                ROUND(SUM(share_pct * share_pct), 0) AS hhi_index,
                CASE 
                    WHEN SUM(share_pct * share_pct) > 2500 THEN 'Highly Concentrated'
                    WHEN SUM(share_pct * share_pct) BETWEEN 1500 AND 2500 THEN 'Moderately Concentrated'
                    ELSE 'Competitive'
                END AS market_structure,
                COUNT(DISTINCT brand) AS brand_count
            FROM subcat_shares
            GROUP BY subcategory
            ORDER BY hhi_index DESC;
        """,
        "6. Category Norm Divergence (Overpriced Outliers with Lower Ratings)": """
            WITH category_benchmarks AS (
                SELECT 
                    category,
                    AVG(price) AS cat_avg_price,
                    AVG(rating) AS cat_avg_rating
                FROM products
                GROUP BY category
            )
            SELECT 
                p.product_name,
                p.brand,
                p.category,
                p.price,
                ROUND(b.cat_avg_price, 2) AS cat_avg_price,
                ROUND(((p.price - b.cat_avg_price) / b.cat_avg_price) * 100, 1) AS price_premium_pct,
                p.rating,
                ROUND(b.cat_avg_rating, 2) AS cat_avg_rating
            FROM products p
            JOIN category_benchmarks b ON p.category = b.category
            WHERE p.price > b.cat_avg_price AND p.rating < b.cat_avg_rating
            ORDER BY price_premium_pct DESC
            LIMIT 5;
        """
    }

    for title, query in queries.items():
        print(f"\n--- {title} ---")
        try:
            df = pd.read_sql(query, conn)
            print(df.to_string(index=False))
        except Exception as err:
            print(f"Error running query: {err}")

    conn.close()


if __name__ == "__main__":
    run_analytics()
