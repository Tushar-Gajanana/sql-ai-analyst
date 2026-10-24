-- Synthetic demo data only. This script is transactional and rerunnable.
BEGIN;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE TABLE IF NOT EXISTS analytics.products (
 product_id integer PRIMARY KEY, product_name text NOT NULL,
 category text NOT NULL, unit_price numeric(10,2) NOT NULL CHECK(unit_price >= 0));
CREATE TABLE IF NOT EXISTS analytics.sales (
 sale_id integer PRIMARY KEY, sale_date date NOT NULL,
 product_id integer NOT NULL REFERENCES analytics.products,
 region text NOT NULL, quantity integer NOT NULL CHECK(quantity > 0),
 discount_pct numeric(5,2) NOT NULL CHECK(discount_pct BETWEEN 0 AND 100));
INSERT INTO analytics.products VALUES
 (1,'Notebook','Stationery',4.50),(2,'Pen set','Stationery',7.00),
 (3,'Desk lamp','Home',29.00),(4,'Storage box','Home',12.00),
 (5,'Headphones','Electronics',59.00),(6,'Keyboard','Electronics',45.00)
ON CONFLICT DO NOTHING;
INSERT INTO analytics.sales
SELECT n, DATE '2025-01-01' + ((n-1) % 180), 1 + ((n-1) % 6),
 (ARRAY['North','South','East','West'])[1 + ((n/6) % 4)],
 1 + ((n*7) % 12), CASE WHEN n % 5 = 0 THEN 15 ELSE 0 END
FROM generate_series(1,1080) AS n ON CONFLICT DO NOTHING;
CREATE INDEX IF NOT EXISTS sales_date_idx ON analytics.sales(sale_date);
COMMIT;
