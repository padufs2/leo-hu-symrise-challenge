-- ============================================
-- Q1: Top 5 product categories by revenue
-- ============================================

-- LEVEL 1: by category (Flavor / Fragrance)
-- Note: there are only 2 unique values in products.category,
-- so a "top 5" doesn't really make sense at this granularity
-- (the LIMIT 5 won't change anything, we'll always get at most 2 rows).
SELECT
    p.category,
    SUM(s.total_amount_usd) AS total_revenue
FROM sales_transactions s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
LIMIT 5;

-- LEVEL 2: by subcategory (Fresh, Sweet, Aquatic, Fruity, Oriental, ...)
-- DECISION: products.subcategory has 13 unique values, which allows for a
-- real, meaningful "top 5" to identify the most profitable segments.
-- This level is considered more actionable for answering the business
-- intent of the question, even though the question mentions "category".
SELECT
    p.subcategory,
    SUM(s.total_amount_usd) AS total_revenue
FROM sales_transactions s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.subcategory
ORDER BY total_revenue DESC
LIMIT 5;