USE blinkit;


-- ==========================================
-- 1. PRODUCT OVERVIEW
-- ==========================================

-- Q1. Total number of products
SELECT COUNT(*) AS total_products
FROM products;


-- Q2. Products by availability status
SELECT
    state,
    COUNT(*) AS product_count
FROM products
GROUP BY state;


-- ==========================================
-- 2. BRAND ANALYSIS
-- ==========================================

-- Q3. Number of products by brand
SELECT
    brand,
    COUNT(*) AS product_count
FROM products
GROUP BY brand
ORDER BY product_count DESC;


-- Q4. Average price and product count by brand
SELECT
    brand,
    ROUND(AVG(price), 2) AS avg_price,
    COUNT(*) AS product_count
FROM products
GROUP BY brand
ORDER BY avg_price DESC;


-- Q5. Average discount by brand
SELECT
    brand,
    ROUND(AVG((mrp - price) / mrp * 100), 2) AS avg_discount_percentage,
    COUNT(*) AS discounted_products
FROM products
WHERE mrp > price
GROUP BY brand
ORDER BY avg_discount_percentage DESC;


-- ==========================================
-- 3. PRICING ANALYSIS
-- ==========================================

-- Q6. Top 10 most expensive products
SELECT
    product_name,
    brand,
    price,
    mrp
FROM products
ORDER BY price DESC
LIMIT 10;


-- Q7. Products with the highest discounts
SELECT
    product_name,
    brand,
    price,
    mrp,
    ROUND((mrp - price) / mrp * 100, 2) AS discount_percentage
FROM products
WHERE mrp > price
ORDER BY discount_percentage DESC;


-- ==========================================
-- 4. INVENTORY ANALYSIS
-- ==========================================

-- Q8. Out-of-stock products
SELECT
    product_name,
    brand,
    inventory,
    price
FROM products
WHERE state = 'out_of_stock'
ORDER BY brand, product_name;


-- Q9. Out-of-stock rate by brand
SELECT
    brand,
    COUNT(*) AS total_products,
    SUM(state = 'out_of_stock') AS out_of_stock_products,
    ROUND(
        SUM(state = 'out_of_stock') / COUNT(*) * 100,
        2
    ) AS out_of_stock_rate
FROM products
GROUP BY brand
ORDER BY out_of_stock_rate DESC;


-- ==========================================
-- 5. PRODUCT-LEVEL ANALYSIS
-- ==========================================

-- Q10. Pricing, discount and availability
SELECT
    product_name,
    brand,
    state,
    price,
    mrp,
    ROUND((mrp - price) / mrp * 100, 2) AS discount_percentage
FROM products
ORDER BY state, discount_percentage DESC;

-- Q11. Product state distribution
SELECT
    product_state,
    COUNT(*) AS product_count
FROM products
GROUP BY product_state
ORDER BY product_count DESC;

-- Q12. Products by merchant type
SELECT
    merchant_type,
    COUNT(*) AS product_count
FROM products
GROUP BY merchant_type
ORDER BY product_count DESC;

-- Q13. Rating distribution
SELECT
    rating,
    COUNT(*) AS product_count
FROM products
GROUP BY rating
ORDER BY rating DESC;

-- Q14. Products by product position
SELECT
    product_position,
    COUNT(*) AS product_count
FROM products
GROUP BY product_position
ORDER BY product_count DESC;

-- Q15. Products by widget position
SELECT
    widget_position,
    COUNT(*) AS product_count
FROM products
GROUP BY widget_position
ORDER BY widget_position;