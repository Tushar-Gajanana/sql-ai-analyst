-- LOCAL DEMO ONLY. For cloud use docs/DEPLOYMENT.md and a fresh password.
CREATE ROLE analyst LOGIN PASSWORD 'local-demo-only'
 NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA analytics FROM PUBLIC;
GRANT USAGE ON SCHEMA analytics TO analyst;
GRANT SELECT ON analytics.products, analytics.sales TO analyst;
ALTER ROLE analyst SET default_transaction_read_only = on;
ALTER ROLE analyst SET statement_timeout = '5s';
ALTER ROLE analyst SET search_path = pg_catalog;
