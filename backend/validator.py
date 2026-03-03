import re
import sqlglot
from sqlglot import exp

MAX_LIMIT = 1000


# --------------------------------------------------
# CLEAN LLM OUTPUT
# --------------------------------------------------

def clean_sql(sql: str) -> str:
    """
    Extract only SQL from LLM output.
    Removes markdown, explanations, etc.
    """
    sql = re.sub(r"```sql", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"```", "", sql)

    match = re.search(r"(SELECT\s.+)", sql, re.IGNORECASE | re.DOTALL)
    if match:
        sql = match.group(1)

    return sql.strip()


# --------------------------------------------------
# VALIDATE SQL USING AST PARSING
# --------------------------------------------------

def is_safe_query(sql: str) -> tuple[bool, str]:
    """
    Validates SQL using sqlglot AST parsing.
    Only allows a single SELECT statement.
    Blocks DDL/DML operations structurally.
    """

    try:
        parsed = sqlglot.parse_one(sql)

        # Must be SELECT
        if not isinstance(parsed, exp.Select):
            return False, "❌ Only SELECT queries are allowed"

        # Disallow dangerous operations anywhere in AST
        forbidden_nodes = (
            exp.Delete,
            exp.Update,
            exp.Insert,
            exp.Drop,
            exp.Alter,
            exp.Create,
            exp.Truncate,
        )

        for node in parsed.walk():
            if isinstance(node, forbidden_nodes):
                return False, "❌ Dangerous SQL operation detected"

        return True, "✅ Query is safe"

    except Exception as e:
        return False, f"❌ Invalid SQL syntax: {str(e)}"


# --------------------------------------------------
# ENFORCE LIMIT (Auto Guardrail)
# --------------------------------------------------

def enforce_limit(sql: str, max_limit: int = MAX_LIMIT) -> str:
    """
    Ensures every query has a LIMIT clause.
    Injects LIMIT if missing.
    """

    try:
        parsed = sqlglot.parse_one(sql)

        # Only modify SELECT queries
        if isinstance(parsed, exp.Select):
            if not parsed.args.get("limit"):
                parsed.set(
                    "limit",
                    exp.Limit(this=exp.Literal.number(max_limit))
                )

        return parsed.sql()

    except Exception:
        return sql  # fallback safely