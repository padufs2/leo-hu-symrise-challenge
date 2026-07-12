# Symrise Data Engineering Challenge — Léo Hu

Solution to the Symrise data engineering challenge: an ETL (Extract, Transform, Load) pipeline
in Python + SQLite, with answers to the 5 business questions.

---

## Project structure
```
leo-hu-symrise-challenge/
├── README.md
├── requirements.txt
├── config.yaml
├── data/                       # Source CSVs (not versioned if large)
├── src/
│   ├── config.py               # Loads config.yaml
│   ├── extract.py               # Reads the 4 CSVs
│   ├── transform.py             # Cleaning and validation
│   ├── load.py                  # Schema creation + SQLite insertion
│   └── main.py                  # Orchestrates the full pipeline
├── sql/
│   ├── schema.sql                # Table definitions
│   └── queries.sql               # The 5 business queries
└── output/
    ├── symrise.db                 # Final database
    ├── pipeline.log                # Execution logs
    ├── data_quality_report.md      # Issues detected and fixed
    └── business_answers.md         # Answers to the 5 questions
```

## Setup

**Prerequisites:** Python 3.12+

```bash
# Create and activate the virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## How to run the pipeline

```bash
mkdir -p output
uv run main.py
```

The pipeline will, in order:
1. Load `config.yaml`
2. Read the 4 CSVs from `data/`
3. Clean and validate the data (see `output/data_quality_report.md`)
4. Create the SQLite schema (`sql/schema.sql`) and insert the clean data
5. Generate `output/symrise.db` and `output/pipeline.log`

## How to run the business queries

```bash
sqlite3 output/symrise.db
.read sql/queries.sql
```

Or directly, for a specific query:
```bash
sqlite3 output/symrise.db < sql/queries.sql
```

Commented results are available in `output/business_answers.md`.

---

## Design decisions & assumptions

### Architecture
- **Python + pandas** for extraction and cleaning, **SQLite** for storage and analysis. This choice is sized to the actual data volume (a few dozen to a few hundred rows per table) — a tool like Databricks or dbt would be overkill here, but would become relevant if the volume grew significantly (see the "Improvement ideas" section).
- **Simplified star schema**: `products` and `ingredient_costs` as dimension tables, `sales_transactions` and `customer_feedback` as fact tables.
- **Centralized configuration** (`config.yaml`): file paths and validation thresholds are never hardcoded in the Python code.

### General cleaning principle
For any invalid value whose true value cannot be recovered with certainty, the data is set to `NULL` rather than guessed or fabricated. The full detail of the issues detected and the decisions made is in `output/data_quality_report.md`.

All cleaning rules are **generic** (based on conditions, not on specific row identifiers) — they would automatically apply to any new dataset presenting the same types of issues.

### Customer rating scale (0-5)
Not documented in the source files. Deduced empirically from the fact that `performance_rating` and `value_rating` cap exactly at 5.0 without ever exceeding it. Applied consistently between Python validation (`transform.py`) and the SQL schema's `CHECK` constraints.

### Text join between products and ingredient_costs
`products.primary_ingredient` (text) is linked to `ingredient_costs.ingredient_name` (text), due to the lack of a common identifier in the source data. Verified as functional on this dataset (no orphan values), but more fragile than a real foreign key — sensitive to case and typos.

### Margin calculation (Q5)
Based solely on the **primary** ingredient of each product, due to the lack of a multi-ingredient composition table in the data. This is therefore a margin approximation, not a full cost of goods sold.

---

## Known limitations and assumptions to verify

- **Q2 (satisfaction by region)**: `customer_feedback` has no region column; it is inferred via `(customer_id, product_id)`, assuming a customer always buys a given product from the same region — an assumption verified on this dataset but not guaranteed in general.
- **Q3 (complexity vs. satisfaction)**: the 0-5 ingredient bracket contains only a single product, making its average not very representative.
- **Q4 (quarterly decline)**: the data stops on August 20, 2024, making Q3 incomplete. Only 8 out of 40 products have data in both compared quarters.

The full detail of each limitation is documented directly as comments in `sql/queries.sql` and in `output/business_answers.md`.

---

## Improvement ideas (if the project were to grow)

- **Multi-ingredient composition table** per product, for an accurate margin calculation (instead of the primary ingredient alone).
- **Ingredient ID instead of name** as the join key between `products` and `ingredient_costs`, to eliminate the text-based fragility.
- **`rejected_rows` table** (already present in the schema): currently unused by the pipeline (rejections are tracked via logs), but could be populated for SQL-queryable traceability.
- At larger scale (millions of rows, multiple sources, real time), a stack like dbt + a cloud warehouse (Snowflake/BigQuery) would provide the dependency management and built-in tests that this Python + SQLite pipeline doesn't offer natively.

---

## Author

Léo Hu