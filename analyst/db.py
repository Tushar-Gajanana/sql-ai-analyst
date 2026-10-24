import psycopg
from analyst.guard import validate_sql


def query(database_url: str, proposed_sql: str) -> dict:
    safe_sql = validate_sql(proposed_sql)
    with psycopg.connect(database_url, connect_timeout=10) as conn:
        with conn.transaction():
            conn.execute("SET TRANSACTION READ ONLY")
            conn.execute("SET LOCAL statement_timeout = '5000ms'")
            conn.execute("SET LOCAL lock_timeout = '1000ms'")
            conn.execute("SET LOCAL search_path = pg_catalog")
            with conn.cursor() as cur:
                cur.execute(safe_sql)
                columns = [d.name for d in cur.description]
                rows = cur.fetchmany(201)
    return {"columns": columns, "rows": rows[:200], "truncated": len(rows) > 200}
