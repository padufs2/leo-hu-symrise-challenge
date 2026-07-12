-- ============================================
-- Q1 : Top 5 catégories de produits par revenu
-- ============================================

-- NIVEAU 1 : par category (Flavor / Fragrance)
-- Note : il n'existe que 2 valeurs uniques dans products.category,
-- donc un "top 5" n'a pas vraiment de sens à ce niveau de granularité
-- (le LIMIT 5 ne changera rien, on aura toujours 2 lignes max).
SELECT 
    p.category,
    SUM(s.total_amount_usd) AS total_revenue
FROM sales_transactions s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY total_revenue DESC
LIMIT 5;

-- NIVEAU 2 : par subcategory (Fresh, Sweet, Aquatic, Fruity, Oriental, ...)
-- DÉCISION : products.subcategory a 13 valeurs uniques, ce qui permet un
-- vrai "top 5" pertinent pour identifier les segments les plus rentables.
-- On considère ce niveau plus actionnable pour répondre à l'intention
-- business de la question, même si la question mentionne "category".
SELECT 
    p.subcategory,
    SUM(s.total_amount_usd) AS total_revenue
FROM sales_transactions s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.subcategory
ORDER BY total_revenue DESC
LIMIT 5;