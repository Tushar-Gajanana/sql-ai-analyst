import os
import psycopg
import pytest
from analyst.db import query

URL = os.getenv("TEST_DATABASE_URL")
pytestmark = [pytest.mark.integration, pytest.mark.skipif(not URL, reason="Set TEST_DATABASE_URL")]


def test_known_data():
    result = query(URL, "SELECT COUNT(*) AS n FROM analytics.sales")
    assert result["rows"] == [(1080,)]
    assert not result["truncated"]


def test_row_cap():
    result = query(URL, "SELECT * FROM analytics.sales ORDER BY sale_id")
    assert len(result["rows"]) == 200
    assert result["truncated"]


def test_database_denies_write_even_without_guard():
    with psycopg.connect(URL) as conn:
        with pytest.raises(psycopg.Error):
            conn.execute("DELETE FROM analytics.sales")


def test_role_is_not_owner():
    with psycopg.connect(URL) as conn:
        assert conn.execute("SELECT rolsuper, rolcreaterole, rolbypassrls FROM pg_roles WHERE rolname = current_user").fetchone() == (False, False, False)
