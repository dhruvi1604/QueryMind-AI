import pymysql
from config.settings import DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME

connection = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    port=int(DB_PORT)
)

cursor = connection.cursor()
cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
cursor.execute(f"USE {DB_NAME}")

# Drop existing tables to start fresh
cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
cursor.execute("DROP TABLE IF EXISTS order_items")
cursor.execute("DROP TABLE IF EXISTS orders")
cursor.execute("DROP TABLE IF EXISTS products")
cursor.execute("DROP TABLE IF EXISTS customers")
cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

# Create tables
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

# 50 customers
customers = [
    ("Aman Sharma", "aman@email.com", "Mumbai", "Maharashtra", "2023-01-15", "Premium"),
    ("Priya Singh", "priya@email.com", "Delhi", "Delhi", "2023-02-20", "Regular"),
    ("Rahul Verma", "rahul@email.com", "Bangalore", "Karnataka", "2023-03-10", "Premium"),
    ("Nandini Gupta", "nandini@email.com", "Mumbai", "Maharashtra", "2023-04-05", "Regular"),
    ("Divyansh Patel", "divyansh@email.com", "Pune", "Maharashtra", "2023-05-18", "Premium"),
    ("Sneha Joshi", "sneha@email.com", "Delhi", "Delhi", "2023-06-22", "Regular"),
    ("Karan Mehta", "karan@email.com", "Hyderabad", "Telangana", "2023-07-30", "Premium"),
    ("Ananya Roy", "ananya@email.com", "Kolkata", "West Bengal", "2023-08-14", "Regular"),
    ("Vikram Das", "vikram@email.com", "Chennai", "Tamil Nadu", "2023-09-01", "Premium"),
    ("Pooja Mishra", "pooja@email.com", "Mumbai", "Maharashtra", "2023-10-25", "Regular"),
    ("Arjun Nair", "arjun@email.com", "Bangalore", "Karnataka", "2023-11-10", "Premium"),
    ("Kavya Reddy", "kavya@email.com", "Hyderabad", "Telangana", "2023-12-05", "Regular"),
    ("Rohan Kapoor", "rohan@email.com", "Delhi", "Delhi", "2024-01-08", "Premium"),
    ("Meera Iyer", "meera@email.com", "Chennai", "Tamil Nadu", "2024-01-20", "Regular"),
    ("Aditya Shah", "aditya@email.com", "Pune", "Maharashtra", "2024-02-14", "Premium"),
    ("Shreya Pillai", "shreya@email.com", "Mumbai", "Maharashtra", "2024-02-28", "Regular"),
    ("Nikhil Bose", "nikhil@email.com", "Kolkata", "West Bengal", "2024-03-15", "Premium"),
    ("Riya Choudhary", "riya@email.com", "Jaipur", "Rajasthan", "2024-03-22", "Regular"),
    ("Varun Malhotra", "varun@email.com", "Delhi", "Delhi", "2024-04-10", "Premium"),
    ("Tanvi Saxena", "tanvi@email.com", "Lucknow", "Uttar Pradesh", "2024-04-18", "Regular"),
    ("Harsh Agarwal", "harsh@email.com", "Mumbai", "Maharashtra", "2024-05-05", "Premium"),
    ("Ishaan Trivedi", "ishaan@email.com", "Ahmedabad", "Gujarat", "2024-05-20", "Regular"),
    ("Diya Menon", "diya@email.com", "Bangalore", "Karnataka", "2024-06-08", "Premium"),
    ("Siddharth Rao", "siddharth@email.com", "Hyderabad", "Telangana", "2024-06-25", "Regular"),
    ("Bhavna Tiwari", "bhavna@email.com", "Bhopal", "Madhya Pradesh", "2024-07-12", "Regular"),
    ("Yash Pandey", "yash@email.com", "Varanasi", "Uttar Pradesh", "2024-07-28", "Regular"),
    ("Kritika Bajaj", "kritika@email.com", "Delhi", "Delhi", "2024-08-10", "Premium"),
    ("Manish Oberoi", "manish@email.com", "Mumbai", "Maharashtra", "2024-08-22", "Premium"),
    ("Swati Kulkarni", "swati@email.com", "Pune", "Maharashtra", "2024-09-05", "Regular"),
    ("Rajesh Nambiar", "rajesh@email.com", "Chennai", "Tamil Nadu", "2024-09-18", "Regular"),
    ("Preeti Ghosh", "preeti@email.com", "Kolkata", "West Bengal", "2024-10-02", "Premium"),
    ("Akash Srivastava", "akash@email.com", "Lucknow", "Uttar Pradesh", "2024-10-15", "Regular"),
    ("Neha Desai", "neha@email.com", "Ahmedabad", "Gujarat", "2024-10-28", "Premium"),
    ("Kunal Jain", "kunal@email.com", "Jaipur", "Rajasthan", "2024-11-10", "Regular"),
    ("Anjali Bhatt", "anjali@email.com", "Mumbai", "Maharashtra", "2024-11-22", "Premium"),
    ("Sameer Wadia", "sameer@email.com", "Delhi", "Delhi", "2024-12-05", "Regular"),
    ("Pallavi Hegde", "pallavi@email.com", "Bangalore", "Karnataka", "2024-12-18", "Premium"),
    ("Deepak Chauhan", "deepak@email.com", "Delhi", "Delhi", "2023-03-12", "Regular"),
    ("Sunita Yadav", "sunita@email.com", "Agra", "Uttar Pradesh", "2023-05-30", "Regular"),
    ("Gautam Chandra", "gautam@email.com", "Bangalore", "Karnataka", "2023-08-08", "Premium"),
    ("Lakshmi Venkat", "lakshmi@email.com", "Chennai", "Tamil Nadu", "2023-09-25", "Regular"),
    ("Mohit Bansal", "mohit@email.com", "Chandigarh", "Punjab", "2023-11-15", "Regular"),
    ("Shweta Thakur", "shweta@email.com", "Mumbai", "Maharashtra", "2024-01-05", "Premium"),
    ("Abhinav Misra", "abhinav@email.com", "Patna", "Bihar", "2024-03-28", "Regular"),
    ("Ramya Krishnan", "ramya@email.com", "Hyderabad", "Telangana", "2024-05-15", "Premium"),
    ("Tarun Bhardwaj", "tarun@email.com", "Delhi", "Delhi", "2024-07-04", "Regular"),
    ("Chitra Suresh", "chitra@email.com", "Chennai", "Tamil Nadu", "2024-08-30", "Regular"),
    ("Vivek Anand", "vivek@email.com", "Pune", "Maharashtra", "2024-10-10", "Premium"),
    ("Nisha Rawat", "nisha@email.com", "Dehradun", "Uttarakhand", "2024-11-28", "Regular"),
    ("Pranav Sethi", "pranav@email.com", "Mumbai", "Maharashtra", "2024-12-20", "Premium"),
]

