import sys
import os

# Add the current directory to sys.path to allow importing from the 'app' package
sys.path.append(os.getcwd())

from app.db.base import engine
from sqlalchemy import text

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            row = result.fetchone()
            print(f"✅ Successfully connected to PostgreSQL!")
            print(f"Database version: {row[0]}")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL.")
        print(f"Error: {e}")

if __name__ == "__main__":
    test_connection()
