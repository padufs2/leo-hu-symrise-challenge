-- Q4 : Produits avec tendance de vente en déclin (Q2 vs Q3 2024)
-- NOTE : les données s'arrêtent au 20 août 2024, donc Q3 (juil-sept) est
-- INCOMPLET (il manque tout septembre). La comparaison Q2 (complet) vs
-- Q3 (partiel) est donc une comparaison volume-à-volume imparfaite —
-- un produit peut sembler "en déclin" simplement parce que Q3 a moins
-- de jours de données, pas une vraie baisse de demande.
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