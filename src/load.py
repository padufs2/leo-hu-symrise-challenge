import sqlite3
import logging

logger = logging.getLogger(__name__)


def create_schema(conn, schema_path):
    """Runs the schema.sql file to create the tables."""
    with open(schema_path, "r") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    logger.info(f"Schema created successfully from {schema_path}")


def load_all(clean_data: dict, config: dict):
    """Inserts the cleaned DataFrames into the SQLite database."""

    db_path = config["database"]["path"]
    schema_path = config["database"]["schema_path"]

    conn = sqlite3.connect(db_path)
    create_schema(conn, schema_path)

    table_names = {
        "products": "products",
        "sales_transactions": "sales_transactions",
        "customer_feedback": "customer_feedback",
        "ingredient_costs": "ingredient_costs",
    }

    for key, table_name in table_names.items():
        df = clean_data[key]
        df.to_sql(table_name, conn, if_exists="append", index=False)
        logger.info(f"{table_name}: {len(df)} rows inserted")

    conn.close()
    logger.info(f"Load complete, database: {db_path}")
