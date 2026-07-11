import pandas as pd
from transform import (
    transform_products,
    transform_feedback,
    transform_ingredient_costs,
    transform_sales,
)


def transform_all(raw: dict) -> dict:
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
