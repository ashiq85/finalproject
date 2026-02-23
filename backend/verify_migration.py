import sys
import os
from sqlalchemy import text

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import engine, Base
from app.db.models import User

def verify_migration():
    print("🔄 Testing PostgreSQL Connection...")
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Connected to: {version}")
            
        print("\n🔄 Verifying Table Creation...")
        # Create tables
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created successfully")
        
        # Check tables
        with engine.connect() as connection:
            result = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ Found tables: {', '.join(tables)}")
            
            # Verify specific tables exist
            required_tables = ['users', 'patients', 'appointments', 'medical_records']
            missing = [t for t in required_tables if t not in tables]
            
            if missing:
                print(f"❌ Missing tables: {missing}")
            else:
                print("✅ All core tables present")
                
        print("\n✨ Migration Verification Complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nPossible solutions:")
        print("1. Make sure PostgreSQL is installed and running")
        print("2. Create the database 'agenthealth' if it doesn't exist")
        print("3. Check your credentials in .env file")
        return False

if __name__ == "__main__":
    verify_migration()
