from langchain_core.prompts import ChatPromptTemplate

# Business rules context
BUSINESS_CONTEXT = """
Business Rules:
- 'revenue' means SUM(total_amount) from orders where status = 'delivered'
- 'pending orders' means orders where status = 'pending'
- 'cancelled orders' means orders where status = 'cancelled'
- 'delivered orders' means orders where status = 'delivered'
- 'top customers' means customers with highest SUM(total_amount) in delivered orders
- 'premium customers' means customers where customer_segment = 'Premium'
- 'regular customers' means customers where customer_segment = 'Regular'
- 'best selling product' means product with highest SUM(quantity) in order_items
- 'average order value' means AVG(total_amount) from orders
- 'low stock' means products where stock < 30
- 'top rated products' means products with rating >= 4.5
- 'most popular category' means category with highest COUNT of orders
- 'most popular payment method' means payment_method with highest COUNT in orders
"""

# Few shot examples
FEW_SHOT_EXAMPLES = """
Example 1:
Question: What is the total revenue?
SQL: SELECT SUM(total_amount) as total_revenue FROM orders WHERE status = 'delivered'

Example 2:
Question: Show me top 5 customers by spending
SQL: SELECT c.name, c.city, SUM(o.total_amount) as total_spent FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status = 'delivered' GROUP BY c.id, c.name, c.city ORDER BY total_spent DESC LIMIT 5

Example 3:
Question: Which product is selling the most?
SQL: SELECT p.name, p.category, SUM(oi.quantity) as total_sold FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.id, p.name, p.category ORDER BY total_sold DESC LIMIT 1

Example 4:
Question: Show me all pending orders
SQL: SELECT o.id, c.name, c.city, o.order_date, o.total_amount, o.payment_method FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'pending' ORDER BY o.order_date DESC

Example 5:
Question: What is the revenue by category?
SQL: SELECT p.category, SUM(o.total_amount) as revenue FROM orders o JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id WHERE o.status = 'delivered' GROUP BY p.category ORDER BY revenue DESC

Example 6:
Question: Show me premium customers
SQL: SELECT name, city, state, joined_date FROM customers WHERE customer_segment = 'Premium' ORDER BY joined_date DESC

Example 7:
Question: What is the most popular payment method?
SQL: SELECT payment_method, COUNT(*) as total_orders FROM orders GROUP BY payment_method ORDER BY total_orders DESC

Example 8:
Question: Show me top rated products
SQL: SELECT name, category, brand, rating, price FROM products WHERE rating >= 4.5 ORDER BY rating DESC

Example 9:
Question: Find second highest spending customer
SQL: SELECT name, city, total_spent FROM (SELECT c.name, c.city, SUM(o.total_amount) as total_spent, DENSE_RANK() OVER (ORDER BY SUM(o.total_amount) DESC) as rnk FROM customers c JOIN orders o ON c.id = o.customer_id WHERE o.status = 'delivered' GROUP BY c.id, c.name, c.city) t WHERE rnk = 2

Example 10:
Question: Show me orders above average order value
SQL: SELECT o.id, c.name, c.city, o.total_amount, o.order_date, o.payment_method FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.total_amount > (SELECT AVG(total_amount) FROM orders) ORDER BY o.total_amount DESC

Example 11:
Question: Running total revenue by month
SQL: SELECT order_month, monthly_revenue, SUM(monthly_revenue) OVER (ORDER BY order_month) as running_total FROM (SELECT DATE_FORMAT(order_date, '%Y-%m') as order_month, SUM(total_amount) as monthly_revenue FROM orders WHERE status = 'delivered' GROUP BY order_month) t ORDER BY order_month
"""

sql_prompt = ChatPromptTemplate.from_template("""
You are a senior SQL expert working with a MySQL ecommerce database.
Your job is to convert natural language questions into correct MySQL queries.

{business_context}

Database Schema:
{schema}

Past Successful Query Examples (from memory):
{rag_examples}

Additional Examples:
{examples}

STRICT MySQL Rules:
1. Use ONLY the tables and columns that exist in the schema above
2. Return ONLY the SQL query, nothing else — no explanations, no markdown, no backticks
3. Always use proper MySQL syntax
4. Always use proper JOINs when data from multiple tables is needed
5. NEVER use 'rank' as a column alias — it is a reserved keyword in MySQL. Use 'rnk' or 'ranking' instead
6. NEVER use 'row_number', 'dense_rank', 'percent_rank' as column aliases — use 'row_num', 'rnk', 'pct_rnk'
7. When using window functions in subqueries, always wrap in an outer SELECT and reference the safe alias
8. NEVER use reserved words as aliases: rank, row, key, value, name, index, select, from, where, order, group
9. For ranking patterns always follow this structure:
   SELECT cols FROM (SELECT cols, DENSE_RANK() OVER (...) as rnk FROM ...) t WHERE rnk = N
10. Always test mentally that column aliases in subqueries are not MySQL reserved words before writing

Question: {question}

SQL Query:
""")


def get_prompt_inputs(schema: str, question: str, rag_examples: str = "") -> dict:
    return {
        "business_context": BUSINESS_CONTEXT,
        "schema": schema,
        "examples": FEW_SHOT_EXAMPLES,
        "rag_examples": rag_examples if rag_examples else "No past examples yet.",
        "question": question
    }