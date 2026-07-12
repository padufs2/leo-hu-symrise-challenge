import pandas as pd
import logging

logger = logging.getLogger(__name__)


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    # Work on a copy so the original DataFrame is never modified
    df = df.copy()
    before = len(df)

    # RULE: a product_id must never appear more than once.
    # keep="first" keeps the first occurrence found, drops the rest.
    df = df.drop_duplicates(subset="product_id", keep="first")
    dropped = before - len(df)
    if dropped:
        logger.info(f"products: {dropped} duplicate(s) removed on product_id")

    # STANDARDIZATION: normalizes case and strips stray whitespace
    # (e.g. "active ", "ACTIVE" -> "Active") so identical statuses
    # are properly recognized as such.
    df["status"] = df["status"].str.strip().str.title()

    # CLEANING num_ingredients (in 3 steps):
    # 1) "NULL" is a literal text string in the CSV, not a real NaN
    #    -> convert it to a proper pandas missing value
    df["num_ingredients"] = df["num_ingredients"].replace("NULL", pd.NA)

    # 2) Once "NULL" is removed, force numeric conversion.
    #    errors="coerce" turns anything that isn't a valid number into NaN,
    #    instead of crashing the program.
    df["num_ingredients"] = pd.to_numeric(df["num_ingredients"], errors="coerce")

    # 3) RULE: a number of ingredients can never be negative.
    # DECISION: set to null rather than guess the true value
    # (e.g. abs(-5) -> 5 would be an unverifiable assumption).
    mask = df["num_ingredients"] < 0
    nb_negative = mask.sum()
    if nb_negative:
        logger.warning(
            f"products: {nb_negative} negative value(s) in num_ingredients, set to null"
        )
        df.loc[mask, "num_ingredients"] = pd.NA

    logger.info(f"products: {before} rows before, {len(df)} rows after")

    # DECISION: missing product_name -> keep the row (the product still
    # exists) but log which product_id are affected for traceability.
    missing_name = df["product_name"].isna()
    if missing_name.any():
        ids = df.loc[missing_name, "product_id"].tolist()
        logger.warning(f"products: product_name missing for {ids}")

    # DATE PARSING: format="mixed" handles the case where some rows use a
    # different format than the rest (e.g. P040 was in "15-12-2023" instead
    # of "2023-12-15"). Without this, those valid dates would be lost
    # (-> NaT) even though they are recoverable.
    df["launch_date"] = pd.to_datetime(
        df["launch_date"], format="mixed", dayfirst=False, errors="coerce"
    )

    # launch_date values still NaT after this smart parsing are TRUE
    # originally missing values (e.g. P019), not format errors.
    missing_date = df["launch_date"].isna()
    if missing_date.any():
        ids = df.loc[missing_date, "product_id"].tolist()
        logger.warning(f"products: launch_date missing or invalid for {ids}")

    return df


def transform_sales(df: pd.DataFrame, valid_product_ids: set) -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    # DATE PARSING: as with products, handle mixed formats so valid dates
    # written differently aren't lost.
    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], format="mixed", errors="coerce"
    )

    missing_dates = df["transaction_date"].isna()
    if missing_dates.any():
        ids = df.loc[missing_dates, "transaction_id"].tolist()
        logger.warning(f"sales_transactions: invalid transaction_date for {ids}")

    # RULE: a transaction_id must be unique. If a duplicate is found, it is
    # probably 2 genuinely different transactions that ended up with the
    # same ID by mistake (not a duplicate to drop) — we make them unique
    # instead of losing one of them.
    dup_mask = df.duplicated(subset="transaction_id", keep=False)

    if dup_mask.any():
        dup_ids = df.loc[dup_mask, "transaction_id"].unique().tolist()
        logger.warning(
            f"sales_transactions: duplicate transaction_id(s) detected: {dup_ids}"
        )

        counters = {}
        new_ids = []
        for tid in df["transaction_id"]:
            counters[tid] = counters.get(tid, 0) + 1
            if counters[tid] == 1:
                new_ids.append(tid)
            else:
                new_ids.append(f"{tid}_{counters[tid]}")

        df["transaction_id"] = new_ids

    # ASSUMPTION: total_amount_usd = quantity_kg * unit_price_usd, with no
    # taxes or discounts. This formula is used only to recompute missing
    # values, never to overwrite values that are already present.
    missing_total = df["total_amount_usd"].isna()

    if missing_total.any():
        ids = df.loc[missing_total, "transaction_id"].tolist()
        logger.warning(
            f"sales_transactions: total_amount_usd missing for {ids}, recomputed"
        )

        df.loc[missing_total, "total_amount_usd"] = (
            df.loc[missing_total, "quantity_kg"]
            * df.loc[missing_total, "unit_price_usd"]
        )

    # RULE: any transaction whose product_id does not exist in the (cleaned)
    # products table is an orphan reference — it cannot be kept because it
    # would violate the FOREIGN KEY constraint at load time.
    orphan_mask = ~df["product_id"].isin(valid_product_ids)

    if orphan_mask.any():
        orphan_rows = df.loc[orphan_mask, ["transaction_id", "product_id"]]
        logger.warning(
            f"sales_transactions: removing {orphan_mask.sum()} row(s) "
            f"with invalid product_id:\n{orphan_rows.to_string(index=False)}"
        )
        df = df[~orphan_mask]

    logger.info(f"sales_transactions: {before} rows before, {len(df)} rows after")
    return df


