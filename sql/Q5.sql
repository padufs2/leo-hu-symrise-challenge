-- Q5: Margin by product category (Revenue - Ingredient costs)
-- IMPORTANT ASSUMPTION: the cost is computed solely from the PRIMARY
-- ingredient (primary_ingredient), not the product's full formulation.
-- A true margin would require a multi-ingredient composition table per
-- product, which does not exist in this data. This calculation is
-- therefore an approximation, not a real margin.
--
-- TECHNICAL LIMITATION: the products <-> ingredient_costs join is done
-- on TEXT (primary_ingredient = ingredient_name), not a real ID
-- -> more fragile than a FOREIGN KEY (sensitive to case, whitespace,
-- typos). Worth monitoring if new data comes in.
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