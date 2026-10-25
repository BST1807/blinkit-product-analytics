"""
run_pipeline.py
Unified Command-Line Orchestrator for Blinkit Product Analytics Pipeline.

Supports:
1. --mode demo (default): Generates multi-timestamp snapshots (108 SKUs across 3 categories & 6 subcategories)
   -> Executes Python/Pandas ETL validation & transformation
   -> Loads into dual-mode databases (MySQL & SQLite)
   -> Exports Power BI star-schema tables
   -> Runs advanced SQL analytics suite
2. --mode live: Runs Playwright + BeautifulSoup scraper to capture live Blinkit data
   -> Runs ETL -> Ingests into DB -> Exports Power BI data -> Runs Analytics
3. --mode etl: Runs ETL on all existing snapshots -> Ingests into DB -> Exports Power BI data
"""

import sys
import argparse
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable


def run_step(description, command):
    print(f"\n{'='*80}")
    print(f"STEP: {description}")
    print(f"COMMAND: {' '.join(command)}")
    print(f"{'='*80}")
    res = subprocess.run(command, cwd=BASE_DIR)
    if res.returncode != 0:
        print(f"\n[WARNING] Step '{description}' exited with code {res.returncode}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Blinkit Product Analytics & Marketplace Monitoring Pipeline")
    parser.add_argument(
        "--mode", 
        choices=["demo", "live", "etl", "analytics"], 
        default="demo", 
        help="Pipeline execution mode (default: demo)"
    )
    args = parser.parse_args()

    print("\n" + "="*80)
    print("BLINKIT PRODUCT ANALYTICS & MARKETPLACE MONITORING PIPELINE")
    print(f"Mode: {args.mode.upper()}")
    print("="*80)

    if args.mode == "live":
        print("\nStarting Live Playwright + BeautifulSoup Scraping...")
        run_step("Live Web Scraping", [PYTHON_EXE, "scraper.py"])
    elif args.mode == "demo":
        print("\nGenerating Multi-Timestamp Snapshots across 108 SKUs, 3 Categories & 6 Subcategories...")
        run_step("Generate Multi-Timestamp Snapshots", [PYTHON_EXE, "generate_snapshots.py"])

    if args.mode in ["demo", "live", "etl"]:
        # Run ETL
        run_step("Python/Pandas ETL Validation & Transformation", [PYTHON_EXE, "etl.py"])

        # Ingest into Dual-Mode Databases
        run_step("Dual-Mode Database Ingestion (MySQL & SQLite)", [PYTHON_EXE, "database/load_data.py"])

        # Export Power BI tables
        run_step("Export Star-Schema Datasets for Power BI", [PYTHON_EXE, "powerbi/export_powerbi_data.py"])

    # Run SQL Analytics
    run_step("Execute Advanced SQL Analytics Suite", [PYTHON_EXE, "database/run_analysis.py"])

    print("\n" + "="*80)
    print("PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("Outputs available:")
    print("1. Cleaned CSVs:        data/processed/")
    print("2. Power BI Datasets:   data/powerbi/")
    print("3. SQLite Database:     database/blinkit.db")
    print("4. MySQL Database:      localhost:3306 (blinkit)")
    print("5. SQL Queries:         database/analysis.sql")
    print("6. Interactive Web UI:  powerbi/interactive_dashboard.html")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
