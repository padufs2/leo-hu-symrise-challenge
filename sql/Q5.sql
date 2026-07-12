-- Q5 : Marge par catégorie de produit (Revenue - Coûts ingrédients)
-- ASSOMPTION IMPORTANTE : le coût est calculé uniquement à partir de
-- l'ingrédient PRINCIPAL (primary_ingredient), pas de la formulation
-- complète du produit. Une vraie marge nécessiterait une table de
-- composition multi-ingrédients par produit, qui n'existe pas dans
-- ces données. Ce calcul est donc une approximation, pas une marge réelle.
--
-- LIMITE TECHNIQUE : la jointure products <-> ingredient_costs se fait
-- sur un TEXTE (primary_ingredient = ingredient_name), pas un vrai ID
-- -> plus fragile qu'une FOREIGN KEY (sensible à la casse, aux espaces,
-- aux fautes de frappe). À surveiller si de nouvelles données arrivent.
SELECT
    p.category,
    SUM(s.total_amount_usd) AS total_revenue,
    SUM(s.quantity_kg * ic.cost_per_kg_usd) AS total_ingredient_cost,
    ROUND(
        SUM(s.total_amount_usd) - SUM(s.quantity_kg * ic.cost_per_kg_usd),
        2
    ) AS estimated_margin
FROM sales_transactions s
JOIN products p ON s.product_id = p.product_id
JOIN ingredient_costs ic ON p.primary_ingredient = ic.ingredient_name
GROUP BY p.category
ORDER BY estimated_margin DESC;