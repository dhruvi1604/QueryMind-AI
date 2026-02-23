from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from config.settings import DATABASE_URL

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# LangChain SQLDatabase wrapper
db = SQLDatabase.from_uri(DATABASE_URL)

def get_schema() -> str:
    """Returns the database schema for prompt context"""
    return db.get_table_info()

def run_query(sql: str):
    """Executes a SQL query and returns results"""
    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = result.fetchall()
        columns = result.keys()
        return columns, rows

def test_connection():
    """Test if DB connection is working"""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✅ Database connected successfully!")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
    print("\n📋 Schema:")
    print(get_schema())