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

Rules:
- Use ONLY the tables and columns that exist in the schema above
- Do NOT use tables or columns that are not in the schema
- Return ONLY the SQL query, nothing else
- No explanations, no markdown, no backticks
- Always use proper MySQL syntax
- Always use proper JOINs when data from multiple tables is needed

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