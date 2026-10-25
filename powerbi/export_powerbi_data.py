"""
powerbi/export_powerbi_data.py
Exports optimized Star-Schema tables and aggregated reporting layers
specifically formatted for Power BI ingestion.

Outputs generated in data/powerbi/:
1. dim_products.csv
2. dim_categories.csv
3. dim_dates.csv
4. fact_snapshots.csv
5. oos_risk_monitoring.csv
"""

import os
import sqlite3
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "data" / "powerbi"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def export_powerbi_tables():
    print("Connecting to database for Power BI export...")
    # Read from SQLite for maximum reproducibility
    db_path = BASE_DIR / "database" / "blinkit.db"
    conn = sqlite3.connect(db_path)

    # 1. dim_products
    dim_products_df = pd.read_sql("""
        SELECT 
            product_id,
            product_name,
            brand,
            category,
            subcategory,
            ptype,
            variant,
            mrp
        FROM dim_products
    """, conn)
    dim_products_df.to_csv(OUTPUT_DIR / "dim_products.csv", index=False)
    print(f"Exported dim_products.csv: {len(dim_products_df)} rows")

    # 2. dim_categories
    dim_categories_df = pd.read_sql("""
        SELECT 
            category_id,
            category_name,
            subcategory_id,
            subcategory_name
        FROM dim_categories
    """, conn)
    dim_categories_df.to_csv(OUTPUT_DIR / "dim_categories.csv", index=False)
    print(f"Exported dim_categories.csv: {len(dim_categories_df)} rows")

    # 3. fact_snapshots
    fact_snapshots_df = pd.read_sql("""
        SELECT 
            snapshot_id,
            product_id,
            snapshot_time,
            price,
            mrp,
            discount_amount,
            discount_percentage,
            price_tier,
            inventory,
            is_sold_out,
            stock_status,
            rating,
            product_position,
            widget_position,
            merchant_type
        FROM fact_product_snapshots
    """, conn)
    fact_snapshots_df.to_csv(OUTPUT_DIR / "fact_snapshots.csv", index=False)
    print(f"Exported fact_snapshots.csv: {len(fact_snapshots_df)} rows")

    # 4. dim_dates
    fact_snapshots_df["date"] = pd.to_datetime(fact_snapshots_df["snapshot_time"]).dt.date
    dates = pd.date_range(
        start=fact_snapshots_df["date"].min(),
        end=fact_snapshots_df["date"].max(),
        freq="D"
    )
    dim_dates_df = pd.DataFrame({
        "Date": dates,
        "Year": dates.year,
        "Month": dates.month,
        "MonthName": dates.strftime("%B"),
        "Day": dates.day,
        "DayOfWeek": dates.day_name(),
        "IsWeekend": dates.dayofweek.isin([5, 6]).astype(int)
    })
    dim_dates_df.to_csv(OUTPUT_DIR / "dim_dates.csv", index=False)
    print(f"Exported dim_dates.csv: {len(dim_dates_df)} rows")

    # 5. Recurring Stockout Monitoring Layer
    oos_monitoring_df = pd.read_sql("""
        SELECT 
            p.product_id,
            p.product_name,
            p.brand,
            p.category,
            p.subcategory,
            COUNT(s.snapshot_id) AS snapshots_tracked,
            SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) AS oos_instances,
            ROUND(100.0 * SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) / COUNT(s.snapshot_id), 1) AS oos_risk_percentage,
            CASE 
                WHEN SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) >= 2 THEN 'HIGH RISK'
                WHEN SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) = 1 THEN 'MODERATE RISK'
                ELSE 'LOW / STABLE'
            END AS risk_classification
        FROM dim_products p
        JOIN fact_product_snapshots s ON p.product_id = s.product_id
        GROUP BY p.product_id, p.product_name, p.brand, p.category, p.subcategory
    """, conn)
    oos_monitoring_df.to_csv(OUTPUT_DIR / "oos_risk_monitoring.csv", index=False)
    print(f"Exported oos_risk_monitoring.csv: {len(oos_monitoring_df)} rows")

    conn.close()
    print(f"\nAll Power BI star-schema tables successfully exported to: {OUTPUT_DIR}")


if __name__ == "__main__":
    export_powerbi_tables()
