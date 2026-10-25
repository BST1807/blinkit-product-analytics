# Power BI Dashboard Specification & Architecture
## Blinkit Product Analytics & Marketplace Monitoring

This document details the multi-page Power BI dashboard architecture, data model relationships, visual card configurations, and filter interactions designed for executive and category management stakeholders.

---

### 1. Data Model & Star-Schema Relationships

```
+-------------------------------------------------------------+
|                        dim_dates                            |
|  - Date (PK) | Year | Month | MonthName | Day | DayOfWeek   |
+-------------------------------------------------------------+
                              | 1
                              |
                              | * (1-to-Many on Date = snapshot_time::date)
+-------------------------------------------------------------+
|                     fact_snapshots                          |
|  - snapshot_id (PK)                                         |
|  - product_id (FK) --------------------+                    |
|  - snapshot_time                       |                    |
|  - price                               |                    |
|  - mrp                                 |                    |
|  - discount_percentage                 |                    |
|  - inventory                           |                    |
|  - is_sold_out                         |                    |
|  - stock_status                        |                    |
|  - rating                              |                    |
+-------------------------------------------------------------+
                              | *
                              |
                              | 1 (Many-to-1 on product_id)
+-------------------------------------------------------------+
|                      dim_products                           |
|  - product_id (PK)                                          |
|  - product_name                                             |
|  - brand                                                    |
|  - category ---------------------------+                    |
|  - subcategory                         |                    |
|  - ptype                               |                    |
|  - variant                             |                    |
+-------------------------------------------------------------+
                                         | *
                                         |
                                         | 1 (Many-to-1 on category_name)
+-------------------------------------------------------------+
|                     dim_categories                          |
|  - category_id | category_name | subcategory_id | name      |
+-------------------------------------------------------------+
```

---

### 2. Multi-Page Dashboard Architecture

#### Page 1: Executive KPI & Category Health Overview
* **Purpose**: Top-level executive monitoring of catalog scale, availability, pricing, and discount depth across categories.
* **Top KPI Scorecards**:
  - `Total SKUs Monitored` (128 SKUs)
  - `Overall Stock-Out Rate %` (7.03%)
  - `Average Selling Price` (₹51.36)
  - `Average Discount Depth` (6.21%)
  - `Active Brands Count` (52 Brands)
* **Visual 1 (Donut Chart)**: Assortment share by Category (`Dairy, Bread & Eggs`, `Cold Drinks & Juices`, `Snacks & Munchies`).
* **Visual 2 (Grouped Bar Chart)**: Stock-out Rate % vs In-Stock % by Category.
* **Visual 3 (Clustered Column Chart)**: Average Selling Price vs Average MRP by Subcategory.
* **Slicers**: Category Dropdown, Date Range Slider, Merchant Type.

---

#### Page 2: Stock-Out & Availability Monitoring Layer (Time-Aware)
* **Purpose**: Real-time detection of inventory depletion, recurring stock-out risk, and availability degradation across snapshots.
* **Top KPI Scorecards**:
  - `Current In-Stock SKUs`
  - `Current Out-of-Stock SKUs`
  - `High Recurring Risk SKUs` (Items out of stock in $\ge 50\%$ of tracked snapshots)
* **Visual 1 (Line Chart - Time Series)**: Stock-out Rate % across Snapshot Timestamps (T1 $\rightarrow$ T2 $\rightarrow$ T3).
* **Visual 2 (Matrix / Heatmap Table)**: Product-level Stock-out Telemetry:
  - Columns: Product Name, Brand, Subcategory, Snapshot 1 State, Snapshot 2 State, Snapshot 3 State, Recurring Risk Flag.
* **Visual 3 (Horizontal Bar Chart)**: Brands with highest stock-out rates.
* **Slicers**: Availability Status (`In Stock`, `Low Stock`, `Out of Stock`), Risk Tier (`High Recurring Risk`, `Moderate Risk`).

---

#### Page 3: Pricing & Discount Depth Diagnostics
* **Purpose**: In-depth analysis of discounting strategies, pricing tiers, and promotional depth across subcategories.
* **Top KPI Scorecards**:
  - `Discounted SKUs Penetration %`
  - `Maximum Discount Depth %`
  - `Average Discount on Discounted SKUs`
* **Visual 1 (Scatter Plot - Rating vs Price Alignment)**:
  - X-Axis: Price (₹)
  - Y-Axis: Customer Rating (0 - 5.0)
  - Reference Lines: Category Average Price, Category Average Rating
  - Color: Category Norm Quadrant (`Overpriced Outlier`, `High Value Gem`, `Premium Justified`, `Budget Standard`).
* **Visual 2 (Stacked Bar Chart)**: Discount Bracket Distribution by Category (`0%`, `1-5%`, `6-15%`, `>15%`).
* **Visual 3 (Table)**: Top 10 Deepest Discounted SKUs.

---

#### Page 4: Brand Assortment & Market Share (HHI)
* **Purpose**: Assessing brand dominance, shelf share concentration, and competitive structure.
* **Top KPI Scorecards**:
  - `Total Competing Brands` (52)
  - `Highest HHI Subcategory` (Milk & Cream: 2,368)
  - `Most Competitive Subcategory` (Soft Drinks & Sodas: 926)
* **Visual 1 (Treemap)**: Brand Shelf Share within Subcategories.
* **Visual 2 (Gauge / Bar Chart)**: HHI Concentration Index by Subcategory with thresholds (Competitive < 1500, Moderate 1500-2500, Concentrated > 2500).
* **Visual 3 (Table)**: Brand Benchmarking Table: SKU Count, Shelf Share %, Avg Price, Avg Rating, Stock-out Rate.
