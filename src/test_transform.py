import pandas as pd
from transform import transform_products, transform_feedback

# On a besoin des product_id valides, comme pour sales
products_df = pd.read_csv("data/products.csv")
clean_products = transform_products(products_df)
valid_ids = set(clean_products["product_id"])

# On charge et nettoie feedback
feedback_df = pd.read_csv("data/customer_feedback.csv")
result = transform_feedback(feedback_df, valid_product_ids=valid_ids)

# Maintenant "result" existe, et contient le DataFrame nettoyé

print(result[result["feedback_id"] == "F034"])
