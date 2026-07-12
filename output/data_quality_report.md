# Data Quality Report

*Generated from running the ETL pipeline (`main.py`) on the 4 source files.
Full, timestamped details are available in `output/pipeline.log`.*

---

## Summary

| Table | Rows in | Rows out | Rows dropped |
|---|---|---|---|
| products | 41 | 40 | 1 |
| sales_transactions | 90 | 89 | 1 |
| customer_feedback | 55 | 54 | 1 |
| ingredient_costs | 42 | 41 | 1 |

---

## products.csv

| Issue detected | Rule applied | Decision |
|---|---|---|
| 1 exact duplicate on `product_id` | Detection of any `product_id` appearing more than once | Duplicate removed (keeps the 1st occurrence) |
| `num_ingredients = -5` (P033) | Any negative value is invalid | Set to `NULL` rather than guessing the true value (e.g. `abs(-5)`) — no evidence of the correct value exists |
| `num_ingredients = "NULL"` (literal text, P024) | Converted to a real `NaN` before any numeric computation | Converted to clean `NULL` |
| `product_name` missing (P029) | Missing value kept, no row dropped | Row kept, logged for traceability |
| `launch_date` — mixed format (P040: `15-12-2023` instead of `YYYY-MM-DD`) | Parsing with `format="mixed"` so valid dates aren't lost due to a different format | Date correctly recovered (`2023-12-15`) instead of being lost |
| `launch_date` genuinely missing (P019) | Originally missing value, distinct from the format case above | Row kept, logged |
| `status`: inconsistent case (`active`, `Active`, `ACTIVE`) | Standardized via `.str.strip().str.title()` | Normalized to `Active` / `Discontinued` |

---

## sales_transactions.csv

| Issue detected | Rule applied | Decision |
|---|---|---|
| `transaction_id` "T011" duplicated (2 genuinely distinct transactions, different dates and quantities) | Not a duplicate to drop — 2 real transactions that got the same ID by mistake | Automatically renamed the 2nd occurrence (`T011` → `T011_2`) to make IDs unique, without losing data |
| `total_amount_usd` missing (T024) | Recomputed via `quantity_kg × unit_price_usd` | Value recomputed (7700.0) instead of dropping the row |
| `customer_id` missing (1 row) | Missing value kept | Row kept, logged |
| Orphan reference: `product_id = P999` (T059) does not exist in any `products` row | Any row referencing a non-existent product is removed (required to satisfy the schema's `FOREIGN KEY` constraint) | Row removed |

**Documented assumption:** `total_amount_usd = quantity_kg × unit_price_usd`, with no taxes or discounts. Used only to recompute missing values, never to overwrite values already present (in case a legitimate commercial discount exists).

---

## customer_feedback.csv

| Issue detected | Rule applied | Decision |
|---|---|---|
| `quality_rating = 6.0` (F052), outside the expected [0, 5] scale | Validation applied uniformly to all 4 rating columns (`quality_rating`, `performance_rating`, `value_rating`, `overall_satisfaction`), not just the column where the issue was manually spotted | Set to `NULL` |
| `overall_satisfaction = 5.2` (F052) | This column is derived (≈ average of the other 3 ratings) — its invalid value is a direct consequence of the `quality_rating = 6.0` on the same row, not an independent error | Set to `NULL` (rather than recomputed, to avoid fabricating a value from already-invalid data) |
| `quality_rating` missing (F024, and F052 after cleaning) | Missing value kept | Row kept, logged |
| `customer_id` missing (F053) | Missing value kept | Row kept, logged |
| `would_reorder`: inconsistent case (`yes`, `Yes`, `YES`) | Standardized via `.str.strip().str.title()` | Normalized to `Yes` / `No` / `Maybe` |
| Orphan reference: `product_id = P999` (F034) | Same rule as for `sales_transactions` | Row removed |

**Rating scale (0-5):** not documented in the source files. Deduced empirically: `performance_rating` and `value_rating` cap exactly at 5.0 without ever exceeding it, and 0-5 is the standard customer satisfaction scale. This assumption is applied consistently between the Python code (validation) and the SQL schema (`CHECK` constraint).

---

## ingredient_costs.csv

| Issue detected | Rule applied | Decision |
|---|---|---|
| `Lemon Oil` duplicate (I001 / I018), identical on name, cost and supplier, only the ID differs | Two rows with the same `ingredient_name`, `cost_per_kg_usd` and `supplier` are considered a true duplicate | Duplicate removed (keeps `I001`) |

---

## General methodological notes

- **General principle applied throughout:** prefer an honest `NULL` value over a guessed/fabricated one, when the true value cannot be recovered with certainty.
- **All cleaning rules are generic**, not targeted fixes on specific rows: they would automatically detect and fix the same type of issue on any future dataset with the same characteristics.
- **Fragile text join:** the relationship between `products.primary_ingredient` and `ingredient_costs.ingredient_name` is done on text, not an identifier — verified as functional on this dataset (no orphan values), but more sensitive to typos/case than a real foreign key would be.
