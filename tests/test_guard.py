import pytest
from analyst.guard import UnsafeSQL, validate_sql


@pytest.mark.parametrize("sql", [
    "SELECT COUNT(*) FROM analytics.sales",
    "SELECT p.category, SUM(s.quantity*p.unit_price) FROM analytics.sales s JOIN analytics.products p USING(product_id) GROUP BY p.category",
    "SELECT DATE_TRUNC('month', sale_date), SUM(quantity) FROM analytics.sales GROUP BY 1",
    "SELECT ROUND(AVG(quantity)::numeric, 2) FROM analytics.sales",
    "SELECT * FROM analytics.sales LIMIT 999999",
])
def test_accepted(sql):
    assert validate_sql(sql).endswith("LIMIT 201")


@pytest.mark.parametrize("sql", [
    "DELETE FROM analytics.sales", "SELECT 1; DROP TABLE analytics.sales",
    "SELECT * FROM public.sales", "SELECT * FROM pg_catalog.pg_roles",
    "SELECT pg_sleep(10) FROM analytics.sales",
    "SELECT set_config('search_path','public',false) FROM analytics.sales",
    "SELECT * INTO temp copied FROM analytics.sales",
    "SELECT * FROM analytics.sales FOR UPDATE",
    "WITH x AS (DELETE FROM analytics.sales RETURNING *) SELECT * FROM x",
    "WITH x AS (SELECT * FROM analytics.sales) SELECT * FROM x",
    "SELECT * FROM generate_series(1,999999)",
    "COPY analytics.sales TO '/tmp/data'",
    "SELECT pg_catalog.version() FROM analytics.sales",
    "SELECT quantity::regclass FROM analytics.sales",
    "SELECT * FROM other.analytics.sales",
    "SELECT (SELECT password FROM public.users) FROM analytics.sales",
    "SELECT * FROM analytics.sales UNION SELECT * FROM analytics.sales",
    "SELECT pg_read_file('/etc/passwd') FROM analytics.sales",
])
def test_blocked(sql):
    with pytest.raises(UnsafeSQL):
        validate_sql(sql)
