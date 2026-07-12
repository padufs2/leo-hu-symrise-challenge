-- Q3: Relationship between num_ingredients and customer satisfaction
-- METHOD: products are grouped into complexity brackets (number of
-- ingredients), and average satisfaction is computed per bracket to
-- observe a possible trend.
-- NOTE: num_ingredients contains NULLs (invalid values cleaned upstream
-- in transform_products.py, e.g. -5 set to null) — these rows are
-- explicitly excluded here with WHERE p.num_ingredients IS NOT NULL,
-- rather than relying on the implicit behavior of AVG().
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