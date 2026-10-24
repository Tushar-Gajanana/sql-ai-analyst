# This is the only schema supplied to the model. Never send database rows.
TABLES = {"products", "sales"}
SCHEMA = """
PostgreSQL schema analytics:
analytics.products(product_id integer PRIMARY KEY, product_name text,
 category text, unit_price numeric)
analytics.sales(sale_id integer PRIMARY KEY, sale_date date,
 product_id integer REFERENCES analytics.products(product_id),
 region text, quantity integer, discount_pct numeric)
Revenue = quantity * unit_price * (1 - discount_pct / 100.0).
Join sales.product_id = products.product_id. Currency: EUR.
Synthetic data covers 2025-01-01 through 2025-06-29.
Use explicit dates for period comparisons. There are no costs, profit,
customer identities, inventory or forecasts in this database.
"""