# 20 products
products = [
    ("iPhone 15", "Electronics", "Apple", 79999.00, 50, 4.8),
    ("Samsung Galaxy S24", "Electronics", "Samsung", 74999.00, 45, 4.7),
    ("Sony 55inch 4K TV", "Electronics", "Sony", 55999.00, 30, 4.6),
    ("boAt Smartwatch", "Electronics", "boAt", 4999.00, 120, 4.3),
    ("Sony WH-1000XM5", "Electronics", "Sony", 24999.00, 75, 4.9),
    ("Nike Air Max 270", "Footwear", "Nike", 8999.00, 100, 4.5),
    ("Adidas Ultraboost", "Footwear", "Adidas", 12999.00, 80, 4.6),
    ("Puma Running Shoes", "Footwear", "Puma", 5999.00, 150, 4.2),
    ("Levi's 511 Jeans", "Clothing", "Levi's", 3499.00, 200, 4.4),
    ("Adidas Track Suit", "Clothing", "Adidas", 4999.00, 120, 4.3),
    ("Allen Solly Shirt", "Clothing", "Allen Solly", 1999.00, 300, 4.1),
    ("Whirlpool Washing Machine", "Appliances", "Whirlpool", 32999.00, 20, 4.5),
    ("LG Refrigerator", "Appliances", "LG", 45999.00, 15, 4.7),
    ("Prestige Induction", "Kitchen", "Prestige", 3499.00, 100, 4.4),
    ("Instant Pot", "Kitchen", "Instant Pot", 8999.00, 60, 4.6),
    ("Himalaya Face Wash", "Beauty", "Himalaya", 299.00, 500, 4.2),
    ("Lakme Lipstick Set", "Beauty", "Lakme", 899.00, 400, 4.3),
    ("Yoga Mat Premium", "Sports", "Decathlon", 1499.00, 200, 4.5),
    ("Protein Whey 2kg", "Sports", "MuscleBlaze", 2999.00, 150, 4.6),
    ("Harry Potter Box Set", "Books", "Bloomsbury", 2499.00, 80, 4.9),
]

# 150 orders with varied dates and statuses
import random
from datetime import date, timedelta

random.seed(42)

orders = []
order_items = []

statuses = ["delivered", "delivered", "delivered", "pending", "cancelled"]
payment_methods = ["Credit Card", "UPI", "Debit Card", "Net Banking", "COD"]

order_id = 1
item_id = 1

for customer_id in range(1, 51):
    num_orders = random.randint(2, 5)
    for _ in range(num_orders):
        days_ago = random.randint(1, 365)
        order_date = date(2024, 1, 1) + timedelta(days=random.randint(0, 364))
        status = random.choice(statuses)
        payment = random.choice(payment_methods)

        num_items = random.randint(1, 3)
        total = 0
        items_for_order = []

        for _ in range(num_items):
            product_id = random.randint(1, 20)
            quantity = random.randint(1, 3)
            # Get product price
            price_map = {
                1: 79999, 2: 74999, 3: 55999, 4: 4999, 5: 24999,
                6: 8999, 7: 12999, 8: 5999, 9: 3499, 10: 4999,
                11: 1999, 12: 32999, 13: 45999, 14: 3499, 15: 8999,
                16: 299, 17: 899, 18: 1499, 19: 2999, 20: 2499
            }
            unit_price = price_map[product_id]
            total += unit_price * quantity
            items_for_order.append((order_id, product_id, quantity, unit_price))

        orders.append((customer_id, order_date, status, payment, total))
        order_items.extend(items_for_order)
        order_id += 1

cursor.executemany("""
    INSERT INTO customers (name, email, city, state, joined_date, customer_segment)
    VALUES (%s, %s, %s, %s, %s, %s)
""", customers)

cursor.executemany("""
    INSERT INTO products (name, category, brand, price, stock, rating)
    VALUES (%s, %s, %s, %s, %s, %s)
""", products)

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

print("✅ Rich ecommerce database created!")
print(f"✅ 50 customers")
print(f"✅ 20 products")
print(f"✅ {len(orders)} orders")
print(f"✅ {len(order_items)} order items")