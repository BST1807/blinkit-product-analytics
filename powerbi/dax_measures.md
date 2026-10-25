# Power BI DAX Measures Library
## Blinkit Product Analytics & Marketplace Monitoring

This document provides the complete DAX calculation library for the Power BI dashboard, architected to support time-aware marketplace monitoring, stock-out detection, brand concentration, and category norm divergence.

---

### 1. Catalog & Assortment KPIs

#### 1.1 Total Monitored SKUs
```dax
Total SKUs = 
DISTINCTCOUNT(dim_products[product_id])
```

#### 1.2 Active Brands Count
```dax
Total Brands = 
DISTINCTCOUNT(dim_products[brand])
```

#### 1.3 Brand Shelf Share %
Measures a brand's share of total catalog SKUs within a selected category or subcategory.
```dax
Brand Shelf Share % = 
DIVIDE(
    [Total SKUs],
    CALCULATE([Total SKUs], ALLSELECTED(dim_products[brand])),
    0
)
```

#### 1.4 Herfindahl-Hirschman Index (HHI)
Quantifies brand assortment concentration within each category/subcategory.
```dax
HHI Concentration Score = 
SUMX(
    VALUES(dim_products[brand]),
    ([Brand Shelf Share %] * 100) ^ 2
)
```

---

### 2. Availability & Stock-Out Dynamics

#### 2.1 Currently In-Stock SKUs
```dax
In-Stock SKUs = 
CALCULATE(
    DISTINCTCOUNT(fact_snapshots[product_id]),
    fact_snapshots[stock_status] = "In Stock"
)
```

#### 2.2 Currently Out-of-Stock SKUs
```dax
Out-of-Stock SKUs = 
CALCULATE(
    DISTINCTCOUNT(fact_snapshots[product_id]),
    fact_snapshots[is_sold_out] = 1 || fact_snapshots[stock_status] = "Out of Stock"
)
```

#### 2.3 Stock-Out Rate %
Percentage of catalog facing availability failure in the selected time period.
```dax
Stock-Out Rate % = 
DIVIDE(
    CALCULATE(COUNT(fact_snapshots[snapshot_id]), fact_snapshots[is_sold_out] = 1),
    COUNT(fact_snapshots[snapshot_id]),
    0
)
```

#### 2.4 Recurring Stock-Out Risk Flag
Surfaces chronic stock-out items that fail availability across multiple historical snapshots.
```dax
Recurring OOS Risk Score = 
VAR TotalTracked = COUNT(fact_snapshots[snapshot_id])
VAR OOSTimes = CALCULATE(COUNT(fact_snapshots[snapshot_id]), fact_snapshots[is_sold_out] = 1)
RETURN
    DIVIDE(OOSTimes, TotalTracked, 0)
```

```dax
Recurring Risk Tier = 
IF([Recurring OOS Risk Score] >= 0.5, "High Recurring Risk", 
    IF([Recurring OOS Risk Score] > 0, "Moderate Risk", "Stable Availability")
)
```

---

### 3. Pricing, Discount Depth & Category Norm Divergence

#### 3.1 Average Selling Price (ASP)
```dax
Average Selling Price = 
AVERAGE(fact_snapshots[price])
```

#### 3.2 Average Catalog MRP
```dax
Average MRP = 
AVERAGE(fact_snapshots[mrp])
```

#### 3.3 Average Discount Depth %
```dax
Avg Discount Depth % = 
AVERAGE(fact_snapshots[discount_percentage])
```

#### 3.4 Discounted SKUs Penetration %
```dax
Discount Penetration % = 
DIVIDE(
    CALCULATE(DISTINCTCOUNT(fact_snapshots[product_id]), fact_snapshots[discount_percentage] > 0),
    [Total SKUs],
    0
)
```

#### 3.5 Category Benchmark Selling Price
Calculates the category baseline price ignoring individual product selection.
```dax
Category Benchmark Price = 
CALCULATE(
    AVERAGE(fact_snapshots[price]),
    ALLEXCEPT(dim_products, dim_products[category])
)
```

#### 3.6 Category Benchmark Rating
Calculates the category baseline rating ignoring individual product selection.
```dax
Category Benchmark Rating = 
CALCULATE(
    AVERAGE(fact_snapshots[rating]),
    ALLEXCEPT(dim_products, dim_products[category])
)
```

#### 3.7 Price Divergence from Category Norm %
Quantifies how much a SKU's price deviates from its category peer average.
```dax
Price Divergence from Norm % = 
DIVIDE(
    [Average Selling Price] - [Category Benchmark Price],
    [Category Benchmark Price],
    0
)
```

#### 3.8 Category Norm Positioning Quadrant
Classifies products into 4 strategic quadrants based on price vs rating divergence.
```dax
Category Norm Quadrant = 
VAR PriceDiff = [Average Selling Price] - [Category Benchmark Price]
VAR RatingDiff = AVERAGE(fact_snapshots[rating]) - [Category Benchmark Rating]
RETURN
    SWITCH(
        TRUE(),
        PriceDiff > 0 && RatingDiff < 0, "Overpriced / Underperforming",
        PriceDiff < 0 && RatingDiff > 0, "High Value / Underpriced Gem",
        PriceDiff > 0 && RatingDiff >= 0, "Premium Justified",
        "Budget Standard"
    )
```

---

### 4. Time-Aware Telemetry & Price Fluctuation

#### 4.1 Price Volatility Flag
Detects if a SKU experienced price adjustments across monitoring snapshots.
```dax
Price Volatility Flag = 
VAR MinPrice = MIN(fact_snapshots[price])
VAR MaxPrice = MAX(fact_snapshots[price])
RETURN
    IF(MaxPrice > MinPrice, "Price Fluctuation Detected", "Stable Pricing")
```
