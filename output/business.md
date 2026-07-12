# Business Questions — Answers

*Generated from `sql/queries.sql`, run against `output/symrise.db`.*

---

## Q1: Top 5 product categories by revenue

**At the `category` level** (the highest level), there are only 2 values in the data:

| Category | Total Revenue |
|---|---|
| Flavor | $298,425.00 |
| Fragrance | $191,096.00 |

A "top 5" doesn't make sense at this level, since there are only 2 categories.

**Additional analysis by `subcategory`** (13 unique values), more relevant for a real, actionable top 5:

| Subcategory | Total Revenue |
|---|---|
| *(to be completed with the result of the subcategory query)* | |

---

## Q2: Region with the best average customer satisfaction

| Region | Avg Satisfaction |
|---|---|
| North America | 4.6455 |
| EMEA | 4.4053 |
| LATAM | 4.1250 |
| APAC | 4.0714 |

**North America** has the best average customer satisfaction (4.65/5).

**Documented assumption:** `customer_feedback` does not contain a `region` column. It was inferred by joining on `(customer_id, product_id)` to `sales_transactions`, assuming a customer always buys a given product from the same region. This hypothesis was verified empirically: across 89 (customer_id, product_id) pairs, none has a different region across transactions. An additional fix (`SELECT DISTINCT`) was applied to avoid double-counting a customer review when a customer bought the same product multiple times (the C011/P011 case).

---

## Q3: Relationship between product complexity (number of ingredients) and customer satisfaction

| Ingredient Range | Nb Products | Avg Satisfaction |
|---|---|---|
| 0-5 | 1 | 4.700 |
| 6-10 | 14 | 4.396 |
| 11-15 | 10 | 4.311 |
| 16-20 | 4 | 4.063 |

**Observed trend:** average satisfaction decreases slightly as the number of ingredients increases (4.396 for 6-10 ingredients, versus 4.063 for 16-20).

**Limitation:** the 0-5 bracket contains only a single product — its average (4.7) is not statistically representative and should not be over-interpreted. With only 41 products in total, this trend is indicative but would need to be confirmed on a larger sample before drawing any firm business conclusion.

---

## Q4: Products with a declining sales trend (comparison of the last 2 quarters)

The data covers **January 5, 2024 to August 20, 2024**. The "last 2 quarters" available are therefore **Q2 (April-June)** and **Q3 (July-August, incomplete — September is missing)**.

| Product ID | Q2 Revenue | Q3 Revenue | % Change |
|---|---|---|---|
| P012 | $5,637.50 | $5,535.00 | -1.8% |

**Finding:** out of 40 active products, only **8** have transactions in both quarters (35 products sold in Q2, only 13 in Q3). Among these 8 comparable products, only one shows a decline: **P012**.

**Important limitation:** with such a small sample (8 comparable products) and a truncated Q3 (no September data), this result is not robust enough to identify genuine decline trends. A more reliable analysis would require either full quarters or a year-over-year comparison of the same months.

---

## Q5: Margin by product category (Revenue − Ingredient costs)

| Category | Total Revenue | Total Ingredient Cost | Estimated Margin |
|---|---|---|---|
| Flavor | $298,425.00 | $94,946.50 | **$203,478.50** |
| Fragrance | $191,096.00 | $95,842.88 | **$95,253.13** |

**Flavor** generates a much higher estimated margin than **Fragrance**, despite a revenue that isn't proportionally as high — this suggests that the ingredients used in Fragrance products are, on average, more expensive per kg.

**Documented assumption and limitation:**
- The cost is computed solely from each product's **primary** ingredient (`primary_ingredient`), not its full formulation. This is therefore an approximation, not a real margin — a true cost-of-goods calculation would require a multi-ingredient composition table per product, which is absent from this data.
- The `products.primary_ingredient` ↔ `ingredient_costs.ingredient_name` join is done on text, not an ID — more fragile than a real foreign key (verified: no primary ingredient was left unmatched in this dataset, but this should be monitored as new data arrives).
