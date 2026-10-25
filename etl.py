"""
etl.py
Production-Grade Python/Pandas ETL Pipeline for Blinkit Product Analytics.

Stages:
1. EXTRACT: Ingests raw JSON snapshots from data/raw/
2. VALIDATE: Performs schema checks, range validations, null audits, and business rules
3. TRANSFORM: Calculates discounts, price tiers, stock status flags, and standardized fields
4. EXPORT: Generates clean, timestamped processed CSVs for database ingestion and Power BI
"""

import os
import glob
import json
import logging
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("BlinkitETL")


class BlinkitETLPipeline:
    def __init__(self, raw_dir="data/raw", processed_dir="data/processed"):
        self.raw_dir = Path(raw_dir)
        self.processed_dir = Path(processed_dir)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.validation_report = {}

    def extract_from_file(self, file_path):
        """Extracts product records from a raw JSON snapshot."""
        logger.info(f"Extracting raw snapshot: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        snippets = data.get("response", {}).get("snippets", [])
        snapshot_time_str = data.get("scrape_timestamp", datetime.now().isoformat())
        try:
            snapshot_time = datetime.fromisoformat(snapshot_time_str.replace("Z", "+00:00"))
        except Exception:
            snapshot_time = datetime.now()

        extracted_records = []
        for s in snippets:
            common = s.get("tracking", {}).get("common_attributes", {})
            s_data = s.get("data", {})

            product_id = str(common.get("product_id") or s_data.get("identity", {}).get("id") or "").strip()
            if not product_id:
                continue

            name = common.get("name") or s_data.get("name", {}).get("text") or s_data.get("display_name", {}).get("text")
            brand = common.get("brand") or "Generic"
            price = common.get("price")
            mrp = common.get("mrp") or price
            rating_raw = common.get("rating") or s_data.get("rating", {}).get("value") or 0.0
            inventory = common.get("inventory")
            is_sold_out = s_data.get("is_sold_out", False)
            state = common.get("state") or s_data.get("product_state") or ("out_of_stock" if is_sold_out else "available")
            
            category = common.get("l0_category") or "General"
            subcategory = common.get("l1_category") or "General"
            ptype = common.get("ptype") or common.get("l2_category") or "Standard"
            variant = s_data.get("variant", {}).get("text") or common.get("variant") or "Standard"

            rec = {
                "product_id": product_id,
                "product_name": str(name).strip() if name else "Unknown Product",
                "brand": str(brand).strip(),
                "category": category,
                "subcategory": subcategory,
                "ptype": ptype,
                "variant": str(variant).strip(),
                "price": price,
                "mrp": mrp,
                "rating": rating_raw,
                "inventory": inventory,
                "is_sold_out": bool(is_sold_out),
                "state": state,
                "product_position": common.get("product_position", 0),
                "widget_position": common.get("widget_position", 0),
                "merchant_type": s_data.get("merchant_type", "express"),
                "snapshot_time": snapshot_time
            }
            extracted_records.append(rec)

        df = pd.DataFrame(extracted_records)
        logger.info(f"Extracted {len(df)} candidate products from {Path(file_path).name}")
        return df, snapshot_time

    def validate(self, df):
        """
        Validates data quality:
        - Required keys not null
        - Valid numeric price and mrp > 0
        - Logical price <= mrp check
        - Rating bounded between 0 and 5
        - Inventory >= 0
        - Deduplication per product_id within snapshot
        """
        initial_count = len(df)
        if initial_count == 0:
            return df, {"status": "EMPTY", "pass_count": 0, "fail_count": 0}

        # 1. Deduplicate by product_id within the snapshot
        df = df.drop_duplicates(subset=["product_id"], keep="first").copy()
        dedup_count = len(df)

        # 2. Coerce numeric types
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        df["mrp"] = pd.to_numeric(df["mrp"], errors="coerce")
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0.0)
        df["inventory"] = pd.to_numeric(df["inventory"], errors="coerce").fillna(0)

        # 3. Quality rules mask
        valid_mask = (
            df["product_id"].notna() & (df["product_id"] != "") &
            df["product_name"].notna() & (df["product_name"] != "") &
            df["price"].notna() & (df["price"] > 0) &
            df["mrp"].notna() & (df["mrp"] > 0) &
            (df["rating"] >= 0.0) & (df["rating"] <= 5.0) &
            (df["inventory"] >= 0)
        )

        invalid_records = df[~valid_mask]
        valid_df = df[valid_mask].copy()

        # Check price <= mrp anomaly (fix if price > mrp by aligning mrp = price)
        price_anomaly_mask = valid_df["price"] > valid_df["mrp"]
        if price_anomaly_mask.any():
            logger.warning(f"Found {price_anomaly_mask.sum()} records where price > mrp; normalizing mrp = price.")
            valid_df.loc[price_anomaly_mask, "mrp"] = valid_df.loc[price_anomaly_mask, "price"]

        report = {
            "initial_records": initial_count,
            "after_dedup": dedup_count,
            "valid_records": len(valid_df),
            "quarantined_records": len(invalid_records),
            "pass_rate_pct": round((len(valid_df) / max(1, initial_count)) * 100, 2)
        }
        logger.info(f"Validation Report: {report['valid_records']} valid / {report['initial_records']} raw ({report['pass_rate_pct']}%)")
        return valid_df, report

    def transform(self, df):
        """
        Calculates business metrics & analytical dimensions:
        - discount_amount and discount_percentage
        - price_tier classification (Budget, Mid-Range, Premium)
        - stock_status classification (In Stock, Low Stock, Out of Stock)
        - normalized brand and text cleaning
        """
        df = df.copy()

        # Ensure numeric precision
        df["price"] = df["price"].astype(float).round(2)
        df["mrp"] = df["mrp"].astype(float).round(2)
        df["rating"] = df["rating"].astype(float).round(2)
        df["inventory"] = df["inventory"].astype(int)

        # Calculate discount metrics
        df["discount_amount"] = (df["mrp"] - df["price"]).clip(lower=0.0).round(2)
        df["discount_percentage"] = np.where(
            df["mrp"] > 0,
            ((df["mrp"] - df["price"]) / df["mrp"] * 100.0).clip(lower=0.0).round(2),
            0.0
        )

        # Classify Price Tier
        def get_price_tier(price):
            if price < 35:
                return "Budget"
            elif price <= 80:
                return "Mid-Range"
            else:
                return "Premium"

        df["price_tier"] = df["price"].apply(get_price_tier)

        # Classify Stock Status
        def get_stock_status(row):
            if row["inventory"] == 0 or row["is_sold_out"] or str(row["state"]).lower() == "out_of_stock":
                return "Out of Stock"
            elif row["inventory"] <= 10:
                return "Low Stock"
            else:
                return "In Stock"

        df["stock_status"] = df.apply(get_stock_status, axis=1)
        df["is_sold_out"] = df["stock_status"] == "Out of Stock"
        df["state"] = np.where(df["is_sold_out"], "out_of_stock", "available")

        # Standardize brand casing
        df["brand"] = df["brand"].str.strip().str.title()

        return df

    def run_pipeline(self, specific_file=None):
        """
        Executes the ETL pipeline over raw snapshot JSONs.
        If specific_file is None, processes all available snapshots in data/raw/.
        """
        if specific_file:
            files_to_process = [Path(specific_file)]
        else:
            files_to_process = sorted(list(self.raw_dir.glob("blinkit_snapshot_*.json")))

        if not files_to_process:
            logger.error("No raw snapshot JSON files found to process.")
            return []

        processed_dfs = []
        for file_path in files_to_process:
            raw_df, snap_time = self.extract_from_file(file_path)
            valid_df, val_report = self.validate(raw_df)
            if valid_df.empty:
                continue

            trans_df = self.transform(valid_df)

            # Export individual processed CSV
            timestamp_str = snap_time.strftime("%Y-%m-%d_%H-%M-%S")
            csv_path = self.processed_dir / f"products_{timestamp_str}.csv"
            trans_df.to_csv(csv_path, index=False)
            logger.info(f"Saved processed CSV: {csv_path}")

            processed_dfs.append(trans_df)

        if processed_dfs:
            combined_df = pd.concat(processed_dfs, ignore_index=True)
            combined_path = self.processed_dir / "all_snapshots_consolidated.csv"
            combined_df.to_csv(combined_path, index=False)
            logger.info(f"Exported consolidated snapshot dataset ({len(combined_df)} rows) to {combined_path}")
            return processed_dfs
        
        return []


if __name__ == "__main__":
    pipeline = BlinkitETLPipeline()
    results = pipeline.run_pipeline()
    print(f"\nETL Execution Complete. Processed {len(results)} snapshots.")
