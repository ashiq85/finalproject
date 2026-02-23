import sys
import os

# Add the current directory to sys.path to allow importing from the 'app' package
sys.path.append(os.getcwd())

from app.db.base import Base, engine, SessionLocal
from app.db.init_db import init_db
from sqlalchemy import text

def refresh_db():
    try:
        print("🔄 Refreshing database schema...")
        # Drop all tables and recreate them to ensure new columns are added
        # (This is acceptable in a fresh development environment)
        Base.metadata.drop_all(bind=engine)
        print("✅ Tables dropped.")
        
        init_db()
        print("✅ Database initialized with new schema and default users.")
        
    except Exception as e:
        print(f"❌ Failed to refresh database.")
        print(f"Error: {e}")

if __name__ == "__main__":
    refresh_db()
