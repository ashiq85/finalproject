import sys
import os
sys.path.append(os.getcwd())

from app.db.base import engine
from sqlalchemy import text, inspect

def fix_schema():
    print("Checking schema...")
    try:
        inspector = inspect(engine)
        columns = [c['name'] for c in inspector.get_columns('patients')]
        print(f"Current columns in patients: {columns}")
        
        if 'medical_id' not in columns:
            print("Adding missing 'medical_id' column...")
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE patients ADD COLUMN medical_id VARCHAR"))
                conn.execute(text("CREATE UNIQUE INDEX ix_patients_medical_id ON patients (medical_id)"))
                conn.commit()
            print("✅ 'medical_id' column added successfully!")
        else:
            print("✅ 'medical_id' column already exists.")
            
        if 'primary_doctor_id' not in columns:
             print("Adding missing 'primary_doctor_id' column...")
             with engine.connect() as conn:
                 conn.execute(text("ALTER TABLE patients ADD COLUMN primary_doctor_id INTEGER REFERENCES users(id)"))
                 conn.commit()
             print("✅ 'primary_doctor_id' column added successfully!")

        print("Checking appointments table...")
        columns_app = [c['name'] for c in inspector.get_columns('appointments')]
        print(f"Current columns in appointments: {columns_app}")
        
        missing_app = []
        if 'requested_new_date' not in columns_app:
            missing_app.append("ALTER TABLE appointments ADD COLUMN requested_new_date TIMESTAMP")
        if 'is_follow_up' not in columns_app:
            missing_app.append("ALTER TABLE appointments ADD COLUMN is_follow_up BOOLEAN DEFAULT FALSE")
        if 'parent_appointment_id' not in columns_app:
            missing_app.append("ALTER TABLE appointments ADD COLUMN parent_appointment_id INTEGER REFERENCES appointments(id)")
            
        if missing_app:
            print(f"Adding {len(missing_app)} missing columns to appointments...")
            with engine.connect() as conn:
                for stmt in missing_app:
                    print(f"Executing: {stmt}")
                    conn.execute(text(stmt))
                conn.commit()
            print("✅ Missing columns added to appointments!")
        else:
            print("✅ No missing columns in appointments.")
        
    except Exception as e:
        print(f"❌ Error fixing schema: {e}")

if __name__ == "__main__":
    fix_schema()
