import pymysql
import random
from faker import Faker
from datetime import datetime, timedelta
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

fake = Faker()

# --------------------------------------------------
# CONNECT
# --------------------------------------------------
connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    port=int(DB_PORT)
)

cursor = connection.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")

# --------------------------------------------------
# DROP OLD TABLES
# --------------------------------------------------
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
cursor.execute("DROP TABLE IF EXISTS order_items")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

# --------------------------------------------------
# CREATE TABLES
# --------------------------------------------------
cursor.execute("""
CREATE TABLE customers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(100),
    state VARCHAR(100),
    joined_date DATE,
    customer_segment VARCHAR(50)
)
""")

cursor.execute("""
CREATE TABLE products (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    category VARCHAR(100),
    brand VARCHAR(100),
    price DECIMAL(10,2),
    stock INT,
    rating DECIMAL(3,2)
)
""")

cursor.execute("""
CREATE TABLE orders (
    id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT,
    order_date DATE,
    status VARCHAR(50),
    payment_method VARCHAR(50),
    total_amount DECIMAL(10,2),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
)
""")

cursor.execute("""
CREATE TABLE order_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
""")

# --------------------------------------------------
# GENERATE CUSTOMERS (5K)
# --------------------------------------------------
print("Generating customers...")

customers = []
for _ in range(5000):
    customers.append((
        fake.name(),
        fake.email(),
        fake.city(),
        fake.state(),
        fake.date_between(start_date="-3y", end_date="today"),
        random.choice(["Premium", "Regular"])
    ))

cursor.executemany("""
INSERT INTO customers (name, email, city, state, joined_date, customer_segment)
VALUES (%s, %s, %s, %s, %s, %s)
""", customers)

# --------------------------------------------------
# GENERATE PRODUCTS (1000)
# --------------------------------------------------
print("Generating products...")

categories = ["Electronics", "Clothing", "Sports", "Beauty", "Books", "Kitchen"]

products = []
for _ in range(1000):
    price = round(random.uniform(100, 50000), 2)
    products.append((
        fake.word().capitalize() + " " + fake.word().capitalize(),
        random.choice(categories),
        fake.company(),
        price,
        random.randint(10, 500),
        round(random.uniform(3.0, 5.0), 1)
    ))

cursor.executemany("""
INSERT INTO products (name, category, brand, price, stock, rating)
VALUES (%s, %s, %s, %s, %s, %s)
""", products)

# --------------------------------------------------
# GENERATE ORDERS (~30K)
# --------------------------------------------------
print("Generating orders...")

statuses = ["delivered", "delivered", "pending", "cancelled"]
payment_methods = ["Credit Card", "UPI", "Debit Card", "Net Banking", "COD"]

orders = []
order_items = []

order_id = 1

for _ in range(30000):
    customer_id = random.randint(1, 5000)
    order_date = fake.date_between(start_date="-1y", end_date="today")
    status = random.choice(statuses)
    payment = random.choice(payment_methods)

    num_items = random.randint(1, 3)
    total = 0
    items_for_order = []

    for _ in range(num_items):
        product_id = random.randint(1, 1000)
        quantity = random.randint(1, 5)
        price = random.uniform(100, 50000)
        total += price * quantity

        items_for_order.append((
            order_id,
            product_id,
            quantity,
            round(price, 2)
        ))

    orders.append((
        customer_id,
        order_date,
        status,
        payment,
        round(total, 2)
    ))

    order_items.extend(items_for_order)
    order_id += 1

cursor.executemany("""
INSERT INTO orders (customer_id, order_date, status, payment_method, total_amount)
VALUES (%s, %s, %s, %s, %s)
""", orders)

cursor.executemany("""
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
VALUES (%s, %s, %s, %s)
""", order_items)

connection.commit()
cursor.close()
connection.close()

print("✅ Database created successfully!")
print("Customers:", len(customers))
print("Products:", len(products))
print("Orders:", len(orders))
print("Order Items:", len(order_items))