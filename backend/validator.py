import re

# Dangerous SQL keywords that should never be executed
DANGEROUS_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "INSERT",
    "UPDATE", "REPLACE", "CREATE", "GRANT", "REVOKE",
    "EXEC", "EXECUTE", "xp_", "--", ";"
]

def is_safe_query(sql: str) -> tuple[bool, str]:
    """
    Validates SQL query for safety.
    Returns (is_safe, reason)
    """
    sql_upper = sql.upper()

    # Check for dangerous keywords
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            return False, f"❌ Dangerous keyword detected: '{keyword}'"

    # Must be a SELECT statement only
    stripped = sql.strip().upper()
    if not stripped.startswith("SELECT"):
        return False, "❌ Only SELECT queries are allowed"

    # Check for multiple statements
    if sql.count(";") > 1:
        return False, "❌ Multiple statements are not allowed"

    return True, "✅ Query is safe"


def clean_sql(sql: str) -> str:
    """
    Cleans LLM output to extract only the SQL query.
    LLMs sometimes add markdown like ```sql ... ```
    """
    # Remove markdown code blocks
    sql = re.sub(r"```sql", "", sql)
    sql = re.sub(r"```", "", sql)

    # Remove any explanation before SELECT
    match = re.search(r"(SELECT\s.+)", sql, re.IGNORECASE | re.DOTALL)
    if match:
        sql = match.group(1)

    return sql.strip()


if __name__ == "__main__":
    # Test the validator
    test_queries = [
        "SELECT * FROM grades",
        "DROP TABLE grades",
        "SELECT * FROM students; DROP TABLE students",
        "DELETE FROM grades WHERE id = 1",
        "SELECT name, score FROM grades WHERE grade = 'A'",
    ]

    print("🔍 Testing Validator:\n")
    for query in test_queries:
        safe, reason = is_safe_query(query)
        print(f"Query: {query}")
        print(f"Result: {reason}\n")