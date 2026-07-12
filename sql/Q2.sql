-- Q2 : Région avec la meilleure satisfaction client moyenne
-- ASSOMPTION : customer_feedback n'a pas de colonne region, donc on
-- la déduit en joignant sur (customer_id, product_id) à sales_transactions.
-- Vérifié : sur 89 paires (customer_id, product_id), aucune n'a de région
-- différente selon la transaction -> hypothèse "1 client + 1 produit =
-- 1 région stable" confirmée par les données.
--
-- CORRECTION : une paire (C011, P011) a 2 transactions distinctes (même
-- région LATAM les 2 fois). Sans précaution, un JOIN direct dupliquerait
-- l'avis client correspondant. On utilise donc SELECT DISTINCT côté
-- sales_transactions pour ne garder qu'une seule ligne (customer_id,
-- product_id, region) avant de joindre.
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