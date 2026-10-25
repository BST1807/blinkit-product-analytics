-- ========================================================================================
-- Blinkit Product Analytics & Marketplace Monitoring
-- Advanced SQL Analytics Suite
-- 
-- Compatible with both MySQL 8.0+ and SQLite 3.25+ (Standard ANSI SQL with CTEs & Window Functions)
-- 
-- Resume Alignment:
-- 1. Evaluates stock-out patterns & recurring availability risk across time snapshots
-- 2. Calculates brand assortment concentration & market share (Herfindahl-Hirschman Index - HHI)
-- 3. Measures discount depth and promotional distribution by category/subcategory
-- 4. Assesses rating-to-price alignment and surfaces where pricing diverges from category norms
-- ========================================================================================

-- ========================================================================================
-- SECTION 1: CATALOG OVERVIEW & ASSORTMENT ARCHITECTURE
-- ========================================================================================

-- Q1. Total SKU scale, unique brands, and category coverage across the catalog
SELECT 
    COUNT(DISTINCT product_id) AS total_skus,
    COUNT(DISTINCT brand) AS total_brands,
    COUNT(DISTINCT category) AS total_categories,
    COUNT(DISTINCT subcategory) AS total_subcategories,
    ROUND(AVG(price), 2) AS catalog_avg_price,
    ROUND(AVG(discount_percentage), 2) AS catalog_avg_discount_pct
FROM products;

-- Q2. Assortment distribution across categories and subcategories
SELECT 
    category,
    subcategory,
    COUNT(*) AS total_skus,
    COUNT(DISTINCT brand) AS brand_count,
    ROUND(AVG(price), 2) AS avg_price,
    ROUND(MIN(price), 2) AS min_price,
    ROUND(MAX(price), 2) AS max_price,
    ROUND(AVG(rating), 2) AS avg_rating
FROM products
GROUP BY category, subcategory
ORDER BY category, total_skus DESC;


-- ========================================================================================
-- SECTION 2: STOCK-OUT PATTERNS & RECURRING AVAILABILITY RISK
-- (Analyzes time-series telemetry in fact_product_snapshots to detect recurring stock-out risk)
-- ========================================================================================

-- Q3. Category-level availability health & stock-out rate
SELECT 
    category,
    COUNT(*) AS total_products,
    SUM(CASE WHEN state = 'out_of_stock' OR is_sold_out = 1 THEN 1 ELSE 0 END) AS out_of_stock_count,
    SUM(CASE WHEN state = 'available' AND is_sold_out = 0 THEN 1 ELSE 0 END) AS in_stock_count,
    ROUND(
        100.0 * SUM(CASE WHEN state = 'out_of_stock' OR is_sold_out = 1 THEN 1 ELSE 0 END) / COUNT(*), 
        2
    ) AS stock_out_rate_pct
FROM products
GROUP BY category
ORDER BY stock_out_rate_pct DESC;

-- Q4. Chronic & Recurring Stock-Out Detection Across Time Snapshots
-- Surfacing SKUs that repeatedly experience stock-outs across historical monitoring snapshots
SELECT 
    p.product_id,
    p.product_name,
    p.brand,
    p.category,
    p.subcategory,
    COUNT(s.snapshot_id) AS total_snapshots_tracked,
    SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) AS out_of_stock_instances,
    ROUND(
        100.0 * SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) / COUNT(s.snapshot_id), 
        1
    ) AS recurring_oos_risk_pct,
    CASE 
        WHEN SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) >= 2 THEN 'HIGH RECURRING RISK'
        WHEN SUM(CASE WHEN s.is_sold_out = 1 OR s.inventory = 0 THEN 1 ELSE 0 END) = 1 THEN 'MODERATE RISK'
        ELSE 'STABLE AVAILABILITY'
    END AS stockout_risk_tier
FROM dim_products p
JOIN fact_product_snapshots s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.brand, p.category, p.subcategory
HAVING out_of_stock_instances > 0
ORDER BY recurring_oos_risk_pct DESC, out_of_stock_instances DESC;


-- ========================================================================================
-- SECTION 3: BRAND ASSORTMENT CONCENTRATION & MARKET COMPETITIVENESS
-- (Evaluates shelf-share dominance and computes Herfindahl-Hirschman Index - HHI)
-- ========================================================================================

-- Q5. Top brands by shelf space / SKU share per subcategory
WITH brand_share_cte AS (
    SELECT 
        subcategory,
        brand,
        COUNT(*) AS brand_sku_count,
        ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY subcategory), 2) AS shelf_share_pct,
        DENSE_RANK() OVER (PARTITION BY subcategory ORDER BY COUNT(*) DESC) AS rank_in_subcategory
    FROM products
    GROUP BY subcategory, brand
)
SELECT 
    subcategory,
    rank_in_subcategory,
    brand,
    brand_sku_count,
    shelf_share_pct
FROM brand_share_cte
WHERE rank_in_subcategory <= 3
ORDER BY subcategory, rank_in_subcategory;

-- Q6. Herfindahl-Hirschman Index (HHI) for Assortment Concentration
-- HHI < 1500 = Competitive; 1500-2500 = Moderately Concentrated; > 2500 = Highly Concentrated / Monopolistic
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
    category,
    subcategory,
    ROUND(SUM(share_pct * share_pct), 0) AS hhi_index,
    CASE 
        WHEN SUM(share_pct * share_pct) > 2500 THEN 'Highly Concentrated'
        WHEN SUM(share_pct * share_pct) BETWEEN 1500 AND 2500 THEN 'Moderately Concentrated'
        ELSE 'Competitive Marketplace'
    END AS concentration_level,
    COUNT(DISTINCT brand) AS total_brands_competing
FROM subcat_shares
GROUP BY category, subcategory
ORDER BY hhi_index DESC;