def transform_feedback(df: pd.DataFrame, valid_product_ids: set) -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    # STANDARDIZATION: normalizes case and strips stray whitespace
    # (e.g. "Yes ", "yes" -> "Yes") so identical statuses
    # are properly recognized as such.
    df["would_reorder"] = df["would_reorder"].str.strip().str.title()

    # RULE: any rating outside [0, 5] is invalid -> set to null.
    # Applied identically to all 4 rating columns, rather than only the
    # column where the issue was manually spotted — this also catches any
    # undetected out-of-range values.
    RATING_MIN, RATING_MAX = 0, 5
    RATING_COLUMNS = [
        "quality_rating",
        "performance_rating",
        "value_rating",
        "overall_satisfaction",
    ]

    for col in RATING_COLUMNS:
        out_of_range = (df[col] < RATING_MIN) | (df[col] > RATING_MAX)
        if out_of_range.any():
            ids = df.loc[out_of_range, "feedback_id"].tolist()
            logger.warning(
                f"customer_feedback: {col} out of [{RATING_MIN}, {RATING_MAX}] for {ids}"
            )
            df.loc[out_of_range, col] = pd.NA

    # DECISION: missing quality_rating -> keep the row, log it.
    missing_quality = df["quality_rating"].isna()
    if missing_quality.any():
        ids = df.loc[missing_quality, "feedback_id"].tolist()
        logger.warning(f"customer_feedback: quality_rating missing for {ids}")

    # DECISION: missing customer_id -> keep the row, log it.
    missing_cust = df["customer_id"].isna() | (
        df["customer_id"].astype(str).str.strip() == ""
    )
    if missing_cust.any():
        ids = df.loc[missing_cust, "feedback_id"].tolist()
        logger.warning(f"customer_feedback: customer_id missing for {ids}")

    # DATE PARSING: as with products, handle mixed formats so valid dates
    # written differently aren't lost.
    df["feedback_date"] = pd.to_datetime(
        df["feedback_date"], format="mixed", errors="coerce"
    )

    # RULE: any feedback whose product_id does not exist in the (cleaned)
    # products table is an orphan reference — it cannot be kept because it
    # would violate the FOREIGN KEY constraint at load time.
    orphan_mask = ~df["product_id"].isin(valid_product_ids)
    if orphan_mask.any():
        orphan_rows = df.loc[orphan_mask, ["feedback_id", "product_id"]]
        logger.warning(
            f"customer_feedback: removing {orphan_mask.sum()} row(s) "
            f"with invalid product_id:\n{orphan_rows.to_string(index=False)}"
        )
        df = df[~orphan_mask]

    logger.info(f"customer_feedback: {before} rows before, {len(df)} rows after")
    return df


def transform_ingredient_costs(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)
    df = df.drop_duplicates(
        subset=["ingredient_name", "cost_per_kg_usd", "supplier"], keep="first"
    )

    # DATE PARSING: as with products, handle mixed formats so valid dates
    # written differently aren't lost.
    df["last_updated"] = pd.to_datetime(
        df["last_updated"], format="mixed", errors="coerce"
    )
    logger.info(f"ingredient_costs: {before} rows before, {len(df)} rows after")

    return df


def transform_all(raw: dict) -> dict:
    """Run all transforms in dependency order (products first, since
    sales and feedback need its product_id list for orphan checks)."""
    products = transform_products(raw["products"])
    valid_product_ids = set(products["product_id"])

    sales = transform_sales(raw["sales_transactions"], valid_product_ids)
    feedback = transform_feedback(raw["customer_feedback"], valid_product_ids)
    costs = transform_ingredient_costs(raw["ingredient_costs"])

    return {
        "products": products,
        "sales_transactions": sales,
        "customer_feedback": feedback,
        "ingredient_costs": costs,
    }
