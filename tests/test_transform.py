"""
tests/test_transform.py
Tests unitaires pour les fonctions de transform.py.
Chaque test fabrique un petit DataFrame minimal et vérifie qu'une
règle de nettoyage précise est bien appliquée.
"""

import pandas as pd
from src.transform import (
    transform_products,
    transform_sales,
    transform_feedback,
    transform_ingredient_costs,
)

# ============================================
# transform_products
# ============================================


def test_transform_products_removes_duplicates():
    df = pd.DataFrame(
        {
            "product_id": ["P001", "P001", "P002"],
            "product_name": ["A", "A", "B"],
            "category": ["Flavor", "Flavor", "Fragrance"],
            "subcategory": ["Sweet", "Sweet", "Fresh"],
            "launch_date": ["2023-01-01", "2023-01-01", "2023-02-01"],
            "status": ["Active", "Active", "Active"],
            "num_ingredients": [5, 5, 8],
            "primary_ingredient": ["Sugar", "Sugar", "Lemon"],
            "region_developed": ["EMEA", "EMEA", "APAC"],
        }
    )

    result = transform_products(df)

    assert len(result) == 2
    assert result["product_id"].tolist() == ["P001", "P002"]


def test_transform_products_negative_num_ingredients_to_null():
    df = pd.DataFrame(
        {
            "product_id": ["P001", "P002"],
            "product_name": ["A", "B"],
            "category": ["Flavor", "Fragrance"],
            "subcategory": ["Sweet", "Fresh"],
            "launch_date": ["2023-01-01", "2023-02-01"],
            "status": ["Active", "Active"],
            "num_ingredients": [-5, 8],
            "primary_ingredient": ["Sugar", "Lemon"],
            "region_developed": ["EMEA", "APAC"],
        }
    )

    result = transform_products(df)

    # La ligne avec -5 doit devenir NULL, l'autre reste inchangée
    assert pd.isna(
        result.loc[result["product_id"] == "P001", "num_ingredients"].iloc[0]
    )
    assert result.loc[result["product_id"] == "P002", "num_ingredients"].iloc[0] == 8


def test_transform_products_status_standardized():
    df = pd.DataFrame(
        {
            "product_id": ["P001", "P002", "P003"],
            "product_name": ["A", "B", "C"],
            "category": ["Flavor", "Flavor", "Flavor"],
            "subcategory": ["Sweet", "Sweet", "Sweet"],
            "launch_date": ["2023-01-01", "2023-01-01", "2023-01-01"],
            "status": ["active", "ACTIVE", " Active "],
            "num_ingredients": [5, 5, 5],
            "primary_ingredient": ["Sugar", "Sugar", "Sugar"],
            "region_developed": ["EMEA", "EMEA", "EMEA"],
        }
    )

    result = transform_products(df)

    # Les 3 variantes de casse doivent devenir identiques
    assert result["status"].unique().tolist() == ["Active"]


def test_transform_products_mixed_date_formats():
    df = pd.DataFrame(
        {
            "product_id": ["P001", "P002"],
            "product_name": ["A", "B"],
            "category": ["Flavor", "Flavor"],
            "subcategory": ["Sweet", "Sweet"],
            "launch_date": ["2023-01-15", "15-12-2023"],  # formats différents
            "status": ["Active", "Active"],
            "num_ingredients": [5, 8],
            "primary_ingredient": ["Sugar", "Lemon"],
            "region_developed": ["EMEA", "APAC"],
        }
    )

    result = transform_products(df)

    # Les deux dates doivent être correctement parsées, aucune ne doit être NaT
    assert result["launch_date"].isna().sum() == 0


# ============================================
# transform_sales
# ============================================


def test_transform_sales_resolves_duplicate_transaction_id():
    df = pd.DataFrame(
        {
            "transaction_id": ["T001", "T001"],
            "product_id": ["P001", "P001"],
            "customer_id": ["C001", "C001"],
            "transaction_date": ["2024-01-01", "2024-05-01"],
            "quantity_kg": [10.0, 12.0],
            "unit_price_usd": [100.0, 100.0],
            "total_amount_usd": [1000.0, 1200.0],
            "region": ["EMEA", "EMEA"],
            "sales_channel": ["Direct", "Direct"],
        }
    )
    valid_ids = {"P001"}

    result = transform_sales(df, valid_product_ids=valid_ids)

    # Les 2 lignes doivent être conservées, avec des IDs désormais uniques
    assert len(result) == 2
    assert result["transaction_id"].is_unique