-- ========================================================================================
-- SECTION 4: DISCOUNT DEPTH & PROMOTIONAL SPREAD BY CATEGORY
-- ========================================================================================

-- Q7. Discount depth metrics by category & subcategory
SELECT 
    category,
    subcategory,
    COUNT(*) AS total_skus,
    SUM(CASE WHEN discount_percentage > 0 THEN 1 ELSE 0 END) AS discounted_skus,
    ROUND(100.0 * SUM(CASE WHEN discount_percentage > 0 THEN 1 ELSE 0 END) / COUNT(*), 1) AS promo_penetration_pct,
    ROUND(AVG(discount_percentage), 2) AS avg_discount_pct,
    ROUND(MAX(discount_percentage), 2) AS max_discount_pct,
    ROUND(AVG(CASE WHEN discount_percentage > 0 THEN discount_percentage ELSE NULL END), 2) AS avg_depth_on_discounted_skus
FROM products
GROUP BY category, subcategory
ORDER BY avg_discount_pct DESC;

-- Q8. Discount Bracket Breakdown across the catalog
SELECT 
    category,
    CASE 
        WHEN discount_percentage = 0 THEN 'No Discount (0%)'
        WHEN discount_percentage <= 5 THEN 'Low Discount (1-5%)'
        WHEN discount_percentage <= 15 THEN 'Moderate Discount (6-15%)'
        ELSE 'Deep Discount (>15%)'
    END AS discount_bracket,
    COUNT(*) AS sku_count,
    ROUND(AVG(price), 2) AS avg_selling_price
FROM products
GROUP BY category, discount_bracket
ORDER BY category, sku_count DESC;


-- ========================================================================================
-- SECTION 5: RATING-TO-PRICE ALIGNMENT & CATEGORY NORM DIVERGENCE
-- (Identifies where product pricing or rating diverges significantly from category norms)
-- ========================================================================================

-- Q9. Category Norm Benchmarking & Divergence Analysis
WITH category_benchmarks AS (
    SELECT 
        category,
        ROUND(AVG(price), 2) AS cat_avg_price,
        ROUND(AVG(rating), 2) AS cat_avg_rating
    FROM products
    GROUP BY category
)
SELECT 
    p.product_id,
    p.product_name,
    p.brand,
    p.category,
    p.price,
    b.cat_avg_price,
    ROUND(100.0 * (p.price - b.cat_avg_price) / b.cat_avg_price, 1) AS price_divergence_from_norm_pct,
    p.rating,
    b.cat_avg_rating,
    ROUND(p.rating - b.cat_avg_rating, 2) AS rating_divergence_from_norm,
    CASE 
        WHEN p.price > b.cat_avg_price AND p.rating < b.cat_avg_rating THEN 'Overpriced / Low Satisfaction'
        WHEN p.price < b.cat_avg_price AND p.rating > b.cat_avg_rating THEN 'High Value / Underpriced Gem'
        WHEN p.price > b.cat_avg_price AND p.rating >= b.cat_avg_rating THEN 'Premium Justified'
        ELSE 'Budget / Standard Value'
    END AS category_norm_classification
FROM products p
JOIN category_benchmarks b ON p.category = b.category
ORDER BY price_divergence_from_norm_pct DESC;

-- Q10. High-Risk Outliers: Products where price is significantly above category norm but rating is below average
WITH category_benchmarks AS (
    SELECT 
        category,
        AVG(price) AS cat_avg_price,
        AVG(rating) AS cat_avg_rating
    FROM products
    GROUP BY category
)
SELECT 
    p.product_id,
    p.product_name,
    p.brand,
    p.category,
    p.price,
    ROUND(b.cat_avg_price, 2) AS category_avg_price,
    ROUND(((p.price - b.cat_avg_price) / b.cat_avg_price) * 100, 1) AS price_premium_pct,
    p.rating,
    ROUND(b.cat_avg_rating, 2) AS category_avg_rating
FROM products p
JOIN category_benchmarks b ON p.category = b.category
WHERE p.price > b.cat_avg_price AND p.rating < b.cat_avg_rating
ORDER BY price_premium_pct DESC;


-- ========================================================================================
-- SECTION 6: TIME-SERIES MONITORING LAYER
-- (Tracks price volatility, inventory depletion, and assortment shifts over time)
-- ========================================================================================

-- Q11. Price Fluctuation Monitoring across snapshots
WITH snapshot_ranked AS (
    SELECT 
        product_id,
        snapshot_time,
        price,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY snapshot_time ASC) AS rn_earliest,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY snapshot_time DESC) AS rn_latest
    FROM fact_product_snapshots
),
earliest_snap AS (
    SELECT product_id, price AS initial_price, snapshot_time AS initial_time 
    FROM snapshot_ranked WHERE rn_earliest = 1
),
latest_snap AS (
    SELECT product_id, price AS latest_price, snapshot_time AS latest_time 
    FROM snapshot_ranked WHERE rn_latest = 1
)
SELECT 
    p.product_name,
    p.brand,
    p.category,
    e.initial_price,
    l.latest_price,
    ROUND(l.latest_price - e.initial_price, 2) AS price_change,
    ROUND(100.0 * (l.latest_price - e.initial_price) / e.initial_price, 1) AS price_change_pct,
    CASE 
        WHEN l.latest_price < e.initial_price THEN 'Price Drop / Promotion'
        WHEN l.latest_price > e.initial_price THEN 'Price Increase'
        ELSE 'Stable Price'
    END AS price_trajectory
FROM earliest_snap e
JOIN latest_snap l ON e.product_id = l.product_id
JOIN dim_products p ON p.product_id = e.product_id
WHERE e.initial_price <> l.latest_price
ORDER BY price_change_pct ASC;