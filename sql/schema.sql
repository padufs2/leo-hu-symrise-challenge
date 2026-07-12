-- ============================================
-- Symrise Data Engineering Challenge - Schema
-- ============================================

-- Dimension table: products
CREATE TABLE IF NOT EXISTS products (
    product_id          TEXT PRIMARY KEY,
    product_name         TEXT,
    category             TEXT NOT NULL,
    subcategory          TEXT NOT NULL,
    launch_date          DATE,
    status               TEXT NOT NULL,
    num_ingredients      INTEGER,
    primary_ingredient   TEXT NOT NULL,
    region_developed     TEXT NOT NULL
);

-- Dimension table: ingredient costs
CREATE TABLE IF NOT EXISTS ingredient_costs (
    ingredient_id     TEXT PRIMARY KEY,
    ingredient_name   TEXT NOT NULL UNIQUE,
    cost_per_kg_usd   REAL NOT NULL CHECK (cost_per_kg_usd > 0),
    supplier          TEXT NOT NULL,
    last_updated      DATE,
    category          TEXT NOT NULL
);

-- Fact table: sales transactions
CREATE TABLE IF NOT EXISTS sales_transactions (
    transaction_id     TEXT PRIMARY KEY,
    product_id         TEXT NOT NULL,
    customer_id        TEXT,
    transaction_date   DATE NOT NULL,
    quantity_kg        REAL NOT NULL CHECK (quantity_kg > 0),
    unit_price_usd     REAL NOT NULL CHECK (unit_price_usd > 0),
    total_amount_usd   REAL NOT NULL CHECK (total_amount_usd > 0),
    region             TEXT NOT NULL,
    sales_channel      TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Fact table: customer feedback
-- Rating scale: 0-5 (deduced empirically, see README)
CREATE TABLE IF NOT EXISTS customer_feedback (
    feedback_id            TEXT PRIMARY KEY,
    product_id             TEXT NOT NULL,
    customer_id            TEXT,
    feedback_date          DATE NOT NULL,
    quality_rating         REAL CHECK (quality_rating BETWEEN 0 AND 5),
    performance_rating     REAL CHECK (performance_rating BETWEEN 0 AND 5),
    value_rating           REAL CHECK (value_rating BETWEEN 0 AND 5),
    overall_satisfaction   REAL CHECK (overall_satisfaction BETWEEN 0 AND 5),
    would_reorder          TEXT NOT NULL,
    comments               TEXT,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Logging table: rows rejected during cleaning
CREATE TABLE IF NOT EXISTS rejected_rows (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source_table    TEXT NOT NULL,
    original_id     TEXT,
    reason          TEXT NOT NULL,
    raw_data        TEXT,
    rejected_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Useful indexes for frequent joins (Q1-Q5)
CREATE INDEX IF NOT EXISTS idx_sales_product ON sales_transactions(product_id);
CREATE INDEX IF NOT EXISTS idx_sales_date ON sales_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_feedback_product ON customer_feedback(product_id);