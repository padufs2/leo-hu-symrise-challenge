-- Q3 : Relation entre num_ingredients et satisfaction client
-- MÉTHODE : on regroupe les produits par tranches de complexité (nombre
-- d'ingrédients), et on calcule la satisfaction moyenne par tranche pour
-- observer une éventuelle tendance.
-- NOTE : num_ingredients contient des NULL (valeurs invalides nettoyées
-- en amont dans transform_products.py, ex: -5 mis à null) — ces lignes
-- sont explicitement exclues ici avec WHERE p.num_ingredients IS NOT NULL,
-- plutôt que de compter sur le comportement implicite de AVG().
SELECT 
    CASE 
        WHEN p.num_ingredients BETWEEN 0 AND 5 THEN '0-5'
        WHEN p.num_ingredients BETWEEN 6 AND 10 THEN '6-10'
        WHEN p.num_ingredients BETWEEN 11 AND 15 THEN '11-15'
        WHEN p.num_ingredients BETWEEN 16 AND 20 THEN '16-20'
    END AS ingredient_range,
    COUNT(DISTINCT p.product_id) AS nb_products,
    ROUND(AVG(f.overall_satisfaction), 3) AS avg_satisfaction
FROM products p
JOIN customer_feedback f ON p.product_id = f.product_id
WHERE p.num_ingredients IS NOT NULL
GROUP BY ingredient_range
ORDER BY MIN(p.num_ingredients);