-- Q4: Products with a declining sales trend (Q2 vs Q3 2024)
-- NOTE: the data stops on August 20, 2024, so Q3 (Jul-Sep) is
-- INCOMPLETE (all of September is missing). The Q2 (complete) vs
-- Q3 (partial) comparison is therefore an imperfect volume-to-volume
-- comparison — a product may appear to be "declining" simply because
-- Q3 has fewer days of data, not a genuine drop in demand.
WITH quarterly_revenue AS (
    SELECT
        product_id,
        CASE
            WHEN transaction_date BETWEEN '2024-04-01' AND '2024-06-30' THEN 'Q2'
            WHEN transaction_date BETWEEN '2024-07-01' AND '2024-09-30' THEN 'Q3'
        END AS quarter,
        SUM(total_amount_usd) AS revenue
    FROM sales_transactions
    WHERE transaction_date BETWEEN '2024-04-01' AND '2024-09-30'
    GROUP BY product_id, quarter
)
SELECT
    q2.product_id,
    q2.revenue AS q2_revenue,
    q3.revenue AS q3_revenue,
    ROUND(((q3.revenue - q2.revenue) * 100.0 / q2.revenue), 1) AS pct_change
FROM quarterly_revenue q2
JOIN quarterly_revenue q3 ON q2.product_id = q3.product_id
WHERE q2.quarter = 'Q2' AND q3.quarter = 'Q3'
    AND q3.revenue < q2.revenue
ORDER BY pct_change ASC;