-- Q2: Region with the best average customer satisfaction
-- ASSUMPTION: customer_feedback has no region column, so it is inferred
-- by joining on (customer_id, product_id) to sales_transactions.
-- Verified: across 89 (customer_id, product_id) pairs, none has a
-- different region across transactions -> the "1 customer + 1 product =
-- 1 stable region" hypothesis is confirmed by the data.
--
-- FIX: one pair (C011, P011) has 2 distinct transactions (same LATAM
-- region both times). Without care, a direct JOIN would duplicate the
-- corresponding customer feedback. We therefore use SELECT DISTINCT on
-- the sales_transactions side to keep only one row (customer_id,
-- product_id, region) before joining.
SELECT 
    sr.region,
    ROUND(AVG(f.overall_satisfaction), 4) AS avg_satisfaction
FROM customer_feedback f
JOIN (
    SELECT DISTINCT customer_id, product_id, region
    FROM sales_transactions
) sr ON f.customer_id = sr.customer_id AND f.product_id = sr.product_id
GROUP BY sr.region
ORDER BY avg_satisfaction DESC;