-- ====================================================================
-- Blinkit Product Analytics & Marketplace Monitoring - Database Schema
-- Supports both MySQL and SQLite (ANSI SQL compatible standard DDL)
-- ====================================================================

-- 1. Dimension: Categories & Subcategories
CREATE TABLE IF NOT EXISTS dim_categories (
    category_id INT PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    subcategory_id INT NOT NULL,
    subcategory_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Dimension: Products (Master Catalog Dimension)
CREATE TABLE IF NOT EXISTS dim_products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100) NOT NULL,
    ptype VARCHAR(100),
    variant VARCHAR(100),
    mrp DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. Fact: Product Snapshots (Time-Aware Telemetry Layer)
CREATE TABLE IF NOT EXISTS fact_product_snapshots (
    snapshot_id INT AUTO_INCREMENT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    snapshot_time DATETIME NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    mrp DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    discount_percentage DECIMAL(5, 2) DEFAULT 0.00,
    price_tier VARCHAR(20),
    inventory INT DEFAULT 0,
    is_sold_out TINYINT(1) DEFAULT 0,
    stock_status VARCHAR(50) NOT NULL,
    rating DECIMAL(3, 2) DEFAULT 0.00,
    product_position INT DEFAULT 0,
    widget_position INT DEFAULT 0,
    merchant_type VARCHAR(100) DEFAULT 'express',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES dim_products(product_id),
    INDEX idx_prod_snapshot (product_id, snapshot_time),
    INDEX idx_snapshot_time (snapshot_time),
    INDEX idx_stock_status (stock_status)
);

-- 4. Backward Compatibility Table / Current View: products
CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255),
    brand VARCHAR(100),
    category VARCHAR(100),
    subcategory VARCHAR(100),
    price DECIMAL(10, 2),
    mrp DECIMAL(10, 2),
    discount_percentage DECIMAL(5, 2),
    rating DECIMAL(3, 2),
    inventory INT,
    product_position INT,
    widget_position INT,
    variant VARCHAR(255),
    is_sold_out TINYINT(1),
    merchant_type VARCHAR(100),
    product_state VARCHAR(100),
    product_display_name VARCHAR(255),
    currency VARCHAR(10),
    ptype VARCHAR(100),
    quantity INT,
    state VARCHAR(50),
    scrape_timestamp DATETIME
);
