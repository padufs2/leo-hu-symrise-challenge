import pandas as pd
from transform import transform_products

df = pd.read_csv("data/products.csv")
result = transform_products(df)

print(result[["product_id", "num_ingredients", "launch_date", "status"]])