def test_transform_sales_recalculates_missing_total():
    df = pd.DataFrame(
        {
            "transaction_id": ["T001"],
            "product_id": ["P001"],
            "customer_id": ["C001"],
            "transaction_date": ["2024-01-01"],
            "quantity_kg": [10.0],
            "unit_price_usd": [50.0],
            "total_amount_usd": [None],
            "region": ["EMEA"],
            "sales_channel": ["Direct"],
        }
    )
    valid_ids = {"P001"}

    result = transform_sales(df, valid_product_ids=valid_ids)

    assert result["total_amount_usd"].iloc[0] == 500.0  # 10 * 50


def test_transform_sales_removes_orphan_product_id():
    df = pd.DataFrame(
        {
            "transaction_id": ["T001", "T002"],
            "product_id": ["P001", "P999"],  # P999 n'existe pas
            "customer_id": ["C001", "C002"],
            "transaction_date": ["2024-01-01", "2024-01-02"],
            "quantity_kg": [10.0, 5.0],
            "unit_price_usd": [50.0, 60.0],
            "total_amount_usd": [500.0, 300.0],
            "region": ["EMEA", "APAC"],
            "sales_channel": ["Direct", "Direct"],
        }
    )
    valid_ids = {"P001"}  # P999 volontairement absent

    result = transform_sales(df, valid_product_ids=valid_ids)

    assert len(result) == 1
    assert result["product_id"].tolist() == ["P001"]


# ============================================
# transform_feedback
# ============================================


def test_transform_feedback_ratings_out_of_range_to_null():
    df = pd.DataFrame(
        {
            "feedback_id": ["F001"],
            "product_id": ["P001"],
            "customer_id": ["C001"],
            "feedback_date": ["2024-01-01"],
            "quality_rating": [6.0],  # hors de [0, 5]
            "performance_rating": [4.0],
            "value_rating": [4.0],
            "overall_satisfaction": [4.0],
            "would_reorder": ["Yes"],
            "comments": ["test"],
        }
    )
    valid_ids = {"P001"}

    result = transform_feedback(df, valid_product_ids=valid_ids)

    assert pd.isna(result["quality_rating"].iloc[0])
    assert result["performance_rating"].iloc[0] == 4.0  # inchangée


def test_transform_feedback_standardizes_would_reorder():
    df = pd.DataFrame(
        {
            "feedback_id": ["F001", "F002", "F003"],
            "product_id": ["P001", "P001", "P001"],
            "customer_id": ["C001", "C002", "C003"],
            "feedback_date": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "quality_rating": [4.0, 4.0, 4.0],
            "performance_rating": [4.0, 4.0, 4.0],
            "value_rating": [4.0, 4.0, 4.0],
            "overall_satisfaction": [4.0, 4.0, 4.0],
            "would_reorder": ["yes", "YES", "Yes"],
            "comments": ["a", "b", "c"],
        }
    )
    valid_ids = {"P001"}

    result = transform_feedback(df, valid_product_ids=valid_ids)

    assert result["would_reorder"].unique().tolist() == ["Yes"]


def test_transform_feedback_removes_orphan_product_id():
    df = pd.DataFrame(
        {
            "feedback_id": ["F001", "F002"],
            "product_id": ["P001", "P999"],
            "customer_id": ["C001", "C002"],
            "feedback_date": ["2024-01-01", "2024-01-02"],
            "quality_rating": [4.0, 4.0],
            "performance_rating": [4.0, 4.0],
            "value_rating": [4.0, 4.0],
            "overall_satisfaction": [4.0, 4.0],
            "would_reorder": ["Yes", "Yes"],
            "comments": ["a", "b"],
        }
    )
    valid_ids = {"P001"}

    result = transform_feedback(df, valid_product_ids=valid_ids)

    assert len(result) == 1
    assert result["product_id"].tolist() == ["P001"]


# ============================================
# transform_ingredient_costs
# ============================================


def test_transform_ingredient_costs_removes_true_duplicate():
    df = pd.DataFrame(
        {
            "ingredient_id": ["I001", "I018"],
            "ingredient_name": ["Lemon Oil", "Lemon Oil"],
            "cost_per_kg_usd": [45.5, 45.5],
            "supplier": ["CitrusSupply Co", "CitrusSupply Co"],
            "last_updated": ["2024-08-01", "2024-08-01"],
            "category": ["Essential Oil", "Essential Oil"],
        }
    )

    result = transform_ingredient_costs(df)

    assert len(result) == 1
    assert result["ingredient_id"].tolist() == ["I001"]


def test_transform_ingredient_costs_keeps_different_ingredients():
    df = pd.DataFrame(
        {
            "ingredient_id": ["I001", "I002"],
            "ingredient_name": ["Lemon Oil", "Vanilla Extract"],
            "cost_per_kg_usd": [45.5, 120.0],
            "supplier": ["CitrusSupply Co", "VanillaPro Ltd"],
            "last_updated": ["2024-08-01", "2024-08-01"],
            "category": ["Essential Oil", "Extract"],
        }
    )

    result = transform_ingredient_costs(df)

    assert len(result) == 2
