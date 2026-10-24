import sqlglot
from sqlglot import exp
from analyst.schema import TABLES


class UnsafeSQL(ValueError):
    pass


# Deliberately narrow analytic subset; expand only with security tests.
FUNCTIONS = {"COUNT", "SUM", "AVG", "MIN", "MAX", "ROUND", "COALESCE",
             "NULLIF", "DATE_TRUNC", "TIMESTAMP_TRUNC", "EXTRACT", "CAST",
             "LOWER", "UPPER", "ABS"}


def validate_sql(sql: str) -> str:
    if len(sql) > 12000:
        raise UnsafeSQL("SQL is too long.")
    try:
        statements = sqlglot.parse(sql, read="postgres")
    except sqlglot.errors.ParseError as exc:
        raise UnsafeSQL("SQL could not be parsed.") from exc
    if len(statements) != 1 or not isinstance(statements[0], exp.Select):
        raise UnsafeSQL("Only one SELECT is supported.")
    tree = statements[0]
    # Reject writable CTEs, locking, SELECT INTO and special SQL forms.
    blocked = (exp.DDL, exp.DML, exp.Into, exp.Lock, exp.Command, exp.With)
    if any(isinstance(node, blocked) for node in tree.walk()):
        raise UnsafeSQL("Unsupported SQL operation.")
    tables = list(tree.find_all(exp.Table))
    if not tables:
        raise UnsafeSQL("A permitted analytics table is required.")
    for table in tables:
        if (table.catalog or table.db != "analytics" or table.name not in TABLES
                or not isinstance(table.this, exp.Identifier)):
            raise UnsafeSQL("Only approved analytics tables are allowed.")
    for node in tree.find_all(exp.Func):
        if isinstance(node, exp.Anonymous) or node.sql_name() not in FUNCTIONS:
            raise UnsafeSQL("Unsupported SQL function.")
    # No schema-qualified functions, custom operators or custom casts.
    if any(isinstance(node, (exp.Dot, exp.Operator)) for node in tree.walk()):
        raise UnsafeSQL("Unsupported expression.")
    for cast in tree.find_all(exp.Cast):
        if cast.to.this not in {exp.DataType.Type.INT, exp.DataType.Type.BIGINT,
                               exp.DataType.Type.DECIMAL, exp.DataType.Type.DOUBLE,
                               exp.DataType.Type.TEXT, exp.DataType.Type.DATE,
                               exp.DataType.Type.TIMESTAMP}:
            raise UnsafeSQL("Unsupported cast.")
    # Outer cap cannot be overridden by a model's LIMIT or OFFSET.
    return f"SELECT * FROM ({tree.sql(dialect='postgres')}) AS bounded_result LIMIT 201"
